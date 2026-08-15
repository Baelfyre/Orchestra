from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Any, Iterable

from .evidence import receipt_digest
from .governance_kernel import ArbiterKernelInput, ArbiterKernelResult, evaluate_arbiter

HOST_PROTOCOL_SCHEMA_VERSION = "orchestra.host-capability.v1"


class HostCapability(str, Enum):
    FILESYSTEM_READ = "FILESYSTEM_READ"
    FILESYSTEM_WRITE = "FILESYSTEM_WRITE"
    SHELL_EXECUTE = "SHELL_EXECUTE"
    GIT_READ = "GIT_READ"
    GIT_WRITE = "GIT_WRITE"
    REMOTE_READ = "REMOTE_READ"
    REMOTE_WRITE = "REMOTE_WRITE"
    NETWORK_READ = "NETWORK_READ"
    STRUCTURED_OUTPUT = "STRUCTURED_OUTPUT"
    MCP_TOOL_CALL = "MCP_TOOL_CALL"
    SANDBOX_EXECUTE = "SANDBOX_EXECUTE"
    SCHEDULED_TASKS = "SCHEDULED_TASKS"


def _text(value: object, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} must be non-empty")
    return text


def _capability(value: HostCapability | str) -> HostCapability:
    if isinstance(value, HostCapability):
        return value
    try:
        return HostCapability(_text(value, "capability"))
    except ValueError as exc:
        raise ValueError(f"unsupported host capability: {value!r}") from exc


def _capabilities(values: Iterable[HostCapability | str], field_name: str) -> tuple[HostCapability, ...]:
    raw = tuple(_capability(value) for value in values)
    if len(raw) != len(set(raw)):
        raise ValueError(f"{field_name} contains duplicate capabilities")
    return tuple(sorted(raw, key=lambda item: item.value))


@dataclass(frozen=True, slots=True)
class HostCapabilityDeclaration:
    host_id: str
    adapter_id: str
    capabilities: tuple[HostCapability | str, ...]
    evidence_refs: tuple[str, ...]
    observed_at: str
    schema_version: str = HOST_PROTOCOL_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != HOST_PROTOCOL_SCHEMA_VERSION:
            raise ValueError(f"unsupported host declaration schema {self.schema_version!r}")
        object.__setattr__(self, "host_id", _text(self.host_id, "host_id"))
        object.__setattr__(self, "adapter_id", _text(self.adapter_id, "adapter_id"))
        object.__setattr__(self, "capabilities", _capabilities(self.capabilities, "capabilities"))
        if not isinstance(self.evidence_refs, tuple) or not self.evidence_refs:
            raise ValueError("evidence_refs must be a non-empty tuple")
        refs = tuple(_text(item, "evidence_ref") for item in self.evidence_refs)
        if len(refs) != len(set(refs)):
            raise ValueError("evidence_refs contain duplicates")
        object.__setattr__(self, "evidence_refs", refs)
        object.__setattr__(self, "observed_at", _text(self.observed_at, "observed_at"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "host_id": self.host_id,
            "adapter_id": self.adapter_id,
            "capabilities": [item.value for item in self.capabilities],
            "evidence_refs": list(self.evidence_refs),
            "observed_at": self.observed_at,
        }

    @property
    def digest(self) -> str:
        return receipt_digest(self.to_dict())


@dataclass(frozen=True, slots=True)
class HostCapabilityGateResult:
    host_id: str
    declaration_digest: str
    required_capabilities: tuple[HostCapability | str, ...]
    missing_capabilities: tuple[HostCapability | str, ...]
    alternate_host_allowed: bool
    ready: bool
    schema_version: str = HOST_PROTOCOL_SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "host_id", _text(self.host_id, "host_id"))
        object.__setattr__(self, "declaration_digest", _text(self.declaration_digest, "declaration_digest"))
        object.__setattr__(self, "required_capabilities", _capabilities(self.required_capabilities, "required_capabilities"))
        object.__setattr__(self, "missing_capabilities", _capabilities(self.missing_capabilities, "missing_capabilities"))
        if not isinstance(self.alternate_host_allowed, bool) or not isinstance(self.ready, bool):
            raise TypeError("alternate_host_allowed and ready must be bool")
        if self.ready is (len(self.missing_capabilities) != 0):
            raise ValueError("ready must equal whether missing_capabilities is empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "host_id": self.host_id,
            "declaration_digest": self.declaration_digest,
            "required_capabilities": [item.value for item in self.required_capabilities],
            "missing_capabilities": [item.value for item in self.missing_capabilities],
            "alternate_host_allowed": self.alternate_host_allowed,
            "ready": self.ready,
        }

    @property
    def digest(self) -> str:
        return receipt_digest(self.to_dict())


def evaluate_host_capabilities(
    declaration: HostCapabilityDeclaration,
    required_capabilities: Iterable[HostCapability | str],
    *,
    alternate_host_allowed: bool,
) -> HostCapabilityGateResult:
    if not isinstance(declaration, HostCapabilityDeclaration):
        raise TypeError("declaration must be HostCapabilityDeclaration")
    required = _capabilities(tuple(required_capabilities), "required_capabilities")
    available = set(declaration.capabilities)
    missing = tuple(item for item in required if item not in available)
    return HostCapabilityGateResult(
        host_id=declaration.host_id,
        declaration_digest=declaration.digest,
        required_capabilities=required,
        missing_capabilities=missing,
        alternate_host_allowed=alternate_host_allowed,
        ready=not missing,
    )


@dataclass(frozen=True, slots=True)
class HostConformanceEvaluation:
    host_gate: HostCapabilityGateResult
    arbiter_result: ArbiterKernelResult

    def to_dict(self) -> dict[str, Any]:
        return {
            "host_gate": self.host_gate.to_dict(),
            "arbiter_result": self.arbiter_result.to_dict(),
        }

    @property
    def digest(self) -> str:
        return receipt_digest(self.to_dict())


def evaluate_host_with_arbiter(
    kernel_input: ArbiterKernelInput,
    host_gate: HostCapabilityGateResult,
) -> HostConformanceEvaluation:
    if not isinstance(kernel_input, ArbiterKernelInput):
        raise TypeError("kernel_input must be ArbiterKernelInput")
    if not isinstance(host_gate, HostCapabilityGateResult):
        raise TypeError("host_gate must be HostCapabilityGateResult")
    effective = kernel_input
    if not host_gate.ready:
        if host_gate.alternate_host_allowed:
            effective = replace(kernel_input, host_capacity_available=False)
        else:
            effective = replace(kernel_input, scope_or_policy_decision_required=True)
    return HostConformanceEvaluation(
        host_gate=host_gate,
        arbiter_result=evaluate_arbiter(effective),
    )
