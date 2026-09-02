# Orchestra AR-2 Domain Governance Authority Extraction

## Status

`AR_2_DOMAIN_GOVERNANCE_AUTHORITY_IMPLEMENTATION_CANDIDATE`

This document describes the bounded AR-2 extraction that moves pure authority state and deterministic authority-value semantics inward to `orchestra_runtime.domain.governance` while preserving the legacy runtime surface.

## Canonical domain ownership

The following semantics are owned by `orchestra_runtime.domain.governance.authority` in this candidate:

- `ProvenanceSource`
- `TargetSelectorType`
- `ConstraintKind`
- `AuthorityReasonCode`
- `AuthorityProvenance`
- `TargetSelector`
- `Constraint`
- `AuthorityScope`
- `AuthorityDecision`
- deterministic identifier/text normalization used by those entities
- deterministic constraint permission and intersection semantics

These entities import only the standard library and `orchestra_runtime.shared.errors`. They do not read files, resolve repository paths, depend on application ports, construct runtime audit events, call providers, or perform host/MCP operations.

## Legacy compatibility boundary

`orchestra_runtime.authority` remains the compatibility and transitional integration surface. Existing imports of the moved authority symbols resolve to the exact canonical domain objects rather than duplicate wrappers or copied classes.

The legacy module deliberately retains:

- trusted repository-policy JSON loading and path-containment checks;
- `AuthorityEvaluator` inheritance from the legacy `IAuthorityEvaluator` port;
- authority evaluation/enforcement orchestration that is still coupled to that port;
- `RuntimeAuditEvent` projection helpers.

Those responsibilities are not pulled into the domain solely to make the legacy facade syntactically smaller. Their final placement belongs to later application and infrastructure phases.

## Dependency rule

The domain surface obeys the machine architecture policy:

```text
orchestra_runtime.domain -> orchestra_runtime.domain | orchestra_runtime.shared
```

The extracted module has no dependency on:

```text
orchestra_runtime.application
orchestra_runtime.infrastructure
orchestra_runtime.entrypoints
orchestra_runtime.authority
orchestra_runtime.interfaces
orchestra_runtime.models
pathlib / filesystem I/O
provider or MCP execution
```

## Behavioral preservation

The extraction preserves the existing authority-value contract, including:

- canonical identifier normalization;
- immutable dataclass state;
- exact target selectors with wildcard rejection;
- unique normalized operations and constraint keys;
- trusted versus delegated provenance invariants;
- deterministic constraint permission and intersection behavior;
- stable dictionary serialization;
- fail-closed malformed or empty authority construction.

Repository-policy loading and authority event projection continue through the legacy module, so this AR-2 unit does not change external authority behavior or grant new authority.

## Validation

`tests/runtime/test_domain_governance_authority.py` verifies:

1. legacy exports are identity-equal to the canonical domain symbols;
2. normalization and deterministic constraint semantics are preserved;
3. untrusted delegation and wildcard selectors still fail closed;
4. the domain authority module has no filesystem or legacy-runtime imports.

The existing authority/runtime suites remain the broader compatibility regression surface.

## Explicit non-goals

This bounded extraction does not:

- start AR-3 application/use-case migration;
- move repository-policy persistence into domain code;
- move application ports into the domain;
- move audit/event presentation into the domain;
- retire the public `orchestra_runtime.authority` import surface;
- alter authority scope, capability, routing, governance, provider, MCP, or execution semantics;
- authorize release/tag publication, deployment, policy activation, integration refresh, destructive action, branch deletion, force push, or history rewrite.

AR-2 remains active after this unit until the remaining qualified pure-domain ownership slices are completed.