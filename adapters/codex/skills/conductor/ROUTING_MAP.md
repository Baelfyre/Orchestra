# Orchestra Routing Map

Load this file only when routing is ambiguous, cross-domain, or order-dependent.
Do not load it for obvious single-owner work.

## Direct Route Rules

- Obvious single-owner work routes directly to owner.
- Ambiguous ownership stays with `conductor`.
- Governance context stays out of ordinary low-risk work unless trigger exists.
- `REFERENCE_CONTEXT.md#governance-decision-protocol` does not load during initial route classification.
- `ROUTING_MAP.md` does not load for obvious single-owner tasks.
- Obvious single-owner work bypasses `the-tuner`; a later material boundary crossing returns to `conductor` for Tuner activation.

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
| Domain narrative, glossary, requirements prose, traceability, research/capstone documentation | `scribe` | Scribe is structuring documented knowledge and not deciding architecture, persistence, formal models, security, UI, implementation, or QA truth |
| Existing-system as-built documentation | `scribe` + only required verification specialists | `SYSTEM_TO_DOCS`; technical facts are verified by their owning specialists where repository evidence alone is insufficient |
| Documentation/system drift reconciliation | `scribe` + affected owner(s) | `RECONCILE`; Scribe classifies drift and the owning specialist resolves disputed technical truth |
| Diagram and model generation | `weaver` | Visual artifact owner is clear |
| Minimal implementation after design is ready | `ponytail` | Execution owner is clear and upstream design/governance are ready |
| Controlled destructive-path simulation | `dagger` | Explicit authorization and guardrail validation are present |
| Compliance Registry cache lifecycle and query operations | `conductor` -> deterministic `scripts/compliance_registry.py` | Explicit `/compliance-registry` command; Registry data remains evidence, not authority |
| Registry-backed governed compliance review | `conductor` | Explicit `/compliance-review` command; Governor applicability, Steward traceability, and Arbiter freshness/set-equality review are required |
| Broad, unclear, or overlapping requests | `conductor` | Ownership overlaps, dependencies exist, or route split is unclear |
| Cross-specialist contract coordination | `the-tuner` | Conductor has classified material multi-domain dependencies, missing ownership, contradiction, stale contract, or late boundary crossing |
| Frontend/backend synchronicity | `conductor` -> `the-tuner` | Frozen packet and authority exist |

The two compliance commands are explicit public commands. They must not rely on the unknown-command ambiguity fallback. `/compliance-registry` uses Conductor only as the command entry boundary and delegates data lifecycle work to the deterministic Registry script. `/compliance-review` follows the governed ordered sequence below; no role may treat Registry evidence as release, deployment, execution, or legal authority.

## Scribe Lifecycle Documentation Routing

Use these patterns only when the documentation task needs lifecycle-aware sequencing. Ordinary documentation editing still routes directly to Scribe.

- **Create requirements before build**: Scribe structures problem context, domain narrative, requirements prose, and traceability (`SPEC_TO_SYSTEM`), then Conductor routes technical decisions to the minimum required specialist set.
- **Turn a problem statement into a system specification**: Scribe leads knowledge structuring; The Steward participates when business scope, requirement approval, or acceptance-governance decisions are required.
- **Create a domain model**: Scribe may produce domain narrative and candidate concept discovery. Formal UML/model decisions route to Weaver; architecture decisions to Clockwork; persistence/entity-storage decisions to Chronicler.
- **Document an existing system**: Scribe uses `SYSTEM_TO_DOCS` and repository evidence, calling only the specialists required to verify disputed architecture, persistence, security, UI, modeling, or validation facts.
- **Update research/capstone documentation from current implementation**: Scribe reconstructs only evidence-supported implementation and validation state, then maps it into the institution's actual required structure. Empirical results are never inferred from implementation alone.
- **Check whether documentation matches code/system state**: Scribe uses `RECONCILE`, classifies `DOC_DRIFT`, `IMPLEMENTATION_DRIFT`, missing evidence, unsupported claims, or other gaps, then routes the disputed truth to the owning specialist before correction.
- **Use approved requirements to guide implementation**: Scribe maintains requirement and evidence traceability; Conductor routes actual technical decisions and implementation to their owners.

Documentation routing does not make Scribe the authority for architecture, persistence, formal models, security, UI, QA, governance, or implementation.

## Ordered Multi-Skill Sequences

- `the-governor -> cipher -> ponytail` for governance-sensitive security implementation
- `clockwork -> ponytail` for architecture-first implementation
- `chronicler -> overseer` for persistence semantics followed by migration or DB validation
- `the-steward -> scribe` for required SDLC documentation shaped by business-alignment governance
- `the-governor -> scribe` for compliance documentation shaped by governance
- `scribe -> conductor -> relevant technical owners -> implementation owner -> overseer -> scribe` for `SPEC_TO_SYSTEM` work where structured requirements guide implementation and Scribe updates the as-built/evidence record afterward
- `conductor -> relevant verification owners -> scribe` for `SYSTEM_TO_DOCS` when existing implementation needs disputed technical facts verified before reconstruction
- `scribe -> affected owner(s) -> scribe` for `RECONCILE` when documentation and system evidence conflict
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
