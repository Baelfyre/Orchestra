from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable

from ...shared.canonicalization import receipt_digest


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


__all__ = [
    "PREEXECUTION_SCHEMA_VERSION",
    "ExecutionAction",
    "ExecutionIntent",
    "PreExecutionConstraint",
    "PreExecutionPolicy",
    "PreExecutionReason",
]
