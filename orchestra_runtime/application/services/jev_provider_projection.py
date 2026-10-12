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
import re
from typing import Any

from ...domain.adaptive.jev_adjudication import (
    JevAdjudicationEligibilityError,
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
        "INVALID_NONCE",
        "INVALID_SOURCE_STATE",
        "INVALID_SOURCE_VALUE",
        "REVIEWED_TEXT_INCOMPLETE",
        "REVIEWED_TEXT_REQUIRED",
        "REVIEWED_TEXT_UNBOUND",
        "SOURCE_STATE_INELIGIBLE",
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


def build_offline_jev_provider_projection(
    state: OrchestraJevAdjudicationState,
    reviewed_text: ReviewedJevTextBundle,
    *,
    nonce: str,
) -> bytes:
    """Build deterministic UTF-8 request bytes for local synthetic validation only.

    The caller must supply fresh, separately reviewed wording. Reusing a nonce
    repeats aliases; neither aliases nor hazard checks prove privacy or consent.
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
        return canonical_json_bytes(request)
    except JevProjectionError:
        raise
    except Exception:
        raise JevProjectionError("INVALID_INPUT") from None


__all__ = [
    "JEV_PROVIDER_PROJECTION_CONTRACT",
    "JevProjectionError",
    "ReviewedJevTextBundle",
    "build_offline_jev_provider_projection",
]
