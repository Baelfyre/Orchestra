# Cross-Module Logic Audit Protocol

## Status and authority

This protocol defines deterministic cross-layer audit evidence for Orchestra. It extends, but does not replace, the canonical [Cross-Specialist Coordination Protocol](../routing/CROSS_SPECIALIST_COORDINATION_PROTOCOL.md).

```text
Protocol status: IMPLEMENTED_FOR_FRONTEND_BACKEND_SYNCHRONICITY
Baseline: 6bce297c7469f9c08ce41308cbb993cc863ac540
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

The trace records source references, owners, field mappings, validation rules, authorization behavior, state transitions, side effects, retries, idempotency, accessibility behavior, and executable evidence. `REPOSITORY_AND_PERSISTENCE` is traced only at an existing contract boundary in this slice. New persistence design is deferred to Chronicler and separate authorization.

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
- request and response field mappings;
- client and server validation parity;
- authentication and authorization parity;
- applicable loading, queued, processing, cancellation, timeout, success, error, empty, deleted, and stale states;
- side effects, retries, and idempotency;
- keyboard, focus, semantic, status, and error accessibility behavior;
- executable happy-path and failure-path evidence;
- explicit missing evidence and invalidation events.

Passing unit tests alone is insufficient. At least one executable end-to-end workflow representation must prove the stage transitions and expected result.

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
| Persistence beyond declared trace | Chronicler plus human scope authorization | Packet and all dependent workflow evidence |
| Baseline, contract hash, or evidence fingerprint | The Tuner, Overseer, Arbiter | All mismatched evidence |

An open invalidation event blocks readiness. Re-entry revises only affected specialist contracts and then refreshes downstream evidence.

## Contradictions and stop conditions

The Tuner records conflicting clauses, owners, severity, participants, and whether human review is required. Conductor routes correction. Human review is mandatory for scope, architecture, security, privacy, persistence, policy, authority, or residual-risk tradeoffs not already frozen.

Stop on baseline drift, protected-path mutation, undeclared generated artifacts, scope growth, secret exposure, destructive behavior, failed parity, or exhausted bounded remediation. No audit result authorizes stage, commit, push, pull request, merge, release, deployment, policy activation, force push, or history rewrite.

## First implemented checklist

The normative first-slice checklist is [Frontend-to-Backend Synchronicity Checklist](checklists/FRONTEND_BACKEND_SYNCHRONICITY_CHECKLIST.md). Backend-persistence and broader cross-module checklists remain deferred.
