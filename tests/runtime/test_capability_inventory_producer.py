# @codebase_provenance_JEO
# @codebase_rights_JEO

from dataclasses import replace

import pytest

from orchestra_runtime.application.ports.capability_inventory_producer import (
    CapabilityInventoryProducer,
    CapabilityInventoryReadResult,
    CapabilityInventoryReadStatus,
)
from orchestra_runtime.domain.adaptive import (
    CapabilityInventoryDescriptor,
    CapabilityInventoryIdentity,
    CapabilityResourceKind,
    InventoryCompatibilityStatus,
    InventoryObservationStatus,
)
from orchestra_runtime.infrastructure.hosts.capability_inventory import (
    UnavailableCapabilityInventoryProducer,
)


def descriptor(resource_id: str, source_id: str) -> CapabilityInventoryDescriptor:
    return CapabilityInventoryDescriptor(
        identity=CapabilityInventoryIdentity(resource_id, source_id),
        resource_kind=CapabilityResourceKind.EXTERNAL_PLUGIN,
        observation=InventoryObservationStatus.UNKNOWN,
        compatibility=InventoryCompatibilityStatus.UNKNOWN,
    )


def test_unavailable_producer_is_unknown_and_performs_no_discovery() -> None:
    producer = UnavailableCapabilityInventoryProducer()

    result = producer.read_cached_snapshot()

    assert isinstance(producer, CapabilityInventoryProducer)
    assert result.status is CapabilityInventoryReadStatus.UNKNOWN
    assert result.descriptors == ()
    assert "No trusted host inventory producer" in result.limitations[0]
    assert not hasattr(producer, "refresh")
    assert not hasattr(producer, "scan")
    assert not hasattr(producer, "connect")
    assert not hasattr(producer, "invoke")


def test_read_result_preserves_unknown_observations_without_promoting_them() -> None:
    observation = descriptor("plugin.one", "publisher.one")

    result = CapabilityInventoryReadResult("READ", (observation,))

    assert result.descriptors == (observation,)
    assert result.descriptors[0].observation is InventoryObservationStatus.UNKNOWN
    assert result.descriptors[0].compatibility is InventoryCompatibilityStatus.UNKNOWN
    assert not hasattr(result, "trusted")
    assert not hasattr(result, "authorized")


def test_read_result_order_is_deterministic() -> None:
    first = descriptor("plugin.b", "publisher.b")
    second = descriptor("plugin.a", "publisher.a")
    one = descriptor("plugin.same", "publisher.same")
    two = replace(one, identity=replace(one.identity, distribution_digest="sha256:two"))
    three = replace(one, identity=replace(one.identity, distribution_digest="sha256:one"))

    assert CapabilityInventoryReadResult("READ", (first, second)) == CapabilityInventoryReadResult(
        "READ", (second, first)
    )
    assert CapabilityInventoryReadResult("READ", (one, two, three)) == CapabilityInventoryReadResult(
        "READ", (three, one, two)
    )


def test_non_read_results_cannot_carry_descriptors() -> None:
    with pytest.raises(ValueError, match="must not contain descriptors"):
        CapabilityInventoryReadResult("UNKNOWN", (descriptor("plugin.one", "publisher.one"),))

    with pytest.raises(ValueError, match="must not contain descriptors"):
        CapabilityInventoryReadResult("UNSUPPORTED", (descriptor("plugin.one", "publisher.one"),))


def test_read_result_rejects_malformed_and_duplicate_descriptors() -> None:
    item = descriptor("plugin.one", "publisher.one")

    with pytest.raises(TypeError, match="must be a list or tuple"):
        CapabilityInventoryReadResult("READ", "not descriptors")  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="must contain CapabilityInventoryDescriptor"):
        CapabilityInventoryReadResult("READ", (object(),))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="unique identities"):
        CapabilityInventoryReadResult("READ", (item, replace(item)))

    with pytest.raises(ValueError, match="status is unsupported"):
        CapabilityInventoryReadResult("AVAILABLE")

    with pytest.raises(TypeError, match="status must be a string"):
        CapabilityInventoryReadResult(1)  # type: ignore[arg-type]


def test_read_result_rejects_malformed_limitations() -> None:
    with pytest.raises(TypeError, match="limitations must be a list or tuple"):
        CapabilityInventoryReadResult("UNKNOWN", limitations="unknown")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="non-empty strings"):
        CapabilityInventoryReadResult("UNKNOWN", limitations=(" ",))
