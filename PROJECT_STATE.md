# Project State

- **Project Name:** Orchestra
- **Active Repo:** `C:\conductor`
- **Canonical Branch:** `main`
- **Base Branch:** `main`
- **Stable Continuation Branch:** `main`
- **Current Public Release:** `v1.1.2`
- **Release Status:** Published July 14, 2026
- **Current Main Status:** Contains the unreleased Spec Kitty-derived governed phase execution contracts through completed Phase 3A-3E and the merged frontend-to-backend synchronicity audit contract through PR #216 (merge commit `3a2f8b7e65cdab0f7e6a3113d1096ec9dccc23d3`).
- **Post-`v1.1.2` Release State:** `NOT_RELEASED`
- **Policy Activation State:** `NOT_PERFORMED`

## Spec Kitty-Derived Contracts

- **Phase 2:** Implemented and merged through PR #208.
- **Phase 2 Reviewed Head:** `1a57c489445a9a333e929cae8f857312bb126a62`
- **Phase 2 Merge Commit:** `1e2992b94abe67a76c1e6ec0b98f8b712ae256e4`
- **Implemented Phase 2 Contracts:** `OrchestraRuntimeEnvelope`, `OrchestraCorrelationID`, `OrchestraPhaseRetrospective`, and the 15-field `ApprovedUnitPlan` extension with contextual validation.
- **Phase 3A:** Design accepted and merged through PR #210.
- **Phase 3A Reviewed Head:** `3d8b14aaffa00d66d1faaaef55ec27ecbc10cdc3`
- **Phase 3A Merge Commit:** `1629eaf3cd3f156f8913f84c9229666257a3145a`
- **Phase 3B:** `OrchestraStatusProjection` implemented and merged through PR #212.
- **Phase 3B Reviewed Head:** `2a6c7ea8db16ce73d66fae566672f3681094b0f7`
- **Phase 3B Merge Commit:** `fa1e052d82301e70a5869258c3fc6af765163353`
- **Phase 3C:** `OrchestraWorktreeContract` implemented and merged through PR #214.
- **Phase 3C Reviewed Head:** `646111325e6de7c5d31915789fdc22a644125b7b`
- **Phase 3C Merge Commit:** `6bce297c7469f9c08ce41308cbb993cc863ac540`
- **Phase 3D:** Consolidated exact-head validation complete.
- **Phase 3E:** Immutable review, bounded remediation, and PR #214 merge complete.
- **Phase 3 Verdict:** `COMPLETE_MERGED_NOT_RELEASED`
- **Explicit Deferred Boundaries:** Cross-session correlation restoration, durable correlation persistence, retry/wait/resume engines, automatic retrospective closeout generation, durable retrospective retention, automatic Steward planning/dispatch integration, revision-history ordering, and automatic policy activation.

## Frontend-to-Backend Synchronicity

- **Status:** `IMPLEMENTED_MERGED`
- **Pull Request:** #216
- **Reviewed Head:** `52d47c2b10770cb5a85dab2eab9e81ce8851adb1`
- **Merge Commit:** `3a2f8b7e65cdab0f7e6a3113d1096ec9dccc23d3`
- **Scope:** Shared cross-module audit protocol, frontend/backend checklist, deterministic executable fixtures, validator and tests, routing/export/governance integration, and documentation.
- **Boundaries:** No runtime model, persistence, installed integration, specialist, plugin, command, release, deployment, or policy expansion.

## Delegated Governance and Tuner

- **Delegated Phase A:** Merged / canonical.
- **Delegated Phase B:** Merged through PR #190; post-merge synchronization through PR #191.
- **Delegated Phase C:** Host reliability evaluation required; repository-hosted preparation may proceed remotely, but host-local evidence remains required.
- **Delegated Phase D:** Typed-runtime overlap reconciliation required before any implementation.
- **The Tuner Phase 1:** Merged / canonical instruction-level protocol.
- **The Tuner Phase 2:** Merged through PR #197.
- **The Tuner Phase 3:** Merged through PR #198.
- **The Tuner Phase 4:** Merged through PR #200; post-merge state through PR #201.
- **The Tuner Runtime Boundary:** In-memory typed coordination, deterministic transitions and rejections, stale-evidence invalidation, minimal specialist re-entry, fail-closed supplied-session preflight, and direct single-owner bypass.
- **The Tuner Excluded Scope:** No persistent collaboration storage, SQLite, migrations, RPC, network or host-process orchestration, consumer-repository mutation, Dagger authority expansion, release, or deployment.

## Validation and Continuation

- **Validation Rule:** Validation results are revision-specific. Use current GitHub Actions and the canonical commands in `docs/setup/VALIDATION.md`; do not reuse historical counts as evidence for a newer revision.
- **Validation Coverage:** Governance consistency, routing, Tuner coordination, cross-layer synchronicity, evidence identity, prompt budget, Codex export parity, structure, manifests, IDE packaging, strict governance, stale references, behavior, runtime coverage, imports, release readiness, links, and exact-scope checks.
- **Startup Verification:**
  ```powershell
  git switch main
  git fetch origin
  git pull --ff-only origin main
  python scripts\preflight_sync_check.py
  ```
- **Issue #215:** Open umbrella finalization issue targeting `v1.2.0`.
- **Next Active Software Task:** Phase F2 read-only design and exact scope freeze for backend-to-persistence integrity and broader cross-module logical-flow auditing.
- **Next Local Task:** Fast-forward the local Orchestra and KB repositories, then run local preflight and installed-host parity checks when available.

This file records stable current state only. Historical decisions remain in `DECISION_LOG.md`, `CHANGELOG.md`, and immutable handoff evidence.
