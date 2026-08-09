# Project State

- **Project Name:** Orchestra
- **Active Repo:** `D:\Dev\Repositories\+conductor`
- **Canonical Branch:** `main`
- **Base Branch:** `main`
- **Stable Continuation Branch:** `main`
- **Current Public Release:** `v1.2.0`
- **Release Status:** `PUBLISHED_VERIFIED` on August 9, 2026
- **Target Release:** `v1.2.0`
- **Release-Candidate Metadata:** `1.2.0`
- **v1.2.0 Release State:** `PUBLISHED_VERIFIED`
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
- **Phase 3 Verdict:** `COMPLETE_MERGED_RELEASED_IN_V1_2_0`.

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
- **Delegated Phase C Live Host Evidence:** `VERIFIED / RECONCILED LOCALLY` through the accepted R7 record in `docs/validation/R7_LIVE_INSTALLED_HOST_VALIDATION_EVIDENCE.md`. The repository fixture remains simulated with live validation pending/empty by design; repository CI does not prove live host behavior.
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
- **R5:** autonomous merge-readiness hardening merged through PR #227 at merge commit `467008db683c346cd086442dbb909c20a9248a3a`.
- **R5B:** delegated-governance current-state reconciliation merged and was independently verified through PR #228 at merge commit `fbe4532ba2083feaa7ed9fcda2988843f1237a78`.
- **Historical R6:** `v1.2.0` release-candidate metadata and documentation were prepared as `PREPARED_NOT_RELEASED` without publication authority. R8 later published the separately authorized release.
- **R7 / PR #230:** accepted live-host evidence was reviewed at head `f49a03c929be7df7c10c457a227a46532ef47854` and merged to canonical `main` as `80f9bc71f00cc86c0021fd9da258f2eec596d7e0`. GitHub's then-used rebase merge rewrote the reviewed commit identity. The reviewed and canonical trees are equal and their content diff is empty, but the canonical rebase commit is unsigned and the reviewed head is not in `main` ancestry.

Maintainer disposition for the PR #230 incident is forward-only:

```text
PRESERVE_CURRENT_CANONICAL_HISTORY=true
HISTORY_REWRITE=false
FORCE_PUSH=false
PR230_REBASE_RESULT_IS_NOT_FUTURE_PRECEDENT=true
```

The incident exposed an ancestry-only post-merge verification assumption. PR #231 remediated that assumption forward-only and was independently verified as a signed, no-bypass Squash at canonical commit `8163c64838d369ea5c4abf45df36f6d6504db9fd`. R7 and R7R are `MERGED_VERIFIED`; PR #230 remains historical incident evidence and not future precedent.

The incident-derived invariants are:

```text
GITHUB_CAN_MERGE != GOVERNANCE_READY_TO_MERGE
BYPASS_CAPABILITY != GOVERNANCE_AUTHORIZATION
```

Autonomous merges follow `docs/governance/AUTONOMOUS_MERGE_READINESS_PROTOCOL.md`.

## Governed Autonomy Modes

- **GA-0:** `NO_DUPLICATE_AUTHORITY_MODEL`; no `orchestra_runtime/**` extension is justified.
- **GA-1:** `HUMAN_GOVERNED`, `SEMI_AUTONOMOUS`, and `FULL_AUTONOMOUS` canonical profiles.
- **GA-2:** Effective transition authority is the intersection of profile, explicit grant, repository/project policy, host capability, phase scope, and evidence.
- **GA-3:** Conductor selection gate with Human-Governed default, effective authority preview, explicit confirmation for increases, and immediate reductions.
- **GA-4:** Profile-aware progression through the existing delegated and Squash-aware merge-readiness protocols.
- **GA-5:** Profile/grant provenance and fail-closed same-host/portable continuity preservation.
- **GA-6:** Deterministic adversarial fixtures and focused validator/runtime regressions.
- **GA-7:** Governance, routing, adapter, project-state, README, roadmap, and release-candidate documentation reconciliation.

No profile creates authority. Claude Code remains `SCAFFOLD_ONLY`; runtime authority, plugin manifests, versions, host fixtures, and installed integrations are unchanged.

## Current `Protect main` Ruleset

The accepted solo-maintainer ruleset is:

```text
Required approvals: 0
Dismiss stale approvals on new reviewable commits: ON
Specific-team review: OFF
Code Owner review: OFF
Most-recent-push approval: OFF
Conversation resolution: ON
Allowed merge method: Squash only
Restrict deletions: ON
Linear history: ON
Signed commits: ON
Pull request required: ON
Required status checks: ON
Branch up to date before merge: ON
Force pushes blocked: ON
```

Required status checks are:

```text
governance-check
validate
runtime-tests
native-windows-latest
native-ubuntu-latest
native-macos-latest
Analyze (actions)
Analyze (python)
```

The current bypass list is intentionally retained for repository-operational access. Bypass capability is not governance authorization; ordinary governed automation must not rely on it to skip evidence or policy gates.

## Validation and Continuation

- **Validation Rule:** Validation results are revision-specific. Historical green runs cannot authorize a newer head.
- **Fail-Closed Rule:** Missing, pending, stale, skipped, cancelled, timed-out, or failed required checks cannot authorize merge.
- **Ruleset Rule:** Live ruleset drift, non-Squash merge selection, unresolved review threads, or unauthorized bypass use blocks ordinary autonomous merge.
- **Baseline Rule:** A new phase must not begin from a red canonical `main`.
- **Post-Merge Rule:** An API response is not completion evidence. For Squash, canonical parent/tree/content/signature evidence and a canonical remote read are required before state advances.
- **Issue #215:** `CLOSED_VERIFIED` after the published release, Orchestra post-publication PR #236, KB publication-closeout PR #32, and the evidence-backed completion comment were independently verified.
- **R6 Repository State:** Release-candidate preparation completed with version surfaces normalized to `1.2.0`.
- **R7 State:** R7 and R7R are `MERGED_VERIFIED`; PR #230 incident history is preserved forward-only and PR #231 is the signed Squash trust anchor.
- **Governed Autonomy Modes:** GA-0 through GA-7 are `MERGED_VERIFIED` through PR #232 and signed canonical Squash commit `900f88d7a3ed480ae8b910e6ba204008a72d2784`.
- **Pre-R8 Repository Hygiene:** README provenance/host/release state and complete conservative file/branch classifications are `MERGED_VERIFIED` through PR #234 and signed canonical Squash commit `8cca62109b10aa06abaf25fc4c9982a02160bcbf`. No tracked file or branch was deleted.
- **Release Readiness:** Hygiene-invalidated candidate evidence has been refreshed against canonical `8cca62109b10aa06abaf25fc4c9982a02160bcbf`; behavior, 541 runtime tests at 94.31% coverage, strict governance, packaging, exact-head CI, signature/tree/base verification, and release-boundary reads are green. See `docs/validation/V1_2_0_RELEASE_READINESS_EVIDENCE.md`.
- **Publication State:** Annotated tag `v1.2.0` and the immutable, non-draft, non-prerelease GitHub Release are `PUBLISHED_VERIFIED` at release commit `4f3c45f6d1e5f290aca108ddf5810c1b18f1dc76`. No deployment, marketplace publication, installed-integration refresh, or policy activation was performed.

## Local Startup Verification

```powershell
git switch main
git fetch origin --prune
git pull --ff-only origin main
python scripts\preflight_sync_check.py
```

This file records stable current state. Historical decisions remain in `DECISION_LOG.md`, `CHANGELOG.md`, the archived autonomous-run branch, and immutable handoff evidence.
