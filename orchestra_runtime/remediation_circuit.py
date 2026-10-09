from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Any

from .evidence import normalize_sha256, receipt_digest
from .governance_kernel import (
    ArbiterKernelInput,
    ArbiterKernelResult,
    TransitionDisposition,
    evaluate_arbiter,
)

CIRCUIT_BREAKER_SCHEMA_VERSION = "orchestra.remediation-circuit.v1"
DEFAULT_MAX_REMEDIATION_ATTEMPTS = 3
DEFAULT_MAX_IDENTICAL_FAILURE_REPETITIONS = 2
DEFAULT_MAX_NO_PROGRESS_CYCLES = 2
DEFAULT_MAX_WAIT_REMEDIATION_TRANSITIONS = 4


class CircuitConstraint(str, Enum):
    ALLOW_REMEDIATION = "ALLOW_REMEDIATION"
    WAIT_FOR_EVIDENCE = "WAIT_FOR_EVIDENCE"
    ESCALATE_HUMAN = "ESCALATE_HUMAN"
    CONTINUE = "CONTINUE"


class CircuitReason(str, Enum):
    REMEDIATION_AVAILABLE = "REMEDIATION_AVAILABLE"
    EVIDENCE_WAIT_RECORDED = "EVIDENCE_WAIT_RECORDED"
    SUCCESS_RECORDED = "SUCCESS_RECORDED"
    TOTAL_BUDGET_EXHAUSTED = "TOTAL_BUDGET_EXHAUSTED"
    IDENTICAL_FAILURE_LIMIT_EXCEEDED = "IDENTICAL_FAILURE_LIMIT_EXCEEDED"
    NO_PROGRESS_LIMIT_EXCEEDED = "NO_PROGRESS_LIMIT_EXCEEDED"
    WAIT_REMEDIATION_LOOP_LIMIT_EXCEEDED = "WAIT_REMEDIATION_LOOP_LIMIT_EXCEEDED"


def _text(value: object, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} must be non-empty")
    return text


def failure_signature(*, validator_id: str, reason_code: str, evidence_digest: str) -> str:
    return receipt_digest(
        {
            "validator_id": _text(validator_id, "validator_id"),
            "reason_code": _text(reason_code, "reason_code"),
            "evidence_digest": normalize_sha256(evidence_digest, "evidence_digest"),
        }
    )


@dataclass(frozen=True, slots=True)
class RemediationCircuitState:
    project_id: str
    unit_id: str
    envelope_id: str
    total_remediation_attempts: int = 0
    current_failure_signature: str | None = None
    identical_failure_repetitions: int = 0
    no_progress_cycles: int = 0
    wait_remediation_transitions: int = 0
    last_progress_digest: str | None = None
    last_action: str = "INITIAL"
    successful_recoveries: int = 0
    maximum_remediation_attempts: int = DEFAULT_MAX_REMEDIATION_ATTEMPTS
    maximum_identical_failure_repetitions: int = DEFAULT_MAX_IDENTICAL_FAILURE_REPETITIONS
    maximum_no_progress_cycles: int = DEFAULT_MAX_NO_PROGRESS_CYCLES
    maximum_wait_remediation_transitions: int = DEFAULT_MAX_WAIT_REMEDIATION_TRANSITIONS
    schema_version: str = CIRCUIT_BREAKER_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != CIRCUIT_BREAKER_SCHEMA_VERSION:
            raise ValueError(f"unsupported remediation circuit schema {self.schema_version!r}")
        object.__setattr__(self, "project_id", _text(self.project_id, "project_id"))
        object.__setattr__(self, "unit_id", _text(self.unit_id, "unit_id"))
        object.__setattr__(self, "envelope_id", _text(self.envelope_id, "envelope_id"))
        object.__setattr__(self, "last_action", _text(self.last_action, "last_action"))
        if self.current_failure_signature is not None:
            object.__setattr__(self, "current_failure_signature", normalize_sha256(self.current_failure_signature, "current_failure_signature"))
        if self.last_progress_digest is not None:
            object.__setattr__(self, "last_progress_digest", normalize_sha256(self.last_progress_digest, "last_progress_digest"))
        for field_name in (
            "total_remediation_attempts",
            "identical_failure_repetitions",
            "no_progress_cycles",
            "wait_remediation_transitions",
            "successful_recoveries",
            "maximum_remediation_attempts",
            "maximum_identical_failure_repetitions",
            "maximum_no_progress_cycles",
            "maximum_wait_remediation_transitions",
        ):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{field_name} must be a non-negative integer")
        for field_name in (
            "maximum_remediation_attempts",
            "maximum_identical_failure_repetitions",
            "maximum_no_progress_cycles",
            "maximum_wait_remediation_transitions",
        ):
            if getattr(self, field_name) <= 0:
                raise ValueError(f"{field_name} must be > 0")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "project_id": self.project_id,
            "unit_id": self.unit_id,
            "envelope_id": self.envelope_id,
            "total_remediation_attempts": self.total_remediation_attempts,
            "current_failure_signature": self.current_failure_signature,
            "identical_failure_repetitions": self.identical_failure_repetitions,
            "no_progress_cycles": self.no_progress_cycles,
            "wait_remediation_transitions": self.wait_remediation_transitions,
            "last_progress_digest": self.last_progress_digest,
            "last_action": self.last_action,
            "successful_recoveries": self.successful_recoveries,
            "maximum_remediation_attempts": self.maximum_remediation_attempts,
            "maximum_identical_failure_repetitions": self.maximum_identical_failure_repetitions,
            "maximum_no_progress_cycles": self.maximum_no_progress_cycles,
            "maximum_wait_remediation_transitions": self.maximum_wait_remediation_transitions,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RemediationCircuitState":
        return cls(**payload)

    @property
    def digest(self) -> str:
        return receipt_digest(self.to_dict())


@dataclass(frozen=True, slots=True)
class CircuitDecision:
    constraint: CircuitConstraint
    reason: CircuitReason
    state: RemediationCircuitState
    schema_version: str = CIRCUIT_BREAKER_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "constraint": self.constraint.value,
            "reason": self.reason.value,
            "state": self.state.to_dict(),
            "state_digest": self.state.digest,
        }

    @property
    def digest(self) -> str:
        return receipt_digest(self.to_dict())


def request_remediation(
    state: RemediationCircuitState,
    *,
    failure_digest: str,
    progress_digest: str | None = None,
) -> CircuitDecision:
    if not isinstance(state, RemediationCircuitState):
        raise TypeError("state must be RemediationCircuitState")
    signature = normalize_sha256(failure_digest, "failure_digest")
    progress = None if progress_digest is None else normalize_sha256(progress_digest, "progress_digest")

    if state.total_remediation_attempts >= state.maximum_remediation_attempts:
        return CircuitDecision(CircuitConstraint.ESCALATE_HUMAN, CircuitReason.TOTAL_BUDGET_EXHAUSTED, state)

    identical = state.identical_failure_repetitions + 1 if signature == state.current_failure_signature else 1
    if identical > state.maximum_identical_failure_repetitions:
        return CircuitDecision(CircuitConstraint.ESCALATE_HUMAN, CircuitReason.IDENTICAL_FAILURE_LIMIT_EXCEEDED, state)

    no_progress = 0
    if progress is not None and state.last_progress_digest is not None:
        no_progress = state.no_progress_cycles + 1 if progress == state.last_progress_digest else 0
    elif state.last_action == "REMEDIATION":
        no_progress = state.no_progress_cycles + 1
    if no_progress > state.maximum_no_progress_cycles:
        return CircuitDecision(CircuitConstraint.ESCALATE_HUMAN, CircuitReason.NO_PROGRESS_LIMIT_EXCEEDED, state)

    wait_transitions = state.wait_remediation_transitions + (1 if state.last_action == "WAIT_FOR_EVIDENCE" else 0)
    if wait_transitions > state.maximum_wait_remediation_transitions:
        return CircuitDecision(CircuitConstraint.ESCALATE_HUMAN, CircuitReason.WAIT_REMEDIATION_LOOP_LIMIT_EXCEEDED, state)

    next_state = replace(
        state,
        total_remediation_attempts=state.total_remediation_attempts + 1,
        current_failure_signature=signature,
        identical_failure_repetitions=identical,
        no_progress_cycles=no_progress,
        wait_remediation_transitions=wait_transitions,
        last_progress_digest=progress if progress is not None else state.last_progress_digest,
        last_action="REMEDIATION",
    )
    return CircuitDecision(CircuitConstraint.ALLOW_REMEDIATION, CircuitReason.REMEDIATION_AVAILABLE, next_state)


def record_evidence_wait(state: RemediationCircuitState) -> CircuitDecision:
    if not isinstance(state, RemediationCircuitState):
        raise TypeError("state must be RemediationCircuitState")
    transitions = state.wait_remediation_transitions + (1 if state.last_action == "REMEDIATION" else 0)
    if transitions > state.maximum_wait_remediation_transitions:
        return CircuitDecision(CircuitConstraint.ESCALATE_HUMAN, CircuitReason.WAIT_REMEDIATION_LOOP_LIMIT_EXCEEDED, state)
    next_state = replace(state, wait_remediation_transitions=transitions, last_action="WAIT_FOR_EVIDENCE")
    return CircuitDecision(CircuitConstraint.WAIT_FOR_EVIDENCE, CircuitReason.EVIDENCE_WAIT_RECORDED, next_state)


def record_success(state: RemediationCircuitState, *, progress_digest: str) -> CircuitDecision:
    if not isinstance(state, RemediationCircuitState):
        raise TypeError("state must be RemediationCircuitState")
    progress = normalize_sha256(progress_digest, "progress_digest")
    next_state = replace(
        state,
        current_failure_signature=None,
        identical_failure_repetitions=0,
        no_progress_cycles=0,
        wait_remediation_transitions=0,
        last_progress_digest=progress,
        last_action="SUCCESS",
        successful_recoveries=state.successful_recoveries + 1,
    )
    return CircuitDecision(CircuitConstraint.CONTINUE, CircuitReason.SUCCESS_RECORDED, next_state)


@dataclass(frozen=True, slots=True)
class CircuitArbiterEvaluation:
    circuit: CircuitDecision
    arbiter_result: ArbiterKernelResult

    @property
    def digest(self) -> str:
        return receipt_digest({"circuit": self.circuit.to_dict(), "arbiter": self.arbiter_result.to_dict()})


def evaluate_circuit_with_arbiter(
    kernel_input: ArbiterKernelInput,
    circuit: CircuitDecision,
) -> CircuitArbiterEvaluation:
    if not isinstance(kernel_input, ArbiterKernelInput):
        raise TypeError("kernel_input must be ArbiterKernelInput")
    if not isinstance(circuit, CircuitDecision):
        raise TypeError("circuit must be CircuitDecision")
    effective = kernel_input
    if circuit.constraint is CircuitConstraint.ESCALATE_HUMAN:
        effective = replace(kernel_input, scope_or_policy_decision_required=True)
    elif circuit.constraint is CircuitConstraint.WAIT_FOR_EVIDENCE:
        effective = replace(kernel_input, governance_evidence_complete=False)
    elif circuit.constraint is CircuitConstraint.ALLOW_REMEDIATION:
        consumed_before_current = max(0, circuit.state.total_remediation_attempts - 1)
        effective = replace(
            kernel_input,
            deterministic_defect=True,
            remediation_authorized=True,
            remediation_in_scope=True,
            remediation_attempt_count=consumed_before_current,
            identical_failure_repetitions=circuit.state.identical_failure_repetitions,
            maximum_remediation_attempts=circuit.state.maximum_remediation_attempts,
            maximum_identical_failure_repetitions=circuit.state.maximum_identical_failure_repetitions,
        )
    return CircuitArbiterEvaluation(circuit=circuit, arbiter_result=evaluate_arbiter(effective))
