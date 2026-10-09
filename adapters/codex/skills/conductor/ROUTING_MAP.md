# Orchestra Routing Map

Current routing authority: Conductor classifies every request and owns every specialist selection. This current policy supersedes conflicting legacy wording in frozen historical UIX guidance; frozen evidence remains byte-stable. `CLEAR_OWNERSHIP != CONDUCTOR_BYPASS`; `FAST_ROUTE != ROUTER_BYPASS`.
Conductor classifies every request and owns every specialist selection.
Load this file only when routing is ambiguous, cross-domain, or order-dependent.
After Conductor classification, do not load it for a clear single-owner fast route.

## Direct Route Rules

- Clear ownership yields a Conductor-selected direct single-specialist fast route.
- The fast route may omit this map, `the-tuner`, governance context, and multi-specialist ceremony when those are not triggered.
- A fast route is not a Conductor bypass; specialists cannot independently dispatch another specialist.
- Ambiguous ownership stays with `conductor`.
- Governance context stays out of ordinary low-risk work unless trigger exists.
- `REFERENCE_CONTEXT.md#governance-decision-protocol` does not load during initial route classification.
- `ROUTING_MAP.md` does not load after Conductor classification for clear single-owner tasks.
- Clear single-owner work may bypass `the-tuner`; a later material boundary crossing returns to `conductor` for Tuner activation.

## Delegated Phase Progression Routing

- Direct single-specialist fast routing remains available after Conductor classification for simple single-unit work outside delegated phases.
- Conductor is required when multiple approved units exist, transition dispositions must be consumed, or checkpoint/resume behavior is needed.
- Conductor loads the full envelope once and passes unit-specific deltas to specialists.
- Routing metadata does not create or expand authority.

## Canonical Routing Rules

| Task Type | Target Skill selected by Conductor | Condition |
| --- | --- | --- |
| Business alignment, scope, requirements, product intent, capacity envelope, acceptance criteria, SDLC sufficiency | `the-steward` | Governance alignment owner is clear |
| Legal, regulatory, privacy-obligation, IP, licensing governance | `the-governor` | Governance compliance owner is clear |
| Continuity, handoff, merge readiness, branch drift, source-of-truth conflict | `arbiter` | Continuation state is uncertain |
| Architecture, layering, service boundaries, complexity decisions, scale posture, refactor structure | `clockwork` | Technical architecture owner is clear |
| Technical security, authorization, secrets, privacy-control design | `cipher` | Technical security owner is clear |
| Database, schema, migration, ORM, persistence semantics | `chronicler` | Persistence owner is clear |
| Migration risk contract, production compatibility, locking, backfill, index and constraint migration semantics | `chronicler` | Migration planning or migration-risk assessment is requested; execution remains with `ponytail` |
| UI/UX, accessibility, responsive layout, interaction design | `cloak` | Frontend design owner is clear |
| QA strategy, validation evidence, release-readiness checks | `overseer` | Validation owner is clear |
| Documentation production and editing | `scribe` | Documentation execution owner is clear |
| Domain narrative, glossary, requirements, research/capstone, as-built documentation | `scribe` | Documentation and knowledge structuring; technical and governance decisions remain with their owning specialists |
| `SPEC_TO_SYSTEM`, `SYSTEM_TO_DOCS`, or `RECONCILE` | `scribe` -> only required specialists -> implementation/validation owners as applicable | Scribe leads the mode-specific narrative, reconstruction, or drift review without inventing intent or specialist-owned decisions |
| Diagram and model generation | `weaver` | Visual artifact owner is clear |
| Minimal implementation after design is ready | `ponytail` | Execution owner is clear and upstream design/governance are ready |
| Controlled destructive-path simulation | `dagger` | Explicit authorization and guardrail validation are present |
| Compliance Registry cache lifecycle and query operations | `conductor` -> deterministic `scripts/compliance_registry.py` | Explicit `/compliance-registry` command; Registry data remains evidence, not authority |
| Registry-backed governed compliance review | `conductor` | Explicit `/compliance-review` command; Governor applicability, Steward traceability, and Arbiter freshness/set-equality review are required |
| Broad, unclear, or overlapping requests | `conductor` | Ownership overlaps, dependencies exist, or route split is unclear |
| Cross-specialist contract coordination | `the-tuner` | Conductor has classified material multi-domain dependencies, governance-contract invalidation, missing ownership, contradiction, stale contract, or late boundary crossing |
| Frontend/backend synchronicity | `conductor` -> `the-tuner` | Frozen packet and authority exist |

## OR-GOV-5 Architecture Governance Intake

Use the canonical `ArchitectureGovernanceIntake` inside the existing Routing
Plan when a request may affect architecture, capacity, tenancy, persistence,
product intent, security, or validation. Load
[the architecture governance intake guide](https://github.com/Baelfyre/Orchestra/blob/main/skills/conductor/ARCHITECTURE_GOVERNANCE_INTAKE_GUIDE.md) only for that
material intake. Classify context, preserve unknown values, and compose the
smallest sufficient route.

- `architecture-governance-intake` -> `conductor` for the canonical classifier and route composition.
- `adaptive-capacity-routing` -> `conductor` when a decision-specific capacity dependency must be detected and routed.
- `route-composition` -> `conductor` when dependent specialist order must be selected.
- Product or strategic intent unresolved -> `the-steward`, then `clockwork` only when architecture is actually needed.
- Capacity measurement required -> `the-steward`, then `overseer`, then `clockwork` only when architecture follows.
- Confirmed persistence semantics -> `chronicler`, then `ponytail` after the persistence guidance is accepted.
- Security-sensitive implementation -> `cipher`, then `ponytail` after security requirements are ready.
- Validation or quantified sufficiency claim -> `overseer`; missing evidence remains `NOT_PROVEN` or the applicable missing-evidence state.
- Unknown production presence -> `chronicler` with `PRODUCTION_PRESENCE_UNRESOLVED`; never emit `production_data=false` from that uncertainty.

Keywords are contextual triggers, not decisions. OR-GOV-5 intake remains the
classifier. When a current Tuner session has declared governance-contract
dependencies, the Tuner compares consumed clauses, distinguishes identity-only
refresh from semantic invalidation, and returns the smallest re-entry
recommendation to Conductor. The Tuner never dispatches specialists.

## OR-GOV-6 Governance Contract Invalidation

- `ArchitectureGovernanceIntake` changes may make the collaboration composition stale and return routing to Conductor.
- `ProductIntentContract` and `CapacityEnvelope` affect only declared downstream architecture decisions and consumed dimensions.
- `ArchitectureComplexityDecision` affects Chronicler only when migration planning declares that dependency.
- `MigrationRiskContract` affects Overseer only when validation evidence consumes the changed migration clauses.
- Identity-only revision or hash changes refresh references without automatic domain re-entry.
- Cyclic invalidation edges are finite revalidation sets; sequence-cycle findings remain separate.
- The upstream trigger owner is not re-entered unless its own contract was explicitly invalidated by an implementation delta.

OR-GOV-6 does not implement OR-GOV-7 validation semantics or OR-GOV-8
specialist refinements.

The two compliance commands are explicit public commands. They must not rely on the unknown-command ambiguity fallback. `/compliance-registry` uses Conductor only as the command entry boundary and delegates data lifecycle work to the deterministic Registry script. `/compliance-review` follows the governed ordered sequence below; no role may treat Registry evidence as release, deployment, execution, or legal authority.

## Scribe SSU Routing Rules

- Existing-system, implemented-system, or current-capstone requests -> `scribe` in `SYSTEM_TO_DOCS` with only required evidence-verification specialists.
- Requirements, problem-to-specification, or approved-requirements requests -> `scribe` in `SPEC_TO_SYSTEM`, then the appropriate technical and implementation owners.
- Domain-model requests -> `scribe` for concept discovery; `weaver`, `clockwork`, or `chronicler` owns formal modeling as applicable.
- Documentation/code alignment -> `scribe` in `RECONCILE`; unresolved correction decisions return to the owning specialist or governance authority.

Do not route every documentation request through every specialist. Progressive disclosure and smallest-sufficient-specialist routing remain required.

## Ordered Multi-Skill Sequences

- `the-governor -> cipher -> ponytail` for governance-sensitive security implementation
- `the-steward -> clockwork` for unresolved product intent or decision-changing capacity before architecture
- `the-steward -> overseer -> clockwork` when capacity must be measured before architecture
- `clockwork -> ponytail` for architecture-first implementation
- `chronicler -> ponytail` for persistence guidance followed by bounded implementation
- `cipher -> ponytail` for security requirements followed by bounded implementation
- `chronicler -> overseer` for persistence semantics followed by migration or DB validation
- `chronicler -> ponytail -> overseer` for an accepted MigrationRiskContract that requires bounded implementation and validation
- `the-steward -> scribe` for required SDLC documentation shaped by business-alignment governance
- `the-governor -> scribe` for compliance documentation shaped by governance
- `scribe -> relevant technical specialists -> ponytail -> overseer -> scribe` for `SPEC_TO_SYSTEM` when implementation is actually authorized and the final artifact must become as-built documentation
- `scribe -> verification specialists as needed -> scribe` for `SYSTEM_TO_DOCS`; technical specialists verify their facts, Scribe owns the documented reconstruction
- `scribe -> conductor -> affected specialist or governance authority -> overseer as needed -> scribe` for `RECONCILE` when drift cannot be resolved by documentation correction alone
- `conductor -> the-governor -> the-steward -> arbiter` for Registry-backed governed compliance review
- `arbiter -> overseer` when validation evidence must be executed or refreshed before continuation
- `cloak -> clockwork -> ponytail` when frontend design changes API shape, data flow, or service boundaries
- `cloak -> cipher -> ponytail` when frontend design affects authorization, privacy, or destructive journeys
- `cloak -> clockwork -> ponytail -> cloak -> overseer` for UI-affecting implementation, correction, renewed static audit, and evidence validation
- `conductor -> the-tuner -> domain specialists -> the-tuner -> ponytail` for material multi-domain contract assembly before implementation
- `ponytail -> the-tuner -> overseer -> arbiter` for post-implementation delta reconciliation, evidence, and continuation review
- `the-tuner -> conductor -> affected specialists or human` when ownership is missing or specialist contracts contradict

The Tuner recommends routes but never invokes specialists directly. Conductor remains the exclusive router.

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
- `CROSS_LAYER_CONTRACT_INCOMPLETE`, `CROSS_SPECIALIST_CONTRADICTION_REVIEW_REQUIRED`, `CROSS_LAYER_CONTRACT_STALE`, and `SPECIALIST_REENTRY_REQUIRED` are blocking coordination states.
- `CROSS_LAYER_CONTRACT_READY` is readiness evidence only and does not create implementation authority.
- No architecture, security, database, or governance task defaults directly to `ponytail`.
- Assign one owner per output and sequence dependencies instead of parallel policy conflicts.
- Use `dagger` only for guarded destructive-path work, never as default QA, security, DB, or UI reviewer.
- For ERDs, use `chronicler` for semantics and `weaver` for notation.
- Scribe reconciliation may identify `DOC_DRIFT`, `IMPLEMENTATION_DRIFT`, `MISSING_EVIDENCE`, or `UNRESOLVED`, but those states do not grant code, policy, approval, validation, or release authority.

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
