from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .domain.governance.kernel import (
    GOVERNANCE_KERNEL_SCHEMA_VERSION,
    ArbiterKernelResult,
    ArbiterReasonCode,
    GovernanceDecision,
    GovernanceDecisionRecord,
    TransitionDisposition,
)
from .evidence import receipt_digest
from .machine_contracts import (
    default_remediation_limits,
    governance_decision_values,
    transition_disposition_values,
    transition_precedence,
)


_POLICY_REMEDIATION = default_remediation_limits()
DEFAULT_MAX_REMEDIATION_ATTEMPTS = _POLICY_REMEDIATION["maximum_remediation_attempts_per_unit"]
DEFAULT_MAX_IDENTICAL_FAILURE_REPETITIONS = _POLICY_REMEDIATION["maximum_identical_failure_repetitions"]


if tuple(item.value for item in GovernanceDecision) != governance_decision_values():
    raise RuntimeError("GovernanceDecision compatibility enum differs from machine governance policy")
if set(item.value for item in TransitionDisposition) != set(transition_disposition_values()):
    raise RuntimeError("TransitionDisposition compatibility enum differs from machine governance policy")


def _nonempty(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} must be non-empty")
    return cleaned


@dataclass(frozen=True, slots=True)
class ArbiterKernelInput:
    project_id: str
    unit_id: str
    governance_decisions: tuple[GovernanceDecisionRecord, ...]
    authority_valid: bool = True
    protected_boundary_clear: bool = True
    scope_or_policy_decision_required: bool = False
    external_authority_missing: bool = False
    contradiction_unresolved: bool = False
    governance_evidence_complete: bool = True
    required_receipts_present: bool = True
    exact_state_valid: bool = True
    evidence_fresh: bool = True
    validation_passed: bool = True
    host_capacity_available: bool = True
    deterministic_defect: bool = False
    remediation_authorized: bool = False
    remediation_in_scope: bool = False
    remediation_attempt_count: int = 0
    identical_failure_repetitions: int = 0
    maximum_remediation_attempts: int = DEFAULT_MAX_REMEDIATION_ATTEMPTS
    maximum_identical_failure_repetitions: int = DEFAULT_MAX_IDENTICAL_FAILURE_REPETITIONS
    schema_version: str = GOVERNANCE_KERNEL_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != GOVERNANCE_KERNEL_SCHEMA_VERSION:
            raise ValueError(f"unsupported Arbiter kernel input schema {self.schema_version!r}")
        object.__setattr__(self, "project_id", _nonempty(self.project_id, "project_id"))
        object.__setattr__(self, "unit_id", _nonempty(self.unit_id, "unit_id"))
        if not isinstance(self.governance_decisions, tuple):
            raise TypeError("governance_decisions must be a tuple")
        if not all(isinstance(item, GovernanceDecisionRecord) for item in self.governance_decisions):
            raise TypeError("governance_decisions must contain GovernanceDecisionRecord values")
        bool_fields = (
            "authority_valid",
            "protected_boundary_clear",
            "scope_or_policy_decision_required",
            "external_authority_missing",
            "contradiction_unresolved",
            "governance_evidence_complete",
            "required_receipts_present",
            "exact_state_valid",
            "evidence_fresh",
            "validation_passed",
            "host_capacity_available",
            "deterministic_defect",
            "remediation_authorized",
            "remediation_in_scope",
        )
        for field_name in bool_fields:
            if not isinstance(getattr(self, field_name), bool):
                raise TypeError(f"{field_name} must be bool")
        for field_name in (
            "remediation_attempt_count",
            "identical_failure_repetitions",
            "maximum_remediation_attempts",
            "maximum_identical_failure_repetitions",
        ):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{field_name} must be int")
            if value < 0:
                raise ValueError(f"{field_name} must be >= 0")
        if self.maximum_remediation_attempts <= 0:
            raise ValueError("maximum_remediation_attempts must be > 0")
        if self.maximum_identical_failure_repetitions <= 0:
            raise ValueError("maximum_identical_failure_repetitions must be > 0")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "project_id": self.project_id,
            "unit_id": self.unit_id,
            "governance_decisions": [item.to_dict() for item in self.governance_decisions],
            "authority_valid": self.authority_valid,
            "protected_boundary_clear": self.protected_boundary_clear,
            "scope_or_policy_decision_required": self.scope_or_policy_decision_required,
            "external_authority_missing": self.external_authority_missing,
            "contradiction_unresolved": self.contradiction_unresolved,
            "governance_evidence_complete": self.governance_evidence_complete,
            "required_receipts_present": self.required_receipts_present,
            "exact_state_valid": self.exact_state_valid,
            "evidence_fresh": self.evidence_fresh,
            "validation_passed": self.validation_passed,
            "host_capacity_available": self.host_capacity_available,
            "deterministic_defect": self.deterministic_defect,
            "remediation_authorized": self.remediation_authorized,
            "remediation_in_scope": self.remediation_in_scope,
            "remediation_attempt_count": self.remediation_attempt_count,
            "identical_failure_repetitions": self.identical_failure_repetitions,
            "maximum_remediation_attempts": self.maximum_remediation_attempts,
            "maximum_identical_failure_repetitions": self.maximum_identical_failure_repetitions,
        }

    @property
    def digest(self) -> str:
        return receipt_digest(self.to_dict())


def _result(
    kernel_input: ArbiterKernelInput,
    disposition: TransitionDisposition,
    *codes: ArbiterReasonCode,
) -> ArbiterKernelResult:
    return ArbiterKernelResult(
        disposition=disposition,
        reason_codes=tuple(codes),
        input_digest=kernel_input.digest,
    )


def _candidate_results(kernel_input: ArbiterKernelInput) -> dict[TransitionDisposition, ArbiterKernelResult]:
    decisions = tuple(record.decision for record in kernel_input.governance_decisions)
    candidates: dict[TransitionDisposition, ArbiterKernelResult] = {}

    if not kernel_input.authority_valid:
        candidates[TransitionDisposition.STOP] = _result(
            kernel_input, TransitionDisposition.STOP, ArbiterReasonCode.AUTHORITY_INVALID
        )
    elif not kernel_input.protected_boundary_clear:
        candidates[TransitionDisposition.STOP] = _result(
            kernel_input,
            TransitionDisposition.STOP,
            ArbiterReasonCode.PROTECTED_BOUNDARY_VIOLATION,
        )
    elif GovernanceDecision.BLOCKED in decisions:
        candidates[TransitionDisposition.STOP] = _result(
            kernel_input, TransitionDisposition.STOP, ArbiterReasonCode.GOVERNANCE_BLOCKED
        )

    revision_required = GovernanceDecision.REVISION_REQUIRED in decisions
    remediation_candidate = (
        (revision_required or not kernel_input.validation_passed)
        and kernel_input.deterministic_defect
        and kernel_input.remediation_authorized
        and kernel_input.remediation_in_scope
    )

    escalation_reason: ArbiterReasonCode | None = None
    if any(record.human_review_required for record in kernel_input.governance_decisions):
        escalation_reason = ArbiterReasonCode.HUMAN_REVIEW_REQUIRED
    elif kernel_input.scope_or_policy_decision_required:
        escalation_reason = ArbiterReasonCode.SCOPE_OR_POLICY_DECISION_REQUIRED
    elif kernel_input.external_authority_missing:
        escalation_reason = ArbiterReasonCode.EXTERNAL_AUTHORITY_REQUIRED
    elif kernel_input.contradiction_unresolved:
        escalation_reason = ArbiterReasonCode.CONTRADICTION_UNRESOLVED
    elif kernel_input.remediation_attempt_count >= kernel_input.maximum_remediation_attempts:
        escalation_reason = ArbiterReasonCode.REMEDIATION_BUDGET_EXHAUSTED
    elif kernel_input.identical_failure_repetitions > kernel_input.maximum_identical_failure_repetitions:
        escalation_reason = ArbiterReasonCode.IDENTICAL_FAILURE_LIMIT_EXCEEDED
    elif revision_required and not remediation_candidate:
        escalation_reason = ArbiterReasonCode.REVISION_NOT_AUTOREMEDIABLE
    if escalation_reason is not None:
        candidates[TransitionDisposition.ESCALATE_HUMAN] = _result(
            kernel_input, TransitionDisposition.ESCALATE_HUMAN, escalation_reason
        )

    if not kernel_input.host_capacity_available:
        candidates[TransitionDisposition.WAIT_FOR_CAPACITY] = _result(
            kernel_input,
            TransitionDisposition.WAIT_FOR_CAPACITY,
            ArbiterReasonCode.HOST_CAPACITY_UNAVAILABLE,
        )

    evidence_reason: ArbiterReasonCode | None = None
    if not kernel_input.governance_evidence_complete:
        evidence_reason = ArbiterReasonCode.GOVERNANCE_EVIDENCE_INCOMPLETE
    elif not kernel_input.required_receipts_present:
        evidence_reason = ArbiterReasonCode.REQUIRED_RECEIPT_MISSING
    elif not kernel_input.exact_state_valid:
        evidence_reason = ArbiterReasonCode.EXACT_STATE_MISMATCH
    elif not kernel_input.evidence_fresh:
        evidence_reason = ArbiterReasonCode.EVIDENCE_STALE
    elif not kernel_input.validation_passed and not remediation_candidate:
        evidence_reason = ArbiterReasonCode.VALIDATION_FAILED
    if evidence_reason is not None:
        candidates[TransitionDisposition.WAIT_FOR_EVIDENCE] = _result(
            kernel_input, TransitionDisposition.WAIT_FOR_EVIDENCE, evidence_reason
        )

    if remediation_candidate:
        candidates[TransitionDisposition.AUTO_REMEDIATE_AND_REVALIDATE] = _result(
            kernel_input,
            TransitionDisposition.AUTO_REMEDIATE_AND_REVALIDATE,
            ArbiterReasonCode.BOUNDED_REMEDIATION_AVAILABLE,
        )

    candidates[TransitionDisposition.AUTO_CONTINUE] = _result(
        kernel_input,
        TransitionDisposition.AUTO_CONTINUE,
        ArbiterReasonCode.CONTINUATION_READY,
    )
    return candidates


def evaluate_arbiter(kernel_input: ArbiterKernelInput) -> ArbiterKernelResult:
    candidates = _candidate_results(kernel_input)
    for disposition_name in transition_precedence():
        disposition = TransitionDisposition(disposition_name)
        result = candidates.get(disposition)
        if result is not None:
            return result
    raise RuntimeError("machine governance policy did not select an Arbiter disposition")


def safe_evaluate_arbiter(candidate: ArbiterKernelInput | Any) -> ArbiterKernelResult:
    """Fail closed at integration boundaries that may supply malformed values."""
    if isinstance(candidate, ArbiterKernelInput):
        return evaluate_arbiter(candidate)
    synthetic = ArbiterKernelInput(
        project_id="malformed-input",
        unit_id="malformed-input",
        governance_decisions=(),
        scope_or_policy_decision_required=True,
    )
    return _result(
        synthetic,
        TransitionDisposition.ESCALATE_HUMAN,
        ArbiterReasonCode.MALFORMED_INPUT,
    )
