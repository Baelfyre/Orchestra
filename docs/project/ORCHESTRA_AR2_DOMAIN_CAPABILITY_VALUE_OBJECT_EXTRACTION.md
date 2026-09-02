# Orchestra AR-2 Domain Capability Value-Object Extraction

## Status

`AR_2_DOMAIN_CAPABILITY_VALUE_OBJECT_IMPLEMENTATION_CANDIDATE`

This document describes the bounded AR-2 extraction that moves pure capability value objects and their deterministic normalization semantics inward to `orchestra_runtime.domain.capabilities` while preserving the legacy runtime surface.

## Canonical domain ownership

The following semantics are owned by `orchestra_runtime.domain.capabilities.core` in this candidate:

- `CapabilityReasonCode`
- `RuntimeCapability`
- `RuntimeCapabilityGrant`
- `CapabilityDecision`
- deterministic capability identifier and text normalization used by those entities

These entities depend only on standard-library types, canonical authority-domain value objects, and `orchestra_runtime.shared.errors`. They do not read files, create run identities, depend on application ports, construct runtime audit events, call providers, or perform host/MCP operations.

## Legacy compatibility boundary

`orchestra_runtime.capabilities` remains the compatibility and transitional integration surface. Existing imports of the moved capability symbols resolve to the exact canonical domain objects rather than duplicate wrappers or copied classes.

The legacy module deliberately retains:

- `RuntimeCapabilityManifest`, because it still depends on legacy `RunIdentity` placement;
- `CapabilityResolver`, because it still inherits the legacy `ICapabilityResolver` application port and coordinates manifest construction/evaluation;
- trusted repository-policy loading through `_load_trusted_json`;
- capability manifest and decision audit-event projection.

Those responsibilities are intentionally not pulled into the domain before their execution-identity, application-port, and infrastructure dependencies are classified in later bounded phases.

## Dependency rule

The extracted capability domain obeys the machine architecture policy:

```text
orchestra_runtime.domain -> orchestra_runtime.domain | orchestra_runtime.shared
```

The extracted module has no dependency on:

```text
orchestra_runtime.application
orchestra_runtime.infrastructure
orchestra_runtime.entrypoints
orchestra_runtime.capabilities
orchestra_runtime.authority
orchestra_runtime.interfaces
orchestra_runtime.models
pathlib / filesystem I/O
provider or MCP execution
```

## Behavioral preservation

The extraction preserves the existing capability-value contract, including:

- canonical case-folded capability, owner, operation, and manifest identifiers;
- immutable dataclass state;
- sorted unique capability operations;
- grant operations constrained to the parent capability operation set;
- unique sorted grant constraint keys;
- stable authority provenance and constraint serialization through canonical authority-domain objects;
- deterministic decision normalization and evaluated-constraint de-duplication;
- fail-closed malformed capability and grant construction.

Manifest loading, resolver behavior, and audit-event projection continue through the legacy module, so this AR-2 unit does not change external capability resolution behavior or grant new authority.

## Validation

`tests/runtime/test_domain_capabilities_core.py` verifies:

1. legacy capability exports are identity-equal to the canonical domain symbols;
2. capability, grant, and decision normalization semantics are preserved;
3. the extracted domain module has no filesystem, provider, application-port, or legacy-runtime imports.

The existing capability and runtime-authority suites remain the broader compatibility regression surface.

## Explicit non-goals

This bounded extraction does not:

- start AR-3 application/use-case migration;
- move `RuntimeCapabilityManifest` before `RunIdentity` placement is classified;
- move `CapabilityResolver` or `ICapabilityResolver` into the domain;
- move trusted policy persistence into domain code;
- move capability audit-event projection into the domain;
- retire the public `orchestra_runtime.capabilities` import surface;
- alter authority scope, capability resolution, routing, governance, provider, MCP, or execution semantics;
- authorize release/tag publication, deployment, policy activation, integration refresh, destructive action, branch deletion, force push, or history rewrite.

AR-2 remains active after this unit until the remaining qualified pure-domain ownership slices are completed.
