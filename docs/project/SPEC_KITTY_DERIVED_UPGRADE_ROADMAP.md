# Spec Kitty Derived Upgrade Roadmap for Orchestra

> [!NOTE]
> **Design Status:** `DESIGN_COMPLETE`
> **Runtime Status:** `NOT_IMPLEMENTED` | `NOT_RELEASED`
> **Source Commit:** `8466727ebbbc01fcaf43575657c9b1b9553784d9` (`Priivacy-ai/spec-kitty` v3.2.6)
> **Base Commit SHA:** `317c9449b2c6d264d0e826f229808439f1549ceb`

---

## 1. Document Overview

This roadmap documents the completed Candidate Phase 1 design specifications and outlines the proposed Phase 2 implementation sequence for Orchestra-native adaptations derived from the Spec Kitty pattern review.

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

---

## 3. Dispositions Summary

### Accepted Design Specifications
1. `OrchestraRuntimeEnvelope`: Non-authorizing JSON result serialization profile.
2. `OrchestraCorrelationID`: Optional RFC 9562 UUIDv7 correlation header.
3. `OrchestraPhaseRetrospective`: Source-backed phase closeout evidence artifact.
4. `OrchestraUnitRecord extension`: Embedded `ApprovedUnitPlan` machine-readable schema extension.

### Rejected Concepts
- Standalone mutable unit-state files (`.orchestra/units/`).
- Manual doctrine packs duplicating `docs/governance/`.
- Workflow-state merge authority or automatic policy mutation.
- Spec Kitty runtime dependency or copying Spec Kitty code/schemas.

### Deferred Concepts
- `OrchestraWorktreeContract` & `OrchestraStatusProjection`.
- UUIDv7 generator implementation strategy.
- Retrospective template & generator implementation.
- Runtime envelope serializer and parser.
- Normative policy integration (`DELEGATED_EXECUTION_POLICY.md` Section 4).

---

## 4. Planned Phase 2 Implementation Sequence (`IMPLEMENTATION_NOT_STARTED`)

- **Phase 2A:** Implementation baseline, compatibility matrix, migration plan, and test plan definition.
- **Phase 2B:** `OrchestraRuntimeEnvelope` runtime model, serializer, parser, and adapter compatibility tests.
- **Phase 2C:** `OrchestraCorrelationID` UUIDv7 implementation strategy decision, generator validation, propagation, persistence, and mixed-version tests.
- **Phase 2D:** `OrchestraPhaseRetrospective` model, generation boundary, validation, restricted-retention handling, and closeout integration.
- **Phase 2E:** `OrchestraUnitRecord` extension integration, policy amendment (`DELEGATED_EXECUTION_POLICY.md` Section 4), schema validation, routing consumption, migration, and stale-revision tests.
- **Phase 2F:** Consolidated behavior, governance, security, packaging, documentation, and backward-compatibility validation.
- **Phase 2G:** Maintainer implementation review, commit authorization, post-commit validation, push authorization, and remote verification.
