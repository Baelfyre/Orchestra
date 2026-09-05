from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .execution_efficiency import (
    DecisiveStopSignal,
    SEARCH_ESCALATION,
    VALIDATION_ESCALATION,
    require_search_escalation,
    require_validation_escalation,
)

SPECIALIST_EXPANSION_REASONS = (
    "CROSS_DOMAIN_AUTHORITY",
    "ADVERSARIAL_REVIEW_REQUIRED",
)
CI_IDLE_NO_REASONING = "IDLE_NO_REASONING"
CI_READ_ONCE = "READ_ONCE"


def _text(value: object, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} must be non-empty")
    return text


def _unique_text(values: Sequence[object], field_name: str) -> tuple[str, ...]:
    normalized = tuple(_text(item, field_name) for item in values)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} values must be unique")
    return normalized


@dataclass(frozen=True)
class SpecialistInvocationPlan:
    owner_specialist: str
    supporting_specialists: tuple[str, ...] = ()
    retry_counts: tuple[tuple[str, int], ...] = ()
    expansion_reason: str | None = None
    expansion_evidence_refs: tuple[str, ...] = ()

    def validate(self) -> None:
        owner = _text(self.owner_specialist, "owner_specialist")
        supporting = _unique_text(self.supporting_specialists, "supporting_specialist")
        if owner in supporting:
            raise ValueError("owner_specialist must not be duplicated in supporting_specialists")

        retry_keys: list[str] = []
        allowed_specialists = {owner, *supporting}
        for specialist, retry_count in self.retry_counts:
            specialist = _text(specialist, "retry_specialist")
            if specialist in retry_keys:
                raise ValueError("retry_counts specialist keys must be unique")
            if specialist not in allowed_specialists:
                raise ValueError("retry_counts may reference only planned specialists")
            if type(retry_count) is not int or retry_count < 0 or retry_count > 1:
                raise ValueError("specialist retry count must be integer 0 or 1")
            retry_keys.append(specialist)

        evidence = _unique_text(self.expansion_evidence_refs, "expansion_evidence_ref")
        if supporting:
            if self.expansion_reason not in SPECIALIST_EXPANSION_REASONS:
                raise ValueError(
                    "supporting specialists require an explicit cross-domain or adversarial expansion reason"
                )
            if not evidence:
                raise ValueError("supporting specialists require expansion evidence")
        elif self.expansion_reason is not None or evidence:
            raise ValueError("single-owner routing must not carry unused expansion metadata")

    @property
    def active_specialists(self) -> tuple[str, ...]:
        self.validate()
        return (self.owner_specialist.strip(),)

    @property
    def planned_specialists(self) -> tuple[str, ...]:
        self.validate()
        return (self.owner_specialist.strip(), *tuple(item.strip() for item in self.supporting_specialists))


def build_owner_first_plan(
    owner_specialist: str,
    supporting_specialists: Sequence[str] = (),
    *,
    retry_counts: Mapping[str, int] | None = None,
    expansion_reason: str | None = None,
    expansion_evidence_refs: Sequence[str] = (),
) -> SpecialistInvocationPlan:
    plan = SpecialistInvocationPlan(
        owner_specialist=_text(owner_specialist, "owner_specialist"),
        supporting_specialists=tuple(supporting_specialists),
        retry_counts=tuple(sorted((str(key), value) for key, value in (retry_counts or {}).items())),
        expansion_reason=expansion_reason,
        expansion_evidence_refs=tuple(expansion_evidence_refs),
    )
    plan.validate()
    return plan


@dataclass(frozen=True)
class ProgressionDecision:
    allowed: bool
    reason_code: str
    downstream_execution_allowed: bool


def evaluate_decisive_progression(signal: DecisiveStopSignal) -> ProgressionDecision:
    signal.validate()
    stopped = signal.evidence_sufficient and signal.stop_required
    if stopped:
        return ProgressionDecision(
            allowed=False,
            reason_code="DECISIVE_EVIDENCE_STOP",
            downstream_execution_allowed=False,
        )
    return ProgressionDecision(
        allowed=True,
        reason_code="NO_DECISIVE_STOP",
        downstream_execution_allowed=True,
    )


@dataclass(frozen=True)
class EvidenceCacheEntry:
    evidence_id: str
    owner_ref: str
    source_revision: str
    source_identity: str
    content_identity: str

    def validate(self) -> None:
        for field_name in (
            "evidence_id",
            "owner_ref",
            "source_revision",
            "source_identity",
            "content_identity",
        ):
            _text(getattr(self, field_name), field_name)


@dataclass(frozen=True)
class EvidenceReuseDecision:
    reusable: bool
    reason_code: str


def evaluate_evidence_reuse(
    entry: EvidenceCacheEntry,
    *,
    source_revision: str,
    source_identity: str,
) -> EvidenceReuseDecision:
    entry.validate()
    revision = _text(source_revision, "source_revision")
    identity = _text(source_identity, "source_identity")
    if entry.source_revision != revision:
        return EvidenceReuseDecision(False, "SOURCE_REVISION_CHANGED")
    if entry.source_identity != identity:
        return EvidenceReuseDecision(False, "SOURCE_IDENTITY_CHANGED")
    return EvidenceReuseDecision(True, "EXACT_SOURCE_IDENTITY_MATCH")


def next_search_stage(current_stage: str, *, current_stage_insufficient: bool) -> str:
    if current_stage not in SEARCH_ESCALATION:
        raise ValueError(f"unknown search stage: {current_stage}")
    if type(current_stage_insufficient) is not bool:
        raise ValueError("current_stage_insufficient must be a boolean")
    index = SEARCH_ESCALATION.index(current_stage)
    if not current_stage_insufficient or index == len(SEARCH_ESCALATION) - 1:
        return current_stage
    target = SEARCH_ESCALATION[index + 1]
    require_search_escalation(
        current_stage,
        target,
        current_stage_insufficient=current_stage_insufficient,
    )
    return target


@dataclass(frozen=True)
class ValidationRequest:
    target_stage: str
    completed_stages: tuple[str, ...]
    candidate_stable: bool

    def validate(self) -> None:
        if self.target_stage not in VALIDATION_ESCALATION:
            raise ValueError(f"unknown validation stage: {self.target_stage}")
        if type(self.candidate_stable) is not bool:
            raise ValueError("candidate_stable must be a boolean")
        completed = tuple(self.completed_stages)
        if any(item not in VALIDATION_ESCALATION for item in completed):
            raise ValueError("completed_stages contains unknown validation stage")
        if len(set(completed)) != len(completed):
            raise ValueError("completed_stages values must be unique")
        target_index = VALIDATION_ESCALATION.index(self.target_stage)
        required = VALIDATION_ESCALATION[:target_index]
        if completed != required:
            raise ValueError(
                "validation stage cannot skip prerequisites; exact ordered prerequisites: "
                + ", ".join(required)
            )
        if self.target_stage in {"REPOSITORY_QUALIFICATION", "PROTECTED_GATES"} and not self.candidate_stable:
            raise ValueError("expensive validation requires a stable candidate")
        if target_index > 0:
            require_validation_escalation(
                VALIDATION_ESCALATION[target_index - 1],
                self.target_stage,
                current_stage_insufficient=True,
            )


def validate_validation_request(
    target_stage: str,
    completed_stages: Sequence[str],
    *,
    candidate_stable: bool,
) -> ValidationRequest:
    request = ValidationRequest(target_stage, tuple(completed_stages), candidate_stable)
    request.validate()
    return request


@dataclass(frozen=True)
class CIActivityDecision:
    action: str
    active_model_reasoning_allowed: bool
    poll_required: bool


def plan_ci_activity(*, ci_state_changed: bool, decision_point: bool) -> CIActivityDecision:
    if type(ci_state_changed) is not bool or type(decision_point) is not bool:
        raise ValueError("CI activity flags must be booleans")
    if ci_state_changed or decision_point:
        return CIActivityDecision(CI_READ_ONCE, True, True)
    return CIActivityDecision(CI_IDLE_NO_REASONING, False, False)


@dataclass(frozen=True)
class ContextEvidence:
    ref: str
    source_identity: str
    required_for: tuple[str, ...]

    def validate(self) -> None:
        _text(self.ref, "context_ref")
        _text(self.source_identity, "source_identity")
        required_for = _unique_text(self.required_for, "required_for")
        if not required_for:
            raise ValueError("context evidence requires at least one consumer")


@dataclass(frozen=True)
class PhaseContextPack:
    phase_id: str
    owner_specialist: str
    source_revision: str
    evidence: tuple[ContextEvidence, ...]
    excluded_refs: tuple[str, ...] = ()

    def validate(self) -> None:
        _text(self.phase_id, "phase_id")
        owner = _text(self.owner_specialist, "owner_specialist")
        _text(self.source_revision, "source_revision")
        if not self.evidence:
            raise ValueError("phase context pack requires evidence")
        refs: list[str] = []
        owner_evidence = False
        for item in self.evidence:
            item.validate()
            if item.ref in refs:
                raise ValueError("phase context evidence refs must be unique")
            refs.append(item.ref)
            if owner in item.required_for or "all" in item.required_for:
                owner_evidence = True
        if not owner_evidence:
            raise ValueError("phase context pack must include evidence for its owner")
        excluded = _unique_text(self.excluded_refs, "excluded_ref")
        if set(refs) & set(excluded):
            raise ValueError("phase context evidence cannot also be excluded")

    def refs_for(self, specialist_slug: str) -> tuple[str, ...]:
        self.validate()
        specialist = _text(specialist_slug, "specialist_slug")
        return tuple(
            item.ref
            for item in self.evidence
            if specialist in item.required_for or "all" in item.required_for
        )


def require_active_phase(active_phase: str, requested_phase: str) -> None:
    active = _text(active_phase, "active_phase")
    requested = _text(requested_phase, "requested_phase")
    if active != requested:
        raise ValueError("autonomous campaign may load only the active phase context")


@dataclass(frozen=True)
class EfficiencyPhaseResult:
    phase_id: str
    passed: bool
    evidence_refs: tuple[str, ...]

    def validate(self) -> None:
        _text(self.phase_id, "phase_id")
        if type(self.passed) is not bool:
            raise ValueError("phase result passed must be a boolean")
        refs = _unique_text(self.evidence_refs, "phase_evidence_ref")
        if self.passed and not refs:
            raise ValueError("passed efficiency phase requires evidence")


def evaluate_program_resume_gate(
    phase_results: Sequence[EfficiencyPhaseResult],
) -> bool:
    expected = tuple(f"OEE-{index}" for index in range(0, 8))
    results = tuple(phase_results)
    if tuple(item.phase_id for item in results) != expected:
        raise ValueError("resume gate requires exact ordered OEE-0 through OEE-7 results")
    for item in results:
        item.validate()
    return all(item.passed for item in results)


__all__ = [
    "CIActivityDecision",
    "CI_IDLE_NO_REASONING",
    "CI_READ_ONCE",
    "ContextEvidence",
    "EfficiencyPhaseResult",
    "EvidenceCacheEntry",
    "EvidenceReuseDecision",
    "PhaseContextPack",
    "ProgressionDecision",
    "SPECIALIST_EXPANSION_REASONS",
    "SpecialistInvocationPlan",
    "ValidationRequest",
    "build_owner_first_plan",
    "evaluate_decisive_progression",
    "evaluate_evidence_reuse",
    "evaluate_program_resume_gate",
    "next_search_stage",
    "plan_ci_activity",
    "require_active_phase",
    "validate_validation_request",
]
