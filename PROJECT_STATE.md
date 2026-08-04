# Project State

- **Project Name:** Orchestra
- **Active Repo:** `C:\conductor`
- **Canonical Branch:** `main`
- **Base Branch:** `main`
- **Stable Continuation Branch:** `main`
- **Current Public Release:** `v1.1.2`
- **Release Status:** Published July 14, 2026
- **Current Main Status:** Contains unreleased Spec Kitty-derived governed phase execution contracts merged through PR #208, and merged Phase 3A deferred-capability design package through PR #210 (merge commit `1629eaf3cd3f156f8913f84c9229666257a3145a`)
- **Spec Kitty-Derived Phase 2:** Merged / Canonical (`orchestra_runtime/`)
- **Spec Kitty-Derived Phase 2 Merge Commit:** `1e2992b94abe67a76c1e6ec0b98f8b712ae256e4`
- **Spec Kitty-Derived Phase 2 Reviewed Head:** `1a57c489445a9a333e929cae8f857312bb126a62`
- **Spec Kitty-Derived Phase 2 Release / Deployment:** Not performed
- **Spec Kitty-Derived Phase 2 Policy Activation:** Not performed
- **Spec Kitty-Derived Phase 2 Validation:** 390 runtime tests passed (93.72% coverage), behavior suite passed (exit 0), 20 cross-contract integration scenarios passed, cross-platform CI passed (Windows, Ubuntu, macOS)
- **Implemented Contracts:** `OrchestraRuntimeEnvelope` (execution_result, transition_decision, audit_event), `OrchestraCorrelationID` (RFC 9562 UUIDv7 root generation and child propagation), `OrchestraPhaseRetrospective` (model and deterministic builder), `ApprovedUnitPlan` (15-field extension and contextual validator)
- **Spec Kitty-Derived Phase 3A:** Design accepted and merged through PR #210
- **Spec Kitty-Derived Phase 3A Reviewed Head:** `3d8b14aaffa00d66d1faaaef55ec27ecbc10cdc3`
- **Spec Kitty-Derived Phase 3A Merge Commit:** `1629eaf3cd3f156f8913f84c9229666257a3145a`
- **Spec Kitty-Derived Phase 3A Merged At:** 2026-08-04T15:48:49Z
- **OrchestraStatusProjection:** Design specified and accepted. `DESIGN_ACCEPTED_MERGED`. Runtime not implemented. Canonical owner: Scribe. Read-only, derived, non-authorizing, not a source of truth. Missing or conflicting data reports UNKNOWN.
- **OrchestraWorktreeContract:** Design specified and accepted. `DESIGN_ACCEPTED_MERGED`. Runtime not implemented. Canonical owner: Ponytail. Optional, host-capability-dependent. Cleanup is EXPLICIT_HOST_ACTION_ONLY. No automatic deletion of dirty or user worktrees.
- **Spec Kitty-Derived Phase 3A Release / Deployment:** Not performed
- **Spec Kitty-Derived Phase 3A Policy Activation:** Not performed
- **Explicit Deferred Boundaries:** Cross-session correlation restoration, durable correlation persistence, retry/wait/resume state machines, automatic retrospective closeout generation, durable retrospective retention, automatic Steward planning/dispatch integration, revision-history ordering, automatic policy activation
- **Delegated Phase A:** Merged / Canonical (`docs/governance/DELEGATED_EXECUTION_POLICY.md`)
- **Delegated Phase B:** Merged / Canonical through PR #190
- **Delegated Phase B Merge Commit:** `d37a2f7b31543efacf7a5e81c3f4d08c12da017d`
- **Delegated Phase B Post-Merge Synchronization:** Merged through PR #191 at `93cf3904fd593eaf267a76598a0d2ccc1514da99`
- **Delegated Phase B Release / Deployment:** Not performed
- **Delegated Phase C:** Not started
- **Delegated Phase D:** Not started
- **The Tuner Phase 1:** Merged / Canonical instruction-level cross-specialist coordination protocol
- **The Tuner Phase 2:** Merged through PR #197 at `7423d3e7db7fb8e32dfe91454f5c2c5d10aba9bb`
- **The Tuner Phase 3:** Merged through PR #198 at `1b73e232930c9289601474a5cddb282e98378261`
- **The Tuner Phase 4:** Merged through PR #200 at `32fb67f8b2fd5c3436a1f2738e13e7903fda5328`
- **The Tuner Phase 4 Post-Merge State:** Merged through PR #201 at `68217d5e406aee9d5f9b8c3b7f8675458121a38c`
- **Issue #195:** Closed / Completed
- **The Tuner Runtime Boundary:** In-memory typed coordination, deterministic transitions and rejections, stale-evidence invalidation, minimal specialist re-entry recommendations, fail-closed supplied-session preflight, and direct single-owner bypass
- **The Tuner Excluded Scope:** No persistent collaboration storage, SQLite, migrations, RPC, network or host-process orchestration, consumer-repository mutation, Dagger authority expansion, release, or deployment
- **Current Validation Rule:** Validation results are revision-specific. Use the current GitHub Actions result and the canonical commands in `docs/setup/VALIDATION.md`; do not reuse historical test counts or coverage percentages as the result for a newer revision.
- **Current Validation Coverage:** Governance protocol consistency, routing contracts, Tuner collaboration contracts, evidence identity, static behavioral expectations, prompt-load budget, Codex export parity, structure, manifests, IDE packaging, strict governance, stale-reference checks, behavior validation, runtime tests and coverage threshold, runtime import smoke, release-readiness checks, links, and exact-scope diff checks
- **Startup Verification Rule:** Resolve current `main` rather than recording a self-referential closeout SHA:
  ```powershell
  git switch main
  git fetch origin
  git rev-parse origin/main
  python scripts\preflight_sync_check.py
  ```
- **Next Projected Portfolio Task:** Separate Remotion Orchestra explainer, beginning with the pre-production brief and storyboard
- **Next Active Software Task:** Candidate Phase 3B: `OrchestraStatusProjection` implementation, subject to separate maintainer authorization

This file records stable current state only. Historical decisions remain in `DECISION_LOG.md` and `CHANGELOG.md`.
