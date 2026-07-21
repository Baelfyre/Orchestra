# Skill Index

## Purpose

Canonical lightweight router lookup for Orchestra. Conductor consults this index first, before loading specialist skills.

## Router Usage

Do not load individual `SKILL.md` files during initial classification unless that specialist will execute or a governance trigger requires deeper review.

## Execution Modes

- **Ideation**: brainstorming, no code edits
- **Prototype**: experimental local work
- **Implementation**: standard development
- **Audit**: read-only formal review
- **Release**: deployment or public artifacts

## Risk Levels

- **Low**: formatting, simple docs, safe UI tweaks
- **Medium**: normal implementation, refactors, ordinary validation
- **High**: auth, security, persistence, compliance-sensitive changes
- **Extreme**: destructive-path or production-impacting work

## Progression Modes

- **DIRECT**: single specialist execution outside delegated phases
- **MANUAL**: standard pause-and-confirm execution
- **DELEGATED**: autonomous phase execution inside a human-authorized envelope
- **LEGACY_FALLBACK**: manual fail-closed pause for unsupported hosts or missing dispositions


## Skill Lookup Table

| Skill | Canonical Purpose | Precise Triggers | Avoid When | Governance vs Execution | Context Dependencies | Output Formats |
| --- | --- | --- | --- | --- | --- | --- |
| `the-steward` | Business alignment, scope, requirements, SDLC sufficiency | roadmap fit, acceptance criteria, scope boundary, required SDLC artifact sufficiency | legal, licensing, privacy-obligation, IP review | Governance decision owner | `docs/governance/GOVERNANCE_LAYER.md` | Governance Review |
| `the-governor` | Legal, regulatory, privacy-obligation, IP, licensing governance | privacy policy impact, ToS impact, license compatibility, IP clearance, compliance obligations | business alignment or scope review | Governance decision owner | `docs/governance/GOVERNANCE_LAYER.md` | Governance Review |
| `arbiter` | Continuity, source-of-truth, branch, handoff, merge-readiness | handoff readiness, branch uncertainty, merge readiness, missing validation evidence, continuation state conflict | normal implementation or normal QA execution | Continuity owner | git status, diffs, validation outputs | Continuity Review,Governance Effectiveness Review |
| `conductor` | Routing and sequencing | ambiguous ownership, cross-domain sequencing, access-routing split, workflow orchestration | one obvious specialist owns full task | Routing owner | `SKILL_INDEX.md`; `ROUTING_MAP.md` only for ambiguity | Routing Plan,Prompts |
| `clockwork` | Architecture, layering, service boundaries, refactor structure | architecture redesign, layering drift, service boundary change, refactor strategy | straightforward code edit already designed | Technical review owner | none by default | Compact,Full |
| `cipher` | Technical security and privacy-control review | authorization model, secrets handling, RBAC, threat exposure, privacy-control design | legal/privacy-obligation governance or offensive testing | Technical review owner | security-sensitive slice only | Caveman,Full Security Review |
| `cloak` | UI/UX, accessibility, responsive layout, interaction design | accessibility remediation, layout design, user-flow clarity, responsive behavior | backend logic, DB design, security policy | Technical review owner | frontend slice only | QUICK_UI_HANDOFF,DOCUMENT_REVIEW,FORMAL_UI_AUDIT |
| `chronicler` | Database and persistence semantics | migration semantics, schema design, ORM behavior, data integrity, normalization | UI review or general QA | Technical review owner | persistence slice only | Caveman,Normalization Output |
| `overseer` | QA strategy, validation evidence, release readiness | test strategy, validation plan, CI readiness, regression evidence, release validation | architecture design or destructive testing | Validation owner | test and validation evidence | Caveman,Full QA Review,Delegated Unit Evidence |
| `dagger` | Guarded destructive-path and resilience simulation | chaos simulation, guarded negative-path validation, resilience stress path | routine QA, security policy, implementation | Guarded execution specialist | `scripts/dagger_guardrail.py` | Caveman |
| `weaver` | Diagrams and visual models | UML, ERD, Mermaid, PlantUML, workflow visualization | code implementation or policy review | Technical artifact owner | diagram target domain only | Mermaid,PlantUML |
| `scribe` | Documentation production and editing | README rewrite, changelog prose, docs cleanup, source-backed narrative | business alignment decisions or architecture ownership | Execution owner for docs | source material only | Mode 1,Mode 2,Mode 3 |
| `ponytail` | Implementation after design is ready | scoped code edit, bug fix with known owner, minimal safe implementation | architecture, security, DB, governance, or ambiguous ownership | Execution owner | active file slice plus routed specialist guidance | IMPLEMENTATION_PLAN,CODE_REVIEW,QUICK_FIX |

## Avoid-When Notes

- **the-steward**: avoid for legal, regulatory, privacy-obligation, licensing, or IP review
- **the-governor**: avoid for business alignment or scope review
- **arbiter**: avoid for feature implementation, architecture design, or replacing normal QA
- **conductor**: avoid when single obvious specialist suffices
- **cipher**: avoid for offensive or destructive testing
- **cloak**: avoid for backend logic, persistence, or security policy
- **dagger**: avoid for ordinary QA, implementation, or production execution
- **chronicler**: avoid for UI or general QA
- **overseer**: avoid for architecture ownership or destructive testing
- **weaver**: avoid for code implementation or policy review
- **scribe**: avoid for architecture, database, or governance decisions
- **clockwork**: avoid for layout tweaks or documentation writing
- **ponytail**: avoid for architecture, UI/UX decisions, security policy, database semantics, or governance

## Canonical References

- [Governance Layer](docs/governance/GOVERNANCE_LAYER.md)
- [Routing Map](ROUTING_MAP.md)
