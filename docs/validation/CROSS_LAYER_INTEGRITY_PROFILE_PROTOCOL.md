# Cross-Layer Integrity Profile Protocol

## Status and relationship to the shared audit protocol

This protocol extends the canonical [Cross-Module Logic Audit Protocol](CROSS_MODULE_LOGIC_AUDIT_PROTOCOL.md) with two additional audit profiles. It does not replace or mutate the frontend-to-backend profile, its evidence identity, or its Codex portable reference bundle.

```text
Profile protocol status: IMPLEMENTED_PHASE_F2
Baseline: 2bc63308415221c54babba578e812ec95bc65f4c
Parent protocol: docs/validation/CROSS_MODULE_LOGIC_AUDIT_PROTOCOL.md
Decision owner per finding: exactly one specialist
Coordination owner: The Tuner
Routing owner: Conductor
Validation owner: Overseer
Transition owner: Arbiter
Implementation authority: external and separately granted
Git and release authority: not created by this protocol
```

All common finding fields, deterministic statuses, evidence-identity rules, contradiction handling, invalidation behavior, specialist re-entry rules, stop conditions, and authority boundaries are inherited from the parent protocol.

## Backend-to-persistence integrity profile

Trace every applicable backend-to-persistence workflow in this order:

1. `SERVICE_INPUT`
2. `DOMAIN_VALIDATION`
3. `TRANSACTION_BOUNDARY`
4. `REPOSITORY_OPERATION`
5. `MAPPING_OR_QUERY`
6. `SCHEMA_CONSTRAINT`
7. `PERSISTENCE_EXECUTION`
8. `COMMIT_OR_ROLLBACK`
9. `READBACK_OR_PROJECTION`
10. `SERVICE_RESULT`

### Ownership

- Clockwork owns service, repository-interface, and architectural-flow decisions.
- Chronicler owns schema, query, migration, transaction-semantics, durability, and stored-record decisions.
- Cipher owns technical security findings only when the persistence path crosses a trust boundary.
- The Tuner coordinates references, contradictions, and re-entry but does not select a winning persistence rule.
- Overseer owns evidence sufficiency.
- Arbiter owns continuation disposition.

### Required evidence

The profile requires:

- `contract_mapping`
- `validation_and_constraint_parity`
- `transaction_semantics`
- `query_mapping`
- `error_mapping`
- `concurrency_and_idempotency`
- `executable_workflow`

Reads must explicitly mark non-applicable commit behavior rather than silently omit `COMMIT_OR_ROLLBACK`. Writes must prove either commit or rollback behavior and observable error propagation.

### Fail-closed conditions

Return the parent protocol's deterministic blocking or re-entry status when any of the following is found:

- service and schema validation rules disagree;
- mapping silently drops, renames, coerces, or defaults a required field;
- transaction ownership is absent or permits partial commit;
- retry or duplicate execution can create unintended duplicate writes;
- repository/query behavior disagrees with the accepted service contract;
- migration or schema assumptions are stale or unsupported by current evidence;
- persistence errors are swallowed or mapped to false success;
- executable happy-path or failure-path evidence is missing.

## Cross-module logical-flow integrity profile

This profile is language-neutral. A module may be a class, package, function, service, job, handler, adapter, or equivalent architectural unit.

Trace every applicable cross-module workflow in this order:

1. `ENTRYPOINT`
2. `INPUT_CONTRACT`
3. `MODULE_A_DECISION`
4. `HANDOFF_PAYLOAD`
5. `MODULE_B_DECISION`
6. `SHARED_STATE_OR_SIDE_EFFECT`
7. `RESULT_PROPAGATION`
8. `ERROR_PROPAGATION`
9. `FINAL_OBSERVABLE_OUTCOME`

### Ownership

Clockwork is the canonical owner for cross-module control flow, dependency direction, interface compatibility, handoff shape, state-mutation ordering, and error propagation. Other specialists retain decision ownership when a traced decision enters their canonical domain. The Tuner coordinates but does not rewrite or resolve specialist-owned decisions.

### Required evidence

The profile requires:

- `input_contract`
- `handoff_contract`
- `control_flow`
- `state_and_side_effects`
- `error_propagation`
- `dependency_direction`
- `executable_workflow`

### Fail-closed conditions

Return the parent protocol's deterministic blocking or re-entry status when any of the following is found:

- required handoff fields are silently dropped, renamed, coerced, or defaulted;
- branch conditions are contradictory across module boundaries;
- dependency direction introduces an accidental cycle;
- a retry or re-entry path can duplicate a side effect;
- an exception or rejected result is swallowed or converted to false success;
- shared mutable state lacks a clear owner or invalidation behavior;
- async, queued, callback, or event-driven handoffs lose required ordering or correlation;
- executable happy-path or failure-path evidence is missing.

## Deterministic status inheritance

Both profiles use the parent protocol's exact status set:

```text
CROSS_LAYER_ALIGNMENT_CONFIRMED
CROSS_LAYER_ALIGNMENT_GAPS_FOUND
CROSS_LAYER_CONTRACT_INCOMPLETE
CROSS_LAYER_CONTRADICTION_REVIEW_REQUIRED
CROSS_LAYER_EVIDENCE_INSUFFICIENT
CROSS_LAYER_CONTRACT_STALE
SPECIALIST_REENTRY_REQUIRED
```

No additional status is introduced by Phase F2.

## Finding and evidence rules

Every non-confirmed case must contain the parent protocol's complete finding contract:

```yaml
finding_id: stable identifier
severity: CRITICAL | MAJOR | MINOR | CLEANUP
owner: exactly one specialist slug
affected_stages: non-empty profile-stage list
evidence: source, executable, or explicit missing-evidence references
impact: observable cross-layer consequence
minimal_remediation: smallest contract-aligned correction
required_validation: evidence needed to close the finding
```

At least one executable happy-path and one executable failure-path trace must exist for each profile. Passing unit tests alone is insufficient evidence for `CROSS_LAYER_ALIGNMENT_CONFIRMED`.

## Invalidation and re-entry additions

| Change | Minimal re-entry | Invalidated evidence |
| --- | --- | --- |
| Repository interface or service contract | Clockwork; Chronicler when persistence semantics change | Affected backend, persistence, and integration evidence |
| Schema, migration, query, transaction, or durability rule | Chronicler; Clockwork when service or repository behavior changes | Persistence and dependent service evidence |
| Cross-module handoff or control-flow condition | Clockwork plus only affected domain owners | Affected module-flow and downstream evidence |
| Profile protocol identity or executable fixture identity | The Tuner, Overseer, Arbiter | All mismatched F2 profile evidence |

An open invalidation blocks alignment confirmation until affected contracts and downstream evidence are refreshed.

## Checklists and executable evidence

- [Backend-to-Persistence Integrity Checklist](checklists/BACKEND_PERSISTENCE_INTEGRITY_CHECKLIST.md)
- [Cross-Module Logical-Flow Integrity Checklist](checklists/CROSS_MODULE_LOGIC_INTEGRITY_CHECKLIST.md)
- `tests/behavior/cross-layer-integrity-fixtures.json`
- `scripts/validate_cross_layer_integrity_contract.py`

## Preserved boundaries

Phase F2 adds audit evidence only. It does not create or widen:

- implementation authority;
- database or migration authority;
- destructive cleanup authority;
- Git staging, commit, push, merge, or force-push authority;
- release, deployment, publication, or installed-host mutation authority;
- policy activation authority;
- specialist, plugin, command, or runtime-model registration.

Material architecture, persistence, security, governance, or residual-risk decisions remain owned by the existing Orchestra specialist and governance paths.
