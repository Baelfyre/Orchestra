# @codebase_provenance_JEO
# @codebase_rights_JEO

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
CAPABILITY = "ui.accessibility"
SCOPE = CapabilityMemoryScope("host.desktop", "user.one", "workspace.one")
FACETS = (TaskCapabilityFacet("task.output", (CAPABILITY,)),)
GAP_TRIGGER = CapabilityDiscoveryTrigger("CAPABILITY_GAP", (CAPABILITY,), ())


def descriptor(
    resource_id: str,
    source_id: str,
    claims: tuple[tuple[str, CapabilityClaim | str], ...] = (
        (CAPABILITY, CapabilityClaim.SUPPORTS),
    ),
    *,
    scope: CapabilityMemoryScope = SCOPE,
    valid_until: str = FUTURE,
    resource_kind: CapabilityResourceKind = CapabilityResourceKind.EXTERNAL_PLUGIN,
) -> CapabilityInventoryDescriptor:
    return CapabilityInventoryDescriptor(
        identity=CapabilityInventoryIdentity(
            resource_id,
            source_id,
            host_id=scope.host_id,
            user_scope_id=scope.user_scope_id,
            workspace_scope_id=scope.workspace_scope_id,
            permission_scope_id="permissions.read.v1",
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
        observed_at="2026-10-14T07:00:00Z",
        valid_until=valid_until,
    )


def record(
    record_id: str,
    observation: CapabilityInventoryDescriptor,
    scope: CapabilityMemoryScope = SCOPE,
) -> CapabilityMemoryRecord:
    return CapabilityMemoryRecord(record_id, scope, "CAPABILITY_OBSERVATION", observation, NOW)


class SyntheticInventoryProducer:
    def __init__(
        self,
        descriptors: tuple[CapabilityInventoryDescriptor, ...],
        events: list[object],
    ) -> None:
        self.result = CapabilityInventoryReadResult(
            CapabilityInventoryReadStatus.READ,
            descriptors,
        )
        self.events = events

    def read_cached_snapshot(self) -> CapabilityInventoryReadResult:
        self.events.append("inventory.read_cached_snapshot")
        return self.result


class SyntheticMemoryStore:
    def __init__(
        self,
        records: tuple[CapabilityMemoryRecord, ...],
        events: list[object],
    ) -> None:
        self.records = records
        self.events = events
        self.loaded_scopes: list[CapabilityMemoryScope] = []

    def load(self, scope: CapabilityMemoryScope, *, include_inactive: bool = False):
        self.events.append(("memory.load", scope))
        self.loaded_scopes.append(scope)
        return tuple(item for item in self.records if item.scope == scope)

    def save(self, record: CapabilityMemoryRecord) -> None:
        raise AssertionError("preview must not write memory")

    def invalidate(self, scope: CapabilityMemoryScope, record_id: str) -> bool:
        raise AssertionError("preview must not mutate memory")

    def supersede(
        self,
        scope: CapabilityMemoryScope,
        record_id: str,
        replacement: CapabilityMemoryRecord,
    ) -> None:
        raise AssertionError("preview must not mutate memory")

    def delete_record(self, scope: CapabilityMemoryScope, record_id: str) -> bool:
        raise AssertionError("preview must not delete memory")

    def delete_scope(self, scope: CapabilityMemoryScope) -> int:
        raise AssertionError("preview must not delete memory")


def run_preview(
    descriptors: tuple[CapabilityInventoryDescriptor, ...],
    records: tuple[CapabilityMemoryRecord, ...],
    *,
    scope: CapabilityMemoryScope | None = SCOPE,
    trigger: CapabilityDiscoveryTrigger | None = GAP_TRIGGER,
):
    events: list[object] = []
    producer = SyntheticInventoryProducer(descriptors, events)
    memory = SyntheticMemoryStore(records, events)
    preview = build_capability_planning_preview(
        trigger=trigger,
        task_facets=FACETS,
        inventory_producer=producer,
        memory_store=memory,
        memory_scope=scope,
        evaluated_at=NOW,
    )
    return preview, events, memory


def test_synthetic_e2e_reuses_scoped_cache_before_targeting_and_stays_non_authorizing() -> None:
    observed = descriptor("plugin.one", "source.one")
    preview, events, memory = run_preview(
        (observed,),
        (record("record.one", observed),),
    )

    assert events == ["inventory.read_cached_snapshot", ("memory.load", SCOPE)]
    assert memory.loaded_scopes == [SCOPE]
    assert preview.memory_read_attempted
    assert preview.current_observations == (observed,)
    assert preview.discovery_plan.disposition is CapabilityDiscoveryDisposition.CACHE_REUSE_HINT
    assert preview.discovery_plan.reuse_hint_identities == (observed.identity,)
    assert preview.discovery_plan.target_capability_ids == ()
    assert preview.coverage is not None
    item = preview.coverage.items[0]
    assert item.status is CapabilityCoverageStatus.DECLARED
    assert item.evidence[0].evidence_ref == observed.capability_claims[0].evidence_refs[0]
    assert item.evidence[0].evidence_level.value == "DECLARED"
    assert item.evidence[0].source_id == "source.one"
    assert not hasattr(preview, "selected_provider")
    assert not hasattr(preview, "may_authorize")


def test_synthetic_e2e_negative_only_and_stale_cache_remain_open_for_discovery() -> None:
    current = descriptor("plugin.one", "source.one", claims=())
    negative = descriptor(
        "plugin.one",
        "source.one",
        ((CAPABILITY, CapabilityClaim.DOES_NOT_SUPPORT),),
    )
    negative_preview, _, _ = run_preview((current,), (record("record.negative", negative),))

    assert negative_preview.discovery_plan.target_capability_ids == (CAPABILITY,)
    assert negative_preview.discovery_plan.reuse_hint_identities == (negative.identity,)
    assert negative_preview.coverage is not None
    assert negative_preview.coverage.items[0].status is CapabilityCoverageStatus.MISSING
    assert negative_preview.coverage.items[0].evidence[0].claim is CapabilityClaim.DOES_NOT_SUPPORT

    stale = descriptor("plugin.one", "source.one", valid_until="2026-10-14T07:59:59Z")
    stale_preview, _, _ = run_preview((current,), (record("record.stale", stale),))

    assert stale_preview.discovery_plan.revalidate_identities == (stale.identity,)
    assert stale_preview.discovery_plan.target_resource_ids == ("plugin.one",)
    assert stale_preview.discovery_plan.relevant_observations == (stale,)
    assert stale_preview.coverage is not None
    assert stale_preview.coverage.items[0].status is CapabilityCoverageStatus.STALE
    assert stale_preview.coverage.items[0].evidence[0].evidence_ref == stale.capability_claims[0].evidence_refs[0]


def test_synthetic_e2e_preserves_cross_source_differences_and_within_source_conflicts() -> None:
    support = descriptor(
        "tool.supports",
        "source.alpha",
        resource_kind=CapabilityResourceKind.REGISTERED_SPECIALIST,
    )
    negative = descriptor(
        "plugin.negative",
        "source.beta",
        ((CAPABILITY, CapabilityClaim.DOES_NOT_SUPPORT),),
    )
    mixed = run_preview(
        (support, negative),
        (record("record.supports", support), record("record.negative", negative)),
    )[0]

    assert mixed.discovery_plan.target_capability_ids == ()
    assert mixed.coverage is not None
    assert mixed.coverage.items[0].status is CapabilityCoverageStatus.DECLARED
    assert {item.source_id for item in mixed.coverage.items[0].evidence} == {
        "source.alpha",
        "source.beta",
    }

    same_source_support = descriptor("tool.one", "source.shared")
    same_source_negative = descriptor(
        "tool.two",
        "source.shared",
        ((CAPABILITY, CapabilityClaim.DOES_NOT_SUPPORT),),
    )
    other_source_support = descriptor("tool.other", "source.other")
    conflicted = run_preview(
        (same_source_support, same_source_negative, other_source_support),
        (
            record("record.shared.supports", same_source_support),
            record("record.shared.negative", same_source_negative),
            record("record.other.supports", other_source_support),
        ),
    )[0]

    assert conflicted.discovery_plan.target_capability_ids == (CAPABILITY,)
    assert conflicted.coverage is not None
    assert conflicted.coverage.items[0].status is CapabilityCoverageStatus.CONFLICT
    assert {item.evidence_ref for item in conflicted.coverage.items[0].evidence} == {
        same_source_support.capability_claims[0].evidence_refs[0],
        same_source_negative.capability_claims[0].evidence_refs[0],
        other_source_support.capability_claims[0].evidence_refs[0],
    }


def test_synthetic_e2e_memory_is_partitioned_by_active_user_and_order_is_deterministic() -> None:
    other_scope = CapabilityMemoryScope("host.desktop", "user.two", "workspace.two")
    active_one = descriptor("plugin.one", "source.one")
    active_two = descriptor("tool.two", "source.two", scope=SCOPE)
    other_user = descriptor("plugin.one", "source.other", scope=other_scope)
    records = (
        record("record.one", active_one),
        record("record.two", active_two),
        record("record.other", other_user, other_scope),
    )

    forward = run_preview((active_one, active_two), records)
    reverse = run_preview((active_two, active_one), tuple(reversed(records)))

    assert forward[0] == reverse[0]
    assert forward[2].loaded_scopes == [SCOPE]
    assert forward[0].coverage is not None
    assert all(item.source_id != "source.other" for item in forward[0].coverage.items[0].evidence)


def test_unavailable_host_producer_keeps_state_unknown_and_skips_memory() -> None:
    class NoReadMemoryStore(SyntheticMemoryStore):
        def load(self, scope: CapabilityMemoryScope, *, include_inactive: bool = False):
            raise AssertionError("unknown inventory must not trigger a memory read")

    events: list[object] = []
    memory = NoReadMemoryStore((), events)
    preview = build_capability_planning_preview(
        trigger=GAP_TRIGGER,
        task_facets=FACETS,
        inventory_producer=UnavailableCapabilityInventoryProducer(),
        memory_store=memory,
        memory_scope=SCOPE,
        evaluated_at=NOW,
    )

    assert preview.inventory_status is CapabilityInventoryReadStatus.UNKNOWN
    assert not preview.memory_read_attempted
    assert preview.coverage is None
    assert preview.discovery_plan.target_capability_ids == (CAPABILITY,)
    assert memory.loaded_scopes == []
    assert events == []


def test_explicit_user_tool_selection_is_preserved_end_to_end() -> None:
    selected = descriptor("tool.selected", "source.selected")
    trigger = CapabilityDiscoveryTrigger("USER_REQUEST", (), ("tool.selected",))
    preview, _, _ = run_preview((selected,), (), trigger=trigger)

    assert preview.discovery_plan.requested_resource_ids == ("tool.selected",)
    assert preview.current_observations == (selected,)
    assert preview.coverage is not None
    assert preview.coverage.items[0].status is CapabilityCoverageStatus.DECLARED


def test_absent_trigger_does_not_start_the_synthetic_flow() -> None:
    observed = descriptor("plugin.one", "source.one")
    preview, events, memory = run_preview(
        (observed,),
        (record("record.one", observed),),
        trigger=None,
    )

    assert events == []
    assert memory.loaded_scopes == []
    assert preview.inventory_status is None
    assert preview.coverage is None
    assert preview.discovery_plan.disposition is CapabilityDiscoveryDisposition.NO_DISCOVERY
