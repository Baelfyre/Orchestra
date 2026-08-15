from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Any, Iterable

from .evidence import receipt_digest
from .governance_kernel import ArbiterKernelInput, ArbiterKernelResult, evaluate_arbiter
from .host_protocol import (
    HostCapability,
    HostCapabilityDeclaration,
    HostCapabilityGateResult,
    evaluate_host_capabilities,
)

PREEXECUTION_SCHEMA_VERSION = "orchestra.preexecution-policy.v1"


class ExecutionAction(str, Enum):
    FILE_READ = "FILE_READ"
    FILE_WRITE = "FILE_WRITE"
    SHELL_EXECUTE = "SHELL_EXECUTE"
    NETWORK_READ = "NETWORK_READ"
    REMOTE_WRITE = "REMOTE_WRITE"
    DESTRUCTIVE_SIMULATION = "DESTRUCTIVE_SIMULATION"
    PRODUCTION_MUTATION = "PRODUCTION_MUTATION"


class PreExecutionConstraint(str, Enum):
    ALLOW = "ALLOW"
    STOP = "STOP"
    ESCALATE_HUMAN = "ESCALATE_HUMAN"
    WAIT_FOR_CAPACITY = "WAIT_FOR_CAPACITY"


class PreExecutionReason(str, Enum):
    READY = "READY"
    ACTION_NOT_ALLOWED = "ACTION_NOT_ALLOWED"
    PATH_OUTSIDE_SCOPE = "PATH_OUTSIDE_SCOPE"
    PROHIBITED_PATH = "PROHIBITED_PATH"
    PRODUCTION_AUTHORITY_REQUIRED = "PRODUCTION_AUTHORITY_REQUIRED"
    DESTRUCTIVE_AUTHORITY_REQUIRED = "DESTRUCTIVE_AUTHORITY_REQUIRED"
    REMOTE_WRITE_AUTHORITY_REQUIRED = "REMOTE_WRITE_AUTHORITY_REQUIRED"
    HOST_CAPABILITY_MISSING = "HOST_CAPABILITY_MISSING"


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


def _text(value: object, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} must be non-empty")
    return text


def _action(value: ExecutionAction | str) -> ExecutionAction:
    if isinstance(value, ExecutionAction):
        return value
    try:
        return ExecutionAction(_text(value, "action"))
    except ValueError as exc:
        raise ValueError(f"unsupported execution action: {value!r}") from exc


def _path(value: object, field_name: str) -> str:
    raw = _text(value, field_name)
    if raw.startswith("file://") or raw.startswith("/") or raw.startswith("\\") or (len(raw) > 1 and raw[1] == ":"):
        raise ValueError(f"{field_name} must be repository-relative: {raw!r}")
    normalized = raw.replace("\\", "/").strip("/")
    parts = normalized.split("/")
    if not normalized or "." in parts or ".." in parts:
        raise ValueError(f"{field_name} contains unsafe path traversal: {raw!r}")
    return normalized


def _paths(values: Iterable[object], field_name: str) -> tuple[str, ...]:
    raw = tuple(_path(value, field_name) for value in values)
    if len(raw) != len(set(raw)):
        raise ValueError(f"{field_name} contains duplicate paths")
    return tuple(sorted(raw))


def _is_within(path: str, root: str) -> bool:
    return path == root or path.startswith(root.rstrip("/") + "/")


@dataclass(frozen=True, slots=True)
class ExecutionIntent:
    intent_id: str
    action: ExecutionAction | str
    requested_paths: tuple[str, ...] = ()
    operation_ref: str | None = None
    evidence_refs: tuple[str, ...] = ()
    schema_version: str = PREEXECUTION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != PREEXECUTION_SCHEMA_VERSION:
            raise ValueError(f"unsupported execution intent schema {self.schema_version!r}")
        object.__setattr__(self, "intent_id", _text(self.intent_id, "intent_id"))
        action = _action(self.action)
        object.__setattr__(self, "action", action)
        object.__setattr__(self, "requested_paths", _paths(self.requested_paths, "requested_paths"))
        if action in _PATH_ACTIONS and not self.requested_paths:
            raise ValueError(f"{action.value} requires at least one requested path")
        if self.operation_ref is not None:
            object.__setattr__(self, "operation_ref", _text(self.operation_ref, "operation_ref"))
        refs = tuple(_text(value, "evidence_ref") for value in self.evidence_refs)
        if len(refs) != len(set(refs)):
            raise ValueError("evidence_refs contains duplicates")
        object.__setattr__(self, "evidence_refs", tuple(sorted(refs)))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "intent_id": self.intent_id,
            "action": self.action.value,
            "requested_paths": list(self.requested_paths),
            "operation_ref": self.operation_ref,
            "evidence_refs": list(self.evidence_refs),
        }

    @property
    def digest(self) -> str:
        return receipt_digest(self.to_dict())


@dataclass(frozen=True, slots=True)
class PreExecutionPolicy:
    policy_id: str
    allowed_actions: tuple[ExecutionAction | str, ...]
    allowed_paths: tuple[str, ...] = ()
    prohibited_paths: tuple[str, ...] = ()
    remote_write_authorized: bool = False
    destructive_simulation_authorized: bool = False
    production_mutation_authorized: bool = False
    alternate_host_allowed: bool = True
    schema_version: str = PREEXECUTION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != PREEXECUTION_SCHEMA_VERSION:
            raise ValueError(f"unsupported pre-execution policy schema {self.schema_version!r}")
        object.__setattr__(self, "policy_id", _text(self.policy_id, "policy_id"))
        actions = tuple(_action(value) for value in self.allowed_actions)
        if not actions or len(actions) != len(set(actions)):
            raise ValueError("allowed_actions must be non-empty and unique")
        object.__setattr__(self, "allowed_actions", tuple(sorted(actions, key=lambda item: item.value)))
        allowed = _paths(self.allowed_paths, "allowed_paths")
        prohibited = _paths(self.prohibited_paths, "prohibited_paths")
        for left in allowed:
            for right in prohibited:
                # A prohibited descendant is a valid deny-subtree carve-out from an
                # otherwise allowed root (for example: allow ``src`` but deny
                # ``src/secrets``). The inverse is ambiguous/unsafe: an allowed
                # path may not live inside a prohibited root, and exact overlap is
                # rejected by the same rule.
                if _is_within(left, right):
                    raise ValueError(f"allowed path is inside prohibited path: {left!r} / {right!r}")
        object.__setattr__(self, "allowed_paths", allowed)
        object.__setattr__(self, "prohibited_paths", prohibited)
        for field_name in (
            "remote_write_authorized",
            "destructive_simulation_authorized",
            "production_mutation_authorized",
            "alternate_host_allowed",
        ):
            if not isinstance(getattr(self, field_name), bool):
                raise TypeError(f"{field_name} must be bool")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "policy_id": self.policy_id,
            "allowed_actions": [item.value for item in self.allowed_actions],
            "allowed_paths": list(self.allowed_paths),
            "prohibited_paths": list(self.prohibited_paths),
            "remote_write_authorized": self.remote_write_authorized,
            "destructive_simulation_authorized": self.destructive_simulation_authorized,
            "production_mutation_authorized": self.production_mutation_authorized,
            "alternate_host_allowed": self.alternate_host_allowed,
        }

    @property
    def digest(self) -> str:
        return receipt_digest(self.to_dict())


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


def _gate(intent: ExecutionIntent, policy: PreExecutionPolicy, constraint: PreExecutionConstraint, reason: PreExecutionReason, host_gate: HostCapabilityGateResult | None = None) -> PreExecutionGateResult:
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
        return _gate(intent, policy, PreExecutionConstraint.ESCALATE_HUMAN, PreExecutionReason.PRODUCTION_AUTHORITY_REQUIRED)
    if intent.action is ExecutionAction.DESTRUCTIVE_SIMULATION and not policy.destructive_simulation_authorized:
        return _gate(intent, policy, PreExecutionConstraint.ESCALATE_HUMAN, PreExecutionReason.DESTRUCTIVE_AUTHORITY_REQUIRED)
    if intent.action is ExecutionAction.REMOTE_WRITE and not policy.remote_write_authorized:
        return _gate(intent, policy, PreExecutionConstraint.ESCALATE_HUMAN, PreExecutionReason.REMOTE_WRITE_AUTHORITY_REQUIRED)

    host_gate = evaluate_host_capabilities(
        host,
        (_ACTION_CAPABILITY[intent.action],),
        alternate_host_allowed=policy.alternate_host_allowed,
    )
    if not host_gate.ready:
        constraint = PreExecutionConstraint.WAIT_FOR_CAPACITY if policy.alternate_host_allowed else PreExecutionConstraint.ESCALATE_HUMAN
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
