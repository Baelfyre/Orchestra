from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .evidence import receipt_digest


GOVERNANCE_KERNEL_SCHEMA_VERSION = "1.0.0"
DEFAULT_MAX_REMEDIATION_ATTEMPTS = 3
DEFAULT_MAX_IDENTICAL_FAILURE_REPETITIONS = 2


class GovernanceDecision(str, Enum):
    APPROVED = "APPROVED"
    ADVISORY_ONLY = "ADVISORY_ONLY"
    REVISION_REQUIRED = "REVISION_REQUIRED"
    BLOCKED = "BLOCKED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class TransitionDisposition(str, Enum):
    AUTO_CONTINUE = "AUTO_CONTINUE"
    AUTO_REMEDIATE_AND_REVALIDATE = "AUTO_REMEDIATE_AND_REVALIDATE"
    WAIT_FOR_EVIDENCE = "WAIT_FOR_EVIDENCE"
    WAIT_FOR_CAPACITY = "WAIT_FOR_CAPACITY"
    ESCALATE_HUMAN = "ESCALATE_HUMAN"
    STOP = "STOP"


class ArbiterReasonCode(str, Enum):
    AUTHORITY_INVALID = "AUTHORITY_INVALID"
    PROTECTED_BOUNDARY_VIOLATION = "PROTECTED_BOUNDARY_VIOLATION"
    GOVERNANCE_BLOCKED = "GOVERNANCE_BLOCKED"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
    SCOPE_OR_POLICY_DECISION_REQUIRED = "SCOPE_OR_POLICY_DECISION_REQUIRED"
    EXTERNAL_AUTHORITY_REQUIRED = "EXTERNAL_AUTHORITY_REQUIRED"
    CONTRADICTION_UNRESOLVED = "CONTRADICTION_UNRESOLVED"
    REVISION_NOT_AUTOREMEDIABLE = "REVISION_NOT_AUTOREMEDIABLE"
    REMEDIATION_BUDGET_EXHAUSTED = "REMEDIATION_BUDGET_EXHAUSTED"
    IDENTICAL_FAILURE_LIMIT_EXCEEDED = "IDENTICAL_FAILURE_LIMIT_EXCEEDED"
    HOST_CAPACITY_UNAVAILABLE = "HOST_CAPACITY_UNAVAILABLE"
    GOVERNANCE_EVIDENCE_INCOMPLETE = "GOVERNANCE_EVIDENCE_INCOMPLETE"
    REQUIRED_RECEIPT_MISSING = "REQUIRED_RECEIPT_MISSING"
    EXACT_STATE_MISMATCH = "EXACT_STATE_MISMATCH"
    EVIDENCE_STALE = "EVIDENCE_STALE"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    BOUNDED_REMEDIATION_AVAILABLE = "BOUNDED_REMEDIATION_AVAILABLE"
    CONTINUATION_READY = "CONTINUATION_READY"
    MALFORMED_INPUT = "MALFORMED_INPUT"


def _nonempty(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} must be non-empty")
    return cleaned


def _enum(value: str | Enum, enum_type: type[Enum], field_name: str):
    if isinstance(value, enum_type):
        return value
    try:
        return enum_type(_nonempty(value, field_name))
    except ValueError as exc:
        raise ValueError(f"unsupported {field_name}: {value!r}") from exc


@dataclass(frozen=True, slots=True)
class GovernanceDecisionRecord:
    reviewer: str
    project_context: str
    decision: GovernanceDecision | str
    reason: str
    risks: tuple[str, ...] = ()
    required_actions: tuple[str, ...] = ()
    human_review_required: bool = False
    evidence_refs: tuple[str, ...] = ()
    schema_version: str = GOVERNANCE_KERNEL_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != GOVERNANCE_KERNEL_SCHEMA_VERSION:
            raise ValueError(f"unsupported governance decision schema {self.schema_version!r}")
        object.__setattr__(self, "reviewer", _nonempty(self.reviewer, "reviewer"))
        object.__setattr__(self, "project_context", _nonempty(self.project_context, "project_context"))
        object.__setattr__(self, "decision", _enum(self.decision, GovernanceDecision, "decision"))
        object.__setattr__(self, "reason", _nonempty(self.reason, "reason"))
        if not isinstance(self.human_review_required, bool):
            raise TypeError("human_review_required must be bool")
        for name in ("risks", "required_actions", "evidence_refs"):
            values = getattr(self, name)
            if not isinstance(values, tuple):
                raise TypeError(f"{name} must be a tuple")
            object.__setattr__(self, name, tuple(_nonempty(item, name) for item in values))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "reviewer": self.reviewer,
            "project_context": self.project_context,
            "decision": self.decision.value,
            "reason": self.reason,
            "risks": list(self.risks),
            "required_actions": list(self.required_actions),
            "human_review_required": self.human_review_required,
            "evidence_refs": list(self.evidence_refs),
        }


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


@dataclass(frozen=True, slots=True)
class ArbiterKernelResult:
    disposition: TransitionDisposition
    reason_codes: tuple[ArbiterReasonCode, ...]
    input_digest: str
    schema_version: str = GOVERNANCE_KERNEL_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "disposition": self.disposition.value,
            "reason_codes": [item.value for item in self.reason_codes],
            "input_digest": self.input_digest,
        }

    @property
    def digest(self) -> str:
        return receipt_digest(self.to_dict())

    def assert_claimed_disposition(self, claimed: str) -> None:
        candidate = _enum(claimed, TransitionDisposition, "claimed_disposition")
        if candidate is not self.disposition:
            raise ValueError(
                f"claimed disposition {candidate.value!r} conflicts with "
                f"kernel disposition {self.disposition.value!r}"
            )


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


def evaluate_arbiter(kernel_input: ArbiterKernelInput) -> ArbiterKernelResult:
    decisions = tuple(record.decision for record in kernel_input.governance_decisions)

    # Canonical precedence 1: STOP.
    if not kernel_input.authority_valid:
        return _result(kernel_input, TransitionDisposition.STOP, ArbiterReasonCode.AUTHORITY_INVALID)
    if not kernel_input.protected_boundary_clear:
        return _result(
            kernel_input,
            TransitionDisposition.STOP,
            ArbiterReasonCode.PROTECTED_BOUNDARY_VIOLATION,
        )
    if GovernanceDecision.BLOCKED in decisions:
        return _result(kernel_input, TransitionDisposition.STOP, ArbiterReasonCode.GOVERNANCE_BLOCKED)

    # Canonical precedence 2: ESCALATE_HUMAN.
    if any(record.human_review_required for record in kernel_input.governance_decisions):
        return _result(
            kernel_input,
            TransitionDisposition.ESCALATE_HUMAN,
            ArbiterReasonCode.HUMAN_REVIEW_REQUIRED,
        )
    if kernel_input.scope_or_policy_decision_required:
        return _result(
            kernel_input,
            TransitionDisposition.ESCALATE_HUMAN,
            ArbiterReasonCode.SCOPE_OR_POLICY_DECISION_REQUIRED,
        )
    if kernel_input.external_authority_missing:
        return _result(
            kernel_input,
            TransitionDisposition.ESCALATE_HUMAN,
            ArbiterReasonCode.EXTERNAL_AUTHORITY_REQUIRED,
        )
    if kernel_input.contradiction_unresolved:
        return _result(
            kernel_input,
            TransitionDisposition.ESCALATE_HUMAN,
            ArbiterReasonCode.CONTRADICTION_UNRESOLVED,
        )

    revision_required = GovernanceDecision.REVISION_REQUIRED in decisions
    remediation_candidate = (
        (revision_required or not kernel_input.validation_passed)
        and kernel_input.deterministic_defect
        and kernel_input.remediation_authorized
        and kernel_input.remediation_in_scope
    )
    if kernel_input.remediation_attempt_count >= kernel_input.maximum_remediation_attempts:
        return _result(
            kernel_input,
            TransitionDisposition.ESCALATE_HUMAN,
            ArbiterReasonCode.REMEDIATION_BUDGET_EXHAUSTED,
        )
    if (
        kernel_input.identical_failure_repetitions
        > kernel_input.maximum_identical_failure_repetitions
    ):
        return _result(
            kernel_input,
            TransitionDisposition.ESCALATE_HUMAN,
            ArbiterReasonCode.IDENTICAL_FAILURE_LIMIT_EXCEEDED,
        )
    if revision_required and not remediation_candidate:
        return _result(
            kernel_input,
            TransitionDisposition.ESCALATE_HUMAN,
            ArbiterReasonCode.REVISION_NOT_AUTOREMEDIABLE,
        )

    # Canonical precedence 3: WAIT_FOR_CAPACITY.
    if not kernel_input.host_capacity_available:
        return _result(
            kernel_input,
            TransitionDisposition.WAIT_FOR_CAPACITY,
            ArbiterReasonCode.HOST_CAPACITY_UNAVAILABLE,
        )

    # Canonical precedence 4: WAIT_FOR_EVIDENCE.
    if not kernel_input.governance_evidence_complete:
        return _result(
            kernel_input,
            TransitionDisposition.WAIT_FOR_EVIDENCE,
            ArbiterReasonCode.GOVERNANCE_EVIDENCE_INCOMPLETE,
        )
    if not kernel_input.required_receipts_present:
        return _result(
            kernel_input,
            TransitionDisposition.WAIT_FOR_EVIDENCE,
            ArbiterReasonCode.REQUIRED_RECEIPT_MISSING,
        )
    if not kernel_input.exact_state_valid:
        return _result(
            kernel_input,
            TransitionDisposition.WAIT_FOR_EVIDENCE,
            ArbiterReasonCode.EXACT_STATE_MISMATCH,
        )
    if not kernel_input.evidence_fresh:
        return _result(
            kernel_input,
            TransitionDisposition.WAIT_FOR_EVIDENCE,
            ArbiterReasonCode.EVIDENCE_STALE,
        )

    # Canonical precedence 5: AUTO_REMEDIATE_AND_REVALIDATE.
    if remediation_candidate:
        return _result(
            kernel_input,
            TransitionDisposition.AUTO_REMEDIATE_AND_REVALIDATE,
            ArbiterReasonCode.BOUNDED_REMEDIATION_AVAILABLE,
        )
    if not kernel_input.validation_passed:
        return _result(
            kernel_input,
            TransitionDisposition.WAIT_FOR_EVIDENCE,
            ArbiterReasonCode.VALIDATION_FAILED,
        )

    # Canonical precedence 6: AUTO_CONTINUE.
    return _result(
        kernel_input,
        TransitionDisposition.AUTO_CONTINUE,
        ArbiterReasonCode.CONTINUATION_READY,
    )


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
