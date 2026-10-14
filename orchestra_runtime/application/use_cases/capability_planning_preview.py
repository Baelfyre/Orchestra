"""Read-only preview over supplied inventory and scoped capability memory."""

# @codebase_provenance_JEO
# @codebase_rights_JEO

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ...application.ports.capability_inventory_producer import (
    CapabilityInventoryProducer,
    CapabilityInventoryReadStatus,
)
from ...application.ports.capability_memory import CapabilityMemoryStore
from ...domain.adaptive.capability_coverage import (
    CapabilityCoverageResult,
    CapabilityDeclaration,
    CapabilitySourceKind,
    TaskCapabilityFacet,
    evaluate_capability_coverage,
)
from ...domain.adaptive.capability_inventory import (
    CapabilityDiscoveryPlan,
    CapabilityDiscoveryTrigger,
    CapabilityInventoryDescriptor,
    CapabilityResourceKind,
    plan_capability_discovery,
)
from ...domain.adaptive.capability_memory import (
    CapabilityMemoryRecord,
    CapabilityMemoryRecordStatus,
    CapabilityMemoryScope,
)


@dataclass(frozen=True, slots=True)
class CapabilityPlanningPreview:
    """Non-authorizing, in-process results for a single explicit preview request."""

    inventory_status: CapabilityInventoryReadStatus | None
    memory_read_attempted: bool
    current_observations: tuple[CapabilityInventoryDescriptor, ...]
    coverage: CapabilityCoverageResult | None
    discovery_plan: CapabilityDiscoveryPlan
    limitations: tuple[str, ...]


def _task_facets(values: Iterable[TaskCapabilityFacet]) -> tuple[TaskCapabilityFacet, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError("task_facets must contain TaskCapabilityFacet records")
    try:
        facets = tuple(values)
    except TypeError as exc:
        raise TypeError("task_facets must be iterable") from exc
    if not facets:
        raise ValueError("task_facets must not be empty")
    if any(not isinstance(facet, TaskCapabilityFacet) for facet in facets):
        raise TypeError("task_facets must contain TaskCapabilityFacet records")
    if len({facet.facet_id for facet in facets}) != len(facets):
        raise ValueError("task_facets must have unique facet_id values")
    return facets


def _scope_matches(
    descriptor: CapabilityInventoryDescriptor,
    scope: CapabilityMemoryScope,
) -> bool:
    identity = descriptor.identity
    return (
        identity.observation_scope is not None
        and (identity.host_id, identity.user_scope_id, identity.workspace_scope_id)
        == (scope.host_id, scope.user_scope_id, scope.workspace_scope_id)
    )


def _matches_trigger(
    descriptor: CapabilityInventoryDescriptor,
    trigger: CapabilityDiscoveryTrigger,
) -> bool:
    return descriptor.identity.resource_id in trigger.resource_ids or any(
        claim.capability_id in trigger.capability_ids
        for claim in descriptor.capability_claims
    )


def _source_kind(resource_kind: CapabilityResourceKind) -> CapabilitySourceKind:
    return (
        CapabilitySourceKind.INTERNAL
        if resource_kind is CapabilityResourceKind.REGISTERED_SPECIALIST
        else CapabilitySourceKind.EXTERNAL
    )


def _declarations(
    facets: tuple[TaskCapabilityFacet, ...],
    observations: tuple[CapabilityInventoryDescriptor, ...],
) -> tuple[CapabilityDeclaration, ...]:
    required_by_facet = {
        facet.facet_id: set(facet.required_capabilities)
        for facet in facets
    }
    declarations = {
        CapabilityDeclaration(
            facet_id=facet.facet_id,
            capability_id=claim.capability_id,
            source_kind=_source_kind(descriptor.resource_kind),
            source_id=descriptor.identity.source_id,
            claim=claim.claim,
            evidence_refs=claim.evidence_refs,
            valid_until=descriptor.valid_until,
        )
        for descriptor in observations
        for facet in facets
        for claim in descriptor.capability_claims
        if claim.capability_id in required_by_facet[facet.facet_id]
    }
    return tuple(
        sorted(
            declarations,
            key=lambda item: (
                item.facet_id,
                item.capability_id,
                item.source_kind.value,
                item.source_id,
                item.claim.value,
                item.evidence_refs,
                item.valid_until or "",
            ),
        )
    )


def build_capability_planning_preview(
    *,
    trigger: CapabilityDiscoveryTrigger | None,
    task_facets: Iterable[TaskCapabilityFacet],
    inventory_producer: CapabilityInventoryProducer,
    memory_store: CapabilityMemoryStore,
    memory_scope: CapabilityMemoryScope | None,
    evaluated_at: str,
) -> CapabilityPlanningPreview:
    """Compose coverage and lookup previews without discovery or execution.

    The supplied scope is descriptive, not authenticated. The preview never
    reads either port without an explicit trigger and complete scoped inventory.
    """
    facets = _task_facets(task_facets)
    if trigger is not None and not isinstance(trigger, CapabilityDiscoveryTrigger):
        raise TypeError("trigger must be CapabilityDiscoveryTrigger or None")
    if memory_scope is not None and not isinstance(memory_scope, CapabilityMemoryScope):
        raise TypeError("memory_scope must be CapabilityMemoryScope or None")

    if trigger is None:
        return CapabilityPlanningPreview(
            None,
            False,
            (),
            None,
            plan_capability_discovery(None, evaluated_at=evaluated_at),
            ("No explicit trigger; inventory and memory were not read.",),
        )

    if memory_scope is None:
        return CapabilityPlanningPreview(
            CapabilityInventoryReadStatus.UNKNOWN,
            False,
            (),
            None,
            plan_capability_discovery(trigger, evaluated_at=evaluated_at),
            ("Active host, user, and workspace scope is unavailable; inventory and memory were not read.",),
        )

    if not isinstance(inventory_producer, CapabilityInventoryProducer):
        raise TypeError("inventory_producer must implement CapabilityInventoryProducer")
    if not isinstance(memory_store, CapabilityMemoryStore):
        raise TypeError("memory_store must implement CapabilityMemoryStore")

    inventory = inventory_producer.read_cached_snapshot()
    if inventory.status is not CapabilityInventoryReadStatus.READ:
        return CapabilityPlanningPreview(
            inventory.status,
            False,
            (),
            None,
            plan_capability_discovery(trigger, evaluated_at=evaluated_at),
            inventory.limitations,
        )

    if not inventory.descriptors:
        return CapabilityPlanningPreview(
            inventory.status,
            False,
            (),
            None,
            plan_capability_discovery(trigger, evaluated_at=evaluated_at),
            tuple(sorted(set((*inventory.limitations, "Inventory supplied no scoped identities; memory was not read.")))),
        )

    if any(not _scope_matches(item, memory_scope) for item in inventory.descriptors):
        return CapabilityPlanningPreview(
            CapabilityInventoryReadStatus.UNKNOWN,
            False,
            (),
            None,
            plan_capability_discovery(trigger, evaluated_at=evaluated_at),
            tuple(sorted(set((*inventory.limitations, "Inventory identity did not match the supplied scope.")))),
        )

    records = memory_store.load(memory_scope)
    if isinstance(records, (str, bytes)):
        raise TypeError("memory store must return CapabilityMemoryRecord records")
    records = tuple(records)
    if any(
        not isinstance(record, CapabilityMemoryRecord)
        or record.scope != memory_scope
        or record.status is not CapabilityMemoryRecordStatus.ACTIVE
        for record in records
    ):
        raise ValueError("memory store returned invalid or out-of-scope records")

    cached_observations = tuple(record.descriptor for record in records)
    current_identities = tuple(item.identity for item in inventory.descriptors)
    discovery_plan = plan_capability_discovery(
        trigger,
        cached_observations,
        current_identities,
        evaluated_at=evaluated_at,
    )
    current_observations = tuple(
        item for item in inventory.descriptors if _matches_trigger(item, trigger)
    )
    coverage_observations = tuple(
        set((*current_observations, *discovery_plan.relevant_observations))
    )
    coverage = (
        evaluate_capability_coverage(
            facets,
            _declarations(facets, coverage_observations),
            evaluated_at=evaluated_at,
        )
        if coverage_observations
        else None
    )
    return CapabilityPlanningPreview(
        inventory.status,
        True,
        current_observations,
        coverage,
        discovery_plan,
        inventory.limitations,
    )


__all__ = ["CapabilityPlanningPreview", "build_capability_planning_preview"]
