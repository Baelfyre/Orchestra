# Spec Kitty Derived Upgrade Roadmap for Orchestra

> [!NOTE]
> **Design Status:** `DESIGN_COMPLETE`
> **Runtime Status:** `IMPLEMENTED_MERGED`
> **Release Status:** `NOT_RELEASED`
> **Merged PR (Phase 2):** `#208`
> **Merge Commit SHA (Phase 2):** `1e2992b94abe67a76c1e6ec0b98f8b712ae256e4`
> **Merged PR (Phase 3A):** `#210`
> **Reviewed Head (Phase 3A):** `3d8b14aaffa00d66d1faaaef55ec27ecbc10cdc3`
> **Merge Commit SHA (Phase 3A):** `1629eaf3cd3f156f8913f84c9229666257a3145a`
> **Merged PR (Phase 3B):** `#212`
> **Reviewed Head (Phase 3B):** `2a6c7ea8db16ce73d66fae566672f3681094b0f7`
> **Merge Commit SHA (Phase 3B):** `fa1e052d82301e70a5869258c3fc6af765163353`
> **Merged PR (Phase 3C-3E):** `#214`
> **Reviewed Head (Phase 3C-3E):** `646111325e6de7c5d31915789fdc22a644125b7b`
> **Merge Commit SHA (Phase 3C-3E):** `6bce297c7469f9c08ce41308cbb993cc863ac540`
> **Source Commit:** `8466727ebbbc01fcaf43575657c9b1b9553784d9` (`Priivacy-ai/spec-kitty` v3.2.6)

---

## 1. Document Overview

This roadmap documents the completed Candidate Phase 1 design specifications, merged Phase 2 runtime contracts, and completed Phase 3 implementation sequence for Orchestra-native adaptations derived from the Spec Kitty pattern review.

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
- [x] Synchronized decision log, changelog, roadmap, ownership matrix, and upgrade roadmap.
- [x] Produced final Phase 1F handoff report `docs/artificer/external-sources/SPEC_KITTY_PHASE_1F_HANDOFF.md`.

### Phase 2A through 2G: Governed Phase Execution Contracts (`IMPLEMENTED_MERGED`)
- [x] Phase 2A: Implementation baseline, compatibility matrix, migration plan, and test plan defined.
- [x] Phase 2B: `OrchestraRuntimeEnvelope` runtime model, serializer, parser, and Codex/Antigravity adapter integration implemented.
- [x] Phase 2C: `OrchestraCorrelationID` zero-dependency RFC 9562 UUIDv7 generator, root generation, and child propagation implemented.
- [x] Phase 2D: `OrchestraPhaseRetrospective` typed model and deterministic builder implemented.
- [x] Phase 2E: `ApprovedUnitPlan` 15-field extension, schema validation, and contextual validator implemented.
- [x] Phase 2F: Consolidated behavior, governance, security, packaging, documentation, and backward-compatibility validation completed.
- [x] Phase 2G: Maintainer review, commit, push, remote verification, and PR #208 merge completed at `1e2992b94abe67a76c1e6ec0b98f8b712ae256e4`.

### Phase 3A: Deferred-Capability Selection & Design Baseline (`DESIGN_ACCEPTED_MERGED`)
- [x] Read-only capability selection, ownership, architecture, compatibility, security, and implementation planning completed.
- [x] Produced `ORCHESTRA_STATUS_PROJECTION.md`, `ORCHESTRA_WORKTREE_CONTRACT.md`, the Phase 3 implementation plan, and the compatibility/security matrix.
- [x] Design accepted and merged through PR #210.

### Phase 3B: `OrchestraStatusProjection` Implementation (`IMPLEMENTED_MERGED`)
- [x] Implemented typed model, JSON serializer, CLI renderer, lazy package exports, deterministic Git fact collection, and focused tests.
- [x] Validated 418 runtime tests with 93.80% package coverage and all required CI checks.
- [x] Merged through PR #212.

### Phase 3C: `OrchestraWorktreeContract` Implementation (`IMPLEMENTED_MERGED`)
- [x] Implemented the typed contract, path confinement, exact-base validation, deterministic identity and serialization, lifecycle enforcement, adapter capability integration, and focused tests.
- [x] Remediated immutable-review findings covering cleanup inspection failure, path escape, branch and unrelated-worktree preservation, identity verification, filesystem case behavior, and release TOCTOU checks.
- [x] Merged through PR #214 at reviewed head `646111325e6de7c5d31915789fdc22a644125b7b` and merge commit `6bce297c7469f9c08ce41308cbb993cc863ac540`.

### Phase 3D: Consolidated Validation & Safety Audit (`COMPLETE`)
- [x] Completed exact-head behavior, governance, security, packaging, compatibility, runtime, coverage, and cross-platform validation.
- [x] Verified Windows junction behavior and Python compatibility regressions.

### Phase 3E: Maintainer Review, PR & Merge (`COMPLETE`)
- [x] Completed immutable review, bounded remediation, commit and push authorization, remote verification, and PR #214 merge.
- [x] Preserved separate release, deployment, and policy-activation gates.

---

## 3. Dispositions & Implementation Summary

### Accepted & Merged Implemented Contracts
1. `OrchestraRuntimeEnvelope`: Non-authorizing JSON result serialization profile with discriminated variants.
2. `OrchestraCorrelationID`: Zero-dependency RFC 9562 UUIDv7 correlation generator and child propagation.
3. `OrchestraPhaseRetrospective`: Source-backed phase closeout evidence model and deterministic builder.
4. `ApprovedUnitPlan extension`: 15-field schema extension and contextual validator.
5. `OrchestraStatusProjection`: Read-only, deterministic, non-authorizing status projection and CLI.
6. `OrchestraWorktreeContract`: Optional host-capability-dependent, path-confined, fail-closed worktree lifecycle contract.

### Rejected Concepts (Remain Rejected)
- Standalone mutable unit-state files (`.orchestra/units/`).
- Manual doctrine packs duplicating `docs/governance/`.
- Workflow-state merge authority or automatic policy mutation.
- Spec Kitty runtime dependency or copying Spec Kitty code or schemas.
- SQLite event stores, RPC network services, background daemons, and web dashboards.

### Explicitly Deferred Concepts
- Cross-session correlation restoration and durable correlation persistence.
- Retry, wait, resume, remediation, and escalation continuation engines.
- Automatic retrospective phase-closeout generation and durable retention enforcement.
- Automatic Steward planning/dispatch integration and revision-history ordering integration.
- Automatic policy activation (`docs/governance/DELEGATED_EXECUTION_POLICY.md` Section 4 remains unamended).

---

## 4. Completed Candidate Phase 3 Sequence

- **Phase 3A:** `DESIGN_ACCEPTED_MERGED` via PR #210.
- **Phase 3B:** `IMPLEMENTED_MERGED` via PR #212.
- **Phase 3C:** `IMPLEMENTED_MERGED` via PR #214.
- **Phase 3D:** `VALIDATION_COMPLETE` on the final reviewed PR #214 head.
- **Phase 3E:** `REVIEW_AND_MERGE_COMPLETE` via PR #214.

Phase 3A through Phase 3E are complete and merged. The capability set remains `NOT_RELEASED`; no deployment or policy activation has occurred.
