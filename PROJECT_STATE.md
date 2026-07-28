# Project State

- **Project Name:** Orchestra
- **Active Repo:** `C:\conductor`
- **Canonical Branch:** `main`
- **Base Branch:** `main`
- **Stable Continuation Branch:** `main`
- **Current Public Release:** `v1.1.2`
- **Release Status:** Published July 14, 2026
- **Current Main Status:** Contains unreleased delegated-progression and cross-specialist coordination work completed after `v1.1.2`
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
- **Next Active Software Task:** Controlled by the external ecosystem knowledge base; no Orchestra runtime next phase is authorized by this state record

This file records stable current state only. Historical decisions remain in `DECISION_LOG.md` and `CHANGELOG.md`.
