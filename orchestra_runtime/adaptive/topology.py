from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re
from typing import Any, Iterable, Mapping

from ..evidence import normalize_sha256, normalize_timestamp, receipt_digest


TOPOLOGY_ELIGIBILITY_SCHEMA_VERSION = "orchestra.adaptive-topology-eligibility-envelope.v1"
TOPOLOGY_EVIDENCE_SCHEMA_VERSION = "orchestra.adaptive-topology-evidence.v1"
TOPOLOGY_DECISION_SCHEMA_VERSION = "orchestra.adaptive-topology-decision.v1"
TOPOLOGY_SCORER_VERSION = "orchestra.adaptive-topology-scorer.v1"

REQUIRED_TOPOLOGY_INVARIANTS = (
    "coordination_validated",
    "required_specialists_complete",
    "ownership_complete",
    "authority_external_to_tuner",
    "governance_complete",
    "contradictions_resolved",
    "stale_contracts_resolved",
    "provider_privacy",
    "lifecycle",
    "resource_ceilings",
    "context_disclosure_ceiling",
)
TOPOLOGY_EVIDENCE_SOURCE_KINDS = frozenset(
    {
        "GOVERNED_COORDINATION_OUTCOME",
        "VALIDATION_EVIDENCE",
        "REMEDIATION_EVIDENCE",
        "TRUSTWORTHY_MEASURED_TELEMETRY",
    }
)
TOPOLOGY_EVIDENCE_DIRECTIONS = frozenset({"POSITIVE", "NEGATIVE", "NEUTRAL"})
TOPOLOGY_QUALIFICATION_STATUSES = frozenset({"QUALIFIED", "REJECTED"})
TOPOLOGY_MEASUREMENT_METRICS = frozenset(
    {
        "LATENCY",
        "COST",
        "TOKENS",
        "ITERATIONS",
        "REMEDIATIONS",
        "VALIDATION_FAILURES",
        "PARALLELISM",
    }
)
TOPOLOGY_DECISION_DISPOSITIONS = frozenset(
    {
        "SHADOW_RANKED",
        "DETERMINISTIC_FALLBACK",
        "NO_ELIGIBLE_TOPOLOGIES",
        "ADAPTIVE_UNAVAILABLE",
    }
)
MIN_DISTINCT_TOPOLOGY_SUPPORT = 2

_IDENTIFIER_RE = re.compile(r"^[a-z0-9][a-z0-9_.:-]{0,127}$")
_REASON_RE = re.compile(r"^[A-Z0-9][A-Z0-9_:-]{0,127}$")


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


def _optional_text(
    value: object | None,
    field_name: str,
    *,
    max_length: int = 512,
) -> str | None:
    return None if value is None else _text(value, field_name, max_length=max_length)


def _identifier(value: object, field_name: str) -> str:
    text = _text(value, field_name, max_length=128).casefold()
    if not _IDENTIFIER_RE.fullmatch(text):
        raise ValueError(f"{field_name} must be a canonical identifier")
    return text


def _positive_revision(value: object, field_name: str = "coordination_contract_revision") -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{field_name} must be a positive integer")
    return value


def _exact_bool(value: object, field_name: str) -> bool:
    if type(value) is not bool:
        raise TypeError(f"{field_name} must be an exact boolean")
    return value


def _ordered_identifiers(
    values: Iterable[object],
    field_name: str,
    *,
    max_items: int,
    require_nonempty: bool = False,
) -> tuple[str, ...]:
    normalized = tuple(_identifier(value, field_name) for value in values)
    if len(normalized) > max_items:
        raise ValueError(f"{field_name} exceeds {max_items} items")
    if require_nonempty and not normalized:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} contains duplicate values")
    return normalized


def _stable_identifiers(
    values: Iterable[object],
    field_name: str,
    *,
    max_items: int,
    require_nonempty: bool = False,
) -> tuple[str, ...]:
    return tuple(
        sorted(
            _ordered_identifiers(
                values,
                field_name,
                max_items=max_items,
                require_nonempty=require_nonempty,
            )
        )
    )


def _stable_strings(
    values: Iterable[object],
    field_name: str,
    *,
    max_items: int,
    require_nonempty: bool = False,
) -> tuple[str, ...]:
    normalized = tuple(_text(value, field_name) for value in values)
    if len(normalized) > max_items:
        raise ValueError(f"{field_name} exceeds {max_items} items")
    if require_nonempty and not normalized:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} contains duplicate values")
    return tuple(sorted(normalized))


def _reason_code(value: object) -> str:
    reason = _text(value, "reason_code", max_length=128).upper()
    if not _REASON_RE.fullmatch(reason):
        raise ValueError("reason_code must be a canonical upper-case code")
    return reason


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    return f"{prefix}.{receipt_digest(dict(payload))[:24]}"


def _utc_timestamp(value: str, field_name: str) -> tuple[str, datetime]:
    normalized = normalize_timestamp(value, field_name)
    parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    return normalized, parsed


@dataclass(frozen=True, slots=True)
class TopologyStage:
    stage_id: str
    mode: str
    specialists: tuple[str, ...]
    join_required: bool
    review_owner: str | None = None

    def __post_init__(self) -> None:
        mode = _text(self.mode, "mode", max_length=32).upper()
        if mode not in {"SEQUENTIAL", "PARALLEL"}:
            raise ValueError(f"unsupported topology stage mode '{mode}'")
        object.__setattr__(self, "stage_id", _identifier(self.stage_id, "stage_id"))
        object.__setattr__(self, "mode", mode)
        object.__setattr__(
            self,
            "specialists",
            _ordered_identifiers(
                self.specialists,
                "specialist",
                max_items=64,
                require_nonempty=True,
            ),
        )
        object.__setattr__(self, "join_required", _exact_bool(self.join_required, "join_required"))
        object.__setattr__(
            self,
            "review_owner",
            None if self.review_owner is None else _identifier(self.review_owner, "review_owner"),
        )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "stage_id": self.stage_id,
            "mode": self.mode,
            "specialists": list(self.specialists),
            "join_required": self.join_required,
        }
        if self.review_owner is not None:
            payload["review_owner"] = self.review_owner
        return payload


@dataclass(frozen=True, slots=True)
class TopologyCandidate:
    candidate_id: str
    coordination_contract_revision: int
    required_specialists: tuple[str, ...]
    stages: tuple[TopologyStage, ...]
    reentry_order: tuple[str, ...]
    prior_output_disclosure_refs: tuple[str, ...]
    eligibility_evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        required = _stable_identifiers(
            self.required_specialists,
            "required_specialist",
            max_items=64,
            require_nonempty=True,
        )
        stages = tuple(self.stages)
        if not stages or len(stages) > 64:
            raise ValueError("stages must contain between 1 and 64 stages")
        if any(not isinstance(stage, TopologyStage) for stage in stages):
            raise TypeError("stages must contain TopologyStage values")
        stage_ids = tuple(stage.stage_id for stage in stages)
        if len(stage_ids) != len(set(stage_ids)):
            raise ValueError("stage ids must be unique")
        required_set = set(required)
        stage_specialists = {
            specialist for stage in stages for specialist in stage.specialists
        }
        if not required_set.issubset(stage_specialists):
            raise ValueError("topology stages must include every required specialist")

        reentry = _ordered_identifiers(
            self.reentry_order,
            "reentry_specialist",
            max_items=64,
        )

        object.__setattr__(
            self,
            "candidate_id",
            _text(self.candidate_id, "candidate_id", max_length=256),
        )
        object.__setattr__(
            self,
            "coordination_contract_revision",
            _positive_revision(self.coordination_contract_revision),
        )
        object.__setattr__(self, "required_specialists", required)
        object.__setattr__(self, "stages", stages)
        object.__setattr__(self, "reentry_order", reentry)
        object.__setattr__(
            self,
            "prior_output_disclosure_refs",
            _stable_strings(
                self.prior_output_disclosure_refs,
                "prior_output_disclosure_ref",
                max_items=128,
            ),
        )
        object.__setattr__(
            self,
            "eligibility_evidence_refs",
            _stable_strings(
                self.eligibility_evidence_refs,
                "eligibility_evidence_ref",
                max_items=64,
                require_nonempty=True,
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "coordination_contract_revision": self.coordination_contract_revision,
            "required_specialists": list(self.required_specialists),
            "stages": [stage.to_dict() for stage in self.stages],
            "reentry_order": list(self.reentry_order),
            "prior_output_disclosure_refs": list(self.prior_output_disclosure_refs),
            "eligibility_status": "ELIGIBLE",
            "eligibility_evidence_refs": list(self.eligibility_evidence_refs),
        }


@dataclass(frozen=True, slots=True)
class TopologyEligibilityEnvelope:
    envelope_id: str
    session_id: str
    created_at: str
    user_key: str
    coordination_contract_ref: str
    coordination_contract_revision: int
    required_specialists: tuple[str, ...]
    invariants_applied: Mapping[str, bool]
    invariant_evidence_refs: tuple[str, ...]
    candidates: tuple[TopologyCandidate, ...]
    project_key: str | None = None
    task_session_key: str | None = None
    deterministic_topology_candidate_id: str | None = None
    explicit_current_constraint_ref: str | None = None
    schema_version: str = TOPOLOGY_ELIGIBILITY_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != TOPOLOGY_ELIGIBILITY_SCHEMA_VERSION:
            raise ValueError(f"unsupported topology eligibility schema '{self.schema_version}'")
        revision = _positive_revision(self.coordination_contract_revision)
        required = _stable_identifiers(
            self.required_specialists,
            "required_specialist",
            max_items=64,
            require_nonempty=True,
        )
        invariants = dict(self.invariants_applied)
        if set(invariants) != set(REQUIRED_TOPOLOGY_INVARIANTS):
            raise ValueError("all frozen topology invariants must be present")
        if any(invariants.get(key) is not True for key in REQUIRED_TOPOLOGY_INVARIANTS):
            raise ValueError("all frozen topology invariants must be true before ranking")

        candidates = tuple(self.candidates)
        if len(candidates) > 128:
            raise ValueError("candidates exceeds 128 items")
        if any(not isinstance(candidate, TopologyCandidate) for candidate in candidates):
            raise TypeError("candidates must contain TopologyCandidate values")
        candidate_ids = tuple(candidate.candidate_id for candidate in candidates)
        if len(candidate_ids) != len(set(candidate_ids)):
            raise ValueError("candidate ids must be unique")
        for candidate in candidates:
            if candidate.coordination_contract_revision != revision:
                raise ValueError("candidate revision must match envelope revision")
            if candidate.required_specialists != required:
                raise ValueError("candidate required_specialists must equal the envelope required set")

        deterministic = _optional_text(
            self.deterministic_topology_candidate_id,
            "deterministic_topology_candidate_id",
            max_length=256,
        )
        if candidates and deterministic is None:
            raise ValueError("eligible topology set requires deterministic_topology_candidate_id")
        if deterministic is not None and candidates and deterministic not in set(candidate_ids):
            raise ValueError("deterministic topology must be present in the immutable eligible set")

        object.__setattr__(self, "envelope_id", _text(self.envelope_id, "envelope_id", max_length=256))
        object.__setattr__(self, "session_id", _text(self.session_id, "session_id", max_length=256))
        object.__setattr__(self, "created_at", normalize_timestamp(self.created_at, "created_at"))
        object.__setattr__(self, "user_key", _text(self.user_key, "user_key", max_length=256))
        object.__setattr__(
            self,
            "project_key",
            _optional_text(self.project_key, "project_key", max_length=256),
        )
        object.__setattr__(
            self,
            "task_session_key",
            _optional_text(self.task_session_key, "task_session_key", max_length=256),
        )
        object.__setattr__(
            self,
            "coordination_contract_ref",
            _text(self.coordination_contract_ref, "coordination_contract_ref"),
        )
        object.__setattr__(self, "coordination_contract_revision", revision)
        object.__setattr__(self, "required_specialists", required)
        object.__setattr__(
            self,
            "invariants_applied",
            {key: True for key in REQUIRED_TOPOLOGY_INVARIANTS},
        )
        object.__setattr__(
            self,
            "invariant_evidence_refs",
            _stable_strings(
                self.invariant_evidence_refs,
                "invariant_evidence_ref",
                max_items=128,
                require_nonempty=True,
            ),
        )
        object.__setattr__(self, "candidates", candidates)
        object.__setattr__(self, "deterministic_topology_candidate_id", deterministic)
        object.__setattr__(
            self,
            "explicit_current_constraint_ref",
            _optional_text(
                self.explicit_current_constraint_ref,
                "explicit_current_constraint_ref",
            ),
        )

    @property
    def disposition(self) -> str:
        return "ELIGIBLE_TOPOLOGY_SET_READY" if self.candidates else "NO_ELIGIBLE_TOPOLOGIES"

    @property
    def candidate_ids(self) -> tuple[str, ...]:
        return tuple(candidate.candidate_id for candidate in self.candidates)

    def candidate_by_id(self, candidate_id: str) -> TopologyCandidate | None:
        return next(
            (candidate for candidate in self.candidates if candidate.candidate_id == candidate_id),
            None,
        )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_version": self.schema_version,
            "envelope_id": self.envelope_id,
            "session_id": self.session_id,
            "created_at": self.created_at,
            "user_key": self.user_key,
            "coordination_contract_ref": self.coordination_contract_ref,
            "coordination_contract_revision": self.coordination_contract_revision,
            "required_specialists": list(self.required_specialists),
            "invariants_applied": dict(self.invariants_applied),
            "invariant_evidence_refs": list(self.invariant_evidence_refs),
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "disposition": self.disposition,
        }
        if self.project_key is not None:
            payload["project_key"] = self.project_key
        if self.task_session_key is not None:
            payload["task_session_key"] = self.task_session_key
        if self.deterministic_topology_candidate_id is not None:
            payload["deterministic_topology_candidate_id"] = self.deterministic_topology_candidate_id
        if self.explicit_current_constraint_ref is not None:
            payload["explicit_current_constraint_ref"] = self.explicit_current_constraint_ref
        return payload

    @property
    def digest(self) -> str:
        return receipt_digest(self.to_dict())


@dataclass(frozen=True, slots=True)
class TopologyMeasuredMetric:
    metric_name: str
    value: float
    unit: str
    measurement_ref: str

    def __post_init__(self) -> None:
        metric = _text(self.metric_name, "metric_name", max_length=64).upper()
        if metric not in TOPOLOGY_MEASUREMENT_METRICS:
            raise ValueError(f"unsupported topology metric '{metric}'")
        if isinstance(self.value, bool) or not isinstance(self.value, (int, float)):
            raise TypeError("measured metric value must be numeric")
        numeric = float(self.value)
        if numeric < 0:
            raise ValueError("measured metric value must be non-negative")
        object.__setattr__(self, "metric_name", metric)
        object.__setattr__(self, "value", numeric)
        object.__setattr__(self, "unit", _text(self.unit, "unit", max_length=64))
        object.__setattr__(
            self,
            "measurement_ref",
            _text(self.measurement_ref, "measurement_ref"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "value": self.value,
            "unit": self.unit,
            "measurement_ref": self.measurement_ref,
        }


@dataclass(frozen=True, slots=True)
class TopologyEvidenceItem:
    evidence_id: str
    source_kind: str
    source_ref: str
    source_digest: str
    candidate_id: str
    session_id: str
    coordination_contract_revision: int
    qualification_status: str
    reason_code: str
    direction: str
    measured_metric: TopologyMeasuredMetric | None = None

    def __post_init__(self) -> None:
        source_kind = _text(self.source_kind, "source_kind", max_length=64).upper()
        if source_kind not in TOPOLOGY_EVIDENCE_SOURCE_KINDS:
            raise ValueError(f"unsupported topology evidence source kind '{source_kind}'")
        status = _text(
            self.qualification_status,
            "qualification_status",
            max_length=32,
        ).upper()
        if status not in TOPOLOGY_QUALIFICATION_STATUSES:
            raise ValueError(f"unsupported qualification status '{status}'")
        direction = _text(self.direction, "direction", max_length=32).upper()
        if direction not in TOPOLOGY_EVIDENCE_DIRECTIONS:
            raise ValueError(f"unsupported topology evidence direction '{direction}'")
        if source_kind == "TRUSTWORTHY_MEASURED_TELEMETRY":
            if not isinstance(self.measured_metric, TopologyMeasuredMetric):
                raise ValueError("trustworthy measured telemetry requires a measured_metric")
        elif self.measured_metric is not None:
            raise ValueError("measured_metric is valid only for trustworthy measured telemetry")

        object.__setattr__(self, "evidence_id", _text(self.evidence_id, "evidence_id", max_length=256))
        object.__setattr__(self, "source_kind", source_kind)
        object.__setattr__(self, "source_ref", _text(self.source_ref, "source_ref"))
        object.__setattr__(
            self,
            "source_digest",
            normalize_sha256(self.source_digest, "source_digest"),
        )
        object.__setattr__(
            self,
            "candidate_id",
            _text(self.candidate_id, "candidate_id", max_length=256),
        )
        object.__setattr__(self, "session_id", _text(self.session_id, "session_id", max_length=256))
        object.__setattr__(
            self,
            "coordination_contract_revision",
            _positive_revision(self.coordination_contract_revision),
        )
        object.__setattr__(self, "qualification_status", status)
        object.__setattr__(self, "reason_code", _reason_code(self.reason_code))
        object.__setattr__(self, "direction", direction)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "evidence_id": self.evidence_id,
            "source_kind": self.source_kind,
            "source_ref": self.source_ref,
            "source_digest": self.source_digest,
            "candidate_id": self.candidate_id,
            "session_id": self.session_id,
            "coordination_contract_revision": self.coordination_contract_revision,
            "qualification_status": self.qualification_status,
            "reason_code": self.reason_code,
            "direction": self.direction,
        }
        if self.measured_metric is not None:
            payload["measured_metric"] = self.measured_metric.to_dict()
        return payload


@dataclass(frozen=True, slots=True)
class TopologyEvidencePacket:
    packet_id: str
    eligibility_envelope_id: str
    eligibility_digest: str
    session_id: str
    coordination_contract_revision: int
    collected_at: str
    items: tuple[TopologyEvidenceItem, ...]
    schema_version: str = TOPOLOGY_EVIDENCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != TOPOLOGY_EVIDENCE_SCHEMA_VERSION:
            raise ValueError(f"unsupported topology evidence schema '{self.schema_version}'")
        items = tuple(self.items)
        if len(items) > 512:
            raise ValueError("topology evidence exceeds 512 items")
        if any(not isinstance(item, TopologyEvidenceItem) for item in items):
            raise TypeError("items must contain TopologyEvidenceItem values")
        evidence_ids = tuple(item.evidence_id for item in items)
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("topology evidence ids must be unique")

        object.__setattr__(self, "packet_id", _text(self.packet_id, "packet_id", max_length=256))
        object.__setattr__(
            self,
            "eligibility_envelope_id",
            _text(self.eligibility_envelope_id, "eligibility_envelope_id", max_length=256),
        )
        object.__setattr__(
            self,
            "eligibility_digest",
            normalize_sha256(self.eligibility_digest, "eligibility_digest"),
        )
        object.__setattr__(self, "session_id", _text(self.session_id, "session_id", max_length=256))
        object.__setattr__(
            self,
            "coordination_contract_revision",
            _positive_revision(self.coordination_contract_revision),
        )
        object.__setattr__(self, "collected_at", normalize_timestamp(self.collected_at, "collected_at"))
        object.__setattr__(self, "items", items)

    def _payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "packet_id": self.packet_id,
            "eligibility_envelope_id": self.eligibility_envelope_id,
            "eligibility_digest": self.eligibility_digest,
            "session_id": self.session_id,
            "coordination_contract_revision": self.coordination_contract_revision,
            "collected_at": self.collected_at,
            "items": [item.to_dict() for item in self.items],
        }

    @property
    def digest(self) -> str:
        return receipt_digest(self._payload())

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "digest": self.digest}


@dataclass(frozen=True, slots=True)
class TopologyDecision:
    decision_id: str
    session_id: str
    coordination_contract_revision: int
    eligibility_envelope_id: str
    eligibility_digest: str
    evidence_packet_id: str
    evidence_digest: str
    evaluated_at: str
    required_specialists: tuple[str, ...]
    ranked_candidate_ids: tuple[str, ...]
    actual_deterministic_candidate_id: str
    disposition: str
    reason_codes: tuple[str, ...]
    shadow_recommendation_id: str | None = None
    scorer_version: str = TOPOLOGY_SCORER_VERSION
    schema_version: str = TOPOLOGY_DECISION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != TOPOLOGY_DECISION_SCHEMA_VERSION:
            raise ValueError(f"unsupported topology decision schema '{self.schema_version}'")
        disposition = _text(self.disposition, "disposition", max_length=64).upper()
        if disposition not in TOPOLOGY_DECISION_DISPOSITIONS:
            raise ValueError(f"unsupported topology disposition '{disposition}'")
        ranked = tuple(
            _text(item, "ranked_candidate_id", max_length=256)
            for item in self.ranked_candidate_ids
        )
        if len(ranked) > 128 or len(ranked) != len(set(ranked)):
            raise ValueError("ranked_candidate_ids must be unique and bounded")
        reasons = tuple(_reason_code(reason) for reason in self.reason_codes)
        if not reasons or len(reasons) > 64 or len(reasons) != len(set(reasons)):
            raise ValueError("reason_codes must be non-empty, unique, and bounded")

        object.__setattr__(self, "decision_id", _text(self.decision_id, "decision_id", max_length=256))
        object.__setattr__(self, "session_id", _text(self.session_id, "session_id", max_length=256))
        object.__setattr__(
            self,
            "coordination_contract_revision",
            _positive_revision(self.coordination_contract_revision),
        )
        object.__setattr__(
            self,
            "eligibility_envelope_id",
            _text(self.eligibility_envelope_id, "eligibility_envelope_id", max_length=256),
        )
        object.__setattr__(
            self,
            "eligibility_digest",
            normalize_sha256(self.eligibility_digest, "eligibility_digest"),
        )
        object.__setattr__(
            self,
            "evidence_packet_id",
            _text(self.evidence_packet_id, "evidence_packet_id", max_length=256),
        )
        object.__setattr__(
            self,
            "evidence_digest",
            normalize_sha256(self.evidence_digest, "evidence_digest"),
        )
        object.__setattr__(self, "evaluated_at", normalize_timestamp(self.evaluated_at, "evaluated_at"))
        object.__setattr__(
            self,
            "scorer_version",
            _identifier(self.scorer_version, "scorer_version"),
        )
        object.__setattr__(
            self,
            "required_specialists",
            _stable_identifiers(
                self.required_specialists,
                "required_specialist",
                max_items=64,
                require_nonempty=True,
            ),
        )
        object.__setattr__(self, "ranked_candidate_ids", ranked)
        object.__setattr__(
            self,
            "actual_deterministic_candidate_id",
            _text(
                self.actual_deterministic_candidate_id,
                "actual_deterministic_candidate_id",
                max_length=256,
            ),
        )
        object.__setattr__(
            self,
            "shadow_recommendation_id",
            _optional_text(
                self.shadow_recommendation_id,
                "shadow_recommendation_id",
                max_length=256,
            ),
        )
        object.__setattr__(self, "disposition", disposition)
        object.__setattr__(self, "reason_codes", reasons)

    def _payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_version": self.schema_version,
            "decision_id": self.decision_id,
            "session_id": self.session_id,
            "coordination_contract_revision": self.coordination_contract_revision,
            "eligibility_envelope_id": self.eligibility_envelope_id,
            "eligibility_digest": self.eligibility_digest,
            "evidence_packet_id": self.evidence_packet_id,
            "evidence_digest": self.evidence_digest,
            "evaluated_at": self.evaluated_at,
            "scorer_version": self.scorer_version,
            "required_specialists": list(self.required_specialists),
            "ranked_candidate_ids": list(self.ranked_candidate_ids),
            "actual_deterministic_candidate_id": self.actual_deterministic_candidate_id,
            "disposition": self.disposition,
            "execution_controlled_by": "DETERMINISTIC_ORCHESTRA",
            "dispatch_controlled_by": "CONDUCTOR",
            "transition_controlled_by": "ARBITER",
            "topology_effective": False,
            "shadow_influenced_execution": False,
            "promotion_state": "NOT_PROMOTED",
            "reason_codes": list(self.reason_codes),
        }
        if self.shadow_recommendation_id is not None:
            payload["shadow_recommendation_id"] = self.shadow_recommendation_id
        return payload

    @property
    def digest(self) -> str:
        return receipt_digest(self._payload())

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "digest": self.digest}


def build_topology_eligibility_envelope(
    *,
    session_id: str,
    created_at: str,
    user_key: str,
    coordination_contract_ref: str,
    coordination_contract_revision: int,
    required_specialists: Iterable[str],
    invariant_evidence_refs: Iterable[str],
    candidates: Iterable[TopologyCandidate],
    deterministic_topology_candidate_id: str | None,
    invariants_applied: Mapping[str, bool],
    project_key: str | None = None,
    task_session_key: str | None = None,
    explicit_current_constraint_ref: str | None = None,
) -> TopologyEligibilityEnvelope:
    candidate_tuple = tuple(candidates)
    normalized_required = _stable_identifiers(
        required_specialists,
        "required_specialist",
        max_items=64,
        require_nonempty=True,
    )
    identity = {
        "session_id": _text(session_id, "session_id", max_length=256),
        "created_at": normalize_timestamp(created_at, "created_at"),
        "user_key": _text(user_key, "user_key", max_length=256),
        "project_key": project_key,
        "task_session_key": task_session_key,
        "coordination_contract_ref": _text(
            coordination_contract_ref,
            "coordination_contract_ref",
        ),
        "coordination_contract_revision": _positive_revision(
            coordination_contract_revision
        ),
        "required_specialists": list(normalized_required),
        "candidate_ids": [candidate.candidate_id for candidate in candidate_tuple],
        "deterministic_topology_candidate_id": deterministic_topology_candidate_id,
    }
    return TopologyEligibilityEnvelope(
        envelope_id=_stable_id("topology-envelope", identity),
        session_id=session_id,
        created_at=created_at,
        user_key=user_key,
        project_key=project_key,
        task_session_key=task_session_key,
        coordination_contract_ref=coordination_contract_ref,
        coordination_contract_revision=coordination_contract_revision,
        deterministic_topology_candidate_id=deterministic_topology_candidate_id,
        explicit_current_constraint_ref=explicit_current_constraint_ref,
        required_specialists=normalized_required,
        invariants_applied=invariants_applied,
        invariant_evidence_refs=tuple(invariant_evidence_refs),
        candidates=candidate_tuple,
    )


def qualify_topology_evidence(
    envelope: TopologyEligibilityEnvelope,
    *,
    candidate_id: str,
    source_kind: str,
    source_ref: str,
    source_digest: str,
    session_id: str,
    coordination_contract_revision: int,
    direction: str,
    measured_metric: TopologyMeasuredMetric | None = None,
) -> TopologyEvidenceItem:
    if not isinstance(envelope, TopologyEligibilityEnvelope):
        raise TypeError("envelope must be TopologyEligibilityEnvelope")
    normalized_source_kind = _text(source_kind, "source_kind", max_length=64).upper()
    if normalized_source_kind not in TOPOLOGY_EVIDENCE_SOURCE_KINDS:
        raise ValueError(f"unsupported topology evidence source kind '{normalized_source_kind}'")

    candidate_key = _text(candidate_id, "candidate_id", max_length=256)
    session_key = _text(session_id, "session_id", max_length=256)
    revision = _positive_revision(coordination_contract_revision)
    candidate = envelope.candidate_by_id(candidate_key)

    qualified = True
    reason = "EXACT_TOPOLOGY_BOUND_GOVERNED_EVIDENCE"
    if candidate is None:
        qualified = False
        reason = "TOPOLOGY_CANDIDATE_NOT_ELIGIBLE"
    elif session_key != envelope.session_id:
        qualified = False
        reason = "TOPOLOGY_SESSION_MISMATCH"
    elif (
        revision != envelope.coordination_contract_revision
        or candidate.coordination_contract_revision != revision
    ):
        qualified = False
        reason = "TOPOLOGY_CONTRACT_REVISION_MISMATCH"
    elif normalized_source_kind == "VALIDATION_EVIDENCE":
        reason = "EXACT_TOPOLOGY_BOUND_VALIDATION_EVIDENCE"
    elif normalized_source_kind == "REMEDIATION_EVIDENCE":
        reason = "EXACT_TOPOLOGY_BOUND_REMEDIATION_EVIDENCE"
    elif normalized_source_kind == "TRUSTWORTHY_MEASURED_TELEMETRY":
        reason = "EXACT_TOPOLOGY_BOUND_MEASURED_TELEMETRY"

    normalized_digest = normalize_sha256(source_digest, "source_digest")
    return TopologyEvidenceItem(
        evidence_id=_stable_id(
            "topology-evidence",
            {
                "source_ref": _text(source_ref, "source_ref"),
                "source_digest": normalized_digest,
                "candidate_id": candidate_key,
                "session_id": session_key,
                "coordination_contract_revision": revision,
            },
        ),
        source_kind=normalized_source_kind,
        source_ref=source_ref,
        source_digest=normalized_digest,
        candidate_id=candidate_key,
        session_id=session_key,
        coordination_contract_revision=revision,
        qualification_status="QUALIFIED" if qualified else "REJECTED",
        reason_code=reason,
        direction=direction,
        measured_metric=measured_metric,
    )


def build_topology_evidence_packet(
    envelope: TopologyEligibilityEnvelope,
    *,
    collected_at: str,
    items: Iterable[TopologyEvidenceItem],
) -> TopologyEvidencePacket:
    if not isinstance(envelope, TopologyEligibilityEnvelope):
        raise TypeError("envelope must be TopologyEligibilityEnvelope")
    item_tuple = tuple(items)
    normalized_at = normalize_timestamp(collected_at, "collected_at")
    return TopologyEvidencePacket(
        packet_id=_stable_id(
            "topology-packet",
            {
                "eligibility_envelope_id": envelope.envelope_id,
                "eligibility_digest": envelope.digest,
                "session_id": envelope.session_id,
                "coordination_contract_revision": envelope.coordination_contract_revision,
                "collected_at": normalized_at,
                "evidence_ids": [item.evidence_id for item in item_tuple],
            },
        ),
        eligibility_envelope_id=envelope.envelope_id,
        eligibility_digest=envelope.digest,
        session_id=envelope.session_id,
        coordination_contract_revision=envelope.coordination_contract_revision,
        collected_at=normalized_at,
        items=item_tuple,
    )


def _decision(
    envelope: TopologyEligibilityEnvelope,
    packet: TopologyEvidencePacket,
    *,
    evaluated_at: str,
    disposition: str,
    ranked_candidate_ids: tuple[str, ...],
    actual_deterministic_candidate_id: str,
    reason_codes: Iterable[str],
    shadow_recommendation_id: str | None = None,
) -> TopologyDecision:
    normalized_at = normalize_timestamp(evaluated_at, "evaluated_at")
    reasons = tuple(_reason_code(reason) for reason in reason_codes)
    payload = {
        "session_id": envelope.session_id,
        "coordination_contract_revision": envelope.coordination_contract_revision,
        "eligibility_envelope_id": envelope.envelope_id,
        "eligibility_digest": envelope.digest,
        "evidence_packet_id": packet.packet_id,
        "evidence_digest": packet.digest,
        "evaluated_at": normalized_at,
        "scorer_version": TOPOLOGY_SCORER_VERSION,
        "ranked_candidate_ids": list(ranked_candidate_ids),
        "actual_deterministic_candidate_id": actual_deterministic_candidate_id,
        "shadow_recommendation_id": shadow_recommendation_id,
        "disposition": disposition,
        "reason_codes": list(reasons),
    }
    return TopologyDecision(
        decision_id=_stable_id("topology-decision", payload),
        session_id=envelope.session_id,
        coordination_contract_revision=envelope.coordination_contract_revision,
        eligibility_envelope_id=envelope.envelope_id,
        eligibility_digest=envelope.digest,
        evidence_packet_id=packet.packet_id,
        evidence_digest=packet.digest,
        evaluated_at=normalized_at,
        required_specialists=envelope.required_specialists,
        ranked_candidate_ids=ranked_candidate_ids,
        actual_deterministic_candidate_id=actual_deterministic_candidate_id,
        shadow_recommendation_id=shadow_recommendation_id,
        disposition=disposition,
        reason_codes=reasons,
    )


def rank_shadow_topologies(
    envelope: TopologyEligibilityEnvelope,
    packet: TopologyEvidencePacket,
    *,
    actual_deterministic_candidate_id: str,
    evaluated_at: str,
    explicit_scoped_preference_candidate_id: str | None = None,
    adaptive_available: bool = True,
) -> TopologyDecision:
    """Rank only pre-qualified topology candidates without influencing execution or dispatch."""

    if not isinstance(envelope, TopologyEligibilityEnvelope):
        raise TypeError("envelope must be TopologyEligibilityEnvelope")
    if not isinstance(packet, TopologyEvidencePacket):
        raise TypeError("packet must be TopologyEvidencePacket")
    if type(adaptive_available) is not bool:
        raise TypeError("adaptive_available must be an exact boolean")

    deterministic_order = envelope.candidate_ids
    actual = _text(
        actual_deterministic_candidate_id,
        "actual_deterministic_candidate_id",
        max_length=256,
    )

    if not adaptive_available:
        return _decision(
            envelope,
            packet,
            evaluated_at=evaluated_at,
            disposition="ADAPTIVE_UNAVAILABLE",
            ranked_candidate_ids=deterministic_order,
            actual_deterministic_candidate_id=actual,
            reason_codes=("ADAPTIVE_LAYER_UNAVAILABLE_DETERMINISTIC_FALLBACK",),
        )

    if not envelope.candidates:
        return _decision(
            envelope,
            packet,
            evaluated_at=evaluated_at,
            disposition="NO_ELIGIBLE_TOPOLOGIES",
            ranked_candidate_ids=(),
            actual_deterministic_candidate_id=actual,
            reason_codes=("NO_ELIGIBLE_TOPOLOGIES_FAIL_CLOSED",),
        )

    if actual not in set(deterministic_order):
        return _decision(
            envelope,
            packet,
            evaluated_at=evaluated_at,
            disposition="DETERMINISTIC_FALLBACK",
            ranked_candidate_ids=deterministic_order,
            actual_deterministic_candidate_id=actual,
            reason_codes=("ACTUAL_DETERMINISTIC_TOPOLOGY_NOT_ELIGIBLE",),
        )

    if envelope.deterministic_topology_candidate_id != actual:
        return _decision(
            envelope,
            packet,
            evaluated_at=evaluated_at,
            disposition="DETERMINISTIC_FALLBACK",
            ranked_candidate_ids=deterministic_order,
            actual_deterministic_candidate_id=actual,
            reason_codes=("DETERMINISTIC_TOPOLOGY_IDENTITY_MISMATCH",),
        )

    if (
        packet.eligibility_envelope_id != envelope.envelope_id
        or packet.eligibility_digest != envelope.digest
        or packet.session_id != envelope.session_id
        or packet.coordination_contract_revision != envelope.coordination_contract_revision
    ):
        return _decision(
            envelope,
            packet,
            evaluated_at=evaluated_at,
            disposition="DETERMINISTIC_FALLBACK",
            ranked_candidate_ids=deterministic_order,
            actual_deterministic_candidate_id=actual,
            reason_codes=("EVIDENCE_PACKET_BINDING_MISMATCH",),
        )

    _, envelope_time = _utc_timestamp(envelope.created_at, "created_at")
    _, packet_time = _utc_timestamp(packet.collected_at, "collected_at")
    if packet_time < envelope_time:
        return _decision(
            envelope,
            packet,
            evaluated_at=evaluated_at,
            disposition="DETERMINISTIC_FALLBACK",
            ranked_candidate_ids=deterministic_order,
            actual_deterministic_candidate_id=actual,
            reason_codes=("EVIDENCE_PACKET_PREDATES_ELIGIBILITY",),
        )
    _, evaluation_time = _utc_timestamp(evaluated_at, "evaluated_at")
    if evaluation_time < packet_time:
        return _decision(
            envelope,
            packet,
            evaluated_at=evaluated_at,
            disposition="DETERMINISTIC_FALLBACK",
            ranked_candidate_ids=deterministic_order,
            actual_deterministic_candidate_id=actual,
            reason_codes=("EVALUATION_PREDATES_EVIDENCE_PACKET",),
        )

    if envelope.explicit_current_constraint_ref is not None:
        return _decision(
            envelope,
            packet,
            evaluated_at=evaluated_at,
            disposition="DETERMINISTIC_FALLBACK",
            ranked_candidate_ids=deterministic_order,
            actual_deterministic_candidate_id=actual,
            reason_codes=("EXPLICIT_CURRENT_CONSTRAINT_PRECEDENCE",),
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
                actual_deterministic_candidate_id=actual,
                reason_codes=("SCOPED_PREFERENCE_NOT_ELIGIBLE",),
            )

    qualified = [
        item for item in packet.items if item.qualification_status == "QUALIFIED"
    ]
    candidate_ids = set(deterministic_order)
    for item in qualified:
        if (
            item.candidate_id not in candidate_ids
            or item.session_id != envelope.session_id
            or item.coordination_contract_revision
            != envelope.coordination_contract_revision
        ):
            return _decision(
                envelope,
                packet,
                evaluated_at=evaluated_at,
                disposition="DETERMINISTIC_FALLBACK",
                ranked_candidate_ids=deterministic_order,
                actual_deterministic_candidate_id=actual,
                reason_codes=("QUALIFIED_EVIDENCE_EXACT_BINDING_FAILURE",),
            )

    digest_bindings: dict[str, str] = {}
    for item in qualified:
        prior = digest_bindings.setdefault(item.source_digest, item.candidate_id)
        if prior != item.candidate_id:
            return _decision(
                envelope,
                packet,
                evaluated_at=evaluated_at,
                disposition="DETERMINISTIC_FALLBACK",
                ranked_candidate_ids=deterministic_order,
                actual_deterministic_candidate_id=actual,
                reason_codes=("EVIDENCE_DIGEST_MULTI_CANDIDATE_BINDING",),
            )

    deduped: list[TopologyEvidenceItem] = []
    seen_digests: set[str] = set()
    for item in qualified:
        if item.source_digest in seen_digests:
            continue
        seen_digests.add(item.source_digest)
        deduped.append(item)

    by_candidate: dict[str, list[TopologyEvidenceItem]] = {
        candidate_id: [] for candidate_id in deterministic_order
    }
    for item in deduped:
        by_candidate[item.candidate_id].append(item)

    if scoped_preference is not None:
        ranked_with_preference = (scoped_preference,) + tuple(
            candidate_id
            for candidate_id in deterministic_order
            if candidate_id != scoped_preference
        )
        return _decision(
            envelope,
            packet,
            evaluated_at=evaluated_at,
            disposition="SHADOW_RANKED",
            ranked_candidate_ids=ranked_with_preference,
            actual_deterministic_candidate_id=actual,
            shadow_recommendation_id=scoped_preference,
            reason_codes=("EXPLICIT_SCOPED_PREFERENCE_PRECEDENCE",),
        )

    support_counts = {
        candidate_id: len(
            {
                item.source_digest
                for item in items
                if item.direction == "POSITIVE"
            }
        )
        for candidate_id, items in by_candidate.items()
    }
    supported_candidates = {
        candidate_id
        for candidate_id, count in support_counts.items()
        if count >= MIN_DISTINCT_TOPOLOGY_SUPPORT
    }
    if not supported_candidates:
        return _decision(
            envelope,
            packet,
            evaluated_at=evaluated_at,
            disposition="DETERMINISTIC_FALLBACK",
            ranked_candidate_ids=deterministic_order,
            actual_deterministic_candidate_id=actual,
            reason_codes=("INSUFFICIENT_DISTINCT_POSITIVE_SUPPORT",),
        )

    def score(candidate_id: str) -> tuple[int, int, int]:
        items = by_candidate[candidate_id]
        positive = sum(item.direction == "POSITIVE" for item in items)
        negative = sum(item.direction == "NEGATIVE" for item in items)
        neutral = sum(item.direction == "NEUTRAL" for item in items)
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
    recommendation = ranked[0] if ranked and ranked[0] in supported_candidates else None
    if recommendation is None:
        return _decision(
            envelope,
            packet,
            evaluated_at=evaluated_at,
            disposition="DETERMINISTIC_FALLBACK",
            ranked_candidate_ids=deterministic_order,
            actual_deterministic_candidate_id=actual,
            reason_codes=("NO_QUALIFIED_SHADOW_RECOMMENDATION",),
        )

    return _decision(
        envelope,
        packet,
        evaluated_at=evaluated_at,
        disposition="SHADOW_RANKED",
        ranked_candidate_ids=ranked,
        actual_deterministic_candidate_id=actual,
        shadow_recommendation_id=recommendation,
        reason_codes=("QUALIFIED_EXACT_TOPOLOGY_EVIDENCE_SHADOW_RANKED",),
    )
