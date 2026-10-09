# Orchestra AR-2 Domain Execution Identity Extraction

## Status

`AR_2_DOMAIN_EXECUTION_IDENTITY_IMPLEMENTATION_CANDIDATE`

This bounded AR-2 increment moves immutable run-identity semantics from the mixed legacy model module into the canonical execution domain after correlation validation was independently extracted and qualified.

## Canonical domain ownership

`orchestra_runtime.domain.execution.identity` owns `RunIdentity`.

The domain entity preserves the existing contract:

- `run_id` is trimmed and must remain non-empty;
- optional `parent_run_id` is trimmed;
- a run cannot name itself as its parent;
- optional `correlation_id` is validated and canonicalized by `orchestra_runtime.domain.execution.correlation`;
- no correlation identifier is generated implicitly;
- `to_dict()` always emits `run_id` and `parent_run_id` and emits `correlation_id` only when present.

The entity is immutable and slot-backed exactly as before.

## Legacy compatibility boundary

`orchestra_runtime.models` remains a transitional mixed-model surface. It imports and re-exposes the canonical `RunIdentity` object rather than defining a second class.

As a result:

- `orchestra_runtime.models.RunIdentity` is the canonical domain class;
- top-level `orchestra_runtime.RunIdentity` remains identity-equal because the public package continues importing through the legacy model surface;
- existing callers in capabilities, lifecycle, delegation, services, and other legacy modules require no import migration in this bounded unit.

The legacy model module also uses the canonical execution-domain correlation validator for its remaining envelope validation behavior.

## Dependency rule

The extracted identity module obeys the AR-2 domain dependency direction:

```text
orchestra_runtime.domain -> orchestra_runtime.domain | orchestra_runtime.shared
```

Its only dependencies are `dataclasses` and the sibling execution-domain correlation contract. It has no clock, entropy, filesystem, application-port, provider, MCP, host, persistence, audit, lifecycle-controller, or legacy-runtime dependency.

## Behavioral preservation

The extraction changes ownership, not runtime semantics.

Focused regression coverage verifies:

1. legacy and top-level `RunIdentity` exports are identity-equal to the canonical domain class;
2. run and parent identifiers preserve existing normalization;
3. correlation identifiers preserve canonical UUIDv7 normalization without implicit generation;
4. invalid empty run identifiers, self-parenting identities, and malformed correlation identifiers fail closed;
5. `to_dict()` preserves the existing serialized shape;
6. the domain identity module contains no I/O, environmental-effect, application-port, or legacy-runtime imports.

Existing runtime suites continue to exercise `RunIdentity` through capability manifests, lifecycle handling, delegation, runtime composition, correlation propagation, and public imports.

## Sequencing value

With correlation validation and `RunIdentity` now independently owned by `domain.execution`, later AR-2 work can classify lifecycle state, capability-manifest composition, and other execution semantics without forcing those domain candidates to depend on the mixed legacy `models.py` surface.

Those later moves remain separate qualification units.

## Explicit non-goals

This bounded extraction does not:

- move lifecycle states, signals, controllers, or terminal results;
- move `RuntimeAuditEvent` or `AuditEventType`;
- move `ExecutionResult` or `OrchestraRuntimeEnvelope`;
- move `RuntimeCapabilityManifest` or capability resolver application behavior;
- alter delegation, coordination, routing, provider, MCP, governance, or execution behavior;
- start AR-3 application/use-case extraction;
- start AR-4 infrastructure extraction;
- retire `orchestra_runtime.models` or top-level public imports;
- authorize release or tag publication, deployment, production mutation, policy activation, installed-integration refresh, destructive cleanup, branch deletion, force push, or history rewrite.

AR-2 remains active after this unit until the remaining qualified pure-domain ownership slices are complete.
