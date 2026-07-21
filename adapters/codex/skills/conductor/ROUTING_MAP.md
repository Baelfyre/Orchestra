# Orchestra Routing Map

Load this file only when routing is ambiguous, cross-domain, or order-dependent.
Do not load it for obvious single-owner work.

## Direct Route Rules

- Obvious single-owner work routes directly to owner.
- Ambiguous ownership stays with `conductor`.
- Governance context stays out of ordinary low-risk work unless trigger exists.
- `REFERENCE_CONTEXT.md#governance-decision-protocol` does not load during initial route classification.
- `ROUTING_MAP.md` does not load for obvious single-owner tasks.

## Delegated Phase Progression Routing

- Direct single-specialist routing remains available for simple single-unit work outside delegated phases.
- Conductor is required when multiple approved units exist, transition dispositions must be consumed, or checkpoint/resume behavior is needed.
- Conductor loads the full envelope once and passes unit-specific deltas to specialists.
- Routing metadata does not create or expand authority.


## Canonical Routing Rules

| Task Type | Target Skill | Condition |
| --- | --- | --- |
| Business alignment, scope, requirements, acceptance criteria, SDLC sufficiency | `the-steward` | Governance alignment owner is clear |
| Legal, regulatory, privacy-obligation, IP, licensing governance | `the-governor` | Governance compliance owner is clear |
| Continuity, handoff, merge readiness, branch drift, source-of-truth conflict | `arbiter` | Continuation state is uncertain |
| Architecture, layering, service boundaries, refactor structure | `clockwork` | Technical architecture owner is clear |
| Technical security, authorization, secrets, privacy-control design | `cipher` | Technical security owner is clear |
| Database, schema, migration, ORM, persistence semantics | `chronicler` | Persistence owner is clear |
| UI/UX, accessibility, responsive layout, interaction design | `cloak` | Frontend design owner is clear |
| QA strategy, validation evidence, release-readiness checks | `overseer` | Validation owner is clear |
| Documentation production and editing | `scribe` | Documentation execution owner is clear |
| Diagram and model generation | `weaver` | Visual artifact owner is clear |
| Minimal implementation after design is ready | `ponytail` | Execution owner is clear and upstream design/governance are ready |
| Controlled destructive-path simulation | `dagger` | Explicit authorization and guardrail validation are present |
| Broad, unclear, or overlapping requests | `conductor` | Ownership overlaps, dependencies exist, or route split is unclear |

## Ordered Multi-Skill Sequences

- `the-governor -> cipher -> ponytail` for governance-sensitive security implementation
- `clockwork -> ponytail` for architecture-first implementation
- `chronicler -> overseer` for persistence semantics followed by migration or DB validation
- `the-steward -> scribe` for required SDLC documentation shaped by business-alignment governance
- `the-governor -> scribe` for compliance documentation shaped by governance
- `arbiter -> overseer` when validation evidence must be executed or refreshed before continuation
- `cloak -> clockwork -> ponytail` when frontend design changes API shape, data flow, or service boundaries
- `cloak -> cipher -> ponytail` when frontend design affects authorization, privacy, or destructive journeys
- `cloak -> clockwork -> ponytail -> cloak -> overseer` for UI-affecting implementation, correction, renewed static audit, and evidence validation

## UI Engineering and Validation Ownership

Layered UI validation is jointly governed by Cloak, Clockwork, and Overseer because defects can originate from visual relationships, implementation structure, or incomplete evidence.

```text
Conductor detects UI-affecting change
-> Cloak performs static UI risk audit
-> Clockwork owns engineering correction; Ponytail implements when delegated
-> Cloak repeats static UI risk audit
-> Butler selects rendered-validation owner
-> Overseer validates technical and rendered evidence
-> Caveman enforces explicit stop-condition reporting in the handoff
-> Butler or maintainer performs final approval
```

Required boundary:
- Cloak identifies whether the UI is structurally at risk.
- Clockwork ensures that the UI is correctly engineered.
- Overseer proves that implementation claims match current technical and rendered evidence.

No single role may treat successful source inspection, implementation, or automated testing as independent proof of complete rendered correctness.

## Gate and Conflict Rules

- Dagger stays `BLOCKED_PENDING_AUTHORIZATION` until explicit authorization and guardrail validation exist.
- Governor human-review behavior is blocking.
- Arbiter `HOLD` and `BLOCKED` are blocking.
- No architecture, security, database, or governance task defaults directly to `ponytail`.
- Assign one owner per output and sequence dependencies instead of parallel policy conflicts.
- Use `dagger` only for guarded destructive-path work, never as default QA, security, DB, or UI reviewer.
- For ERDs, use `chronicler` for semantics and `weaver` for notation.

## Legacy Routing Aliases

| Legacy Key | Resolved Slug |
| --- | --- |
| `amalgam-conductor` | `conductor` |
| `cloak-meister` | `cloak` |
| `scribe-meister` | `scribe` |
| `clockwork-meister` | `clockwork` |
| `meister-chronicler` | `chronicler` |
| `acme-overseer` | `overseer` |
| `hidden-dagger` | `dagger` |
| `cipher-meister` | `cipher` |
| `meister-weaver` | `weaver` |
