# @codebase_provenance_JEO
# @codebase_rights_JEO

from dataclasses import replace

import pytest

from orchestra_runtime.application.ports.capability_inventory_producer import (
    CapabilityInventoryReadResult,
    CapabilityInventoryReadStatus,
)
from orchestra_runtime.application.use_cases.capability_planning_preview import (
    build_capability_planning_preview,
)
from orchestra_runtime.domain.adaptive.capability_coverage import (
    CapabilityClaim,
    CapabilityCoverageStatus,
    TaskCapabilityFacet,
)
from orchestra_runtime.domain.adaptive.capability_inventory import (
    CapabilityDiscoveryDisposition,
    CapabilityDiscoveryTrigger,
    CapabilityInventoryClaim,
    CapabilityInventoryDescriptor,
    CapabilityInventoryIdentity,
    CapabilityResourceKind,
    InventoryCompatibilityStatus,
    InventoryObservationStatus,
)
from orchestra_runtime.domain.adaptive.capability_memory import (
    CapabilityMemoryRecord,
    CapabilityMemoryScope,
)
from orchestra_runtime.infrastructure.hosts.capability_inventory import (
    UnavailableCapabilityInventoryProducer,
)


NOW = "2026-10-14T08:00:00Z"
FUTURE = "2026-10-14T09:00:00Z"
SCOPE = CapabilityMemoryScope("host.desktop", "user.one", "workspace.one")
FACETS = (TaskCapabilityFacet("task.output", ("ui.accessibility",)),)


def descriptor(
    resource_id: str = "plugin.one",
    source_id: str = "source.plugin.one",
    claims: tuple[tuple[str, CapabilityClaim | str], ...] = (
        ("ui.accessibility", CapabilityClaim.SUPPORTS),
    ),
    *,
    scope: CapabilityMemoryScope = SCOPE,
    observed_at: str = "2026-10-14T07:00:00Z",
    valid_until: str = FUTURE,
    resource_kind: CapabilityResourceKind | str = CapabilityResourceKind.EXTERNAL_PLUGIN,
    permission_scope_id: str | None = "permissions.read.v1",
) -> CapabilityInventoryDescriptor:
    return CapabilityInventoryDescriptor(
        identity=CapabilityInventoryIdentity(
            resource_id,
            source_id,
            host_id=scope.host_id,
            user_scope_id=scope.user_scope_id,
            workspace_scope_id=scope.workspace_scope_id,
            permission_scope_id=permission_scope_id,
        ),
        resource_kind=resource_kind,
        observation=InventoryObservationStatus.PRESENT,
        compatibility=InventoryCompatibilityStatus.COMPATIBLE,
        capability_claims=tuple(
            CapabilityInventoryClaim(
                capability_id,
                claim,
                (f"evidence:{resource_id}:{capability_id}:{claim}",),
            )
            for capability_id, claim in claims
        ),
        observation_evidence_refs=(f"evidence:{resource_id}:inventory",),
        compatibility_evidence_refs=(f"evidence:{resource_id}:compatibility",),
        review_refs=(f"evidence:{resource_id}:review",),
        observed_at=observed_at,
        valid_until=valid_until,
    )


def record(
    record_id: str,
    observation: CapabilityInventoryDescriptor,
    scope: CapabilityMemoryScope = SCOPE,
) -> CapabilityMemoryRecord:
    return CapabilityMemoryRecord(record_id, scope, "CAPABILITY_OBSERVATION", observation, NOW)


class SnapshotProducer:
    def __init__(self, result: CapabilityInventoryReadResult) -> None:
        self.result = result
        self.reads = 0

    def read_cached_snapshot(self) -> CapabilityInventoryReadResult:
        self.reads += 1
        return self.result


class MemoryStore:
    def __init__(
        self,
        records: tuple[CapabilityMemoryRecord, ...] = (),
        *,
        raw_result: object | None = None,
    ) -> None:
        self.records = records
        self.raw_result = raw_result
        self.reads = 0
        self.writes = 0

    def load(self, scope: CapabilityMemoryScope, *, include_inactive: bool = False):
        self.reads += 1
        if self.raw_result is not None:
            return self.raw_result
        return tuple(item for item in self.records if item.scope == scope)

    def save(self, record: CapabilityMemoryRecord) -> None:
        self.writes += 1

    def invalidate(self, scope: CapabilityMemoryScope, record_id: str) -> bool:
        self.writes += 1
        return False

    def supersede(
        self,
        scope: CapabilityMemoryScope,
        record_id: str,
        replacement: CapabilityMemoryRecord,
    ) -> None:
        self.writes += 1

    def delete_record(self, scope: CapabilityMemoryScope, record_id: str) -> bool:
        self.writes += 1
        return False

    def delete_scope(self, scope: CapabilityMemoryScope) -> int:
        self.writes += 1
        return 0


def run_preview(
    producer: SnapshotProducer | UnavailableCapabilityInventoryProducer,
    memory: MemoryStore,
    *,
    scope: CapabilityMemoryScope | None = SCOPE,
    trigger: CapabilityDiscoveryTrigger | None = CapabilityDiscoveryTrigger(
        "CAPABILITY_GAP", ("ui.accessibility",), ()
    ),
):
    return build_capability_planning_preview(
        trigger=trigger,
        task_facets=FACETS,
        inventory_producer=producer,
        memory_store=memory,
        memory_scope=scope,
        evaluated_at=NOW,
    )


def test_cache_first_preview_reuses_scoped_memory_without_qualifying_declarations() -> None:
    current = descriptor()
    producer = SnapshotProducer(CapabilityInventoryReadResult("READ", (current,)))
    memory = MemoryStore((record("record.cached", current),))

    preview = run_preview(producer, memory)

    assert producer.reads == 1
    assert memory.reads == 1
    assert memory.writes == 0
    assert preview.inventory_status is CapabilityInventoryReadStatus.READ
    assert preview.memory_read_attempted
    assert preview.current_observations == (current,)
    assert preview.discovery_plan.disposition is CapabilityDiscoveryDisposition.CACHE_REUSE_HINT
    assert preview.discovery_plan.reuse_hint_identities == (current.identity,)
    assert preview.coverage is not None
    assert preview.coverage.items[0].status is CapabilityCoverageStatus.DECLARED
    assert preview.coverage.items[0].status is not CapabilityCoverageStatus.VERIFIED
    assert not hasattr(preview, "may_authorize")


def test_no_trigger_does_not_read_inventory_or_memory() -> None:
    producer = SnapshotProducer(CapabilityInventoryReadResult("READ", (descriptor(),)))
    memory = MemoryStore((record("record.cached", descriptor()),))

    preview = run_preview(producer, memory, trigger=None)

    assert producer.reads == 0
    assert memory.reads == 0
    assert preview.inventory_status is None
    assert preview.coverage is None
    assert preview.discovery_plan.disposition is CapabilityDiscoveryDisposition.NO_DISCOVERY


def test_missing_scope_keeps_inventory_and_memory_unknown_without_reads() -> None:
    producer = SnapshotProducer(CapabilityInventoryReadResult("READ", (descriptor(),)))
    memory = MemoryStore((record("record.cached", descriptor()),))

    preview = run_preview(producer, memory, scope=None)

    assert producer.reads == 0
    assert memory.reads == 0
    assert preview.inventory_status is CapabilityInventoryReadStatus.UNKNOWN
    assert preview.current_observations == ()
    assert preview.coverage is None
    assert preview.discovery_plan.target_capability_ids == ("ui.accessibility",)


@pytest.mark.parametrize(
    "status",
    (CapabilityInventoryReadStatus.UNKNOWN, CapabilityInventoryReadStatus.UNSUPPORTED),
)
def test_unavailable_inventory_never_reads_or_exposes_scoped_memory(
    status: CapabilityInventoryReadStatus,
) -> None:
    producer = SnapshotProducer(CapabilityInventoryReadResult(status))
    cached = descriptor()
    memory = MemoryStore((record("record.cached", cached),))

    preview = run_preview(producer, memory)

    assert producer.reads == 1
    assert memory.reads == 0
    assert preview.inventory_status is status
    assert preview.current_observations == ()
    assert preview.coverage is None
    assert preview.discovery_plan.relevant_observations == ()
    assert preview.discovery_plan.target_capability_ids == ("ui.accessibility",)


def test_cross_scope_inventory_fails_closed_before_memory_read() -> None:
    other_scope = CapabilityMemoryScope("host.desktop", "user.two", "workspace.two")
    producer = SnapshotProducer(
        CapabilityInventoryReadResult("READ", (descriptor(scope=other_scope),))
    )
    memory = MemoryStore((record("record.cached", descriptor()),))

    preview = run_preview(producer, memory)

    assert producer.reads == 1
    assert memory.reads == 0
    assert preview.inventory_status is CapabilityInventoryReadStatus.UNKNOWN
    assert preview.current_observations == ()
    assert preview.coverage is None
    assert preview.discovery_plan.relevant_observations == ()


def test_incomplete_permission_identity_fails_closed_before_memory_read() -> None:
    producer = SnapshotProducer(
        CapabilityInventoryReadResult("READ", (descriptor(permission_scope_id=None),))
    )
    memory = MemoryStore((record("record.cached", descriptor()),))

    preview = run_preview(producer, memory)

    assert memory.reads == 0
    assert preview.inventory_status is CapabilityInventoryReadStatus.UNKNOWN
    assert preview.current_observations == ()
    assert preview.coverage is None


def test_empty_or_unrelated_inventory_never_implies_absence() -> None:
    empty_producer = SnapshotProducer(CapabilityInventoryReadResult("READ"))
    empty_memory = MemoryStore((record("record.cached", descriptor()),))
    empty_preview = run_preview(empty_producer, empty_memory)

    assert empty_preview.inventory_status is CapabilityInventoryReadStatus.READ
    assert empty_preview.memory_read_attempted is False
    assert empty_preview.coverage is None
    assert empty_preview.discovery_plan.target_capability_ids == ("ui.accessibility",)

    unrelated = descriptor(
        "plugin.other",
        "source.other",
        (("code.formatting", "SUPPORTS"),),
    )
    unrelated_producer = SnapshotProducer(CapabilityInventoryReadResult("READ", (unrelated,)))
    unrelated_memory = MemoryStore((record("record.other", unrelated),))
    unrelated_preview = run_preview(unrelated_producer, unrelated_memory)

    assert unrelated_memory.reads == 1
    assert unrelated_preview.current_observations == ()
    assert unrelated_preview.coverage is None
    assert unrelated_preview.discovery_plan.target_capability_ids == ("ui.accessibility",)


def test_user_selected_resource_keeps_claim_and_request_identity() -> None:
    current = descriptor(
        "tool.selected",
        "source.selected",
        (("code.formatting", "SUPPORTS"),),
    )
    producer = SnapshotProducer(CapabilityInventoryReadResult("READ", (current,)))
    memory = MemoryStore()
    trigger = CapabilityDiscoveryTrigger("USER_REQUEST", (), ("tool.selected",))

    preview = run_preview(producer, memory, trigger=trigger)

    assert preview.current_observations == (current,)
    assert preview.coverage is not None
    assert preview.coverage.items[0].status is CapabilityCoverageStatus.MISSING
    assert preview.discovery_plan.requested_resource_ids == ("tool.selected",)
    assert preview.discovery_plan.target_resource_ids == ("tool.selected",)


def test_invalid_memory_store_output_fails_closed() -> None:
    current = descriptor()
    producer = SnapshotProducer(CapabilityInventoryReadResult("READ", (current,)))
    memory = MemoryStore(raw_result="not-records")
    with pytest.raises(TypeError, match="must return CapabilityMemoryRecord"):
        run_preview(producer, memory)

    other_scope = CapabilityMemoryScope("host.desktop", "user.two", "workspace.two")
    other_record = record("record.other", descriptor(scope=other_scope), scope=other_scope)
    with pytest.raises(ValueError, match="out-of-scope"):
        run_preview(producer, MemoryStore(raw_result=(other_record,)))

    inactive = replace(record("record.inactive", current), status="INVALIDATED")
    with pytest.raises(ValueError, match="out-of-scope"):
        run_preview(producer, MemoryStore(raw_result=(inactive,)))


def test_stale_memory_remains_evidence_and_is_targeted_for_revalidation() -> None:
    current = descriptor()
    stale = descriptor(valid_until="2026-10-14T07:59:59Z")
    producer = SnapshotProducer(CapabilityInventoryReadResult("READ", (current,)))
    memory = MemoryStore((record("record.stale", stale),))

    preview = run_preview(producer, memory)

    assert preview.discovery_plan.revalidate_identities == (stale.identity,)
    assert preview.discovery_plan.target_resource_ids == ("plugin.one",)
    assert preview.discovery_plan.relevant_observations == (stale,)
    assert preview.coverage is not None
    assert preview.coverage.items[0].status is CapabilityCoverageStatus.DECLARED


def test_different_sources_are_not_ranked_or_collapsed_into_conflict() -> None:
    source_a_support = descriptor(
        "tool.a",
        "source.a",
        (("ui.accessibility", "SUPPORTS"),),
        resource_kind=CapabilityResourceKind.REGISTERED_SPECIALIST,
    )
    source_b_negative = descriptor(
        "tool.b",
        "source.b",
        (("ui.accessibility", "DOES_NOT_SUPPORT"),),
    )
    different_sources = run_preview(
        SnapshotProducer(CapabilityInventoryReadResult("READ", (source_a_support, source_b_negative))),
        MemoryStore(),
    )

    assert different_sources.coverage is not None
    assert different_sources.coverage.items[0].status is CapabilityCoverageStatus.DECLARED
    assert {item.source_id for item in different_sources.coverage.items[0].evidence} == {
        "source.a",
        "source.b",
    }
    assert not hasattr(different_sources, "selected_provider")

    source_a_negative = descriptor(
        "tool.c",
        "source.a",
        (("ui.accessibility", "DOES_NOT_SUPPORT"),),
        resource_kind=CapabilityResourceKind.REGISTERED_SPECIALIST,
    )
    source_b_support = descriptor(
        "tool.d",
        "source.b",
        (("ui.accessibility", "SUPPORTS"),),
    )
    producer = SnapshotProducer(
        CapabilityInventoryReadResult("READ", (source_a_support, source_a_negative, source_b_support))
    )
    preview = run_preview(producer, MemoryStore())

    assert preview.coverage is not None
    assert preview.coverage.items[0].status is CapabilityCoverageStatus.CONFLICT
    assert {item.source_id for item in preview.coverage.items[0].evidence} == {"source.a", "source.b"}
    assert preview.discovery_plan.target_capability_ids == ("ui.accessibility",)
    assert not hasattr(preview, "selected_provider")


def test_preview_is_independent_of_inventory_and_memory_input_order() -> None:
    first = descriptor("tool.a", "source.a")
    second = descriptor("tool.b", "source.b", (("ui.accessibility", "UNKNOWN"),))
    memory_records = (record("record.a", first), record("record.b", second))

    forward = run_preview(
        SnapshotProducer(CapabilityInventoryReadResult("READ", (first, second))),
        MemoryStore(memory_records),
    )
    reverse = run_preview(
        SnapshotProducer(CapabilityInventoryReadResult("READ", (second, first))),
        MemoryStore(tuple(reversed(memory_records))),
    )

    assert forward == reverse


def test_invalid_or_duplicate_task_facet_inputs_fail_closed() -> None:
    producer = SnapshotProducer(CapabilityInventoryReadResult("UNKNOWN"))
    memory = MemoryStore()

    with pytest.raises(ValueError, match="must not be empty"):
        build_capability_planning_preview(
            trigger=CapabilityDiscoveryTrigger("CAPABILITY_GAP", ("ui.accessibility",)),
            task_facets=(),
            inventory_producer=producer,
            memory_store=memory,
            memory_scope=SCOPE,
            evaluated_at=NOW,
        )
    with pytest.raises(ValueError, match="unique facet_id"):
        build_capability_planning_preview(
            trigger=CapabilityDiscoveryTrigger("CAPABILITY_GAP", ("ui.accessibility",)),
            task_facets=(FACETS[0], FACETS[0]),
            inventory_producer=producer,
            memory_store=memory,
            memory_scope=SCOPE,
            evaluated_at=NOW,
        )
    with pytest.raises(TypeError, match="must contain TaskCapabilityFacet"):
        build_capability_planning_preview(
            trigger=None,
            task_facets="not-facets",  # type: ignore[arg-type]
            inventory_producer=producer,
            memory_store=memory,
            memory_scope=SCOPE,
            evaluated_at=NOW,
        )
    with pytest.raises(TypeError, match="must be iterable"):
        build_capability_planning_preview(
            trigger=None,
            task_facets=None,  # type: ignore[arg-type]
            inventory_producer=producer,
            memory_store=memory,
            memory_scope=SCOPE,
            evaluated_at=NOW,
        )
    with pytest.raises(TypeError, match="must contain TaskCapabilityFacet"):
        build_capability_planning_preview(
            trigger=None,
            task_facets=(object(),),  # type: ignore[arg-type]
            inventory_producer=producer,
            memory_store=memory,
            memory_scope=SCOPE,
            evaluated_at=NOW,
        )
    with pytest.raises(TypeError, match="trigger must be"):
        build_capability_planning_preview(
            trigger="not-trigger",  # type: ignore[arg-type]
            task_facets=FACETS,
            inventory_producer=producer,
            memory_store=memory,
            memory_scope=SCOPE,
            evaluated_at=NOW,
        )
    with pytest.raises(TypeError, match="memory_scope must be"):
        build_capability_planning_preview(
            trigger=None,
            task_facets=FACETS,
            inventory_producer=producer,
            memory_store=memory,
            memory_scope=object(),  # type: ignore[arg-type]
            evaluated_at=NOW,
        )
    with pytest.raises(TypeError, match="inventory_producer must implement"):
        build_capability_planning_preview(
            trigger=CapabilityDiscoveryTrigger("CAPABILITY_GAP", ("ui.accessibility",)),
            task_facets=FACETS,
            inventory_producer=object(),  # type: ignore[arg-type]
            memory_store=memory,
            memory_scope=SCOPE,
            evaluated_at=NOW,
        )
    with pytest.raises(TypeError, match="memory_store must implement"):
        build_capability_planning_preview(
            trigger=CapabilityDiscoveryTrigger("CAPABILITY_GAP", ("ui.accessibility",)),
            task_facets=FACETS,
            inventory_producer=producer,
            memory_store=object(),  # type: ignore[arg-type]
            memory_scope=SCOPE,
            evaluated_at=NOW,
        )
