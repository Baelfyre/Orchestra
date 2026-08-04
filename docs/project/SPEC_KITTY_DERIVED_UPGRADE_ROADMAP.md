# Spec Kitty Derived Upgrade Roadmap for Orchestra

> [!NOTE]
> **Design Status:** `DESIGN_COMPLETE`
> **Runtime Status:** `IMPLEMENTED_MERGED`
> **Release Status:** `NOT_RELEASED`
> **Merged PR:** `#208`
> **Merge Commit SHA:** `1e2992b94abe67a76c1e6ec0b98f8b712ae256e4`
> **Source Commit:** `8466727ebbbc01fcaf43575657c9b1b9553784d9` (`Priivacy-ai/spec-kitty` v3.2.6)

---

## 1. Document Overview

This roadmap documents the completed Candidate Phase 1 design specifications and the merged Phase 2 runtime contract implementation sequence for Orchestra-native adaptations derived from the Spec Kitty pattern review.

---

## 2. Phase Progression & Status

### Phase 0: Read-Only Baseline & Pattern Review (`DESIGN_COMPLETE`)
- [x] Conducted pattern review of `Priivacy-ai/spec-kitty` v3.2.6 (`8466727ebbbc01fcaf43575657c9b1b9553784d9`).
- [x] Reconfirmed clean canonical baseline at commit `317c9449b2c6d264d0e826f229808439f1549ceb`.
- [x] Produced promotion records `PROM-SPEC-KITTY-001` through `005`.

### Phase 1A / 1A.1: Contract Ownership & Placement (`DESIGN_COMPLETE`)
- [x] Established single canonical owners in `docs/project/SPEC_KITTY_DERIVED_CONTRACT_OWNERSHIP.md`.
- [x] Clockwork: `OrchestraRuntimeEnvelope`
- [x] Chronicler: `OrchestraCorrelationID`
- [x] Overseer: `OrchestraPhaseRetrospective`
- [x] The Steward: `OrchestraUnitRecord extension`

### Phase 1B / 1B.1: OrchestraRuntimeEnvelope Schema Specification (`DESIGN_COMPLETE`)
- [x] Produced specification in `docs/project/ORCHESTRA_RUNTIME_ENVELOPE.md`.
- [x] Standardized standalone UTF-8 JSON payload (`json:orchestra-envelope`) across 3 discriminated variants (`execution_result`, `transition_decision`, `audit_event`).

### Phase 1C / 1C.1: OrchestraCorrelationID Protocol Specification (`DESIGN_COMPLETE`)
- [x] Produced specification in `docs/governance/CORRELATION_ID_PROTOCOL.md`.
- [x] Established RFC 9562 UUIDv7 wire format with 0 PyPI dependencies authorized.

### Phase 1D / 1D.1: OrchestraPhaseRetrospective Protocol Specification (`DESIGN_COMPLETE`)
- [x] Produced specification in `docs/governance/PHASE_RETROSPECTIVE_PROTOCOL.md`.
- [x] Standardized 16-field closeout evidence artifact (`replacement_effect: none`) with `MIXED_RETENTION_MODEL`.

### Phase 1E / 1E.1 / 1E.2: OrchestraUnitRecord Schema Extension Specification (`DESIGN_COMPLETE`)
- [x] Produced specification in `docs/project/ORCHESTRA_UNIT_RECORD_EXTENSION.md`.
- [x] Standardized 15-field JSON schema extension embedded inside `ApprovedUnitPlan` with canonical `scope_ref` and predecessor acceptance rules.

### Phase 1F: Cross-Document Synchronization & Final Design Roadmap (`DESIGN_COMPLETE`)
- [x] Synchronized decision log (`DECISION_LOG.md`), changelog (`CHANGELOG.md`), roadmap (`docs/project/ROADMAP.md`), ownership matrix (`docs/project/SPEC_KITTY_DERIVED_CONTRACT_OWNERSHIP.md`), and upgrade roadmap (`docs/project/SPEC_KITTY_DERIVED_UPGRADE_ROADMAP.md`).
- [x] Produced final Phase 1F handoff report `docs/artificer/external-sources/SPEC_KITTY_PHASE_1F_HANDOFF.md`.

### Phase 2A through 2G: Governed Phase Execution Contracts (`IMPLEMENTED_MERGED`)
- [x] Phase 2A: Implementation baseline, compatibility matrix, migration plan, and test plan defined.
- [x] Phase 2B: `OrchestraRuntimeEnvelope` runtime model, serializer, parser, and Codex/Antigravity adapter integration implemented.
- [x] Phase 2C: `OrchestraCorrelationID` zero-dependency RFC 9562 UUIDv7 generator, root generation, and child propagation implemented.
- [x] Phase 2D: `OrchestraPhaseRetrospective` typed model and deterministic builder implemented.
- [x] Phase 2E: `ApprovedUnitPlan` 15-field extension, schema validation, and contextual validator implemented.
- [x] Phase 2F: Consolidated behavior, governance, security, packaging, documentation, and backward-compatibility validation completed.
- [x] Phase 2G: Maintainer review, commit, push, remote verification, and PR #208 merge completed at `1e2992b94abe67a76c1e6ec0b98f8b712ae256e4`.

### Phase 3A: Deferred-Capability Selection & Design Baseline (`DESIGN_COMPLETE`)
- [x] Phase 3A: Read-only capability selection, ownership, architecture, compatibility, security, and implementation planning completed (`docs/project/SPEC_KITTY_DERIVED_PHASE_3_CAPABILITY_ASSESSMENT.md`).
- [x] Produced design specifications `docs/project/ORCHESTRA_STATUS_PROJECTION.md` and `docs/project/ORCHESTRA_WORKTREE_CONTRACT.md`.
- [x] Produced implementation plan `docs/project/SPEC_KITTY_DERIVED_PHASE_3_IMPLEMENTATION_PLAN.md` and matrix `docs/project/SPEC_KITTY_DERIVED_PHASE_3_COMPATIBILITY_AND_SECURITY_MATRIX.md`.

---

## 3. Dispositions & Implementation Summary

### Accepted & Merged Implemented Contracts
1. `OrchestraRuntimeEnvelope`: Non-authorizing JSON result serialization profile with discriminated variants (`execution_result`, `transition_decision`, `audit_event`).
2. `OrchestraCorrelationID`: Project-owned zero-dependency RFC 9562 UUIDv7 correlation generator and child propagation.
3. `OrchestraPhaseRetrospective`: Source-backed phase closeout evidence model and deterministic builder.
4. `ApprovedUnitPlan extension`: 15-field schema extension and contextual validator.

### Promoted Candidate Phase 3 Designs
1. `OrchestraStatusProjection`: Read-only status summary & JSON schema (`docs/project/ORCHESTRA_STATUS_PROJECTION.md`). Canonical owner: Scribe. Target for Phase 3B.
2. `OrchestraWorktreeContract`: Optional host worktree negotiation contract (`docs/project/ORCHESTRA_WORKTREE_CONTRACT.md`). Canonical owner: Ponytail. Target for Phase 3C.

### Rejected Concepts (Remains Rejected)
- Standalone mutable unit-state files (`.orchestra/units/`).
- Manual doctrine packs duplicating `docs/governance/`.
- Workflow-state merge authority or automatic policy mutation.
- Spec Kitty runtime dependency or copying Spec Kitty code/schemas.
- SQLite event stores, RPC network services, background daemons, web dashboards.

### Explicitly Deferred Concepts
- Cross-session correlation restoration and durable correlation persistence.
- Retry, wait, resume, remediation, and escalation continuation engines.
- Automatic retrospective phase-closeout generation and durable retention enforcement.
- Automatic Steward planning/dispatch integration and revision-history ordering integration.
- Automatic policy activation (`docs/governance/DELEGATED_EXECUTION_POLICY.md` Section 4 remains unamended).

---

## 4. Planned Candidate Phase 3 Sequence (`DESIGN_COMPLETE` / `IMPLEMENTATION_NOT_STARTED`)

- **Phase 3A:** Read-only capability selection, ownership, architecture, compatibility, security, and implementation planning (`DESIGN_COMPLETE`).
- **Phase 3B:** `OrchestraStatusProjection` model, JSON serializer, CLI renderer, and unit tests.
- **Phase 3C:** `OrchestraWorktreeContract` model, path confinement validator, base SHA checker, and unit tests.
- **Phase 3D:** Consolidated cross-platform, behavior, governance, security, and compatibility validation.
- **Phase 3E:** Maintainer review, commit authorization, push authorization, remote verification, and PR merge.

Phase 3A design and planning only; runtime not implemented; not released; no policy activation.
