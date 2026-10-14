# Adaptive Capability Memory

## D3B-3 scope

D3B-3 adds a scoped local record model and explicit-root persistence adapter for capability observations and evidence-backed reusable-pattern references. It has no default storage location and is not wired into runtime composition. This unit and its tests use synthetic records only; it performs no real private-memory writes.

The record format is versioned as `orchestra.capability-memory.v1`. A record contains a canonical record ID, an explicit host/user/workspace partition, a typed inventory descriptor, its record timestamp, and its lifecycle state. Reusable patterns are references only: they require a `PRIVATE_REFERENCE` resource and evidence references. Records do not contain free-form conversation text or learned preferences.

## Scope, cache, and evidence rules

The store requires complete host, user, and workspace scope identifiers. It hashes that scope to select a storage file, then verifies the same scope when loading. A descriptor must also have a complete inventory observation scope and match the record's host, user, and workspace. Missing scope is rejected instead of being assigned to a default identity.

`JsonCapabilityMemoryStore.load()` returns active records for one exact scope. It preserves stale descriptors and their original evidence references. Freshness, identity revalidation, and selective lookup remain the responsibility of the existing `plan_capability_discovery` planner. The store does not turn `SUPPORTS`, review references, producer status, or permission observations into verified expertise or execution authority.

Unknown or unsupported inventory, compatibility, or permission values remain unchanged in stored descriptors. Active observations with the same complete descriptor identity cannot be duplicated; callers must explicitly supersede the prior record. Input and output ordering is deterministic.

## Storage and lifecycle

The adapter requires an explicit storage root and repository root. It refuses a root inside the repository and uses:

```text
<injected-root>/v1/<sha256-of-host-user-workspace>.json
```

Each file contains one scope's versioned records and a canonical content digest. Writes use a temporary file and atomic replacement. The digest detects accidental content changes; it does not authenticate the writer or protect against an attacker who can rewrite the file and recompute the digest. The adapter supplies no encryption and does not select a retention duration.

Active records can be invalidated or superseded. Supersession atomically marks the prior record and adds the replacement. Record deletion removes the selected record; scope deletion removes its storage file. These operations do not claim forensic secure erasure from filesystem snapshots, backups, or storage media. Expired observations are retained so the D3B-2A planner can classify them as stale and selectively revalidate them; storage does not silently delete useful revalidation evidence.

## Trust and activation boundary

`CapabilityMemoryScope` identifiers and `CapabilityMemoryRecord` types are descriptive, not authenticated. The store is not connected to the D3B-2B-P unavailable producer, Conductor, routing, plugin execution, JEV, or any host permission system. Its synthetic fixtures cannot establish current user/workspace identity, trusted provenance, compatibility, consent, or permission to execute.

Live private-memory use remains blocked until a trusted host identity bridge, explicit consent and privacy review, storage protection, retention, revocation, deletion, and recovery requirements are independently established. The adapter's explicit-root API is not production activation authority.

## Validation

`tests/runtime/test_capability_memory.py` uses temporary roots outside the repository and synthetic identities. It covers scoped round trips, cross-user/workspace isolation, planner-driven stale revalidation, reusable-pattern reference constraints, invalidation, supersession, deletion, repository-root rejection, schema and content-integrity failures, and malformed states. It does not qualify concurrent multi-process writers, encryption, secure erasure, real identity, or live private-data handling.
