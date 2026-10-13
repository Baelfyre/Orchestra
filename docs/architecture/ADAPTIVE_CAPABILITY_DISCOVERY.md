# Adaptive Capability Discovery Contract

## Purpose and scope

D3B-2A adds a pure, host-neutral contract for describing supplied capability inventory observations and planning bounded lookups after an explicit trigger. It does not discover tools, scan a host, access the network or filesystem, persist memory, invoke JEV, route work, grant permissions, activate plugins, or execute resources.

The contract is additive to the D3B-1 offline coverage evaluator. It does not change `TaskProfile` v1, D2 v1, existing routing contracts, or D3B-1 source-neutral status rules. Required task facets are not inferred from prose here; callers provide explicit capability IDs in a trigger.

## Versioned descriptor

`CAPABILITY_INVENTORY_SCHEMA_VERSION` is `orchestra.capability-inventory.v1`. `CapabilityInventoryDescriptor` records one resource and keeps these evidence layers distinct:

- Resource kind: registered specialist, external plugin, host-native tool, public or private reference, or prospective candidate.
- Source identity: descriptive resource/source IDs, optional host and adapter IDs, publisher and distribution identity, versions and revisions, digest, user/workspace scope, permission-scope revision, inventory-scope revision, and optional recheck token.
- Capability claims: source-associated `SUPPORTS`, `DOES_NOT_SUPPORT`, or `UNKNOWN` claims with evidence references.
- Inventory observation: `PRESENT`, `ABSENT`, `UNKNOWN`, or `UNSUPPORTED`, with separate observation references.
- Compatibility: `COMPATIBLE`, `INCOMPATIBLE`, `UNKNOWN`, or `UNSUPPORTED`, with separate compatibility references.
- Operation permissions: per-operation `ALLOWED`, `DENIED`, `UNKNOWN`, or `UNSUPPORTED` observations. These are historical observations, not grants of authority.
- Side effects: typed command, hook, network, file read/write, dependency-change, and credential-access observations, each separated from capability claims and permissions.
- Independent task-output references, review references, observation timestamps, expiry, and limitations.

Known positive or negative observations require evidence references. Unknown and unsupported states stay explicit; missing host or adapter evidence is never converted into `ABSENT` or `PRESENT`. Claims and evidence references remain attached to their source record. The descriptor does not combine provider claims into a winner or an aggregate conflict.

All identity values and references are descriptive data. The descriptor's type, schema version, `review_refs`, source label, or digest does not authenticate a host, user, publisher, reviewer, permission, or evidence producer. Trust must be established by a future host-specific boundary.

## Trigger and lookup plan

`CapabilityDiscoveryTrigger` accepts only these explicit reasons:

- `USER_REQUEST`: a named resource or capability/options request;
- `CAPABILITY_GAP`: a relevant D3B-1 gap;
- `QUALITY_ISSUE`: a demonstrated quality problem;
- `TOOL_FAILURE`: an unavailable, failed, incompatible, or permission-changed resource;
- `STALE_OBSERVATION`: relevant evidence needs refresh;
- `ENVIRONMENT_CHANGE`: a relevant identity, version, scope, or permission context changed.

Each trigger must carry at least one relevant resource or capability ID. An installation event by itself is not a trigger, and a missing trigger returns `NO_DISCOVERY` without consuming cached observations. There is no startup scan, full catalogue, background refresh, or arbitrary “all plugins” request.

`plan_capability_discovery` is a deterministic planner over the explicit trigger, supplied cached descriptors, supplied current identity snapshots, and an evaluation time. It does not invoke a host adapter. It returns the original user-selected resource IDs, relevant cached records, targeted capability/resource IDs, reusable knowledge hints, and resource IDs that need revalidation.

A reuse hint requires an exact current identity match, a non-expired observation, `PRESENT` inventory state, `COMPATIBLE` status, and a review reference. Identity includes host and user/workspace scope, resource/source and distribution identity, version and digest/revision, and permission scope. A version, source, scope, or permission-scope change invalidates only the affected observation. Missing current identity, unknown freshness, expired evidence, unsupported host capability, or incomplete review evidence produces revalidation or a targeted lookup, never a claim of absence.

Quality issues, tool failures, stale observations, and environment changes force targeted revalidation. Capability-gap lookups retain the requested capability scope and all relevant source records. Multiple providers are returned in deterministic identity order; differences between providers are not treated as a contradiction, and claims from one source remain visible for the existing D3B-1 source-specific assessment. No provider is ranked or selected. Explicit user-selected resources are preserved and are not silently replaced.

## Cache and authority boundaries

This unit defines cache identity and invalidation hints only. It creates no disk cache, private record, memory write, consent receipt, or synchronization path. Host/user/workspace scope identifiers should be opaque and host-provided; this code only validates their syntax. A reusable record is source-backed knowledge to consider, not proof that the resource is currently installed, permitted, technically qualified, or correct.

Permission observations never authorize an operation. A future execution path must independently recheck live host permissions, package identity, and action scope. Capability inventory cannot grant specialist authority, alter Conductor/AWF routing, activate JEV, or authorize external research or tool execution.

## Validation and limitations

`tests/runtime/test_capability_inventory.py` uses synthetic records to cover explicit and absent triggers, narrow user selections, cache hints, version/scope/permission invalidation, stale and unknown states, unsupported host interfaces, source-neutral claims, input-order invariance, malformed and duplicate inputs, and non-authorizing behavior.

D3B-2B still requires a verified host-specific inventory and permission source. Private adaptive memory still requires separate identity, consent, storage-isolation, lifecycle, and deletion design. Conductor/AWF consumption, optional JEV, plugin execution, and specialist admission remain separate approval-gated units.
