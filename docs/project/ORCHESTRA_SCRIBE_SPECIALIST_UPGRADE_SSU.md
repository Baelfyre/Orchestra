# Orchestra Scribe Specialist Upgrade (SSU)

Status: `SSU_IMPLEMENTATION_CANDIDATE`

Canonical source baseline: `422f01dbe0df9707e27519be5ff059feb463735b`

Canonical source tree: `e7dd10d2a37ce2a75141572077bea77fe05db474`

AR state at SSU entry: AR-2 technical residual closeout is canonical and post-merge qualified; AR-3 is not started. SSU is a specialist-capability workstream and does not start AR-3.

## Purpose

Upgrade the existing Scribe specialist from primarily system/evidence-to-documentation work into a broader documentation and knowledge-traceability capability while preserving all existing specialist boundaries.

The conceptual advanced role is:

**Documentation, Domain Narrative, and Knowledge Traceability Specialist**

This is an enhancement of the existing Scribe, not a replacement specialist and not an authority expansion into architecture, persistence, formal modeling, security, QA, UI/UX, implementation, governance, or empirical research results.

## Existing Capability Preserved

SSU preserves Scribe's existing support for:

- README and setup documentation;
- technical summaries;
- changelogs and release notes;
- SDLC and project documentation;
- architecture, database, security, QA, and UI documentation based on facts established by their owning specialists;
- source-backed documentation and evidence mapping;
- claim verification;
- requirements documentation;
- decision logs;
- API/versioned documentation;
- documentation audits;
- known-issues records;
- final submission and handoff packaging.

## New Documentation Directions

SSU introduces three explicit lifecycle-aware documentation directions independent from Scribe's existing Mode 1/2/3 output-length modes.

### `SPEC_TO_SYSTEM`

Structured intent, domain narrative, requirements, and traceability guide later engineering. Scribe does not make the technical decisions that realize the specification.

### `SYSTEM_TO_DOCS`

Existing implementation, configuration, tests, schemas, UI, Git history, and runtime evidence are used to reconstruct an evidence-backed as-built record. Historical intent is not inferred as fact from code alone.

### `RECONCILE`

Scribe compares intent, specification, implementation, validation, and documentation/research claims. Differences are classified and routed rather than silently normalized.

## New Progressive-Disclosure Guides

SSU adds:

- `skills/scribe/DOMAIN_NARRATIVE_MODELING_GUIDE.md`
- `skills/scribe/REQUIREMENTS_TRACEABILITY_GUIDE.md`
- `skills/scribe/RESEARCH_CAPSTONE_DOCUMENTATION_GUIDE.md`
- `skills/scribe/DOCUMENTATION_SYSTEM_RECONCILIATION_GUIDE.md`

Equivalent portable Scribe references are mirrored under `adapters/codex/skills/scribe/`.

### Domain Narrative

Scribe can document context, vocabulary, stakeholders, actors, business rules, processes, events, states, assumptions, constraints, scope boundaries, external systems, and candidate concepts.

Candidate concept discovery remains non-authoritative. Noun extraction is only a discovery heuristic and cannot independently establish classes, aggregates, tables, services, components, or persistence entities.

### Requirements Traceability

Scribe can maintain stable requirement records and bidirectional links among problem/objective, requirement, design/model, implementation, verification/evaluation, evidence, and documented claim where those links exist.

Traceability may use `NOT_APPLICABLE` instead of fabricating relationships.

### Research and Capstone Documentation

Scribe can map a semantic research/project record into the actual institution, course, adviser, panel, journal, or research-office structure without hardcoding a universal Chapter 1 to Chapter 5 template.

Supported development/research orders include plan-first, prototype-first, existing-system, and continuous-development workflows.

Implementation evidence never becomes empirical evidence of effectiveness by implication. Results and conclusions require actual qualifying evidence.

### Documentation-System Reconciliation

Scribe can identify and explicitly report conditions including:

- `DOC_DRIFT`;
- `IMPLEMENTATION_DRIFT`;
- `MISSING_DOCUMENTATION`;
- `UNDOCUMENTED_IMPLEMENTATION`;
- `ORPHANED_REQUIREMENT`;
- `UNSUPPORTED_CLAIM` / `MISSING_EVIDENCE`;
- `OBSOLETE_MODEL` / `SUPERSEDED_REFERENCE`;
- `VALIDATION_GAP`;
- `STALE_OR_UNSUPPORTED_RESEARCH_CLAIM`;
- `UNRESOLVED` evidence conflict.

A drift classification does not itself decide which side must change. The underlying technical or governance truth remains with the owning specialist or authority.

## Specialist Boundaries

SSU preserves these ownership rules:

- Scribe: documented domain narrative, terminology, requirements prose, research narrative, traceability, evidence-backed technical explanation, as-built documentation, and documentation reconciliation.
- Clockwork: architecture, service/module boundaries, architectural constraints, and architecture decisions.
- Chronicler: data/persistence semantics, schemas, storage structures, normalization, and migration decisions.
- Weaver: formal UML, ERD, visual models, and diagram/model consistency.
- Overseer: QA strategy, verification/validation evidence, and QA conclusions.
- Cipher: security/privacy technical decisions and controls.
- Cloak: UX/UI and interface-behavior decisions.
- The Steward / The Governor: their existing governance domains.
- Ponytail or the appropriate implementation specialist: source-code implementation.
- Conductor: routing and sequencing when ownership is ambiguous or multi-specialist.

Scribe converts established facts into coherent documentation. It does not re-own those facts.

## Routing Integration

`ROUTING_MAP.md` and its Codex portable projection gain bounded lifecycle-documentation guidance for:

- requirements before build;
- problem statement to structured system specification;
- domain narrative before formal technical modeling;
- existing-system documentation;
- capstone/research updates from current implementation;
- documentation-to-code/system reconciliation;
- approved-requirement traceability through implementation and validation.

Ordinary documentation editing remains a direct Scribe route. SSU does not route every documentation task through every specialist.

## Output and Audit Enhancements

`OUTPUT_TEMPLATES.md` adds adaptable structures for:

- Domain Narrative;
- Requirements Traceability Matrix;
- As-Built System Reconstruction;
- Documentation Reconciliation Report;
- Research-to-System Traceability;
- Capstone Evidence Map;
- Documentation Drift Report.

`AUDIT_CHECKLIST.md` adds checks for domain-concept authority boundaries, bidirectional traceability, lifecycle-state discipline, documentation/system drift, institutional-template authority, research evidence ceilings, and empirical-claim discipline.

## Provenance and Copyright Boundary

Two MMDC academic materials supplied during SSU planning were treated as informative pattern references only. No course-specific wording, protected template content, or original instructional text from those materials is copied into Orchestra.

The generalized patterns were synthesized into original Orchestra guidance and cross-checked conceptually against public/authoritative reference families:

- ISO/IEC/IEEE 29148 for requirements engineering and requirements information principles;
- ISO/IEC/IEEE 15289 for lifecycle information/documentation principles;
- ISO/IEC/IEEE 42010 for architecture-description concepts and the distinction between architecture and its documentation;
- OMG UML for formal modeling terminology;
- NASA systems/software engineering guidance for requirements flowdown, verification matrices, and bidirectional traceability;
- APA Journal Article Reporting Standards for quantitative, qualitative, and mixed-method reporting guidance where applicable;
- ACM artifact-evaluation/reproducibility guidance for computing-research artifact documentation.

SSU does not reproduce substantial copyrighted text from those sources. Institution-specific requirements remain authoritative for a submission.

## Validation Surface

Targeted SSU regression coverage is added at `tests/runtime/test_scribe_ssu.py` and verifies:

- progressive disclosure to all four new guides;
- explicit `SPEC_TO_SYSTEM`, `SYSTEM_TO_DOCS`, and `RECONCILE` support;
- Scribe technical-authority boundaries;
- exact source/Codex guide parity;
- exact source/Codex template and audit-checklist parity;
- normalized source/Codex `SKILL.md` body parity with Codex-simple frontmatter;
- examples for all three documentation directions;
- institutional-template authority and evidence ceilings;
- documentation versus implementation drift distinctions;
- lifecycle-documentation routing without authority expansion.

Existing repository validation and protected CI remain required before canonicalization.

## Acceptance Criteria Mapping

SSU is ready for canonicalization only when the exact candidate head demonstrates all of the following:

1. planning documentation before implementation via `SPEC_TO_SYSTEM`;
2. evidence-backed documentation reconstruction via `SYSTEM_TO_DOCS`;
3. continuous reconciliation via `RECONCILE`;
4. domain narrative without architecture/persistence/formal-model authority transfer;
5. research/capstone documentation without invented evidence or results;
6. requirements traceability;
7. implementation traceability;
8. validation traceability;
9. research-claim traceability;
10. institution-specific mapping without one hardcoded academic template;
11. explicit specialist handoff for technical modeling or disputed facts;
12. explicit documentation-drift reporting;
13. no regression in existing Scribe documentation capabilities;
14. source/Codex portable documentation parity for the changed Scribe surfaces;
15. all applicable protected repository checks pass on the exact canonicalization candidate and on resulting canonical main.

## Non-Goals and Authority

SSU does not:

- start AR-3;
- modify runtime architecture or provider/MCP behavior;
- make Scribe an architecture, persistence, UML, security, QA, UI, governance, or implementation authority;
- invent research evidence or validate research conclusions;
- publish a release or tag;
- deploy or mutate production;
- activate policy or modify repository rulesets;
- refresh installed integrations;
- delete branches;
- force push or rewrite history.

Validation, mergeability, specialist capability, and documentation state do not independently grant any protected-action authority.
