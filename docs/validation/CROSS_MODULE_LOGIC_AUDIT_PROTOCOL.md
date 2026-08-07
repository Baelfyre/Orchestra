# Cross-Module Logic Audit Protocol

## Status and authority

This protocol defines deterministic cross-layer audit evidence for Orchestra. It extends, but does not replace, the canonical [Cross-Specialist Coordination Protocol](../routing/CROSS_SPECIALIST_COORDINATION_PROTOCOL.md).

```text
Protocol status: IMPLEMENTED_FOR_FRONTEND_BACKEND_BACKEND_PERSISTENCE_AND_CROSS_MODULE_LOGIC
Baseline for Phase F2: 2bc63308415221c54babba578e812ec95bc65f4c
Decision owner per finding: exactly one specialist
Coordination owner: The Tuner
Routing owner: Conductor
Validation owner: Overseer
Transition owner: Arbiter
Implementation authority: external and separately granted
Git and release authority: not created by this protocol
```

## Audit lifecycle

```text
Conductor classifies the request
-> The Tuner assembles the frozen cross-layer packet
-> domain specialists own their decisions
-> Ponytail implements the authorized slice
-> executable workflow evidence is collected
-> The Tuner reconciles the handoff delta and invalidations
-> Overseer assesses evidence sufficiency
-> Arbiter decides continuation
```

Unknown status, missing ownership, missing evidence, stale identity, an open contradiction, or a path outside the frozen scope fails closed.

## Frontend-to-backend workflow

Every applicable workflow is traced in this order:

1. `UI_CONTROL`
2. `CLIENT_EVENT`
3. `CLIENT_STATE_OR_FORM_MODEL`
4. `SERIALIZED_REQUEST`
5. `API_ROUTE`
6. `BACKEND_HANDLER`
7. `SERVICE_OPERATION`
8. `REPOSITORY_AND_PERSISTENCE`
9. `API_RESPONSE`
10. `CLIENT_CACHE_OR_STATE_UPDATE`
11. `FINAL_RENDERED_STATE`

The trace records source references, owners, field mappings, validation rules, authorization behavior, state transitions, side effects, retries, idempotency, accessibility behavior, and executable evidence. `REPOSITORY_AND_PERSISTENCE` may reference an existing persistence contract; when persistence semantics themselves are in scope, use the backend-to-persistence profile below.

## Backend-to-persistence workflow

Backend-to-persistence integrity is traced in this order:

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

Clockwork owns service, repository-interface, and architectural-flow decisions. Chronicler owns schema, query, migration, transaction-semantics, durability, and stored-record decisions. Cipher owns security findings only when the persistence path crosses a technical trust boundary. The Tuner coordinates references and contradictions but never selects the winning persistence rule.

Required evidence covers contract mapping, validation-versus-constraint parity, transaction semantics, ORM/query mapping, error mapping, concurrency/idempotency, and executable happy/failure paths. Reads must explicitly mark non-applicable commit behavior rather than silently omitting a stage. Writes must prove commit or rollback behavior and observable error propagation.

## Cross-module logical-flow workflow

Language-neutral cross-module integrity is traced in this order:

1. `ENTRYPOINT`
2. `INPUT_CONTRACT`
3. `MODULE_A_DECISION`
4. `HANDOFF_PAYLOAD`
5. `MODULE_B_DECISION`
6. `SHARED_STATE_OR_SIDE_EFFECT`
7. `RESULT_PROPAGATION`
8. `ERROR_PROPAGATION`
9. `FINAL_OBSERVABLE_OUTCOME`

Clockwork is the canonical decision owner for cross-module control flow, dependency direction, interface compatibility, handoff shape, state mutation ordering, and error propagation. Other domain specialists retain ownership when a traced decision enters their domain. This profile is language-neutral: modules may be classes, packages, services, functions, jobs, handlers, adapters, or equivalent architectural units.

Required evidence covers the input contract, handoff contract, control-flow conditions, state and side effects, error propagation, dependency direction, and executable happy/failure paths. Cycles, swallowed errors, duplicated side effects, incompatible handoffs, and contradictory branch conditions fail closed.

## Finding contract

Each finding contains:

```yaml
finding_id: stable identifier
severity: CRITICAL | MAJOR | MINOR | CLEANUP
owner: exactly one specialist slug
affected_stages: non-empty workflow-stage list
evidence: source, executable, or explicit missing-evidence references
impact: observable cross-layer consequence
minimal_remediation: smallest contract-aligned correction
required_validation: evidence needed to close the finding
```

Supporting specialists may be listed, but decision ownership remains singular. The Tuner detects contradictions and never selects a winning requirement.

## Evidence contract

Evidence must bind to the approved baseline, frozen contract revision and hash, current commit, branch, working-tree fingerprint, tracked patch hash, staged patch hash, complete non-ignored untracked manifest, added-file identities, and relevant artifact lifecycle records.

Required workflow evidence includes:

- stage references and owners;
- boundary field and type mappings;
- validation and constraint parity;
- authentication and authorization parity when applicable;
- transaction, side-effect, retry, concurrency, and idempotency semantics when applicable;
- dependency direction and handoff compatibility;
- result and error propagation;
- applicable loading, queued, processing, cancellation, timeout, success, error, empty, deleted, and stale states;
- keyboard, focus, semantic, status, and error accessibility behavior for user-visible flows;
- executable happy-path and failure-path evidence;
- explicit missing evidence and invalidation events.

Passing unit tests alone is insufficient. At least one executable end-to-end workflow representation must prove the applicable stage transitions and expected result for each active audit profile.

## Deterministic statuses

```text
CROSS_LAYER_ALIGNMENT_CONFIRMED
CROSS_LAYER_ALIGNMENT_GAPS_FOUND
CROSS_LAYER_CONTRACT_INCOMPLETE
CROSS_LAYER_CONTRADICTION_REVIEW_REQUIRED
CROSS_LAYER_EVIDENCE_INSUFFICIENT
CROSS_LAYER_CONTRACT_STALE
SPECIALIST_REENTRY_REQUIRED
```

- `CROSS_LAYER_ALIGNMENT_CONFIRMED` requires complete current evidence and no open finding.
- `CROSS_LAYER_ALIGNMENT_GAPS_FOUND` requires at least one single-owner finding.
- `CROSS_LAYER_CONTRACT_INCOMPLETE` blocks when an owner, contract, criterion, or authority reference is missing.
- `CROSS_LAYER_CONTRADICTION_REVIEW_REQUIRED` blocks until Conductor routes revision or human review.
- `CROSS_LAYER_EVIDENCE_INSUFFICIENT` blocks until Overseer receives current evidence.
- `CROSS_LAYER_CONTRACT_STALE` blocks when identity or a dependency revision changes.
- `SPECIALIST_REENTRY_REQUIRED` names the minimal evidence-based specialist set.

## Invalidation and re-entry

| Change | Minimal re-entry | Invalidated evidence |
| --- | --- | --- |
| UI contract | Cloak; Clockwork or Cipher only when API or authorization changes | Affected UI and Overseer evidence |
| API shape or backend validation | Clockwork; Cipher when a trust boundary changes | Affected frontend and integration evidence |
| Authorization | Cipher, Cloak, Overseer | Persona, route, content, and visible-state evidence |
| Repository interface or service contract | Clockwork; Chronicler when persistence semantics change | Affected backend, persistence, and integration evidence |
| Schema, migration, query, transaction, or durability rule | Chronicler; Clockwork when service/repository behavior changes | Persistence and dependent service evidence |
| Cross-module handoff or control-flow condition | Clockwork plus only affected domain owners | Affected module-flow and downstream evidence |
| Baseline, contract hash, or evidence fingerprint | The Tuner, Overseer, Arbiter | All mismatched evidence |

An open invalidation event blocks readiness. Re-entry revises only affected specialist contracts and then refreshes downstream evidence.

## Contradictions and stop conditions

The Tuner records conflicting clauses, owners, severity, participants, and whether human review is required. Conductor routes correction. Material scope, architecture, security, privacy, persistence, policy, authority, or residual-risk tradeoffs require the applicable existing governance decision path.

Stop on baseline drift, protected-path mutation, undeclared generated artifacts, scope growth, secret exposure, destructive behavior, failed parity, or exhausted bounded remediation. No audit result authorizes stage, commit, push, pull request, merge, release, deployment, policy activation, force push, or history rewrite.

## Implemented checklists

- [Frontend-to-Backend Synchronicity Checklist](checklists/FRONTEND_BACKEND_SYNCHRONICITY_CHECKLIST.md)
- [Backend-to-Persistence Integrity Checklist](checklists/BACKEND_PERSISTENCE_INTEGRITY_CHECKLIST.md)
- [Cross-Module Logical-Flow Integrity Checklist](checklists/CROSS_MODULE_LOGIC_INTEGRITY_CHECKLIST.md)

All profiles reuse the same Tuner packet, finding contract, deterministic statuses, identity binding, invalidation model, Overseer evidence ownership, and Arbiter continuation boundary.
