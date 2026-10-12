"""Offline-only projection for synthetic JEV privacy validation.

Separate reviewed wording is required for free text. The bundle type and hazard
checks do not prove human review or privacy; future host review and consent remain
separate requirements. This module never dispatches or persists a request.
"""

# @codebase_provenance_JEO
# @codebase_rights_JEO

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import hmac
import json
import re
from typing import Any

from ...domain.adaptive.jev_adjudication import (
    JevAdjudicationEligibilityError,
    JevCandidateBinding,
    JevChoiceAnswer,
    JevNoulAnswer,
    JevProviderResponse,
    OrchestraJevAdjudicationState,
    OrchestraJevQuestionBuilder,
    TYPESAFE_JEV_MODEL,
    validate_jev_adjudication_eligibility,
)
from ...shared.canonicalization import canonical_json_bytes


JEV_PROVIDER_PROJECTION_CONTRACT = "orchestra.jev.provider_projection.v1"

# Keep this snapshot aligned with machine/specialists/registry.v1.json.
_KNOWN_PRODUCERS = frozenset(
    {
        "arbiter",
        "cipher",
        "cloak",
        "clockwork",
        "conductor",
        "chronicler",
        "dagger",
        "overseer",
        "ponytail",
        "scribe",
        "the-governor",
        "the-steward",
        "the-tuner",
        "weaver",
    }
)
_FINDING_STATUSES = frozenset({"VERIFIED", "UNVERIFIED"})
_VERIFICATION_RESULTS = frozenset(
    {"CONFIRMED", "INCOMPLETE", "NOT_STARTED", "PENDING", "RUNNING"}
)
_ALIAS_PREFIXES = {
    "finding": "F",
    "verification": "V",
    "mitigation": "M",
    "dissent": "D",
    "producer": "P",
}
_ERROR_CODES = frozenset(
    {
        "ALIAS_COLLISION",
        "INVALID_INPUT",
        "INVALID_MAPPING_CONTEXT",
        "INVALID_NONCE",
        "INVALID_SOURCE_STATE",
        "INVALID_SOURCE_VALUE",
        "REQUEST_MISMATCH",
        "REVIEWED_TEXT_INCOMPLETE",
        "REVIEWED_TEXT_REQUIRED",
        "REVIEWED_TEXT_UNBOUND",
        "RESPONSE_CONTRACT_INCOMPATIBLE",
        "SOURCE_STATE_INELIGIBLE",
        "SOURCE_STATE_MISMATCH",
        "UNSAFE_REVIEWED_TEXT",
        "UNKNOWN_PRODUCER",
    }
)
_UNSAFE_TEXT_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE | re.MULTILINE)
    for pattern in (
        r"https?://\S+",
        r"\bwww\.\S+",
        r"\b[A-Z]:\\[^\s<>|]+",
        r"\\\\[A-Z0-9_.-]+\\[^\s<>|]+",
        r"/(?:home|Users|private|tmp)/[^\s<>|]+",
        r"(?:^|[\s(])(?:\./|\.\./)?(?:src|tests|docs|scripts|artifacts|\.git)/[^\s,;)]+",
        r"\b(?:api[_ -]?key|access[_ -]?token|password|secret|bearer)\s*[:=]\s*\S+",
        r"\bsk-[A-Z0-9_-]{12,}\b",
        r"\bAKIA[0-9A-Z]{16}\b",
        r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----",
        r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        r"^\s*diff --git ",
        r"^\s*Traceback \(most recent call last\):",
        r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]",
    )
)


@dataclass(frozen=True, slots=True, repr=False)
class ReviewedJevTextBundle:
    """Separate wording reviewed for one source scope; not a consent receipt."""

    source_scope_hash: str
    task_domain: str
    finding_summaries: Mapping[str, str]
    overseer_assessment: Mapping[str, str]
    mitigation_summaries: Mapping[str, str]
    mitigation_tradeoffs: Mapping[str, object]
    dissent_summaries: Mapping[str, str]


class JevProjectionMappingContext:
    """Transient local state; deliberately has no normal serializer or value repr."""

    __slots__ = (
        "_candidate_binding",
        "_source_scope_hash",
        "_request_digest",
        "_question_ids",
        "_mitigation_ids",
    )

    _candidate_binding: JevCandidateBinding
    _source_scope_hash: str
    _request_digest: str
    _question_ids: tuple[tuple[str, str], ...]
    _mitigation_ids: tuple[tuple[str, str], ...]

    def __init__(self) -> None:
        raise TypeError("projection mapping context is created by the local projection builder")

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("projection mapping context is immutable")

    def __repr__(self) -> str:
        return "JevProjectionMappingContext(<transient>)"

    def __reduce__(self) -> object:
        raise TypeError("projection mapping context is transient")


class JevProjectionError(ValueError):
    """A sanitized projection failure that never includes rejected source text."""

    def __init__(self, code: str) -> None:
        self.code = code if isinstance(code, str) and code in _ERROR_CODES else "INVALID_INPUT"
        super().__init__(self.code)


def _fail(code: str) -> None:
    raise JevProjectionError(code)


def _alias(kind: str, value: str, nonce: bytes) -> str:
    prefix = _ALIAS_PREFIXES[kind]
    message = f"{JEV_PROVIDER_PROJECTION_CONTRACT}\0{kind}\0{value}".encode("utf-8")
    suffix = hmac.new(nonce, message, hashlib.sha256).hexdigest()[:32]
    return f"{prefix}-{suffix}"


def _aliases(kind: str, values: list[str], nonce: bytes) -> dict[str, str]:
    aliases: dict[str, str] = {}
    generated: set[str] = set()
    for value in values:
        if value in aliases:
            continue
        alias = _alias(kind, value, nonce)
        if alias in generated:
            _fail("ALIAS_COLLISION")
        aliases[value] = alias
        generated.add(alias)
    return aliases


def _safe_text(value: object, blocked_values: set[str]) -> str:
    if not isinstance(value, str) or not value.strip():
        _fail("REVIEWED_TEXT_INCOMPLETE")
    if any(pattern.search(value) for pattern in _UNSAFE_TEXT_PATTERNS):
        _fail("UNSAFE_REVIEWED_TEXT")
    folded = value.casefold()
    if any(blocked and blocked.casefold() in folded for blocked in blocked_values):
        _fail("UNSAFE_REVIEWED_TEXT")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        _fail("UNSAFE_REVIEWED_TEXT")
    return value


def _text_map(
    value: object,
    source_ids: list[str],
    blocked_values: set[str],
) -> dict[str, str]:
    if not isinstance(value, Mapping) or set(value) != set(source_ids):
        _fail("REVIEWED_TEXT_INCOMPLETE")
    return {
        source_id: _safe_text(value[source_id], blocked_values)
        for source_id in source_ids
    }


def _producer_value(value: object) -> str:
    if not isinstance(value, str) or value.casefold() not in _KNOWN_PRODUCERS:
        _fail("UNKNOWN_PRODUCER")
    return value.casefold()


def _blocked_source_values(source: Mapping[str, Any]) -> set[str]:
    blocked = {value for value in source["candidate"].values() if isinstance(value, str)}
    for section in ("findings", "verification", "mitigation_options", "dissent"):
        for record in source[section]:
            blocked.add(record["id"])
            if "producer" in record:
                blocked.add(record["producer"])
            for field in ("producers", "evidence_refs"):
                blocked.update(record.get(field, []))
    for option in source["mitigation_options"]:
        blocked.update(option["addresses"])
    for record in source["verification"]:
        blocked.add(record["finding_id"])
    return blocked


def _reviewed_text(
    bundle: ReviewedJevTextBundle,
    source: Mapping[str, Any],
    blocked_values: set[str],
) -> dict[str, Any]:
    finding_ids = [item["id"] for item in source["findings"]]
    mitigation_ids = [item["id"] for item in source["mitigation_options"]]
    dissent_ids = [item["id"] for item in source["dissent"]]
    overseer_fields = {"evidence_sufficiency", "impact", "residual_risk_context"}
    if not isinstance(bundle.source_scope_hash, str) or bundle.source_scope_hash != source["candidate"]["scope_hash"]:
        _fail("REVIEWED_TEXT_UNBOUND")
    if not isinstance(bundle.overseer_assessment, Mapping) or set(bundle.overseer_assessment) != overseer_fields:
        _fail("REVIEWED_TEXT_INCOMPLETE")
    overseer = {
        field: _safe_text(bundle.overseer_assessment[field], blocked_values)
        for field in ("evidence_sufficiency", "impact", "residual_risk_context")
    }
    if not isinstance(bundle.mitigation_tradeoffs, Mapping) or set(bundle.mitigation_tradeoffs) != set(
        mitigation_ids
    ):
        _fail("REVIEWED_TEXT_INCOMPLETE")
    tradeoffs: dict[str, list[str]] = {}
    source_tradeoffs = {
        item["id"]: item["tradeoffs"] for item in source["mitigation_options"]
    }
    for mitigation_id in mitigation_ids:
        items = bundle.mitigation_tradeoffs[mitigation_id]
        if (
            not isinstance(items, (list, tuple))
            or len(items) != len(source_tradeoffs[mitigation_id])
        ):
            _fail("REVIEWED_TEXT_INCOMPLETE")
        tradeoffs[mitigation_id] = [
            _safe_text(item, blocked_values) for item in items
        ]
    return {
        "task_domain": _safe_text(bundle.task_domain, blocked_values),
        "finding_summaries": _text_map(
            bundle.finding_summaries, finding_ids, blocked_values
        ),
        "overseer_assessment": overseer,
        "mitigation_summaries": _text_map(
            bundle.mitigation_summaries, mitigation_ids, blocked_values
        ),
        "mitigation_tradeoffs": tradeoffs,
        "dissent_summaries": _text_map(
            bundle.dissent_summaries, dissent_ids, blocked_values
        ),
    }


def _question_id_aliases(
    source_questions: Mapping[str, Mapping[str, Any]],
    mitigation_aliases: Mapping[str, str],
    projected_questions: Mapping[str, Mapping[str, Any]],
) -> tuple[tuple[str, str], ...]:
    aliases: dict[str, str] = {}
    dynamic_source_ids: set[str] = set()
    for source_id, alias in mitigation_aliases.items():
        for projected_id, original_id in (
            (f"evidence_supports_{alias}", f"evidence_supports_{source_id}"),
            (f"{alias}_introduces_scope_risk", f"{source_id}_introduces_scope_risk"),
            (f"{alias}_preserves_architecture", f"{source_id}_preserves_architecture"),
        ):
            if projected_id in aliases or original_id in dynamic_source_ids:
                _fail("INVALID_MAPPING_CONTEXT")
            aliases[projected_id] = original_id
            dynamic_source_ids.add(original_id)

    if not dynamic_source_ids.issubset(source_questions):
        _fail("INVALID_MAPPING_CONTEXT")
    for question_id in source_questions:
        if question_id not in dynamic_source_ids:
            if question_id in aliases:
                _fail("INVALID_MAPPING_CONTEXT")
            aliases[question_id] = question_id

    if (
        set(aliases) != set(projected_questions)
        or set(aliases.values()) != set(source_questions)
        or len(aliases.values()) != len(set(aliases.values()))
    ):
        _fail("INVALID_MAPPING_CONTEXT")
    return tuple(sorted(aliases.items()))


def _new_mapping_context(
    state: OrchestraJevAdjudicationState,
    request_bytes: bytes,
    question_ids: tuple[tuple[str, str], ...],
    mitigation_aliases: Mapping[str, str],
) -> JevProjectionMappingContext:
    context = object.__new__(JevProjectionMappingContext)
    object.__setattr__(context, "_candidate_binding", state.candidate_binding)
    object.__setattr__(context, "_source_scope_hash", state.candidate_binding.scope_hash)
    object.__setattr__(context, "_request_digest", hashlib.sha256(request_bytes).hexdigest())
    object.__setattr__(context, "_question_ids", question_ids)
    object.__setattr__(
        context,
        "_mitigation_ids",
        tuple(sorted((alias, source_id) for source_id, alias in mitigation_aliases.items())),
    )
    return context


def build_offline_jev_provider_projection_with_context(
    state: OrchestraJevAdjudicationState,
    reviewed_text: ReviewedJevTextBundle,
    *,
    nonce: str,
) -> tuple[bytes, JevProjectionMappingContext]:
    """Build local synthetic request bytes and their transient reverse-map context.

    The caller must supply fresh, separately reviewed wording. Reusing a nonce
    repeats aliases; neither aliases nor hazard checks prove privacy or consent.
    The context is local-only and must not be serialized, logged, or sent.
    """
    try:
        if not isinstance(state, OrchestraJevAdjudicationState):
            _fail("INVALID_SOURCE_STATE")
        if type(reviewed_text) is not ReviewedJevTextBundle:
            _fail("REVIEWED_TEXT_REQUIRED")
        if not isinstance(nonce, str) or not nonce:
            _fail("INVALID_NONCE")
        try:
            nonce_bytes = nonce.encode("utf-8")
        except UnicodeEncodeError:
            _fail("INVALID_NONCE")

        source = state.to_payload()
        if any(item["status"] not in _FINDING_STATUSES for item in source["findings"]):
            _fail("INVALID_SOURCE_VALUE")
        if any(item["result"] not in _VERIFICATION_RESULTS for item in source["verification"]):
            _fail("INVALID_SOURCE_VALUE")
        try:
            validate_jev_adjudication_eligibility(state)
        except (JevAdjudicationEligibilityError, TypeError, ValueError):
            _fail("SOURCE_STATE_INELIGIBLE")
        if not source["mitigation_options"]:
            _fail("SOURCE_STATE_INELIGIBLE")

        blocked_values = _blocked_source_values(source)
        reviewed = _reviewed_text(reviewed_text, source, blocked_values)
        producers = [
            _producer_value(record[field])
            for section in ("findings", "verification", "dissent")
            for record in source[section]
            for field in ("producer",)
        ]
        producers.extend(
            _producer_value(producer)
            for option in source["mitigation_options"]
            for producer in option["producers"]
        )
        producer_aliases = _aliases("producer", producers, nonce_bytes)
        finding_aliases = _aliases(
            "finding", [item["id"] for item in source["findings"]], nonce_bytes
        )
        verification_aliases = _aliases(
            "verification", [item["id"] for item in source["verification"]], nonce_bytes
        )
        mitigation_aliases = _aliases(
            "mitigation", [item["id"] for item in source["mitigation_options"]], nonce_bytes
        )
        dissent_aliases = _aliases(
            "dissent", [item["id"] for item in source["dissent"]], nonce_bytes
        )

        projected = OrchestraJevAdjudicationState.create(
            candidate={
                "repository": "offline/projection",
                "commit": "0" * 40,
                "tree": "1" * 40,
            },
            task={
                "domain": reviewed["task_domain"],
                "risk_level": source["task"]["risk_level"],
                "assurance_depth": source["task"]["assurance_depth"],
            },
            findings=[
                {
                    "id": finding_aliases[item["id"]],
                    "producer": producer_aliases[_producer_value(item["producer"])],
                    "status": item["status"],
                    "summary": reviewed["finding_summaries"][item["id"]],
                    "evidence_refs": [],
                }
                for item in source["findings"]
            ],
            verification=[
                {
                    "id": verification_aliases[item["id"]],
                    "producer": producer_aliases[_producer_value(item["producer"])],
                    "finding_id": finding_aliases[item["finding_id"]],
                    "result": item["result"],
                    "evidence_refs": [],
                }
                for item in source["verification"]
            ],
            overseer_assessment=reviewed["overseer_assessment"],
            mitigation_options=[
                {
                    "id": mitigation_aliases[item["id"]],
                    "producers": [
                        producer_aliases[_producer_value(producer)]
                        for producer in item["producers"]
                    ],
                    "summary": reviewed["mitigation_summaries"][item["id"]],
                    "addresses": [
                        finding_aliases[finding_id] for finding_id in item["addresses"]
                    ],
                    "tradeoffs": reviewed["mitigation_tradeoffs"][item["id"]],
                }
                for item in source["mitigation_options"]
            ],
            dissent=[
                {
                    "id": dissent_aliases[item["id"]],
                    "producer": producer_aliases[_producer_value(item["producer"])],
                    "summary": reviewed["dissent_summaries"][item["id"]],
                    "evidence_refs": [],
                }
                for item in source["dissent"]
            ],
            constraints=source["constraints"],
        )
        projected_payload = projected.to_payload()
        projected_payload.pop("candidate")
        projected_payload["contract"] = JEV_PROVIDER_PROJECTION_CONTRACT
        for section in ("findings", "verification", "dissent"):
            for record in projected_payload[section]:
                record.pop("evidence_refs")

        request = {
            "state": projected_payload,
            "model": TYPESAFE_JEV_MODEL,
            "questions": OrchestraJevQuestionBuilder().build(projected),
        }
        request_bytes = canonical_json_bytes(request)
        source_questions = OrchestraJevQuestionBuilder().build(state)
        question_ids = _question_id_aliases(
            source_questions,
            mitigation_aliases,
            request["questions"],
        )
        return request_bytes, _new_mapping_context(
            state,
            request_bytes,
            question_ids,
            mitigation_aliases,
        )
    except JevProjectionError:
        raise
    except Exception:
        raise JevProjectionError("INVALID_INPUT") from None


def build_offline_jev_provider_projection(
    state: OrchestraJevAdjudicationState,
    reviewed_text: ReviewedJevTextBundle,
    *,
    nonce: str,
) -> bytes:
    """Build the existing deterministic request-byte output without exposing context."""
    request_bytes, _ = build_offline_jev_provider_projection_with_context(
        state,
        reviewed_text,
        nonce=nonce,
    )
    return request_bytes


def reverse_map_offline_jev_provider_response(
    state: OrchestraJevAdjudicationState,
    request_bytes: bytes,
    mapping_context: JevProjectionMappingContext,
    response: JevProviderResponse,
) -> JevProviderResponse:
    """Restore typed synthetic answers using only the matching local context."""
    try:
        if not isinstance(state, OrchestraJevAdjudicationState):
            _fail("INVALID_SOURCE_STATE")
        if type(mapping_context) is not JevProjectionMappingContext:
            _fail("INVALID_MAPPING_CONTEXT")
        if not isinstance(request_bytes, bytes):
            _fail("INVALID_INPUT")
        if not isinstance(response, JevProviderResponse):
            _fail("RESPONSE_CONTRACT_INCOMPATIBLE")

        source = state.to_payload()
        if (
            state.candidate_binding != mapping_context._candidate_binding
            or source["candidate"]["scope_hash"] != mapping_context._source_scope_hash
        ):
            _fail("SOURCE_STATE_MISMATCH")
        request_digest = hashlib.sha256(request_bytes).hexdigest()
        if not hmac.compare_digest(request_digest, mapping_context._request_digest):
            _fail("REQUEST_MISMATCH")

        request = json.loads(request_bytes.decode("utf-8"))
        if (
            not isinstance(request, dict)
            or set(request) != {"state", "model", "questions"}
            or request["model"] != TYPESAFE_JEV_MODEL
            or not isinstance(request["questions"], dict)
        ):
            _fail("INVALID_MAPPING_CONTEXT")

        projected_questions = request["questions"]
        source_questions = OrchestraJevQuestionBuilder().build(state)
        question_ids = dict(mapping_context._question_ids)
        mitigation_ids = dict(mapping_context._mitigation_ids)
        if (
            len(question_ids) != len(mapping_context._question_ids)
            or len(set(question_ids.values())) != len(question_ids)
            or len(mitigation_ids) != len(mapping_context._mitigation_ids)
            or len(set(mitigation_ids.values())) != len(mitigation_ids)
            or set(question_ids) != set(projected_questions)
            or set(question_ids.values()) != set(source_questions)
            or set(mitigation_ids.values()) != set(state.mitigation_ids)
            or set(mitigation_ids)
            != set(projected_questions["recommended_mitigation"]["criteria"])
            - {"NO_CLEAR_PREFERENCE"}
        ):
            _fail("INVALID_MAPPING_CONTEXT")

        source_to_alias = {source_id: alias for alias, source_id in mitigation_ids.items()}
        expected_question_ids = _question_id_aliases(
            source_questions,
            source_to_alias,
            projected_questions,
        )
        if tuple(sorted(question_ids.items())) != expected_question_ids:
            _fail("INVALID_MAPPING_CONTEXT")

        answer_ids = [question_id for question_id, _ in response.answers]
        if (
            len(answer_ids) != len(set(answer_ids))
            or any(not isinstance(question_id, str) for question_id in answer_ids)
            or set(answer_ids) != set(projected_questions)
        ):
            _fail("RESPONSE_CONTRACT_INCOMPATIBLE")

        for question_id, answer in response.answers:
            question = projected_questions[question_id]
            if not isinstance(question, dict):
                _fail("INVALID_MAPPING_CONTEXT")
            answer_type = question.get("type")
            if answer_type == "noul":
                if type(answer) is not JevNoulAnswer:
                    _fail("RESPONSE_CONTRACT_INCOMPATIBLE")
            elif answer_type == "choice":
                if type(answer) is not JevChoiceAnswer or answer.confidence is None:
                    _fail("RESPONSE_CONTRACT_INCOMPATIBLE")
                criteria = question.get("criteria")
                probabilities = answer.probabilities
                if (
                    not isinstance(criteria, dict)
                    or len(probabilities) != len(dict(probabilities))
                    or set(dict(probabilities)) != set(criteria)
                    or answer.selected not in criteria
                    or dict(probabilities)[answer.selected] != max(dict(probabilities).values())
                ):
                    _fail("RESPONSE_CONTRACT_INCOMPATIBLE")
            else:
                _fail("INVALID_MAPPING_CONTEXT")

        mapped_answers: list[tuple[str, JevNoulAnswer | JevChoiceAnswer]] = []
        for question_id, answer in response.answers:
            source_question_id = question_ids[question_id]
            if type(answer) is JevNoulAnswer:
                mapped_answers.append((source_question_id, JevNoulAnswer(answer.probability)))
                continue

            criterion_ids = (
                {**mitigation_ids, "NO_CLEAR_PREFERENCE": "NO_CLEAR_PREFERENCE"}
                if question_id == "recommended_mitigation"
                else {key: key for key, _ in answer.probabilities}
            )
            if set(criterion_ids) != set(dict(answer.probabilities)):
                _fail("RESPONSE_CONTRACT_INCOMPATIBLE")
            mapped_probabilities = tuple(
                (criterion_ids[key], probability)
                for key, probability in answer.probabilities
            )
            mapped_answers.append(
                (
                    source_question_id,
                    JevChoiceAnswer(
                        criterion_ids[answer.selected],
                        answer.confidence,
                        mapped_probabilities,
                    ),
                )
            )

        return JevProviderResponse(
            response.model,
            mapping_context._candidate_binding,
            tuple(mapped_answers),
        )
    except JevProjectionError:
        raise
    except Exception:
        raise JevProjectionError("RESPONSE_CONTRACT_INCOMPATIBLE") from None


__all__ = [
    "JEV_PROVIDER_PROJECTION_CONTRACT",
    "JevProjectionError",
    "JevProjectionMappingContext",
    "ReviewedJevTextBundle",
    "build_offline_jev_provider_projection",
    "build_offline_jev_provider_projection_with_context",
    "reverse_map_offline_jev_provider_response",
]
