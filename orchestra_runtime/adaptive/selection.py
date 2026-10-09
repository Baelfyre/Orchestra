from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re
from typing import Any, Iterable, Mapping

from ..evidence import normalize_sha256, normalize_timestamp, receipt_digest
from .models import AdaptiveScope
from .shadow import ShadowCandidate, ShadowComparison

ELIGIBILITY_ENVELOPE_SCHEMA_VERSION = "orchestra.adaptive-selection-eligibility-envelope.v1"
SELECTION_EVIDENCE_SCHEMA_VERSION = "orchestra.adaptive-selection-evidence.v1"
SELECTION_DECISION_SCHEMA_VERSION = "orchestra.adaptive-selection-decision.v1"
SELECTION_SCORER_VERSION = "orchestra.adaptive-selection-scorer.v1"

SELECTION_TYPES = frozenset({"SPECIALIST_STRATEGY", "MODEL", "WORKER"})
REQUIRED_ELIGIBILITY_FILTERS = (
    "ownership",
    "route_binding",
    "authority",
    "capability",
    "governance",
    "provider_privacy",
    "lifecycle",
    "resource_ceilings",
)
EVIDENCE_SOURCE_KINDS = frozenset(
    {
        "A3_SHADOW_CANDIDATE",
        "A3_SHADOW_COMPARISON",
        "GOVERNED_SELECTION_OUTCOME",
        "VALIDATION_EVIDENCE",
        "REMEDIATION_EVIDENCE",
        "TRUSTWORTHY_MEASURED_TELEMETRY",
    }
)
A3_EVIDENCE_SOURCE_KINDS = frozenset({"A3_SHADOW_CANDIDATE", "A3_SHADOW_COMPARISON"})
DIRECT_OPTION_EVIDENCE_SOURCE_KINDS = EVIDENCE_SOURCE_KINDS - A3_EVIDENCE_SOURCE_KINDS
A3_CANDIDATE_TYPES = frozenset(
    {"USER_PREFERENCE_TENDENCY", "WORKFLOW_TENDENCY", "SPECIALIST_STRATEGY_TENDENCY"}
)
EVIDENCE_DIRECTIONS = frozenset({"POSITIVE", "NEGATIVE", "NEUTRAL"})
QUALIFICATION_STATUSES = frozenset({"QUALIFIED", "REJECTED"})
DECISION_DISPOSITIONS = frozenset(
    {
        "SHADOW_RANKED",
        "DETERMINISTIC_FALLBACK",
        "NO_ELIGIBLE_CANDIDATES",
        "INVALID_ELIGIBILITY",
        "INVALID_EVIDENCE",
        "EXPLICIT_CONSTRAINT",
        "UNSUPPORTED_EVIDENCE_FOR_SELECTION_TYPE",
    }
)
MEASUREMENT_METRICS = frozenset({"LATENCY", "COST", "TOKEN_COUNT"})
MIN_DISTINCT_SUPPORT = 2

_IDENTIFIER_RE = re.compile(r"^[a-z0-9][a-z0-9_.:-]{0,127}$")
_REASON_RE = re.compile(r"^[A-Z0-9][A-Z0-9_]{0,127}$")


def _text(value: object, field_name: str, *, max_length: int = 512) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    text = value.strip()
    if not text:
        raise ValueError(f"{field_name} must be non-empty")
    if len(text) > max_length:
        raise ValueError(f"{field_name} exceeds {max_length} characters")
    if any(ord(ch) < 32 for ch in text):
        raise ValueError(f"{field_name} must not contain control characters")
    return text


def _optional_text(value: object | None, field_name: str, *, max_length: int = 512) -> str | None:
    return None if value is None else _text(value, field_name, max_length=max_length)


def _identifier(value: object, field_name: str) -> str:
    text = _text(value, field_name, max_length=128).casefold()
    if not _IDENTIFIER_RE.fullmatch(text):
        raise ValueError(f"{field_name} must be a canonical identifier")
    return text


def _selection_type(value: object) -> str:
    text = _text(value, "selection_type", max_length=64).upper()
    if text not in SELECTION_TYPES:
        raise ValueError(f"unsupported selection_type '{text}'")
    return text


def _stable_strings(values: Iterable[object], field_name: str, *, max_items: int) -> tuple[str, ...]:
    normalized = tuple(_text(value, field_name) for value in values)
    if len(normalized) > max_items:
        raise ValueError(f"{field_name} exceeds {max_items} items")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} contains duplicate values")
    return tuple(sorted(normalized))


def _notes(values: Iterable[object]) -> tuple[str, ...]:
    normalized = tuple(_text(value, "note") for value in values)
    if len(normalized) > 16:
        raise ValueError("notes exceeds 16 items")
    return normalized


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    return f"{prefix}.{receipt_digest(dict(payload))[:24]}"


@dataclass(frozen=True, slots=True)
class SelectionCandidate:
    candidate_id: str
    option_kind: str
    option_key: str
    eligibility_evidence_refs: tuple[str, ...]
    owner_specialist_slug: str | None = None
    provider_id: str | None = None

    def __post_init__(self) -> None:
        option_kind = _selection_type(self.option_kind)
        owner = None if self.owner_specialist_slug is None else _identifier(
            self.owner_specialist_slug, "owner_specialist_slug"
        )
        object.__setattr__(self, "candidate_id", _text(self.candidate_id, "candidate_id", max_length=256))
        object.__setattr__(self, "option_kind", option_kind)
        object.__setattr__(self, "option_key", _text(self.option_key, "option_key", max_length=256))
        object.__setattr__(
            self,
            "eligibility_evidence_refs",
            _stable_strings(self.eligibility_evidence_refs, "eligibility_evidence_ref", max_items=32),
        )
        if not self.eligibility_evidence_refs:
            raise ValueError("eligibility_evidence_refs must not be empty")
        object.__setattr__(self, "owner_specialist_slug", owner)
        object.__setattr__(
            self,
            "provider_id",
            _optional_text(self.provider_id, "provider_id", max_length=128),
        )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "candidate_id": self.candidate_id,
            "option_kind": self.option_kind,
            "option_key": self.option_key,
            "eligibility_status": "ELIGIBLE",
            "eligibility_evidence_refs": list(self.eligibility_evidence_refs),
        }
        if self.owner_specialist_slug is not None:
            payload["owner_specialist_slug"] = self.owner_specialist_slug
        if self.provider_id is not None:
            payload["provider_id"] = self.provider_id
        return payload


@dataclass(frozen=True, slots=True)
class SelectionEligibilityEnvelope:
    envelope_id: str
    selection_type: str
    created_at: str
    user_key: str
    command_name: str
    routed_specialist_slug: str
    deterministic_route_ref: str
    filter_evidence_refs: tuple[str, ...]
    candidates: tuple[SelectionCandidate, ...]
    project_key: str | None = None
    task_session_key: str | None = None
    explicit_current_constraint_ref: str | None = None
    filters_applied: Mapping[str, bool] | None = None
    schema_version: str = ELIGIBILITY_ENVELOPE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != ELIGIBILITY_ENVELOPE_SCHEMA_VERSION:
            raise ValueError(f"unsupported eligibility schema '{self.schema_version}'")
        selection_type = _selection_type(self.selection_type)
        filters = dict(self.filters_applied or {key: True for key in REQUIRED_ELIGIBILITY_FILTERS})
        if set(filters) != set(REQUIRED_ELIGIBILITY_FILTERS) or any(
            filters.get(key) is not True for key in REQUIRED_ELIGIBILITY_FILTERS
        ):
            raise ValueError("all deterministic eligibility filters must be present and true")
        candidates = tuple(self.candidates)
        if len(candidates) > 128:
            raise ValueError("candidates exceeds 128 items")
        if any(not isinstance(candidate, SelectionCandidate) for candidate in candidates):
            raise TypeError("candidates must contain SelectionCandidate values")
        candidate_ids = tuple(candidate.candidate_id for candidate in candidates)
        if len(candidate_ids) != len(set(candidate_ids)):
            raise ValueError("candidate ids must be unique")
        if any(candidate.option_kind != selection_type for candidate in candidates):
            raise ValueError("candidate option_kind must match selection_type")
        routed_specialist_slug = _identifier(self.routed_specialist_slug, "routed_specialist_slug")
        if any(
            candidate.owner_specialist_slug is not None
            and candidate.owner_specialist_slug != routed_specialist_slug
            for candidate in candidates
        ):
            raise ValueError("candidate owner_specialist_slug cannot bypass routed specialist ownership")

        object.__setattr__(self, "envelope_id", _text(self.envelope_id, "envelope_id", max_length=256))
        object.__setattr__(self, "selection_type", selection_type)
        object.__setattr__(self, "created_at", normalize_timestamp(self.created_at, "created_at"))
        object.__setattr__(self, "user_key", _text(self.user_key, "user_key", max_length=256))
        object.__setattr__(self, "project_key", _optional_text(self.project_key, "project_key", max_length=256))
        object.__setattr__(
            self, "task_session_key", _optional_text(self.task_session_key, "task_session_key", max_length=256)
        )
        object.__setattr__(self, "command_name", _identifier(self.command_name, "command_name"))
        object.__setattr__(self, "routed_specialist_slug", routed_specialist_slug)
        object.__setattr__(
            self,
            "deterministic_route_ref",
            _text(self.deterministic_route_ref, "deterministic_route_ref"),
        )
        object.__setattr__(
            self,
            "explicit_current_constraint_ref",
            _optional_text(self.explicit_current_constraint_ref, "explicit_current_constraint_ref"),
        )
        object.__setattr__(self, "filters_applied", {key: True for key in REQUIRED_ELIGIBILITY_FILTERS})
        object.__setattr__(
            self,
            "filter_evidence_refs",
            _stable_strings(self.filter_evidence_refs, "filter_evidence_ref", max_items=64),
        )
        if not self.filter_evidence_refs:
            raise ValueError("filter_evidence_refs must not be empty")
        object.__setattr__(self, "candidates", candidates)

    @property
    def disposition(self) -> str:
        return "ELIGIBLE_SET_READY" if self.candidates else "NO_ELIGIBLE_CANDIDATES"

    @property
    def candidate_ids(self) -> tuple[str, ...]:
        return tuple(candidate.candidate_id for candidate in self.candidates)

    def candidate_by_id(self, candidate_id: str) -> SelectionCandidate | None:
        return next((candidate for candidate in self.candidates if candidate.candidate_id == candidate_id), None)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_version": self.schema_version,
            "envelope_id": self.envelope_id,
            "selection_type": self.selection_type,
            "created_at": self.created_at,
            "user_key": self.user_key,
            "command_name": self.command_name,
            "routed_specialist_slug": self.routed_specialist_slug,
            "deterministic_route_ref": self.deterministic_route_ref,
            "filters_applied": dict(self.filters_applied),
            "filter_evidence_refs": list(self.filter_evidence_refs),
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "disposition": self.disposition,
        }
        if self.project_key is not None:
            payload["project_key"] = self.project_key
        if self.task_session_key is not None:
            payload["task_session_key"] = self.task_session_key
        if self.explicit_current_constraint_ref is not None:
            payload["explicit_current_constraint_ref"] = self.explicit_current_constraint_ref
        return payload

    @property
    def digest(self) -> str:
        return receipt_digest(self.to_dict())


@dataclass(frozen=True, slots=True)
class SelectionMeasurement:
    metric: str
    value: float
    unit: str
    measurement_status: str = "TRUSTWORTHY_MEASURED"

    def __post_init__(self) -> None:
        metric = _text(self.metric, "metric", max_length=64).upper()
        if metric not in MEASUREMENT_METRICS:
            raise ValueError(f"unsupported measurement metric '{metric}'")
        if isinstance(self.value, bool) or not isinstance(self.value, (int, float)) or float(self.value) < 0:
            raise ValueError("measurement value must be a non-negative number")
        if self.measurement_status != "TRUSTWORTHY_MEASURED":
            raise ValueError("measurement_status must be TRUSTWORTHY_MEASURED")
        object.__setattr__(self, "metric", metric)
        object.__setattr__(self, "value", float(self.value))
        object.__setattr__(self, "unit", _text(self.unit, "unit", max_length=64))

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric": self.metric,
            "value": self.value,
            "unit": self.unit,
            "measurement_status": "TRUSTWORTHY_MEASURED",
        }


@dataclass(frozen=True, slots=True)
class SelectionEvidenceItem:
    evidence_id: str
    source_kind: str
    source_ref: str
    source_digest: str
    option_id: str
    selection_type: str
    qualification_status: str
    reason_code: str
    a3_candidate_type: str | None = None
    direction: str | None = None
    measurement: SelectionMeasurement | None = None

    def __post_init__(self) -> None:
        source_kind = _text(self.source_kind, "source_kind", max_length=64).upper()
        if source_kind not in EVIDENCE_SOURCE_KINDS:
            raise ValueError(f"unsupported evidence source kind '{source_kind}'")
        selection_type = _selection_type(self.selection_type)
        status = _text(self.qualification_status, "qualification_status", max_length=32).upper()
        if status not in QUALIFICATION_STATUSES:
            raise ValueError(f"unsupported qualification status '{status}'")
        reason = _text(self.reason_code, "reason_code", max_length=128).upper()
        if not _REASON_RE.fullmatch(reason):
            raise ValueError("reason_code must be a canonical upper-case identifier")
        candidate_type = None
        if self.a3_candidate_type is not None:
            candidate_type = _text(self.a3_candidate_type, "a3_candidate_type", max_length=64).upper()
            if candidate_type not in A3_CANDIDATE_TYPES:
                raise ValueError(f"unsupported A3 candidate type '{candidate_type}'")
        direction = None
        if self.direction is not None:
            direction = _text(self.direction, "direction", max_length=32).upper()
            if direction not in EVIDENCE_DIRECTIONS:
                raise ValueError(f"unsupported evidence direction '{direction}'")
        if source_kind in A3_EVIDENCE_SOURCE_KINDS and candidate_type is None:
            raise ValueError("A3 selection evidence must declare a3_candidate_type")
        if source_kind not in A3_EVIDENCE_SOURCE_KINDS and candidate_type is not None:
            raise ValueError("direct option evidence cannot declare a3_candidate_type")
        if source_kind == "TRUSTWORTHY_MEASURED_TELEMETRY" and not isinstance(
            self.measurement, SelectionMeasurement
        ):
            raise ValueError("trustworthy measured telemetry requires a validated measurement")
        if source_kind != "TRUSTWORTHY_MEASURED_TELEMETRY" and self.measurement is not None:
            raise ValueError("measurement is only valid for trustworthy measured telemetry")
        if status == "QUALIFIED" and direction is None:
            raise ValueError("qualified evidence requires an explicit direction")

        object.__setattr__(self, "evidence_id", _text(self.evidence_id, "evidence_id", max_length=256))
        object.__setattr__(self, "source_kind", source_kind)
        object.__setattr__(self, "source_ref", _text(self.source_ref, "source_ref"))
        object.__setattr__(self, "source_digest", normalize_sha256(self.source_digest, "source_digest"))
        object.__setattr__(self, "option_id", _text(self.option_id, "option_id", max_length=256))
        object.__setattr__(self, "selection_type", selection_type)
        object.__setattr__(self, "qualification_status", status)
        object.__setattr__(self, "reason_code", reason)
        object.__setattr__(self, "a3_candidate_type", candidate_type)
        object.__setattr__(self, "direction", direction)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "evidence_id": self.evidence_id,
            "source_kind": self.source_kind,
            "source_ref": self.source_ref,
            "source_digest": self.source_digest,
            "option_id": self.option_id,
            "selection_type": self.selection_type,
            "qualification_status": self.qualification_status,
            "reason_code": self.reason_code,
        }
        if self.a3_candidate_type is not None:
            payload["a3_candidate_type"] = self.a3_candidate_type
        if self.direction is not None:
            payload["direction"] = self.direction
        if self.measurement is not None:
            payload["measurement"] = self.measurement.to_dict()
        return payload


@dataclass(frozen=True, slots=True)
class SelectionEvidencePacket:
    packet_id: str
    eligibility_envelope_ref: str
    eligibility_envelope_digest: str
    selection_type: str
    collected_at: str
    items: tuple[SelectionEvidenceItem, ...]
    notes: tuple[str, ...] = ()
    schema_version: str = SELECTION_EVIDENCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != SELECTION_EVIDENCE_SCHEMA_VERSION:
            raise ValueError(f"unsupported selection evidence schema '{self.schema_version}'")
        selection_type = _selection_type(self.selection_type)
        items = tuple(self.items)
        if len(items) > 256:
            raise ValueError("selection evidence exceeds 256 items")
        if any(not isinstance(item, SelectionEvidenceItem) for item in items):
            raise TypeError("items must contain SelectionEvidenceItem values")
        if any(item.selection_type != selection_type for item in items):
            raise ValueError("evidence item selection_type must match packet selection_type")
        evidence_ids = tuple(item.evidence_id for item in items)
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("selection evidence ids must be unique")
        object.__setattr__(self, "packet_id", _text(self.packet_id, "packet_id", max_length=256))
        object.__setattr__(
            self,
            "eligibility_envelope_ref",
            _text(self.eligibility_envelope_ref, "eligibility_envelope_ref"),
        )
        object.__setattr__(
            self,
            "eligibility_envelope_digest",
            normalize_sha256(self.eligibility_envelope_digest, "eligibility_envelope_digest"),
        )
        object.__setattr__(self, "selection_type", selection_type)
        object.__setattr__(self, "collected_at", normalize_timestamp(self.collected_at, "collected_at"))
        object.__setattr__(self, "items", items)
        object.__setattr__(self, "notes", _notes(self.notes))

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_version": self.schema_version,
            "packet_id": self.packet_id,
            "eligibility_envelope_ref": self.eligibility_envelope_ref,
            "eligibility_envelope_digest": self.eligibility_envelope_digest,
            "selection_type": self.selection_type,
            "collected_at": self.collected_at,
            "items": [item.to_dict() for item in self.items],
        }
        if self.notes:
            payload["notes"] = list(self.notes)
        return payload

    @property
    def digest(self) -> str:
        return receipt_digest(self.to_dict())


@dataclass(frozen=True, slots=True)
class SelectionDecision:
    decision_id: str
    selection_type: str
    eligibility_envelope_ref: str
    eligibility_envelope_digest: str
    evidence_packet_ref: str
    evidence_packet_digest: str
    evaluated_at: str
    disposition: str
    ranked_candidate_ids: tuple[str, ...]
    shadow_recommendation_id: str | None
    actual_deterministic_choice_id: str | None
    notes: tuple[str, ...] = ()
    scorer_version: str = SELECTION_SCORER_VERSION
    schema_version: str = SELECTION_DECISION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != SELECTION_DECISION_SCHEMA_VERSION:
            raise ValueError(f"unsupported selection decision schema '{self.schema_version}'")
        selection_type = _selection_type(self.selection_type)
        disposition = _text(self.disposition, "disposition", max_length=64).upper()
        if disposition not in DECISION_DISPOSITIONS:
            raise ValueError(f"unsupported decision disposition '{disposition}'")
        ranked = tuple(_text(item, "ranked_candidate_id", max_length=256) for item in self.ranked_candidate_ids)
        if len(ranked) > 128 or len(ranked) != len(set(ranked)):
            raise ValueError("ranked_candidate_ids must be unique and bounded")
        scorer = _identifier(self.scorer_version, "scorer_version")
        object.__setattr__(self, "decision_id", _text(self.decision_id, "decision_id", max_length=256))
        object.__setattr__(self, "selection_type", selection_type)
        object.__setattr__(
            self, "eligibility_envelope_ref", _text(self.eligibility_envelope_ref, "eligibility_envelope_ref")
        )
        object.__setattr__(
            self,
            "eligibility_envelope_digest",
            normalize_sha256(self.eligibility_envelope_digest, "eligibility_envelope_digest"),
        )
        object.__setattr__(self, "evidence_packet_ref", _text(self.evidence_packet_ref, "evidence_packet_ref"))
        object.__setattr__(
            self,
            "evidence_packet_digest",
            normalize_sha256(self.evidence_packet_digest, "evidence_packet_digest"),
        )
        object.__setattr__(self, "evaluated_at", normalize_timestamp(self.evaluated_at, "evaluated_at"))
        object.__setattr__(self, "scorer_version", scorer)
        object.__setattr__(self, "disposition", disposition)
        object.__setattr__(self, "ranked_candidate_ids", ranked)
        object.__setattr__(
            self,
            "shadow_recommendation_id",
            _optional_text(self.shadow_recommendation_id, "shadow_recommendation_id", max_length=256),
        )
        object.__setattr__(
            self,
            "actual_deterministic_choice_id",
            _optional_text(self.actual_deterministic_choice_id, "actual_deterministic_choice_id", max_length=256),
        )
        object.__setattr__(self, "notes", _notes(self.notes))

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_version": self.schema_version,
            "decision_id": self.decision_id,
            "selection_type": self.selection_type,
            "eligibility_envelope_ref": self.eligibility_envelope_ref,
            "eligibility_envelope_digest": self.eligibility_envelope_digest,
            "evidence_packet_ref": self.evidence_packet_ref,
            "evidence_packet_digest": self.evidence_packet_digest,
            "evaluated_at": self.evaluated_at,
            "scorer_version": self.scorer_version,
            "disposition": self.disposition,
            "ranked_candidate_ids": list(self.ranked_candidate_ids),
            "shadow_recommendation_id": self.shadow_recommendation_id,
            "actual_deterministic_choice_id": self.actual_deterministic_choice_id,
            "execution_controlled_by": "DETERMINISTIC_ORCHESTRA",
            "selection_effective": False,
            "shadow_influenced_execution": False,
            "promotion_state": "NOT_PROMOTED",
        }
        if self.notes:
            payload["notes"] = list(self.notes)
        return payload

    @property
    def digest(self) -> str:
        return receipt_digest(self.to_dict())


def build_eligibility_envelope(
    *,
    selection_type: str,
    created_at: str,
    user_key: str,
    command_name: str,
    routed_specialist_slug: str,
    deterministic_route_ref: str,
    filter_evidence_refs: Iterable[str],
    candidates: Iterable[SelectionCandidate],
    project_key: str | None = None,
    task_session_key: str | None = None,
    explicit_current_constraint_ref: str | None = None,
) -> SelectionEligibilityEnvelope:
    candidate_tuple = tuple(candidates)
    identity = {
        "selection_type": _selection_type(selection_type),
        "created_at": normalize_timestamp(created_at, "created_at"),
        "user_key": _text(user_key, "user_key", max_length=256),
        "project_key": project_key,
        "task_session_key": task_session_key,
        "command_name": _identifier(command_name, "command_name"),
        "routed_specialist_slug": _identifier(routed_specialist_slug, "routed_specialist_slug"),
        "deterministic_route_ref": _text(deterministic_route_ref, "deterministic_route_ref"),
        "candidate_ids": [candidate.candidate_id for candidate in candidate_tuple],
    }
    return SelectionEligibilityEnvelope(
        envelope_id=_stable_id("selection-envelope", identity),
        selection_type=selection_type,
        created_at=created_at,
        user_key=user_key,
        project_key=project_key,
        task_session_key=task_session_key,
        command_name=command_name,
        routed_specialist_slug=routed_specialist_slug,
        deterministic_route_ref=deterministic_route_ref,
        explicit_current_constraint_ref=explicit_current_constraint_ref,
        filter_evidence_refs=tuple(filter_evidence_refs),
        candidates=candidate_tuple,
    )


def qualify_a3_candidate(
    candidate: ShadowCandidate,
    envelope: SelectionEligibilityEnvelope,
    *,
    option_id: str,
) -> SelectionEvidenceItem:
    if not isinstance(candidate, ShadowCandidate):
        raise TypeError("candidate must be ShadowCandidate")
    if not isinstance(envelope, SelectionEligibilityEnvelope):
        raise TypeError("envelope must be SelectionEligibilityEnvelope")
    option = envelope.candidate_by_id(option_id)
    if option is None:
        raise ValueError("A3 candidate cannot qualify an option outside the eligibility envelope")

    exact_scope = (
        candidate.scope.user_key == envelope.user_key
        and candidate.scope.project_key == envelope.project_key
        and candidate.scope.specialist_slug in {None, envelope.routed_specialist_slug}
        and candidate.scope.task_session_key in {None, envelope.task_session_key}
    )
    candidate_value = str(candidate.candidate_value)
    qualified = (
        envelope.selection_type == "SPECIALIST_STRATEGY"
        and option.option_kind == "SPECIALIST_STRATEGY"
        and candidate.candidate_type == "SPECIALIST_STRATEGY_TENDENCY"
        and candidate.status == "CANDIDATE"
        and candidate.shadow_only is True
        and candidate.promotion_state == "NOT_PROMOTED"
        and exact_scope
        and candidate_value == option.option_key
    )
    reason = "A3_SPECIALIST_STRATEGY_EXACT_SCOPE_MATCH" if qualified else "A3_EVIDENCE_NOT_QUALIFIED"
    direction = "POSITIVE" if qualified else None
    return SelectionEvidenceItem(
        evidence_id=_stable_id(
            "selection-evidence",
            {"source": candidate.candidate_id, "digest": candidate.digest, "option_id": option_id},
        ),
        source_kind="A3_SHADOW_CANDIDATE",
        source_ref=candidate.candidate_id,
        source_digest=candidate.digest,
        option_id=option_id,
        selection_type=envelope.selection_type,
        a3_candidate_type=candidate.candidate_type,
        direction=direction,
        qualification_status="QUALIFIED" if qualified else "REJECTED",
        reason_code=reason,
    )


def qualify_a3_comparison(
    comparison: ShadowComparison,
    candidate: ShadowCandidate,
    envelope: SelectionEligibilityEnvelope,
    *,
    option_id: str,
) -> SelectionEvidenceItem:
    if not isinstance(comparison, ShadowComparison):
        raise TypeError("comparison must be ShadowComparison")
    if not isinstance(candidate, ShadowCandidate):
        raise TypeError("candidate must be ShadowCandidate")
    option = envelope.candidate_by_id(option_id)
    if option is None:
        raise ValueError("A3 comparison cannot qualify an option outside the eligibility envelope")
    exact_scope = (
        comparison.scope == candidate.scope
        and comparison.scope.user_key == envelope.user_key
        and comparison.scope.project_key == envelope.project_key
        and comparison.scope.specialist_slug in {None, envelope.routed_specialist_slug}
        and comparison.scope.task_session_key in {None, envelope.task_session_key}
    )
    exact_binding = (
        comparison.candidate_ref == candidate.candidate_id
        and comparison.candidate_digest == candidate.digest
        and str(comparison.shadow_recommendation) == option.option_key
    )
    supported_disposition = comparison.disposition in {"MATCH", "MISMATCH"}
    qualified = (
        envelope.selection_type == "SPECIALIST_STRATEGY"
        and candidate.candidate_type == "SPECIALIST_STRATEGY_TENDENCY"
        and candidate.status == "CANDIDATE"
        and candidate.shadow_only is True
        and candidate.promotion_state == "NOT_PROMOTED"
        and exact_scope
        and exact_binding
        and supported_disposition
        and comparison.execution_controlled_by == "DETERMINISTIC_ORCHESTRA"
        and comparison.shadow_influenced_execution is False
    )
    direction = None
    if qualified:
        direction = "POSITIVE" if comparison.disposition == "MATCH" else "NEUTRAL"
    return SelectionEvidenceItem(
        evidence_id=_stable_id(
            "selection-evidence",
            {"source": comparison.comparison_id, "digest": comparison.digest, "option_id": option_id},
        ),
        source_kind="A3_SHADOW_COMPARISON",
        source_ref=comparison.comparison_id,
        source_digest=comparison.digest,
        option_id=option_id,
        selection_type=envelope.selection_type,
        a3_candidate_type=candidate.candidate_type,
        direction=direction,
        qualification_status="QUALIFIED" if qualified else "REJECTED",
        reason_code="A3_SPECIALIST_STRATEGY_COMPARISON_EXACT_BINDING" if qualified else "A3_COMPARISON_NOT_QUALIFIED",
    )


def build_evidence_packet(
    envelope: SelectionEligibilityEnvelope,
    *,
    collected_at: str,
    items: Iterable[SelectionEvidenceItem],
    notes: Iterable[str] = (),
) -> SelectionEvidencePacket:
    if not isinstance(envelope, SelectionEligibilityEnvelope):
        raise TypeError("envelope must be SelectionEligibilityEnvelope")
    item_tuple = tuple(items)
    return SelectionEvidencePacket(
        packet_id=_stable_id(
            "selection-packet",
            {
                "eligibility_envelope_ref": envelope.envelope_id,
                "eligibility_envelope_digest": envelope.digest,
                "collected_at": normalize_timestamp(collected_at, "collected_at"),
                "evidence_ids": [item.evidence_id for item in item_tuple],
            },
        ),
        eligibility_envelope_ref=envelope.envelope_id,
        eligibility_envelope_digest=envelope.digest,
        selection_type=envelope.selection_type,
        collected_at=collected_at,
        items=item_tuple,
        notes=tuple(notes),
    )


def _decision(
    envelope: SelectionEligibilityEnvelope,
    packet: SelectionEvidencePacket,
    *,
    evaluated_at: str,
    disposition: str,
    ranked_candidate_ids: tuple[str, ...],
    shadow_recommendation_id: str | None,
    actual_deterministic_choice_id: str | None,
    notes: Iterable[str] = (),
) -> SelectionDecision:
    normalized_at = normalize_timestamp(evaluated_at, "evaluated_at")
    payload = {
        "selection_type": envelope.selection_type,
        "eligibility_envelope_ref": envelope.envelope_id,
        "eligibility_envelope_digest": envelope.digest,
        "evidence_packet_ref": packet.packet_id,
        "evidence_packet_digest": packet.digest,
        "evaluated_at": normalized_at,
        "disposition": disposition,
        "ranked_candidate_ids": list(ranked_candidate_ids),
        "shadow_recommendation_id": shadow_recommendation_id,
        "actual_deterministic_choice_id": actual_deterministic_choice_id,
        "scorer_version": SELECTION_SCORER_VERSION,
    }
    return SelectionDecision(
        decision_id=_stable_id("selection-decision", payload),
        selection_type=envelope.selection_type,
        eligibility_envelope_ref=envelope.envelope_id,
        eligibility_envelope_digest=envelope.digest,
        evidence_packet_ref=packet.packet_id,
        evidence_packet_digest=packet.digest,
        evaluated_at=normalized_at,
        disposition=disposition,
        ranked_candidate_ids=ranked_candidate_ids,
        shadow_recommendation_id=shadow_recommendation_id,
        actual_deterministic_choice_id=actual_deterministic_choice_id,
        notes=tuple(notes),
    )


def rank_shadow_selection(
    envelope: SelectionEligibilityEnvelope,
    packet: SelectionEvidencePacket,
    *,
    actual_deterministic_choice_id: str | None,
    evaluated_at: str,
    explicit_scoped_preference_candidate_id: str | None = None,
) -> SelectionDecision:
    """Rank only pre-filtered eligible options while preserving deterministic execution control."""

    if not isinstance(envelope, SelectionEligibilityEnvelope):
        raise TypeError("envelope must be SelectionEligibilityEnvelope")
    if not isinstance(packet, SelectionEvidencePacket):
        raise TypeError("packet must be SelectionEvidencePacket")

    deterministic_order = envelope.candidate_ids
    actual = actual_deterministic_choice_id
    if actual is not None:
        actual = _text(actual, "actual_deterministic_choice_id", max_length=256)

    if not envelope.candidates:
        return _decision(
            envelope,
            packet,
            evaluated_at=evaluated_at,
            disposition="NO_ELIGIBLE_CANDIDATES",
            ranked_candidate_ids=(),
            shadow_recommendation_id=None,
            actual_deterministic_choice_id=None,
            notes=("No eligible candidates remained after deterministic filters.",),
        )

    if actual not in set(deterministic_order):
        return _decision(
            envelope,
            packet,
            evaluated_at=evaluated_at,
            disposition="INVALID_ELIGIBILITY",
            ranked_candidate_ids=deterministic_order,
            shadow_recommendation_id=None,
            actual_deterministic_choice_id=actual,
            notes=("Deterministic choice was not present in the immutable eligibility envelope.",),
        )

    if (
        packet.eligibility_envelope_ref != envelope.envelope_id
        or packet.eligibility_envelope_digest != envelope.digest
        or packet.selection_type != envelope.selection_type
    ):
        return _decision(
            envelope,
            packet,
            evaluated_at=evaluated_at,
            disposition="INVALID_EVIDENCE",
            ranked_candidate_ids=deterministic_order,
            shadow_recommendation_id=None,
            actual_deterministic_choice_id=actual,
            notes=("Evidence packet did not bind to the exact eligibility envelope.",),
        )

    envelope_time = datetime.fromisoformat(envelope.created_at.replace("Z", "+00:00"))
    packet_time = datetime.fromisoformat(packet.collected_at.replace("Z", "+00:00"))
    if packet_time < envelope_time:
        return _decision(
            envelope,
            packet,
            evaluated_at=evaluated_at,
            disposition="INVALID_EVIDENCE",
            ranked_candidate_ids=deterministic_order,
            shadow_recommendation_id=None,
            actual_deterministic_choice_id=actual,
            notes=("Evidence packet predates the immutable eligibility envelope.",),
        )
    evaluation_time = datetime.fromisoformat(
        normalize_timestamp(evaluated_at, "evaluated_at").replace("Z", "+00:00")
    )
    if evaluation_time < packet_time:
        return _decision(
            envelope,
            packet,
            evaluated_at=evaluated_at,
            disposition="INVALID_EVIDENCE",
            ranked_candidate_ids=deterministic_order,
            shadow_recommendation_id=None,
            actual_deterministic_choice_id=actual,
            notes=("Selection evaluation predates the bound evidence packet.",),
        )

    scoped_preference = None
    if explicit_scoped_preference_candidate_id is not None:
        scoped_preference = _text(
            explicit_scoped_preference_candidate_id,
            "explicit_scoped_preference_candidate_id",
            max_length=256,
        )
        if scoped_preference not in set(deterministic_order):
            return _decision(
                envelope,
                packet,
                evaluated_at=evaluated_at,
                disposition="DETERMINISTIC_FALLBACK",
                ranked_candidate_ids=deterministic_order,
                shadow_recommendation_id=None,
                actual_deterministic_choice_id=actual,
                notes=("Explicit scoped preference cannot restore an ineligible option.",),
            )

    if envelope.explicit_current_constraint_ref is not None:
        return _decision(
            envelope,
            packet,
            evaluated_at=evaluated_at,
            disposition="EXPLICIT_CONSTRAINT",
            ranked_candidate_ids=deterministic_order,
            shadow_recommendation_id=None,
            actual_deterministic_choice_id=actual,
            notes=("Explicit current constraint retains deterministic precedence.",),
        )

    candidate_ids = set(deterministic_order)
    qualified = [item for item in packet.items if item.qualification_status == "QUALIFIED"]
    if any(item.option_id not in candidate_ids for item in qualified):
        return _decision(
            envelope,
            packet,
            evaluated_at=evaluated_at,
            disposition="INVALID_EVIDENCE",
            ranked_candidate_ids=deterministic_order,
            shadow_recommendation_id=None,
            actual_deterministic_choice_id=actual,
            notes=("Qualified evidence referenced an option outside the eligibility envelope.",),
        )

    source_bindings: dict[str, str] = {}
    for item in qualified:
        prior = source_bindings.setdefault(item.source_digest, item.option_id)
        if prior != item.option_id:
            return _decision(
                envelope,
                packet,
                evaluated_at=evaluated_at,
                disposition="INVALID_EVIDENCE",
                ranked_candidate_ids=deterministic_order,
                shadow_recommendation_id=None,
                actual_deterministic_choice_id=actual,
                notes=("One evidence digest attempted to support multiple options.",),
            )

    if envelope.selection_type in {"MODEL", "WORKER"}:
        if any(item.source_kind in A3_EVIDENCE_SOURCE_KINDS for item in qualified):
            return _decision(
                envelope,
                packet,
                evaluated_at=evaluated_at,
                disposition="UNSUPPORTED_EVIDENCE_FOR_SELECTION_TYPE",
                ranked_candidate_ids=deterministic_order,
                shadow_recommendation_id=None,
                actual_deterministic_choice_id=actual,
                notes=("A3 tendency evidence cannot be reused as model or worker performance evidence.",),
            )
        qualified = [item for item in qualified if item.source_kind in DIRECT_OPTION_EVIDENCE_SOURCE_KINDS]
    else:
        unsupported_a3 = [
            item
            for item in qualified
            if item.source_kind in A3_EVIDENCE_SOURCE_KINDS
            and item.a3_candidate_type != "SPECIALIST_STRATEGY_TENDENCY"
        ]
        if unsupported_a3:
            return _decision(
                envelope,
                packet,
                evaluated_at=evaluated_at,
                disposition="UNSUPPORTED_EVIDENCE_FOR_SELECTION_TYPE",
                ranked_candidate_ids=deterministic_order,
                shadow_recommendation_id=None,
                actual_deterministic_choice_id=actual,
                notes=("Only A3 specialist-strategy tendency evidence may inform specialist-strategy ranking.",),
            )
        qualified = [
            item
            for item in qualified
            if item.source_kind in DIRECT_OPTION_EVIDENCE_SOURCE_KINDS
            or (
                item.source_kind in A3_EVIDENCE_SOURCE_KINDS
                and item.a3_candidate_type == "SPECIALIST_STRATEGY_TENDENCY"
            )
        ]

    deduped: list[SelectionEvidenceItem] = []
    seen_digests: set[str] = set()
    for item in qualified:
        if item.source_digest in seen_digests:
            continue
        seen_digests.add(item.source_digest)
        deduped.append(item)

    by_option: dict[str, list[SelectionEvidenceItem]] = {candidate_id: [] for candidate_id in deterministic_order}
    for item in deduped:
        by_option[item.option_id].append(item)

    support_counts = {
        option_id: len({item.source_digest for item in items if item.direction == "POSITIVE"})
        for option_id, items in by_option.items()
    }
    supported_options = {option_id for option_id, count in support_counts.items() if count >= MIN_DISTINCT_SUPPORT}
    if scoped_preference is not None:
        ranked_with_preference = (scoped_preference,) + tuple(
            candidate_id for candidate_id in deterministic_order if candidate_id != scoped_preference
        )
        return _decision(
            envelope,
            packet,
            evaluated_at=evaluated_at,
            disposition="SHADOW_RANKED",
            ranked_candidate_ids=ranked_with_preference,
            shadow_recommendation_id=scoped_preference,
            actual_deterministic_choice_id=actual,
            notes=("Explicit scoped user preference takes precedence over adaptive evidence.",),
        )
    if not supported_options:
        return _decision(
            envelope,
            packet,
            evaluated_at=evaluated_at,
            disposition="DETERMINISTIC_FALLBACK",
            ranked_candidate_ids=deterministic_order,
            shadow_recommendation_id=None,
            actual_deterministic_choice_id=actual,
            notes=("Qualified distinct positive support did not meet the adaptive preference floor.",),
        )

    def score(candidate_id: str) -> tuple[int, int, int]:
        items = by_option[candidate_id]
        positive = sum(1 for item in items if item.direction == "POSITIVE")
        negative = sum(1 for item in items if item.direction == "NEGATIVE")
        neutral = sum(1 for item in items if item.direction == "NEUTRAL")
        return (positive - negative, positive, neutral)

    ranked = tuple(
        sorted(
            deterministic_order,
            key=lambda candidate_id: (
                -score(candidate_id)[0],
                -score(candidate_id)[1],
                -score(candidate_id)[2],
                deterministic_order.index(candidate_id),
            ),
        )
    )
    recommendation = ranked[0] if ranked[0] in supported_options else actual
    if recommendation is None:
        return _decision(
            envelope,
            packet,
            evaluated_at=evaluated_at,
            disposition="DETERMINISTIC_FALLBACK",
            ranked_candidate_ids=deterministic_order,
            shadow_recommendation_id=None,
            actual_deterministic_choice_id=actual,
            notes=("Adaptive ranking produced no qualified recommendation.",),
        )

    return _decision(
        envelope,
        packet,
        evaluated_at=evaluated_at,
        disposition="SHADOW_RANKED",
        ranked_candidate_ids=ranked,
        shadow_recommendation_id=recommendation,
        actual_deterministic_choice_id=actual,
        notes=("Shadow ranking is non-authorizing and cannot change deterministic execution.",),
    )
