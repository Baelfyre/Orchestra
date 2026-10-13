"""Fail-closed capability inventory producer when no trusted host bridge exists."""

# @codebase_provenance_JEO
# @codebase_rights_JEO

from __future__ import annotations

from ...application.ports.capability_inventory_producer import (
    CapabilityInventoryReadResult,
    CapabilityInventoryReadStatus,
)


class UnavailableCapabilityInventoryProducer:
    """Report unknown inventory without probing or contacting a host."""

    def read_cached_snapshot(self) -> CapabilityInventoryReadResult:
        return CapabilityInventoryReadResult(
            CapabilityInventoryReadStatus.UNKNOWN,
            limitations=("No trusted host inventory producer is configured.",),
        )
