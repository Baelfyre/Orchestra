"""Scoped, non-authorizing capability and reusable-pattern memory records."""

# @codebase_provenance_JEO
# @codebase_rights_JEO

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re

from .capability_inventory import CapabilityInventoryDescriptor, CapabilityInventoryIdentity
from ...shared import normalize_timestamp


CAPABILITY_MEMORY_SCHEMA_VERSION = "orchestra.capability-memory.v1"
_IDENTIFIER_RE = re.compile(r"^[a-z0-9][a-z0-9_.:-]{0,127}$")


def _identifier(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = value.strip().casefold()
    if not _IDENTIFIER_RE.fullmatch(normalized):
        raise ValueError(f"{field_name} must be a canonical identifier")
    return normalized


class CapabilityMemoryRecordKind(str, Enum):
    CAPABILITY_OBSERVATION = "CAPABILITY_OBSERVATION"
    REUSABLE_PATTERN = "REUSABLE_PATTERN"


class CapabilityMemoryRecordStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INVALIDATED = "INVALIDATED"
    SUPERSEDED = "SUPERSEDED"


@dataclass(frozen=True, slots=True)
class CapabilityMemoryScope:
    """Opaque storage partition; its values do not authenticate a host identity."""

    host_id: str
    user_scope_id: str
    workspace_scope_id: str

    def __post_init__(self) -> None:
        for field_name in ("host_id", "user_scope_id", "workspace_scope_id"):
            object.__setattr__(self, field_name, _identifier(getattr(self, field_name), field_name))

    @classmethod
    def from_identity(cls, identity: CapabilityInventoryIdentity) -> CapabilityMemoryScope:
        if not isinstance(identity, CapabilityInventoryIdentity) or any(
            getattr(identity, field_name) is None
            for field_name in ("host_id", "user_scope_id", "workspace_scope_id")
        ):
            raise ValueError("complete host, user, and workspace identity is required")
        return cls(identity.host_id, identity.user_scope_id, identity.workspace_scope_id)


@dataclass(frozen=True, slots=True)
class CapabilityMemoryRecord:
    record_id: str
    scope: CapabilityMemoryScope
    kind: CapabilityMemoryRecordKind | str
    descriptor: CapabilityInventoryDescriptor
    recorded_at: str
    status: CapabilityMemoryRecordStatus | str = CapabilityMemoryRecordStatus.ACTIVE
    superseded_by: str | None = None
    schema_version: str = CAPABILITY_MEMORY_SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "record_id", _identifier(self.record_id, "record_id"))
        if not isinstance(self.scope, CapabilityMemoryScope):
            raise TypeError("scope must be CapabilityMemoryScope")
        if not isinstance(self.descriptor, CapabilityInventoryDescriptor):
            raise TypeError("descriptor must be CapabilityInventoryDescriptor")
        if self.schema_version != CAPABILITY_MEMORY_SCHEMA_VERSION:
            raise ValueError("schema_version is unsupported")
        for field_name, enum_type in (
            ("kind", CapabilityMemoryRecordKind),
            ("status", CapabilityMemoryRecordStatus),
        ):
            value = getattr(self, field_name)
            if not isinstance(value, enum_type):
                if not isinstance(value, str):
                    raise TypeError(f"{field_name} must be a string")
                try:
                    value = enum_type(value)
                except ValueError as exc:
                    raise ValueError(f"{field_name} is unsupported") from exc
            object.__setattr__(self, field_name, value)

        identity = self.descriptor.identity
        if identity.observation_scope is None:
            raise ValueError("memory records require complete inventory identity scope")
        if (identity.host_id, identity.user_scope_id, identity.workspace_scope_id) != (
            self.scope.host_id,
            self.scope.user_scope_id,
            self.scope.workspace_scope_id,
        ):
            raise ValueError("descriptor identity does not match memory scope")
        if self.kind is CapabilityMemoryRecordKind.REUSABLE_PATTERN:
            if self.descriptor.resource_kind.value != "PRIVATE_REFERENCE":
                raise ValueError("reusable patterns must use PRIVATE_REFERENCE resources")
            if not self.descriptor.independent_output_refs:
                raise ValueError("reusable patterns require evidence references")

        object.__setattr__(self, "recorded_at", normalize_timestamp(self.recorded_at, "recorded_at"))
        if self.superseded_by is not None:
            object.__setattr__(self, "superseded_by", _identifier(self.superseded_by, "superseded_by"))
        if self.status is CapabilityMemoryRecordStatus.SUPERSEDED:
            if self.superseded_by is None or self.superseded_by == self.record_id:
                raise ValueError("superseded records require a different superseded_by record")
        elif self.superseded_by is not None:
            raise ValueError("only superseded records may name superseded_by")


__all__ = [
    "CAPABILITY_MEMORY_SCHEMA_VERSION",
    "CapabilityMemoryRecord",
    "CapabilityMemoryRecordKind",
    "CapabilityMemoryRecordStatus",
    "CapabilityMemoryScope",
]
