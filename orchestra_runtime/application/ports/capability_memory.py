"""Application port for scoped local capability-memory lifecycle operations."""

# @codebase_provenance_JEO
# @codebase_rights_JEO

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ...domain.adaptive.capability_memory import CapabilityMemoryRecord, CapabilityMemoryScope


@runtime_checkable
class CapabilityMemoryStore(Protocol):
    def load(
        self,
        scope: CapabilityMemoryScope,
        *,
        include_inactive: bool = False,
    ) -> tuple[CapabilityMemoryRecord, ...]: ...

    def save(self, record: CapabilityMemoryRecord) -> None: ...

    def invalidate(self, scope: CapabilityMemoryScope, record_id: str) -> bool: ...

    def supersede(
        self,
        scope: CapabilityMemoryScope,
        record_id: str,
        replacement: CapabilityMemoryRecord,
    ) -> None: ...

    def delete_record(self, scope: CapabilityMemoryScope, record_id: str) -> bool: ...

    def delete_scope(self, scope: CapabilityMemoryScope) -> int: ...


__all__ = ["CapabilityMemoryStore"]
