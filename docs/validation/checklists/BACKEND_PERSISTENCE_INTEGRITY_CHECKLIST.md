# Backend-to-Persistence Integrity Checklist

Use this checklist with the [Cross-Layer Integrity Profile Protocol](../CROSS_LAYER_INTEGRITY_PROFILE_PROTOCOL.md) and the shared [Cross-Module Logic Audit Protocol](../CROSS_MODULE_LOGIC_AUDIT_PROTOCOL.md).

## Identity and scope

- [ ] Repository, branch, approved baseline, current commit, packet revision, and profile-protocol hash match.
- [ ] Service, repository, mapping/query, schema, migration, and transaction boundaries in scope are explicitly identified.
- [ ] Every changed path is allowlisted and protected persistence paths remain unchanged unless explicitly in scope.
- [ ] Existing data, migration, rollback, backup, and destructive-operation boundaries remain separately governed.

## Workflow trace

- [ ] `SERVICE_INPUT` identifies the accepted domain/service input and caller assumptions.
- [ ] `DOMAIN_VALIDATION` maps required, optional, null, range, format, normalization, and invariant rules.
- [ ] `TRANSACTION_BOUNDARY` identifies transaction ownership, isolation expectations, and read-only/non-applicable behavior.
- [ ] `REPOSITORY_OPERATION` maps the service request to one repository/interface operation.
- [ ] `MAPPING_OR_QUERY` maps domain fields to ORM/query parameters and result fields without silent loss or coercion.
- [ ] `SCHEMA_CONSTRAINT` proves database constraints agree with domain and repository expectations.
- [ ] `PERSISTENCE_EXECUTION` identifies the actual read/write behavior and expected affected rows/records.
- [ ] `COMMIT_OR_ROLLBACK` proves success commit or failure rollback behavior; read-only flows explicitly mark this stage non-applicable.
- [ ] `READBACK_OR_PROJECTION` proves persisted or selected data is reconstructed without drift.
- [ ] `SERVICE_RESULT` proves storage results and failures are mapped back to the service contract deterministically.

## Integrity and failure coverage

- [ ] Validation and schema constraints agree; neither layer silently accepts values rejected by the other.
- [ ] Repository mapping preserves names, types, nullability, defaults, identifiers, and ownership fields.
- [ ] Transaction scope does not partially commit multi-step operations.
- [ ] Constraint, connectivity, timeout, serialization, deadlock/conflict, and zero-row outcomes map to explicit service behavior.
- [ ] Retry and duplicate execution cannot create unintended duplicate writes.
- [ ] Optimistic/pessimistic concurrency behavior is explicit when applicable.
- [ ] Migration or schema-version assumptions are current and source-backed.
- [ ] Secrets, credentials, and sensitive persisted values are not exposed in evidence.

## Findings and evidence

- [ ] Each finding has one owner, severity, affected stages, evidence, impact, minimal remediation, and required validation.
- [ ] Clockwork owns service/repository architecture findings; Chronicler owns schema, query, transaction, and persistence semantics; Cipher owns technical trust-boundary findings.
- [ ] Contradictions are recorded by The Tuner and routed rather than silently resolved.
- [ ] Executable happy-path and failure-path evidence is current and bound to the profile-protocol identity.
- [ ] Missing evidence produces `CROSS_LAYER_EVIDENCE_INSUFFICIENT`.
- [ ] Changed identity produces `CROSS_LAYER_CONTRACT_STALE` or `SPECIALIST_REENTRY_REQUIRED`.
- [ ] No open invalidation remains before `CROSS_LAYER_ALIGNMENT_CONFIRMED`.

## Closeout

- [ ] Focused integrity validator and behavior tests pass.
- [ ] Full behavior, runtime regression, packaging, prompt-budget, governance, scope, secret, and diff checks pass.
- [ ] Overseer records current evidence and Arbiter records continuation state.
- [ ] Release, deployment, destructive migration, and installed-integration actions remain separately governed.
