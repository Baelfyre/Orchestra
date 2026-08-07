# Project State

- **Project Name:** Orchestra
- **Active Repo:** `D:\Dev\Repositories\+conductor`
- **Canonical Branch:** `main`
- **Base Branch:** `main`
- **Stable Continuation Branch:** `main`
- **Current Public Release:** `v1.1.2`
- **Release Status:** Published July 14, 2026
- **Target Release:** `v1.2.0`
- **Post-`v1.1.2` Release State:** `NOT_RELEASED`
- **Policy Activation State:** `NOT_PERFORMED`

## Canonical Capability State

### Spec Kitty-Derived Contracts

- **Phase 2:** Implemented and merged through PR #208.
- **Implemented Phase 2 Contracts:** `OrchestraRuntimeEnvelope`, `OrchestraCorrelationID`, `OrchestraPhaseRetrospective`, and the 15-field `ApprovedUnitPlan` extension with contextual validation.
- **Phase 3A:** Design accepted and merged through PR #210.
- **Phase 3B:** `OrchestraStatusProjection` implemented and merged through PR #212.
- **Phase 3C:** `OrchestraWorktreeContract` implemented and merged through PR #214.
- **Phase 3D:** Consolidated exact-head validation complete.
- **Phase 3E:** Immutable review, bounded remediation, and merge complete.
- **Phase 3 Verdict:** `COMPLETE_MERGED_NOT_RELEASED`.

### Cross-Layer Integrity

- **Frontend-to-Backend Synchronicity:** Implemented, exact-head validated, and merged through PR #216.
- **Backend-to-Persistence Integrity:** Clean replay completed and merged through PR #224.
- **Cross-Module Logical-Flow Integrity:** Clean replay completed and merged through PR #224.
- **Architecture:** F2 is additive and preserves the original frontend/backend protocol identity and Codex portable-reference parity.
- **Authority Boundary:** No new specialist, command, plugin, runtime authority, persistence implementation, migration, or policy authority was created.

### Delegated Governance and Host Reliability

- **Delegated Phase A:** Merged / canonical.
- **Delegated Phase B:** Merged through PR #190; post-merge synchronization through PR #191.
- **Delegated Phase C Repository Contract:** Clean replay completed through PR #225. Deterministic repository simulation covers same-host reset/resume, active-host handoff, capacity waits, stale identity, incomplete checkpoints, scaffold-only hosts, authority expansion, and duplicate replay.
- **Delegated Phase C Live Host Evidence:** `PENDING_LOCAL_HOST_VALIDATION`. Repository CI does not prove an actual installed Codex reset, Antigravity reset, or live cross-host continuation.
- **Delegated Phase D:** Runtime overlap reconciliation completed through PR #226. No duplicate Phase D runtime extension is justified for `v1.2.0`.
- **Phase D Result:** Existing authority, capability, delegation, lifecycle, runtime-envelope, `ApprovedUnitPlan`, audit, Tuner coordination, status/worktree, and cross-layer contracts satisfy the material runtime requirements. Evidence/decision/checkpoint/handoff records remain governance artifacts unless a concrete missing runtime consumer is established.

### The Tuner

- **Phase 1:** Merged / canonical instruction-level protocol.
- **Phase 2:** Merged through PR #197.
- **Phase 3:** Merged through PR #198.
- **Phase 4:** Merged through PR #200; post-merge state through PR #201.
- **Runtime Boundary:** In-memory typed coordination, deterministic transitions and rejections, stale-evidence invalidation, minimal specialist re-entry, fail-closed supplied-session preflight, and direct single-owner bypass.
- **Excluded Scope:** No persistent collaboration storage, SQLite, migrations, RPC, network or host-process orchestration, consumer-repository mutation, Dagger authority expansion, release, or deployment.

## Autonomous Replay and Incident Learning

The first autonomous finalization experiment was archived at:

```text
archive/autonomous-run-2026-08-07-pre-rollback
```

The repository was restored to the verified pre-run recovery point and replayed using fail-closed evidence rules.

Clean replay results:

- **R0:** recovery baseline restored and verified.
- **R1:** Spec Kitty/roadmap closeout merged through replay PR #223 after a fresh all-green matrix.
- **R2:** additive cross-layer integrity merged through replay PR #224 with the previously missing focused changelog update.
- **R3:** host-reliability replay initially failed runtime validation; the merge was blocked, the malformed fixture was corrected, all earlier evidence was discarded, a completely fresh all-green matrix ran, and the remediated head merged through PR #225.
- **R4:** Phase D overlap assessment merged through PR #226 only after the canonical baseline was green and every fresh required check passed.
- **R5:** repository cleanup and autonomous merge-readiness hardening is the active remote phase.

The incident-derived invariant is:

```text
GITHUB_CAN_MERGE != GOVERNANCE_READY_TO_MERGE
```

Autonomous merges must follow `docs/governance/AUTONOMOUS_MERGE_READINESS_PROTOCOL.md` once R5 is canonical.

## Validation and Continuation

- **Validation Rule:** Validation results are revision-specific. Historical green runs cannot authorize a newer head.
- **Fail-Closed Rule:** Missing, pending, stale, skipped, cancelled, timed-out, or failed required checks cannot authorize merge.
- **Baseline Rule:** A new phase must not begin from a red canonical `main`.
- **Post-Merge Rule:** An API response is not completion evidence; the PR and canonical `main` must be independently re-read before state advances.
- **Issue #215:** Open umbrella finalization issue targeting `v1.2.0`.
- **Active Remote Task:** R5 cleanup and autonomous merge-readiness hardening.
- **Next Remote Task:** R6 README, changelog, version, and release-candidate preparation after R5 passes and merges cleanly.
- **Next Local Task:** Fast-forward local Orchestra and KB, run preflight, refresh installed integrations as governed, and execute the R7 live installed-host validation matrix.
- **Publication Boundary:** `v1.2.0` tag/GitHub Release remains blocked until R7 live-host evidence is reconciled and release state is independently verified.

## Local Startup Verification

```powershell
git switch main
git fetch origin --prune
git pull --ff-only origin main
python scripts\preflight_sync_check.py
```

This file records stable current state and the active replay phase only. Historical decisions remain in `DECISION_LOG.md`, `CHANGELOG.md`, the archived autonomous-run branch, and immutable handoff evidence.
