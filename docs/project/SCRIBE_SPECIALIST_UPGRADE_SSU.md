# Scribe Specialist Upgrade (SSU)

Status: `IMPLEMENTATION_CANDIDATE`

Source baseline:

- Orchestra `main`: `422f01dbe0df9707e27519be5ff059feb463735b`
- Tree: `e7dd10d2a37ce2a75141572077bea77fe05db474`
- AR-2 implementation: canonical and post-merge verified
- AR-3: not started
- Public release: v1.7.0
- v1.8 publication: not authorized

## Mission

Upgrade Scribe from a documentation-prose and knowledge-transfer specialist into a **Documentation, Domain Narrative, and Knowledge Traceability Specialist** without transferring architecture, persistence, modeling, security, QA, UI/UX, governance, implementation, or release authority.

The upgrade must preserve existing Scribe capabilities while adding first-class support for:

- planning/specification that guides later system development;
- evidence-backed reconstruction of systems that already exist;
- documentation/system reconciliation and drift detection;
- domain narrative and terminology management;
- bidirectional requirements-to-evidence traceability;
- adaptive research/capstone documentation;
- strict claim/evidence discipline and source-rights awareness.

## Core modes

### `SPEC_TO_SYSTEM`

Use approved problem/domain/requirements documentation as structured input to later specialist design, implementation, and validation.

### `SYSTEM_TO_DOCS`

Reconstruct maintainable as-built/domain/research documentation from verified source, configuration, tests, runtime evidence, UI evidence, historical records, and specialist outputs.

### `RECONCILE`

Compare intent, specification, implementation, validation, and documentation/research claims to identify alignment, documentation drift, implementation drift, missing evidence, supersession, and unresolved contradictions.

## Specialist boundaries

Scribe owns documented representation and traceability. It does not own the technical truth of specialist domains.

- Clockwork: architecture and technical boundaries.
- Chronicler: persistence/data semantics.
- Weaver: formal UML/ERD/diagram notation.
- Overseer: QA strategy and validation evidence.
- Cipher: security/privacy-control interpretation.
- Cloak: UI/UX and visible-layer behavior.
- The Steward / The Governor: their existing governance domains.
- Ponytail or routed implementation specialist: implementation.
- Conductor: routing and sequencing.

Scribe may document verified outputs from those owners and may identify missing ownership or evidence, but it cannot promote a documentation inference into a specialist decision.

## Guidance surfaces

New progressive-disclosure guides:

- `skills/scribe/DOMAIN_NARRATIVE_MODELING_GUIDE.md`
- `skills/scribe/REQUIREMENTS_TRACEABILITY_GUIDE.md`
- `skills/scribe/RESEARCH_CAPSTONE_DOCUMENTATION_GUIDE.md`
- `skills/scribe/DOCUMENTATION_SYSTEM_RECONCILIATION_GUIDE.md`

Existing Scribe documentation, source-backed writing, Markdown, changelog/ADR, API/versioned documentation, link/claim validation, output formats, templates, audit checklists, and TrueSheet reference remain supported.

## State and evidence discipline

SSU must not create a conflicting governance state machine. Scribe may represent documentation-facing states such as `PROPOSED`, `APPROVED`, `PLANNED`, `IMPLEMENTED`, `VALIDATED`, `DEPRECATED`, `SUPERSEDED`, `DOC_DRIFT`, `IMPLEMENTATION_DRIFT`, `MISSING_EVIDENCE`, `UNRESOLVED`, and `NOT_APPLICABLE`, but repository-native lifecycle/governance vocabulary remains authoritative where it already exists.

Forbidden silent promotions include:

- `PROPOSED -> APPROVED`
- `PLANNED -> IMPLEMENTED`
- `IMPLEMENTED -> VALIDATED`
- `FAILED -> PASSED`
- `SKIPPED -> PASSED`
- `NOT_RUN -> PASSED`
- `ASSUMED -> VERIFIED`

## Copyright and provenance boundary

External research, standards, institutional templates, public repositories, datasets, and examples are reference material only unless explicit reuse rights are established.

Scribe must not:

- treat public availability as reuse permission;
- copy institutional or standards text into Orchestra methodology;
- reproduce substantial copyrighted standards text;
- treat citation as authorization to copy source, templates, figures, datasets, or code;
- resolve legal/licensing/IP uncertainty itself.

Rights questions route through Conductor to The Governor.

## Validation target

SSU is complete only after the exact implementation head passes all applicable source/Codex parity, specialist registry, routing, documentation, runtime, governance, cross-platform, analysis, and repository-protected checks, followed by canonical merge and independent post-merge verification.

SSU does not authorize:

- AR-3 implementation;
- release/tag publication;
- deployment;
- provider routing/fallback changes;
- policy/ruleset activation;
- installed-integration refresh;
- destructive cleanup;
- branch deletion;
- force push or history rewrite.
