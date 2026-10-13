# @codebase_provenance_JEO
# @codebase_rights_JEO

from __future__ import annotations

from dataclasses import replace

import pytest

from orchestra_runtime.domain.adaptive import (
    CAPABILITY_INVENTORY_SCHEMA_VERSION,
    CapabilityClaim,
    CapabilityCoverageStatus,
    CapabilityDiscoveryDisposition,
    CapabilityDiscoveryTrigger,
    CapabilityDiscoveryTriggerKind,
    CapabilityDeclaration,
    CapabilityInventoryClaim,
    CapabilityInventoryDescriptor,
    CapabilityInventoryIdentity,
    CapabilityResourceKind,
    CapabilitySideEffectKind,
    InventoryCompatibilityStatus,
    InventoryFreshness,
    InventoryObservationStatus,
    OperationPermissionObservation,
    OperationPermissionStatus,
    SideEffectObservation,
    SideEffectObservationStatus,
    TaskCapabilityFacet,
    evaluate_capability_coverage,
    plan_capability_discovery,
)


AS_OF = "2026-10-14T08:00:00Z"
FRESH_UNTIL = "2026-10-15T08:00:00Z"


def identity(
    resource_id: str = "impeccable",
    *,
    source_id: str = "vendor.impeccable",
    host_id: str | None = "vscode",
    user_scope_id: str | None = "user-a",
    workspace_scope_id: str | None = "workspace-a",
    distribution_id: str | None = "vendor.impeccable",
    distribution_version: str | None = "1.2.3",
    permission_scope_id: str | None = "read-only-v1",
    source_revision: str | None = "release-1.2.3",
    distribution_digest: str | None = None,
    recheck_token: str | None = None,
    identity_refs: tuple[str, ...] = (),
) -> CapabilityInventoryIdentity:
    return CapabilityInventoryIdentity(
        resource_id,
        source_id,
        host_id=host_id,
        user_scope_id=user_scope_id,
        workspace_scope_id=workspace_scope_id,
        distribution_id=distribution_id,
        distribution_version=distribution_version,
        permission_scope_id=permission_scope_id,
        source_revision=source_revision,
        distribution_digest=distribution_digest,
        recheck_token=recheck_token,
        identity_evidence_refs=identity_refs,
    )


def claim(
    capability_id: str = "ui.accessibility",
    value: CapabilityClaim | str = CapabilityClaim.SUPPORTS,
    ref: str = "publisher:accessibility",
) -> CapabilityInventoryClaim:
    return CapabilityInventoryClaim(capability_id, value, (ref,))


def observation(
    source: CapabilityInventoryIdentity | None = None,
    *,
    resource_kind: CapabilityResourceKind | str = CapabilityResourceKind.EXTERNAL_PLUGIN,
    status: InventoryObservationStatus | str = InventoryObservationStatus.PRESENT,
    compatibility: InventoryCompatibilityStatus | str = InventoryCompatibilityStatus.COMPATIBLE,
    claims: tuple[CapabilityInventoryClaim, ...] | None = None,
    permissions: tuple[OperationPermissionObservation, ...] = (),
    side_effects: tuple[SideEffectObservation, ...] = (),
    observation_refs: tuple[str, ...] = ("host:inventory-observation",),
    compatibility_refs: tuple[str, ...] = ("host:compatibility-observation",),
    output_refs: tuple[str, ...] = ("test:output",),
    review_refs: tuple[str, ...] = ("review:capability-record",),
    observed_at: str | None = "2026-10-14T07:00:00Z",
    valid_until: str | None = FRESH_UNTIL,
) -> CapabilityInventoryDescriptor:
    return CapabilityInventoryDescriptor(
        identity=source or identity(),
        resource_kind=resource_kind,
        observation=status,
        compatibility=compatibility,
        capability_claims=claims if claims is not None else (claim(),),
        permissions=permissions,
        side_effects=side_effects,
        observation_evidence_refs=observation_refs,
        compatibility_evidence_refs=compatibility_refs,
        independent_output_refs=output_refs,
        review_refs=review_refs,
        observed_at=observed_at,
        valid_until=valid_until,
    )


def trigger(
    kind: CapabilityDiscoveryTriggerKind | str = CapabilityDiscoveryTriggerKind.USER_REQUEST,
    *,
    capabilities: tuple[str, ...] = (),
    resources: tuple[str, ...] = ("impeccable",),
) -> CapabilityDiscoveryTrigger:
    return CapabilityDiscoveryTrigger(kind, capabilities, resources)


def plan(
    requested: CapabilityDiscoveryTrigger | None,
    entries: tuple[CapabilityInventoryDescriptor, ...] = (),
    current: tuple[CapabilityInventoryIdentity, ...] = (),
):
    return plan_capability_discovery(requested, entries, current, evaluated_at=AS_OF)


def test_descriptor_keeps_claims_observations_permissions_and_outputs_separate() -> None:
    entry = observation(
        resource_kind="HOST_NATIVE_TOOL",
        permissions=(OperationPermissionObservation("file.read", "ALLOWED", ("host:permission",)),),
        side_effects=(SideEffectObservation("NETWORK", "DECLARED", ("publisher:network",)),),
    )

    assert entry.schema_version == CAPABILITY_INVENTORY_SCHEMA_VERSION
    assert entry.resource_kind is CapabilityResourceKind.HOST_NATIVE_TOOL
    assert entry.capability_claims[0].claim is CapabilityClaim.SUPPORTS
    assert entry.observation is InventoryObservationStatus.PRESENT
    assert entry.compatibility is InventoryCompatibilityStatus.COMPATIBLE
    assert entry.permissions[0].status is OperationPermissionStatus.ALLOWED
    assert entry.side_effects[0].kind is CapabilitySideEffectKind.NETWORK
    assert entry.side_effects[0].status is SideEffectObservationStatus.DECLARED
    assert entry.independent_output_refs == ("test:output",)
    assert not hasattr(entry, "trusted")
    assert not hasattr(entry, "authorized")


def test_no_trigger_never_scans_or_uses_unrelated_cached_observations() -> None:
    cached = observation(identity("unrelated-tool"))

    result = plan(None, (cached,), (identity("unrelated-tool"),))

    assert result.disposition is CapabilityDiscoveryDisposition.NO_DISCOVERY
    assert result.target_resource_ids == ()
    assert result.target_capability_ids == ()
    assert result.relevant_observations == ()


def test_explicit_user_selection_is_preserved_and_fresh_cache_only_yields_a_hint() -> None:
    selected = identity("impeccable")
    cached = observation(selected)

    result = plan(trigger(resources=("Impeccable",)), (cached,), (selected,))

    assert result.disposition is CapabilityDiscoveryDisposition.CACHE_REUSE_HINT
    assert result.requested_resource_ids == ("impeccable",)
    assert result.reuse_hint_identities == (selected,)
    assert result.target_resource_ids == ()
    assert result.relevant_observations == (cached,)
    assert not hasattr(result, "selected_provider")
    assert not hasattr(result, "provider_invocation_authorized")


def test_explicit_user_selection_does_not_substitute_another_cached_resource() -> None:
    requested = trigger(resources=("impeccable",))
    other = identity("cloak", source_id="orchestra.cloak", distribution_id=None)

    result = plan(requested, (observation(other),), (other,))

    assert result.disposition is CapabilityDiscoveryDisposition.TARGETED_DISCOVERY
    assert result.requested_resource_ids == ("impeccable",)
    assert result.target_resource_ids == ("impeccable",)
    assert result.relevant_observations == ()


def test_gap_lookup_is_narrow_and_preserves_different_provider_claims() -> None:
    internal = observation(
        identity("cloak", source_id="orchestra.cloak", distribution_id=None),
        resource_kind="REGISTERED_SPECIALIST",
        claims=(claim(value="SUPPORTS", ref="registry:cloak"),),
    )
    external = observation(
        identity("impeccable"),
        claims=(claim(value="DOES_NOT_SUPPORT", ref="publisher:limit"),),
    )
    unrelated = observation(
        identity("research-tool", source_id="vendor.research", distribution_id="vendor.research"),
        claims=(claim("source.review", ref="publisher:source-review"),),
    )
    coverage = evaluate_capability_coverage(
        (TaskCapabilityFacet("ui", ("ui.accessibility",)),),
        (
            CapabilityDeclaration(
                "ui",
                "ui.accessibility",
                "INTERNAL",
                "orchestra.cloak",
                "SUPPORTS",
                ("registry:cloak",),
                FRESH_UNTIL,
            ),
            CapabilityDeclaration(
                "ui",
                "ui.accessibility",
                "EXTERNAL",
                "vendor.impeccable",
                "DOES_NOT_SUPPORT",
                ("publisher:limit",),
                FRESH_UNTIL,
            ),
        ),
        evaluated_at=AS_OF,
    )

    result = plan(
        trigger("CAPABILITY_GAP", capabilities=("ui.accessibility",), resources=()),
        (unrelated, external, internal),
        (identity("cloak", source_id="orchestra.cloak", distribution_id=None), identity()),
    )

    assert result.disposition is CapabilityDiscoveryDisposition.CACHE_REUSE_HINT
    assert result.target_capability_ids == ()
    assert result.requested_resource_ids == ()
    assert {entry.identity.resource_id for entry in result.relevant_observations} == {"cloak", "impeccable"}
    assert {identity.resource_id for identity in result.reuse_hint_identities} == {"cloak", "impeccable"}
    assert [entry.capability_claims[0].claim for entry in result.relevant_observations] == [
        CapabilityClaim.SUPPORTS,
        CapabilityClaim.DOES_NOT_SUPPORT,
    ]
    assert coverage.items[0].status is CapabilityCoverageStatus.DECLARED


def test_capability_trigger_reuses_current_claim_without_qualifying_it() -> None:
    current = identity()
    cached = observation(current)

    result = plan(
        trigger("CAPABILITY_GAP", capabilities=("ui.accessibility",), resources=()),
        (cached,),
        (current,),
    )
    coverage = evaluate_capability_coverage(
        (TaskCapabilityFacet("ui", ("ui.accessibility",)),),
        (
            CapabilityDeclaration(
                "ui",
                "ui.accessibility",
                "EXTERNAL",
                current.source_id,
                "SUPPORTS",
                ("publisher:accessibility",),
                FRESH_UNTIL,
            ),
        ),
        evaluated_at=AS_OF,
    )

    assert result.disposition is CapabilityDiscoveryDisposition.CACHE_REUSE_HINT
    assert result.target_capability_ids == ()
    assert result.relevant_observations == (cached,)
    assert result.reuse_hint_identities == (current,)
    assert coverage.items[0].status is CapabilityCoverageStatus.DECLARED


def test_capability_trigger_targets_only_capabilities_without_reusable_knowledge() -> None:
    current = identity()
    cached = observation(current)

    result = plan(
        trigger(
            "CAPABILITY_GAP",
            capabilities=("ui.accessibility", "ui.data_visualization"),
            resources=(),
        ),
        (cached,),
        (current,),
    )

    assert result.disposition is CapabilityDiscoveryDisposition.TARGETED_DISCOVERY
    assert result.reuse_hint_identities == (current,)
    assert result.target_capability_ids == ("ui.data_visualization",)


def test_negative_only_capability_claim_is_reusable_but_stays_targeted() -> None:
    current = identity()
    negative = observation(
        current,
        claims=(claim(value="DOES_NOT_SUPPORT", ref="publisher:limitation"),),
    )

    result = plan(
        trigger("CAPABILITY_GAP", capabilities=("ui.accessibility",), resources=()),
        (negative,),
        (current,),
    )

    assert result.disposition is CapabilityDiscoveryDisposition.TARGETED_DISCOVERY
    assert result.target_capability_ids == ("ui.accessibility",)
    assert result.reuse_hint_identities == (current,)
    assert result.relevant_observations == (negative,)


def test_cached_observations_from_another_workspace_are_not_disclosed_or_reused() -> None:
    active = identity("shared-tool", host_id="host-a", source_id="vendor.shared")
    other_workspace = identity(
        "shared-tool",
        host_id="host-a",
        source_id="vendor.shared",
        user_scope_id="user-b",
        workspace_scope_id="workspace-b",
    )
    cached = observation(other_workspace)

    result = plan(trigger(resources=("shared-tool",)), (cached,), (active,))

    assert result.relevant_observations == ()
    assert result.reuse_hint_identities == ()
    assert result.revalidate_identities == ()
    assert result.target_resource_ids == ("shared-tool",)


def test_cache_without_complete_active_scope_and_permission_is_not_disclosed() -> None:
    unscoped = identity(
        "impeccable",
        user_scope_id=None,
        workspace_scope_id=None,
        permission_scope_id=None,
    )
    cached = observation(unscoped)

    result = plan(trigger(resources=("impeccable",)), (cached,), (unscoped,))

    assert result.relevant_observations == ()
    assert result.reuse_hint_identities == ()
    assert result.revalidate_identities == ()
    assert result.target_resource_ids == ("impeccable",)


def test_same_resource_name_preserves_distinct_scoped_reuse_entries() -> None:
    host_a = identity(
        "shared-tool",
        source_id="vendor.host-a",
        host_id="host-a",
        distribution_id="vendor.host-a",
    )
    host_b = identity(
        "shared-tool",
        source_id="vendor.host-b",
        host_id="host-b",
        distribution_id="vendor.host-b",
    )

    result = plan(
        trigger(resources=("shared-tool",)),
        (observation(host_b), observation(host_a)),
        (host_a, host_b),
    )

    assert result.relevant_observations == (observation(host_a), observation(host_b))
    assert result.reuse_hint_identities == (host_a, host_b)


def test_same_resource_name_keeps_reuse_and_revalidation_identities_separate() -> None:
    host_a = identity("shared-tool", source_id="vendor.host-a", host_id="host-a")
    host_b = identity("shared-tool", source_id="vendor.host-b", host_id="host-b")
    cached = (
        observation(host_a, valid_until="2026-10-14T07:30:00Z"),
        observation(host_b),
    )
    current = (host_a, host_b)
    requested = trigger("CAPABILITY_GAP", capabilities=("ui.accessibility",), resources=())

    result = plan(requested, cached, current)
    reverse = plan(requested, tuple(reversed(cached)), tuple(reversed(current)))

    assert result == reverse
    assert result.reuse_hint_identities == (host_b,)
    assert result.revalidate_identities == (host_a,)
    assert result.target_resource_ids == ("shared-tool",)
    assert result.target_capability_ids == ()


@pytest.mark.parametrize("missing_scope", ("host_id", "user_scope_id", "workspace_scope_id", "permission_scope_id"))
def test_incomplete_active_identity_cannot_reuse_a_scoped_cache(missing_scope: str) -> None:
    current = replace(identity(), **{missing_scope: None})
    cached_identity = identity()
    cached = observation(cached_identity)

    result = plan(trigger(resources=("impeccable",)), (cached,), (current,))

    assert result.relevant_observations == ()
    assert result.reuse_hint_identities == ()
    assert result.revalidate_identities == ()
    assert result.target_resource_ids == ("impeccable",)


def test_multiple_active_user_workspace_scopes_fail_closed() -> None:
    active_a = identity("tool-a")
    active_b = identity("tool-b", user_scope_id="user-b", workspace_scope_id="workspace-b")

    with pytest.raises(ValueError, match="one active user/workspace scope"):
        plan(trigger(resources=("tool-a",)), (), (active_a, active_b))


def test_unknown_or_contradictory_capability_claims_remain_targeted() -> None:
    current = identity()
    unknown = observation(current, claims=(claim(value="UNKNOWN"),))
    contradictory = observation(
        current,
        claims=(
            claim(value="SUPPORTS", ref="publisher:positive"),
            claim(value="DOES_NOT_SUPPORT", ref="publisher:negative"),
        ),
    )

    unknown_result = plan(
        trigger("CAPABILITY_GAP", capabilities=("ui.accessibility",), resources=()),
        (unknown,),
        (current,),
    )
    contradictory_result = plan(
        trigger("CAPABILITY_GAP", capabilities=("ui.accessibility",), resources=()),
        (contradictory,),
        (current,),
    )

    assert unknown_result.target_capability_ids == ("ui.accessibility",)
    assert unknown_result.disposition is CapabilityDiscoveryDisposition.TARGETED_DISCOVERY
    assert unknown_result.reuse_hint_identities == (current,)
    assert unknown_result.relevant_observations == (unknown,)
    assert contradictory_result.target_capability_ids == ("ui.accessibility",)
    assert contradictory_result.disposition is CapabilityDiscoveryDisposition.TARGETED_DISCOVERY
    assert contradictory_result.reuse_hint_identities == (current,)
    assert contradictory_result.relevant_observations == (contradictory,)


def test_same_source_conflict_stays_targeted_despite_other_source_support() -> None:
    source_support_identity = identity(
        "impeccable-support",
        source_id="vendor.impeccable",
        host_id="host-support",
    )
    source_negative_identity = identity(
        "impeccable-limit",
        source_id="vendor.impeccable",
        host_id="host-limit",
    )
    other_support_identity = identity(
        "cloak",
        source_id="orchestra.cloak",
        host_id="host-cloak",
        distribution_id=None,
    )
    source_support = observation(
        source_support_identity,
        claims=(claim(value="SUPPORTS", ref="publisher:positive"),),
    )
    source_negative = observation(
        source_negative_identity,
        claims=(claim(value="DOES_NOT_SUPPORT", ref="publisher:negative"),),
    )
    other_support = observation(
        other_support_identity,
        resource_kind="REGISTERED_SPECIALIST",
        claims=(claim(value="SUPPORTS", ref="registry:cloak"),),
    )
    requested = trigger("CAPABILITY_GAP", capabilities=("ui.accessibility",), resources=())
    entries = (source_support, source_negative, other_support)
    identities = (source_support_identity, source_negative_identity, other_support_identity)

    result = plan(requested, entries, identities)
    reverse_result = plan(requested, tuple(reversed(entries)), tuple(reversed(identities)))
    coverage = evaluate_capability_coverage(
        (TaskCapabilityFacet("ui", ("ui.accessibility",)),),
        (
            CapabilityDeclaration(
                "ui", "ui.accessibility", "EXTERNAL", "vendor.impeccable", "SUPPORTS",
                ("publisher:positive",), FRESH_UNTIL,
            ),
            CapabilityDeclaration(
                "ui", "ui.accessibility", "EXTERNAL", "vendor.impeccable", "DOES_NOT_SUPPORT",
                ("publisher:negative",), FRESH_UNTIL,
            ),
            CapabilityDeclaration(
                "ui", "ui.accessibility", "INTERNAL", "orchestra.cloak", "SUPPORTS",
                ("registry:cloak",), FRESH_UNTIL,
            ),
        ),
        evaluated_at=AS_OF,
    )

    assert result == reverse_result
    assert result.disposition is CapabilityDiscoveryDisposition.TARGETED_DISCOVERY
    assert result.target_capability_ids == ("ui.accessibility",)
    assert set(result.reuse_hint_identities) == set(identities)
    assert {entry.identity.source_id for entry in result.relevant_observations} == {
        "vendor.impeccable",
        "orchestra.cloak",
    }
    assert coverage.items[0].status is CapabilityCoverageStatus.CONFLICT


@pytest.mark.parametrize(
    ("status", "compatibility", "review_refs", "valid_until"),
    [
        ("UNKNOWN", "COMPATIBLE", ("review:1",), FRESH_UNTIL),
        ("UNSUPPORTED", "COMPATIBLE", ("review:1",), FRESH_UNTIL),
        ("PRESENT", "UNKNOWN", ("review:1",), FRESH_UNTIL),
        ("PRESENT", "UNSUPPORTED", ("review:1",), FRESH_UNTIL),
        ("PRESENT", "INCOMPATIBLE", ("review:1",), FRESH_UNTIL),
        ("PRESENT", "COMPATIBLE", (), FRESH_UNTIL),
        ("PRESENT", "COMPATIBLE", ("review:1",), "2026-10-14T07:30:00Z"),
        ("PRESENT", "COMPATIBLE", ("review:1",), None),
    ],
)
def test_unknown_stale_incompatible_or_unreviewed_observation_is_revalidated(
    status: str,
    compatibility: str,
    review_refs: tuple[str, ...],
    valid_until: str | None,
) -> None:
    current = identity()
    cached = observation(
        current,
        status=status,
        compatibility=compatibility,
        review_refs=review_refs,
        valid_until=valid_until,
    )

    result = plan(trigger(resources=("impeccable",)), (cached,), (current,))

    assert result.disposition is CapabilityDiscoveryDisposition.TARGETED_DISCOVERY
    assert result.revalidate_identities == (current,)
    assert result.target_resource_ids == ("impeccable",)
    assert result.reuse_hint_identities == ()


@pytest.mark.parametrize("changes", [{"distribution_version": "1.2.4"}, {"source_revision": "release-1.2.4"}])
def test_changed_version_or_revision_revalidates_only_the_affected_observation(changes: dict[str, str]) -> None:
    affected_cached = identity("impeccable")
    affected_current = replace(affected_cached, **changes)
    unaffected = identity("cloak", source_id="orchestra.cloak", distribution_id=None)
    unrelated = identity("research-tool", source_id="vendor.research", distribution_id="vendor.research")

    result = plan(
        trigger("CAPABILITY_GAP", capabilities=("ui.accessibility",), resources=()),
        (observation(affected_cached), observation(unaffected), observation(unrelated, claims=(claim("source.review"),))),
        (affected_current, unaffected, unrelated),
    )

    assert result.revalidate_identities == (affected_cached,)
    assert result.reuse_hint_identities == (unaffected,)
    assert result.target_resource_ids == ("impeccable",)
    assert {entry.identity.resource_id for entry in result.relevant_observations} == {"cloak", "impeccable"}


@pytest.mark.parametrize(
    "changes",
    [
        {"permission_scope_id": "read-write-v1"},
        {"workspace_scope_id": "workspace-b"},
        {"user_scope_id": "user-b"},
    ],
)
def test_changed_permission_or_privacy_scope_hides_old_observation(changes: dict[str, str]) -> None:
    affected_cached = identity("impeccable")
    affected_current = replace(affected_cached, **changes)

    result = plan(
        trigger("CAPABILITY_GAP", capabilities=("ui.accessibility",), resources=()),
        (observation(affected_cached),),
        (affected_current,),
    )

    assert result.relevant_observations == ()
    assert result.reuse_hint_identities == ()
    assert result.revalidate_identities == ()
    assert result.target_capability_ids == ("ui.accessibility",)


def test_missing_host_interface_remains_unknown_and_never_becomes_absent() -> None:
    current = identity(host_id=None, user_scope_id=None, workspace_scope_id=None)
    cached = observation(
        current,
        status="UNSUPPORTED",
        compatibility="UNSUPPORTED",
        observation_refs=(),
        compatibility_refs=(),
        review_refs=(),
        observed_at=None,
        valid_until=None,
    )

    result = plan(trigger(resources=("impeccable",)), (cached,), ())

    assert cached.observation is InventoryObservationStatus.UNSUPPORTED
    assert cached.compatibility is InventoryCompatibilityStatus.UNSUPPORTED
    assert result.relevant_observations == ()
    assert result.revalidate_identities == ()
    assert result.target_resource_ids == ("impeccable",)
    assert cached.observation is not InventoryObservationStatus.ABSENT


def test_future_observation_timestamp_is_unknown_not_current() -> None:
    current = identity()
    cached = observation(current, observed_at="2026-10-15T08:00:00Z", valid_until="2026-10-16T08:00:00Z")

    result = plan(trigger(resources=("impeccable",)), (cached,), (current,))

    assert result.revalidate_identities == (current,)
    assert result.reuse_hint_identities == ()


@pytest.mark.parametrize(
    "kind",
    [
        CapabilityDiscoveryTriggerKind.QUALITY_ISSUE,
        CapabilityDiscoveryTriggerKind.TOOL_FAILURE,
        CapabilityDiscoveryTriggerKind.STALE_OBSERVATION,
        CapabilityDiscoveryTriggerKind.ENVIRONMENT_CHANGE,
    ],
)
def test_material_failure_or_change_forces_targeted_revalidation(kind: CapabilityDiscoveryTriggerKind) -> None:
    current = identity()

    result = plan(trigger(kind, resources=("impeccable",)), (observation(current),), (current,))

    assert result.disposition is CapabilityDiscoveryDisposition.TARGETED_DISCOVERY
    assert result.target_resource_ids == ("impeccable",)
    assert result.revalidate_identities == (current,)
    assert result.reuse_hint_identities == ()


def test_provider_claim_differences_are_preserved_without_aggregation_or_ranking() -> None:
    first = observation(
        identity("cloak", source_id="orchestra.cloak", distribution_id=None),
        claims=(claim(value="SUPPORTS", ref="review:cloak-support"),),
    )
    second = observation(
        identity("impeccable"),
        claims=(claim(value="DOES_NOT_SUPPORT", ref="review:impeccable-limit"),),
    )

    result = plan(
        trigger("CAPABILITY_GAP", capabilities=("ui.accessibility",), resources=()),
        (second, first),
        (second.identity, first.identity),
    )

    assert [entry.identity.resource_id for entry in result.relevant_observations] == ["cloak", "impeccable"]
    assert [entry.capability_claims[0].claim for entry in result.relevant_observations] == [
        CapabilityClaim.SUPPORTS,
        CapabilityClaim.DOES_NOT_SUPPORT,
    ]
    assert not hasattr(result, "preferred_resource_id")
    assert not hasattr(result, "conflict_disposition")


def test_plan_is_invariant_to_observation_and_identity_input_order() -> None:
    cloak = observation(identity("cloak", source_id="orchestra.cloak", distribution_id=None))
    impeccable = observation(identity("impeccable"))
    requested = trigger("CAPABILITY_GAP", capabilities=("ui.accessibility",), resources=())

    forward = plan(requested, (cloak, impeccable), (cloak.identity, impeccable.identity))
    reverse = plan(requested, (impeccable, cloak), (impeccable.identity, cloak.identity))

    assert forward == reverse


def test_malformed_duplicate_and_ambiguous_inputs_fail_closed() -> None:
    with pytest.raises(ValueError, match="canonical identifier"):
        identity("../plugin")
    with pytest.raises(ValueError, match="resource_kind"):
        observation(resource_kind="PLUGIN")
    with pytest.raises(ValueError, match="schema_version"):
        replace(observation(), schema_version="orchestra.capability-inventory.v2")
    with pytest.raises(ValueError, match="unique references"):
        CapabilityInventoryClaim("ui.accessibility", "SUPPORTS", ("same", "same"))
    with pytest.raises(ValueError, match="known inventory observations"):
        observation(observation_refs=())
    with pytest.raises(ValueError, match="known compatibility observations"):
        observation(compatibility_refs=())
    with pytest.raises(ValueError, match="known permission observations"):
        OperationPermissionObservation("file.write", "ALLOWED")
    with pytest.raises(ValueError, match="known side-effect observations"):
        SideEffectObservation("NETWORK", "OBSERVED")
    with pytest.raises(ValueError, match="valid_until must be later"):
        observation(observed_at=AS_OF, valid_until=AS_OF)
    with pytest.raises(ValueError, match="capability_claims must not contain duplicates"):
        observation(claims=(claim(), claim()))
    duplicate = observation()
    with pytest.raises(ValueError, match="unique identities"):
        plan(trigger(), (duplicate, duplicate), (duplicate.identity,))
    with pytest.raises(ValueError, match="unique observation scopes"):
        plan(trigger(), (), (identity(), identity()))
    with pytest.raises(ValueError, match="identify relevant"):
        trigger(capabilities=(), resources=())
    with pytest.raises(ValueError, match="kind is unsupported"):
        trigger("PLUGIN_INSTALLED")
    with pytest.raises(TypeError, match="trigger must"):
        plan_capability_discovery("USER_REQUEST", evaluated_at=AS_OF)  # type: ignore[arg-type]


def test_invalid_containers_and_timestamps_are_rejected() -> None:
    with pytest.raises(TypeError, match="cached_observations must contain"):
        plan_capability_discovery(trigger(), "plugin", evaluated_at=AS_OF)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="current_identities must be iterable"):
        plan_capability_discovery(trigger(), (), 1, evaluated_at=AS_OF)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="evaluated_at"):
        plan_capability_discovery(trigger(), evaluated_at="not-a-timestamp")
    with pytest.raises(TypeError, match="observed_at must be a string"):
        observation(observed_at=123)  # type: ignore[arg-type]


def test_remaining_field_validation_branches_fail_closed() -> None:
    with pytest.raises(TypeError, match="resource_id must be a string"):
        identity(123)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="distribution_digest must be a string"):
        identity(distribution_digest=123)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="distribution_digest must be non-empty"):
        identity(distribution_digest=" ")
    with pytest.raises(ValueError, match="control characters"):
        identity(recheck_token="token\x00bad")
    with pytest.raises(ValueError, match="at most 512"):
        identity(distribution_digest="x" * 513)
    with pytest.raises(TypeError, match="resource_kind must be a string"):
        observation(resource_kind=1)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="capability_ids must be a list or tuple"):
        CapabilityDiscoveryTrigger("CAPABILITY_GAP", "ui.accessibility", ())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="capability_ids must contain unique"):
        CapabilityDiscoveryTrigger("CAPABILITY_GAP", ("ui.accessibility", "UI.ACCESSIBILITY"), ())
    with pytest.raises(TypeError, match="evidence_ref must be a list or tuple"):
        CapabilityInventoryClaim("ui.accessibility", "SUPPORTS", "ref:one")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="claim must be a string"):
        CapabilityInventoryClaim("ui.accessibility", 1, ("ref:one",))  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="identity must be CapabilityInventoryIdentity"):
        replace(observation(), identity=object())
    permission = OperationPermissionObservation("file.read", "UNKNOWN")
    with pytest.raises(ValueError, match="permissions must not contain duplicates"):
        observation(permissions=(permission, permission))
    side_effect = SideEffectObservation("NETWORK", "UNKNOWN")
    with pytest.raises(ValueError, match="side_effects must not contain duplicates"):
        observation(side_effects=(side_effect, side_effect))
    with pytest.raises(TypeError, match="limitations must be a list or tuple"):
        replace(observation(), limitations=object())
    with pytest.raises(ValueError, match="limitations must be unique"):
        replace(observation(), limitations=("network", "network"))
    no_host_scope = identity("impeccable", host_id=None, user_scope_id=None, workspace_scope_id=None)
    result = plan(trigger(), (), (no_host_scope,))
    assert result.target_resource_ids == ("impeccable",)


def test_identity_provenance_fields_are_normalized_and_preserved() -> None:
    supplied = identity(
        distribution_digest="sha256:abc123",
        recheck_token="host:recheck-7",
        identity_refs=("host:adapter-identity",),
    )

    assert supplied.distribution_digest == "sha256:abc123"
    assert supplied.recheck_token == "host:recheck-7"
    assert supplied.identity_evidence_refs == ("host:adapter-identity",)
