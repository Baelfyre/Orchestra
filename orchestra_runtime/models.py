from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .lifecycle import StructuredTerminalResult


@dataclass(frozen=True)
class Skill:
    slug: str
    name: str
    description: str
    skill_path: Path
    role: str = ""
    activation_level: str = ""
    depends_on: str = ""
    commands: tuple[str, ...] = ()
    output_formats: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Command:
    name: str
    raw_input: str
    adapter_name: str
    arguments: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ContextPackage:
    adapter_name: str
    prompt: str
    project_root: Path
    available_commands: tuple[str, ...]
    manifest_version: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RouteDecision:
    command_name: str
    skill_slug: str
    governance_required: bool
    reason: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GovernanceRule:
    name: str
    description: str
    skill_slugs: tuple[str, ...] = ()
    command_names: tuple[str, ...] = ()
    validator_key: str = ""
    blocking: bool = True


@dataclass(frozen=True)
class ValidationResult:
    allowed: bool
    status: str
    reasons: tuple[str, ...] = ()
    evaluated_rules: tuple[str, ...] = ()


@dataclass(frozen=True)
class ExecutionResult:
    success: bool
    adapter_name: str
    command_name: str
    route: RouteDecision
    validation: ValidationResult
    output: str
    audit_entry_id: str
    run_identity: RunIdentity | None = None
    authority_decision_id: str | None = None
    capability_decision_id: str | None = None
    authority_mode: str | None = None
    lifecycle_state: str | None = None
    terminal_result: StructuredTerminalResult | None = None
    runtime_audit_event_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        event_ids = tuple(str(item).strip() for item in self.runtime_audit_event_ids)
        if any(not item for item in event_ids) or len(set(event_ids)) != len(event_ids):
            raise ValueError("runtime audit event identifiers must be non-empty and unique")
        object.__setattr__(self, "runtime_audit_event_ids", event_ids)
        if self.run_identity is None:
            if any(
                (
                    self.authority_decision_id,
                    self.capability_decision_id,
                    self.authority_mode,
                    self.lifecycle_state,
                    self.terminal_result,
                    event_ids,
                )
            ):
                raise ValueError("runtime evidence requires run identity")
            return

        mode = str(self.authority_mode or "").strip()
        state = str(self.lifecycle_state or "").strip()
        if mode not in {"ACTIVE", "COMPATIBILITY"}:
            raise ValueError("runtime evidence requires a valid authority mode")
        valid_states = {
            "INITIALIZING",
            "ACTIVE",
            "WAITING",
            "COMPLETED",
            "FAILED",
            "CANCELLED",
            "TIMED_OUT",
            "BLOCKED",
        }
        if state not in valid_states:
            raise ValueError("runtime evidence requires a valid lifecycle state")
        terminal_states = {"COMPLETED", "FAILED", "CANCELLED", "TIMED_OUT", "BLOCKED"}
        if state in terminal_states:
            if (
                self.terminal_result is None
                or self.terminal_result.run_id != self.run_identity.run_id
                or self.terminal_result.state.value != state
            ):
                raise ValueError("terminal runtime evidence must match lifecycle state")
        elif self.terminal_result is not None:
            raise ValueError("non-terminal runtime evidence cannot include a terminal result")
        object.__setattr__(self, "authority_mode", mode)
        object.__setattr__(self, "lifecycle_state", state)


class AuditEventType(str, Enum):
    ROOT_AUTHORITY_CREATED = "ROOT_AUTHORITY_CREATED"
    AUTHORITY_DECIDED = "AUTHORITY_DECIDED"
    CAPABILITY_MANIFEST_CREATED = "CAPABILITY_MANIFEST_CREATED"
    CAPABILITY_DECIDED = "CAPABILITY_DECIDED"
    DELEGATION_ACCEPTED = "DELEGATION_ACCEPTED"
    DELEGATION_REJECTED = "DELEGATION_REJECTED"
    LIFECYCLE_TRANSITIONED = "LIFECYCLE_TRANSITIONED"
    TERMINAL_RESULT_RECORDED = "TERMINAL_RESULT_RECORDED"
    INITIALIZATION_FAILED = "INITIALIZATION_FAILED"
    COLLABORATION_SESSION_OPENED = "COLLABORATION_SESSION_OPENED"
    COLLABORATION_STATUS_TRANSITIONED = "COLLABORATION_STATUS_TRANSITIONED"
    CONTRACT_FROZEN = "CONTRACT_FROZEN"
    CONTRACT_INVALIDATED = "CONTRACT_INVALIDATED"
    SPECIALIST_REENTRY_RECOMMENDED = "SPECIALIST_REENTRY_RECOMMENDED"
    COLLABORATION_SESSION_CLOSED = "COLLABORATION_SESSION_CLOSED"
    COORDINATION_INPUT_REJECTED = "COORDINATION_INPUT_REJECTED"


@dataclass(frozen=True, slots=True)
class RunIdentity:
    run_id: str
    parent_run_id: str | None = None

    def __post_init__(self) -> None:
        run_id = self.run_id.strip()
        parent_run_id = self.parent_run_id.strip() if self.parent_run_id else None
        if not run_id:
            raise ValueError("run_id must be non-empty")
        if parent_run_id == run_id:
            raise ValueError("parent_run_id must differ from run_id")
        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(self, "parent_run_id", parent_run_id)

    def to_dict(self) -> dict[str, str | None]:
        return {"run_id": self.run_id, "parent_run_id": self.parent_run_id}


@dataclass(frozen=True, slots=True)
class RuntimeAuditEvent:
    event_id: str
    event_type: AuditEventType
    run_id: str
    related_id: str
    reason_code: str
    provenance_ids: tuple[str, ...] = ()
    details: tuple[tuple[str, str], ...] = ()
    parent_run_id: str | None = None

    def __post_init__(self) -> None:
        event_id = self.event_id.strip()
        run_id = self.run_id.strip()
        related_id = self.related_id.strip()
        reason_code = self.reason_code.strip()
        if not all((event_id, run_id, related_id, reason_code)):
            raise ValueError("audit event identifiers and reason_code must be non-empty")
        event_type = AuditEventType(self.event_type)
        provenance_ids = tuple(sorted({item.strip() for item in self.provenance_ids if item.strip()}))
        details = tuple(sorted((str(key).strip(), str(value)) for key, value in self.details))
        if any(not key for key, _ in details) or len({key for key, _ in details}) != len(details):
            raise ValueError("audit detail keys must be non-empty and unique")
        object.__setattr__(self, "event_id", event_id)
        object.__setattr__(self, "event_type", event_type)
        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(self, "related_id", related_id)
        object.__setattr__(self, "reason_code", reason_code)
        object.__setattr__(self, "provenance_ids", provenance_ids)
        object.__setattr__(self, "details", details)
        object.__setattr__(self, "parent_run_id", self.parent_run_id.strip() if self.parent_run_id else None)

    def to_dict(self) -> dict[str, object]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "run_id": self.run_id,
            "parent_run_id": self.parent_run_id,
            "related_id": self.related_id,
            "reason_code": self.reason_code,
            "provenance_ids": list(self.provenance_ids),
            "details": {key: value for key, value in self.details},
        }
