"""Passive application boundary for supplied capability inventory snapshots."""

# @codebase_provenance_JEO
# @codebase_rights_JEO

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable

from ...domain.adaptive.capability_inventory import CapabilityInventoryDescriptor


def _identity_sort_key(item: CapabilityInventoryDescriptor) -> tuple[object, ...]:
    identity = item.identity
    return (
        identity.host_id or "",
        identity.user_scope_id or "",
        identity.workspace_scope_id or "",
        identity.resource_id,
        identity.source_id,
        identity.adapter_id or "",
        identity.publisher_id or "",
        identity.distribution_id or "",
        identity.distribution_version or "",
        identity.permission_scope_id or "",
        identity.source_revision or "",
        identity.distribution_digest or "",
        identity.inventory_scope_revision or "",
        identity.recheck_token or "",
        identity.identity_evidence_refs,
    )


class CapabilityInventoryReadStatus(str, Enum):
    READ = "READ"
    UNKNOWN = "UNKNOWN"
    UNSUPPORTED = "UNSUPPORTED"


@dataclass(frozen=True, slots=True)
class CapabilityInventoryReadResult:
    """A passive read result; returned descriptors remain untrusted observations."""

    status: CapabilityInventoryReadStatus | str
    descriptors: tuple[CapabilityInventoryDescriptor, ...] = ()
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        status = self.status
        if not isinstance(status, CapabilityInventoryReadStatus):
            if not isinstance(status, str):
                raise TypeError("status must be a string or CapabilityInventoryReadStatus")
            try:
                status = CapabilityInventoryReadStatus(status)
            except ValueError as exc:
                raise ValueError("status is unsupported") from exc
        object.__setattr__(self, "status", status)

        if not isinstance(self.descriptors, (tuple, list)):
            raise TypeError("descriptors must be a list or tuple")
        descriptors = tuple(self.descriptors)
        if any(not isinstance(item, CapabilityInventoryDescriptor) for item in descriptors):
            raise TypeError("descriptors must contain CapabilityInventoryDescriptor records")
        if len({item.identity for item in descriptors}) != len(descriptors):
            raise ValueError("descriptors must have unique identities")
        if status is not CapabilityInventoryReadStatus.READ and descriptors:
            raise ValueError("unknown or unsupported results must not contain descriptors")
        object.__setattr__(
            self,
            "descriptors",
            tuple(sorted(descriptors, key=_identity_sort_key)),
        )
        if not isinstance(self.limitations, (tuple, list)):
            raise TypeError("limitations must be a list or tuple")
        if any(not isinstance(item, str) or not item.strip() for item in self.limitations):
            raise ValueError("limitations must contain non-empty strings")
        object.__setattr__(self, "limitations", tuple(sorted(set(item.strip() for item in self.limitations))))


@runtime_checkable
class CapabilityInventoryProducer(Protocol):
    """Read an existing snapshot without discovery, refresh, or execution side effects.

    Implementations must scope returned observations to an authenticated active
    user/workspace context. If that context cannot be established, return UNKNOWN
    with no descriptors. This protocol and its labels do not authenticate a producer.
    """

    def read_cached_snapshot(self) -> CapabilityInventoryReadResult: ...


__all__ = [
    "CapabilityInventoryProducer",
    "CapabilityInventoryReadResult",
    "CapabilityInventoryReadStatus",
]
