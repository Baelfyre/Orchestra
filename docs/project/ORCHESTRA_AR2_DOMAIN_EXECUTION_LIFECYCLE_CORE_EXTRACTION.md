# Orchestra AR-2 Domain Execution Lifecycle Core Extraction

Status: `AR_2_DOMAIN_EXECUTION_LIFECYCLE_CORE_IMPLEMENTATION_CANDIDATE`

Phase: `AR-2`

Canonical source baseline: `a451bca21b3a9d8c470ff357daec59fddd335ff1`.

## Purpose

Move deterministic lifecycle state, signal, snapshot, terminal-result, fingerprint, initialization, and transition semantics inward to the execution domain without moving application ports, audit-event projection, or runtime orchestration.

## Canonical domain surface

`orchestra_runtime/domain/execution/lifecycle.py` owns:

- `LifecycleState`;
- `LifecycleSignalType`;
- immutable lifecycle transition maps;
- `StructuredTerminalResult`;
- `LifecycleSignal`;
- `LifecycleSnapshot`;
- `lifecycle_signal_fingerprint`;
- `initialize_lifecycle_snapshot`;
- `apply_lifecycle_signal`.

The domain surface depends only on standard-library deterministic primitives, `orchestra_runtime.domain`, and `orchestra_runtime.shared`.

## Compatibility surface

`orchestra_runtime/lifecycle.py` remains the transitional legacy surface.

It re-exports the same lifecycle domain class and transition objects, retains `LifecycleController(ILifecycleController)`, and delegates controller initialization and transition application to the domain functions. Existing top-level `orchestra_runtime` exports continue to resolve through the legacy module and therefore remain object-identity compatible.

## Deliberately retained outside the domain

The legacy module continues to own:

- `LifecycleController` application-port inheritance;
- runtime audit-event projection;
- `AuditEventType` and `RuntimeAuditEvent` coupling;
- stable audit-event ID construction.

These concerns require later AR-3 or AR-4 placement and are not pulled inward merely to reduce the legacy file size.

## Preserved lifecycle behavior

The extraction preserves:

- `INITIALIZING -> ACTIVE | FAILED | CANCELLED | TIMED_OUT | BLOCKED`;
- `ACTIVE -> WAITING | COMPLETED | FAILED | CANCELLED | TIMED_OUT | BLOCKED`;
- `WAITING -> ACTIVE | FAILED | CANCELLED | TIMED_OUT | BLOCKED`;
- terminal-state immutability;
- explicit `WAIT` and `RESUME` source-state requirements;
- structured terminal-result matching;
- deterministic signal fingerprints;
- exact terminal-signal replay idempotence;
- conflicting terminal-signal rejection;
- fail-closed run/state/signal validation;
- public and legacy object identity.

## Validation

Focused regression coverage is added in `tests/runtime/test_domain_execution_lifecycle.py` for legacy/public identity, deterministic transitions, terminal replay/conflict behavior, controller delegation, and import-boundary purity. Existing lifecycle, delegation, runtime, presentation, provider, specialist-execution, and adaptive tests remain the compatibility surface.

Repository qualification remains authoritative. Passing tests do not grant phase progression or protected-action authority.

## Non-goals

This unit does not:

- move `ILifecycleController` into the domain;
- move lifecycle audit events into the domain;
- move `AuditEventType` or `RuntimeAuditEvent`;
- alter runtime execution, delegation, provider, MCP, or presentation behavior;
- retire `orchestra_runtime.lifecycle`;
- start AR-3 or AR-4;
- authorize release, deployment, production mutation, policy activation, provider routing/fallback, installed-integration refresh, destructive cleanup, branch deletion, force push, or history rewrite.

## Sequencing

If this candidate becomes canonical and post-merge verified, AR-2 remains active. The next bounded extraction must be selected from a fresh dependency audit rather than inferred from lifecycle-core completion.
