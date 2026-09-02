from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from .domain.governance.preexecution import (
    PREEXECUTION_SCHEMA_VERSION,
    ExecutionAction,
    ExecutionIntent,
    PreExecutionConstraint,
    PreExecutionPolicy,
    PreExecutionReason,
    _is_within,
)
from .evidence import receipt_digest
from .governance_kernel import ArbiterKernelInput, ArbiterKernelResult, evaluate_arbiter
from .host_protocol import (
    HostCapability,
    HostCapabilityDeclaration,
    HostCapabilityGateResult,
    evaluate_host_capabilities,
)


_ACTION_CAPABILITY = {
    ExecutionAction.FILE_READ: HostCapability.FILESYSTEM_READ,
    ExecutionAction.FILE_WRITE: HostCapability.FILESYSTEM_WRITE,
    ExecutionAction.SHELL_EXECUTE: HostCapability.SHELL_EXECUTE,
    ExecutionAction.NETWORK_READ: HostCapability.NETWORK_READ,
    ExecutionAction.REMOTE_WRITE: HostCapability.REMOTE_WRITE,
    ExecutionAction.DESTRUCTIVE_SIMULATION: HostCapability.SANDBOX_EXECUTE,
    ExecutionAction.PRODUCTION_MUTATION: HostCapability.REMOTE_WRITE,
}
_PATH_ACTIONS = frozenset({ExecutionAction.FILE_READ, ExecutionAction.FILE_WRITE})


@dataclass(frozen=True, slots=True)
class PreExecutionGateResult:
    constraint: PreExecutionConstraint
    reason: PreExecutionReason
    intent_digest: str
    policy_digest: str
    host_gate: HostCapabilityGateResult | None
    schema_version: str = PREEXECUTION_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "constraint": self.constraint.value,
            "reason": self.reason.value,
            "intent_digest": self.intent_digest,
            "policy_digest": self.policy_digest,
            "host_gate": None if self.host_gate is None else self.host_gate.to_dict(),
        }

    @property
    def digest(self) -> str:
        return receipt_digest(self.to_dict())


def _gate(
    intent: ExecutionIntent,
    policy: PreExecutionPolicy,
    constraint: PreExecutionConstraint,
    reason: PreExecutionReason,
    host_gate: HostCapabilityGateResult | None = None,
) -> PreExecutionGateResult:
    return PreExecutionGateResult(constraint, reason, intent.digest, policy.digest, host_gate)


def evaluate_preexecution(
    intent: ExecutionIntent,
    policy: PreExecutionPolicy,
    host: HostCapabilityDeclaration,
) -> PreExecutionGateResult:
    if not isinstance(intent, ExecutionIntent) or not isinstance(policy, PreExecutionPolicy):
        raise TypeError("intent/policy have invalid types")
    if not isinstance(host, HostCapabilityDeclaration):
        raise TypeError("host must be HostCapabilityDeclaration")

    if intent.action not in policy.allowed_actions:
        return _gate(intent, policy, PreExecutionConstraint.STOP, PreExecutionReason.ACTION_NOT_ALLOWED)

    if intent.action in _PATH_ACTIONS:
        for requested in intent.requested_paths:
            if any(_is_within(requested, root) for root in policy.prohibited_paths):
                return _gate(intent, policy, PreExecutionConstraint.STOP, PreExecutionReason.PROHIBITED_PATH)
            if not policy.allowed_paths or not any(_is_within(requested, root) for root in policy.allowed_paths):
                return _gate(intent, policy, PreExecutionConstraint.STOP, PreExecutionReason.PATH_OUTSIDE_SCOPE)

    if intent.action is ExecutionAction.PRODUCTION_MUTATION and not policy.production_mutation_authorized:
        return _gate(
            intent,
            policy,
            PreExecutionConstraint.ESCALATE_HUMAN,
            PreExecutionReason.PRODUCTION_AUTHORITY_REQUIRED,
        )
    if intent.action is ExecutionAction.DESTRUCTIVE_SIMULATION and not policy.destructive_simulation_authorized:
        return _gate(
            intent,
            policy,
            PreExecutionConstraint.ESCALATE_HUMAN,
            PreExecutionReason.DESTRUCTIVE_AUTHORITY_REQUIRED,
        )
    if intent.action is ExecutionAction.REMOTE_WRITE and not policy.remote_write_authorized:
        return _gate(
            intent,
            policy,
            PreExecutionConstraint.ESCALATE_HUMAN,
            PreExecutionReason.REMOTE_WRITE_AUTHORITY_REQUIRED,
        )

    host_gate = evaluate_host_capabilities(
        host,
        (_ACTION_CAPABILITY[intent.action],),
        alternate_host_allowed=policy.alternate_host_allowed,
    )
    if not host_gate.ready:
        constraint = (
            PreExecutionConstraint.WAIT_FOR_CAPACITY
            if policy.alternate_host_allowed
            else PreExecutionConstraint.ESCALATE_HUMAN
        )
        return _gate(intent, policy, constraint, PreExecutionReason.HOST_CAPABILITY_MISSING, host_gate)
    return _gate(intent, policy, PreExecutionConstraint.ALLOW, PreExecutionReason.READY, host_gate)


@dataclass(frozen=True, slots=True)
class PreExecutionArbiterEvaluation:
    gate: PreExecutionGateResult
    arbiter_result: ArbiterKernelResult

    @property
    def digest(self) -> str:
        return receipt_digest({"gate": self.gate.to_dict(), "arbiter": self.arbiter_result.to_dict()})


def evaluate_preexecution_with_arbiter(
    kernel_input: ArbiterKernelInput,
    gate: PreExecutionGateResult,
) -> PreExecutionArbiterEvaluation:
    if not isinstance(kernel_input, ArbiterKernelInput) or not isinstance(gate, PreExecutionGateResult):
        raise TypeError("kernel_input/gate have invalid types")
    effective = kernel_input
    if gate.constraint is PreExecutionConstraint.STOP:
        effective = replace(kernel_input, protected_boundary_clear=False)
    elif gate.constraint is PreExecutionConstraint.ESCALATE_HUMAN:
        effective = replace(kernel_input, external_authority_missing=True)
    elif gate.constraint is PreExecutionConstraint.WAIT_FOR_CAPACITY:
        effective = replace(kernel_input, host_capacity_available=False)
    return PreExecutionArbiterEvaluation(gate=gate, arbiter_result=evaluate_arbiter(effective))
