"""Deterministic, evidence-only AQ13 staged non-production rollout evaluation."""

# @codebase_provenance_JEO
# @codebase_rights_JEO

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

AQ13_AUTHORITY_MODEL = "EVIDENCE_ONLY_NON_AUTHORIZING"
TARGET_REPOSITORY = "Baelfyre/Orchestra"
CANONICAL_START_SHA = "2fc2d9ce9fc263813981e4dc8c88d1e4f604f036"
ROLLOUT_MODE = "CONTROLLED_NON_PRODUCTION_STAGED_ROLLOUT_EVALUATION"
ENVIRONMENT_SCOPE = "NON_PRODUCTION_ONLY"
CUD10_HOLD_STATE = "READY_NOT_STARTED_HELD_BY_CURRENT_USER"
REQUIRED_STAGES = ("SHADOW", "CANARY", "LIMITED", "EXPANDED")
STAGE_SEQUENCE = {stage: index + 1 for index, stage in enumerate(REQUIRED_STAGES)}
MINIMUM_STAGE_OBSERVATIONS = 10
MINIMUM_TOTAL_OBSERVATIONS = 40
MAXIMUM_REGRESSION_RATE_BPS = 500
MAXIMUM_CRITICAL_VIOLATIONS = 0


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} must be non-empty")
    if any(ord(char) < 32 for char in cleaned):
        raise ValueError(f"{field_name} must not contain control characters")
    return cleaned


def _items(values: Iterable[str], field_name: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{field_name} must be an iterable of strings")
    materialized = tuple(_text(item, f"{field_name} item") for item in values)
    if not materialized:
        raise ValueError(f"{field_name} must contain at least one item")
    if len(materialized) != len(set(materialized)):
        raise ValueError(f"{field_name} must not contain duplicate values")
    return materialized


def _count(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


def _flag(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{field_name} must be boolean")
    return value


@dataclass(frozen=True, slots=True)
class RolloutContext:
    repository: str
    canonical_sha: str
    mode: str
    environment_scope: str
    cud10_state: str
    protected_policy_mutation_performed: bool = False
    production_mutation_performed: bool = False
    provider_activation_performed: bool = False
    telemetry_activation_performed: bool = False
    release_or_deploy_performed: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "repository", _text(self.repository, "repository"))
        object.__setattr__(self, "canonical_sha", _text(self.canonical_sha, "canonical_sha").lower())
        object.__setattr__(self, "mode", _text(self.mode, "mode").upper())
        object.__setattr__(self, "environment_scope", _text(self.environment_scope, "environment_scope").upper())
        object.__setattr__(self, "cud10_state", _text(self.cud10_state, "cud10_state").upper())
        if self.repository != TARGET_REPOSITORY:
            raise ValueError("AQ13 target repository must remain Orchestra")
        if self.canonical_sha != CANONICAL_START_SHA:
            raise ValueError("AQ13 rollout baseline must match the canonical AQ12 closeout SHA")
        if self.mode != ROLLOUT_MODE:
            raise ValueError("AQ13 must remain a controlled staged rollout evaluation")
        if self.environment_scope != ENVIRONMENT_SCOPE:
            raise ValueError("AQ13 rollout evaluation must remain non-production only")
        if self.cud10_state != CUD10_HOLD_STATE:
            raise ValueError("AQ13 cannot alter the CritiQual CUD10 hold state")
        flags = {
            "protected_policy_mutation_performed": self.protected_policy_mutation_performed,
            "production_mutation_performed": self.production_mutation_performed,
            "provider_activation_performed": self.provider_activation_performed,
            "telemetry_activation_performed": self.telemetry_activation_performed,
            "release_or_deploy_performed": self.release_or_deploy_performed,
        }
        for name, value in flags.items():
            _flag(value, name)
            if value:
                raise ValueError(f"AQ13 boundary violation: {name}")


@dataclass(frozen=True, slots=True)
class StageEvidence:
    stage_id: str
    sequence: int
    observation_count: int
    regression_count: int
    critical_violation_count: int
    rollback_signal: bool
    evidence_ids: tuple[str, ...]
    independent_evidence: bool
    deterministic_replay_match: bool

    def __post_init__(self) -> None:
        stage_id = _text(self.stage_id, "stage_id").upper()
        if stage_id not in REQUIRED_STAGES:
            raise ValueError(f"unsupported AQ13 stage_id: {stage_id}")
        object.__setattr__(self, "stage_id", stage_id)
        sequence = _count(self.sequence, "sequence")
        if sequence != STAGE_SEQUENCE[stage_id]:
            raise ValueError("AQ13 stage sequence does not match the registered rollout order")
        object.__setattr__(self, "sequence", sequence)
        observations = _count(self.observation_count, "observation_count")
        regressions = _count(self.regression_count, "regression_count")
        critical = _count(self.critical_violation_count, "critical_violation_count")
        if regressions > observations:
            raise ValueError("regression_count cannot exceed observation_count")
        if critical > observations:
            raise ValueError("critical_violation_count cannot exceed observation_count")
        object.__setattr__(self, "observation_count", observations)
        object.__setattr__(self, "regression_count", regressions)
        object.__setattr__(self, "critical_violation_count", critical)
        _flag(self.rollback_signal, "rollback_signal")
        _flag(self.independent_evidence, "independent_evidence")
        _flag(self.deterministic_replay_match, "deterministic_replay_match")
        object.__setattr__(self, "evidence_ids", _items(self.evidence_ids, "evidence_ids"))

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "StageEvidence":
        if not isinstance(value, Mapping):
            raise TypeError("stage evidence must be a mapping")
        required = {
            "stage_id",
            "sequence",
            "observation_count",
            "regression_count",
            "critical_violation_count",
            "rollback_signal",
            "evidence_ids",
            "independent_evidence",
            "deterministic_replay_match",
        }
        if set(value) != required:
            raise ValueError("stage evidence fields must match the AQ13 rollout contract")
        return cls(
            stage_id=value["stage_id"],
            sequence=value["sequence"],
            observation_count=value["observation_count"],
            regression_count=value["regression_count"],
            critical_violation_count=value["critical_violation_count"],
            rollback_signal=value["rollback_signal"],
            evidence_ids=tuple(value["evidence_ids"]),
            independent_evidence=value["independent_evidence"],
            deterministic_replay_match=value["deterministic_replay_match"],
        )


@dataclass(frozen=True, slots=True)
class StageFinding:
    stage_id: str
    sequence: int
    observation_count: int
    regression_rate_bps: int
    critical_violation_count: int
    evidence_sufficient: bool
    reason_codes: tuple[str, ...]
    authority_granted: bool = False


@dataclass(frozen=True, slots=True)
class StagedRolloutSummary:
    disposition: str
    findings: tuple[StageFinding, ...]
    total_observations: int
    total_regressions: int
    total_critical_violations: int
    regression_rate_bps: int
    reason_codes: tuple[str, ...]
    authority_granted: bool = False
    transition_authorized: bool = False
    release_authorized: bool = False
    production_authorized: bool = False
    cud10_admission_authorized: bool = False
    production_readiness_claimed: bool = False


def _stage_finding(stage: StageEvidence) -> StageFinding:
    rate = stage.regression_count * 10000 // stage.observation_count if stage.observation_count else 0
    evidence_sufficient = (
        stage.observation_count >= MINIMUM_STAGE_OBSERVATIONS
        and stage.independent_evidence
        and stage.deterministic_replay_match
    )
    reasons: list[str] = []
    if stage.observation_count < MINIMUM_STAGE_OBSERVATIONS:
        reasons.append("AQ13_STAGE_OBSERVATIONS_INSUFFICIENT")
    if not stage.independent_evidence:
        reasons.append("AQ13_INDEPENDENT_EVIDENCE_REQUIRED")
    if not stage.deterministic_replay_match:
        reasons.append("AQ13_DETERMINISTIC_REPLAY_MISMATCH")
    if stage.critical_violation_count:
        reasons.append("AQ13_CRITICAL_VIOLATION_DETECTED")
    if rate > MAXIMUM_REGRESSION_RATE_BPS:
        reasons.append("AQ13_STAGE_REGRESSION_THRESHOLD_EXCEEDED")
    if stage.rollback_signal:
        reasons.append("AQ13_ROLLBACK_SIGNAL_PRESENT")
    if not reasons:
        reasons.append("AQ13_STAGE_EVIDENCE_ACCEPTABLE")
    return StageFinding(
        stage_id=stage.stage_id,
        sequence=stage.sequence,
        observation_count=stage.observation_count,
        regression_rate_bps=rate,
        critical_violation_count=stage.critical_violation_count,
        evidence_sufficient=evidence_sufficient,
        reason_codes=tuple(reasons),
    )


def evaluate_staged_rollout(
    context: RolloutContext,
    stages: Iterable[StageEvidence],
) -> StagedRolloutSummary:
    if not isinstance(context, RolloutContext):
        raise TypeError("context must be RolloutContext")
    if isinstance(stages, (str, bytes)):
        raise TypeError("stages must be an iterable of StageEvidence")
    materialized = tuple(stages)
    if any(not isinstance(stage, StageEvidence) for stage in materialized):
        raise TypeError("stages must contain only StageEvidence values")
    if len(materialized) != len(REQUIRED_STAGES):
        raise ValueError("AQ13 requires exactly one evidence record for every rollout stage")
    stage_ids = tuple(stage.stage_id for stage in materialized)
    if len(stage_ids) != len(set(stage_ids)):
        raise ValueError("AQ13 stage_id values must be unique")
    if stage_ids != REQUIRED_STAGES:
        raise ValueError("AQ13 rollout stages must appear in the registered order")

    findings = tuple(_stage_finding(stage) for stage in materialized)
    total_observations = sum(stage.observation_count for stage in materialized)
    total_regressions = sum(stage.regression_count for stage in materialized)
    total_critical = sum(stage.critical_violation_count for stage in materialized)
    rate = total_regressions * 10000 // total_observations if total_observations else 0

    if total_critical > MAXIMUM_CRITICAL_VIOLATIONS or rate > MAXIMUM_REGRESSION_RATE_BPS:
        disposition = "REVISION_REQUIRED"
        reasons = (
            "AQ13_ROLLOUT_RISK_THRESHOLD_EXCEEDED",
            "AQ13_NON_AUTHORIZING_BOUNDARY_PRESERVED",
        )
    elif any(stage.rollback_signal for stage in materialized):
        disposition = "HOLD"
        reasons = (
            "AQ13_ROLLBACK_SIGNAL_HOLD",
            "AQ13_NON_AUTHORIZING_BOUNDARY_PRESERVED",
        )
    elif (
        total_observations < MINIMUM_TOTAL_OBSERVATIONS
        or any(not finding.evidence_sufficient for finding in findings)
    ):
        disposition = "WAIT_FOR_EVIDENCE"
        reasons = (
            "AQ13_ROLLOUT_EVIDENCE_INCOMPLETE",
            "AQ13_NON_AUTHORIZING_BOUNDARY_PRESERVED",
        )
    else:
        disposition = "PASS"
        reasons = (
            "AQ13_STAGED_NON_PRODUCTION_EVALUATION_PASS",
            "AQ13_PASS_IS_NON_AUTHORIZING",
            "AQ13_CUD10_HOLD_PRESERVED",
        )

    return StagedRolloutSummary(
        disposition=disposition,
        findings=findings,
        total_observations=total_observations,
        total_regressions=total_regressions,
        total_critical_violations=total_critical,
        regression_rate_bps=rate,
        reason_codes=reasons,
    )
