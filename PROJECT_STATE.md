# Project State

- **Project Name:** Orchestra
- **Active Repo:** `Baelfyre/Orchestra`
- **Canonical Branch:** `main`
- **Base Branch:** `main`
- **Stable Continuation Branch:** `main`
- **Current Public Release:** `v1.10.0`
- **Release Status:** `v1.10.0 PUBLISHED_VERIFIED`
- **Target Release:** `POST_PUBLICATION_DOCUMENTATION_NORMALIZATION`
- **Release-Candidate Metadata:** `1.10.0` (`PUBLISHED_VERIFIED_COMPLETE`)
- **v1.2.0 Release State:** `PUBLISHED_VERIFIED`
- **v1.3.0 Release State:** `PUBLISHED_VERIFIED`
- **v1.4.0 Release State:** `PUBLISHED_VERIFIED`
- **v1.5.0 Release State:** `PUBLISHED_VERIFIED`
- **v1.6.0 Release State:** `PUBLISHED_VERIFIED`
- **v1.6.0 Release Commit:** `ba35764a14111518c7da729b5a4c69c6af485a9b`
- **v1.6.0 GitHub Release:** id `371748233`, immutable and historical after v1.7.0 publication
- **v1.7.0 Release State:** `PUBLISHED_VERIFIED`
- **v1.7.0 Release Commit:** `e5305ef3e160209a0345bd2c7843c923940e62c5`
- **v1.7.0 Release Tree:** `7b7a0f6d5dd5376a62125ed1c6b037284e519c69`
- **v1.7.0 Sole Parent:** `664079b5fb9e149ea0689ff08bc2d9c039780290`
- **v1.7.0 Tag Ref:** lightweight `commit` ref targeting the exact release commit
- **v1.7.0 GitHub Release:** id `376713145`, immutable, non-draft, non-prerelease, independently verified latest
- **v1.7.0 Post-Publication Verification:** run `32898750932` PASS
- **v1.8.0 Release State:** `PUBLISHED_VERIFIED`
- **v1.8.0 Release Commit:** `dad1f153f1be6522a8a7964258a2122a8d057596`
- **v1.8.0 Release Tree:** `4effcd97e15f843c8c0d9d45217870ee9d6480ff`
- **v1.8.0 Sole Parent:** `b601c2d853ad0dcdc68b8dc652578f19ef663c79`
- **v1.8.0 Tag Ref:** lightweight `commit` ref targeting the exact release commit
- **v1.8.0 GitHub Release:** id `RE_kwDOS_4UtM4WyusI`, immutable, non-draft, non-prerelease, independently verified latest
- **v1.8.0 Post-Publication Verification:** PASS
- **Control Plane State:** `V1_10_0_CANDIDATE`
- **MCP State:** `PUBLISHED_V1_6_STABLE_RETAINED_V1_7`
- **Policy Activation State:** `NOT_PERFORMED`

## v1.10.0 Universal Adaptive Integration and Conductor Routing Publication

The v1.10.0 candidate is an additive, backward-compatible minor release candidate based on the post-v1.9.0 UAI and Conductor routing work. UAI-0 through UAI-10 are canonically verified, the maintainer-run GitHub Copilot `/conductor` promotion retest is `SUPPORTED_VERIFIED`, and Auto-mode provider/model identity remains unresolved and unadmitted.

All 11 package/version surfaces and the host-update contract are aligned to `1.10.0`. Conductor remains the sole internal specialist router; clear ownership may enable a direct single-specialist fast route, but it does not bypass Conductor. UAI transport selection remains separate from AWF specialist routing, and automatic provider routing/fallback, learned routing promotion, concurrency widening, AR-3, and AR-4 remain out of scope.

The publication is `PUBLISHED_VERIFIED` from exact canonical Orchestra commit `756a358f96363f0c377b049adcd87b1991d5aef6`, tree `42c0c8929c4dcfa5b17ff2feb293710d2468ca51`, sole parent `7cfc2b58c3cf3fb9f16d2a1e128bb01b74835b57`, lightweight tag `v1.10.0`, and GitHub Release ID `383668751`. The tag and non-draft, non-prerelease release were independently read back. Post-publication documentation normalization is active and does not rewrite the published identity or candidate qualification evidence.

The published release reference is `docs/reference/releases/v1.10.0.md`; the candidate and readiness documents remain historical qualification evidence. Auto-mode provider/model identity remains unresolved and unadmitted.

## v1.9.0 UI Execution Fidelity Publication

The v1.9.0 release is published from canonical Orchestra `main` at signed commit `7129a690b041bddbf8b58f41db0c4a680317fda1`, tree `babf0a0c61d4a073144891b295b1989c256513eb`, and sole parent `75af3966722edfdde474e8fcf99a1b8002d1527f`. UIEF-5 through UIEF-10 are canonically reconciled. UIEF-7 retains its deterministic-only evidence limit, and UIEF-9 retains the historical `NO_BENEFIT_ESTABLISHED` disposition without a new provider/model experiment.

The v1.9.0 package/version surfaces are published and verified. Adaptive Host Integration is recorded as future work only and is not implemented.

See `docs/validation/V1_9_0_PUBLICATION_CLOSEOUT.md` for the exact tag,
release, signature, qualification, and independent post-publication evidence.

## v1.8.0 Governance Hardening, Runtime Refoundation & Traceability Publication

Orchestra `v1.8.0` is `PUBLISHED_VERIFIED`. Immutable GitHub Release id `RE_kwDOS_4UtM4WyusI` and lightweight tag `v1.8.0` resolve to exact signed canonical release commit `dad1f153f1be6522a8a7964258a2122a8d057596` with tree `4effcd97e15f843c8c0d9d45217870ee9d6480ff` and sole parent `b601c2d853ad0dcdc68b8dc652578f19ef663c79`. Canonical Governance, validate/runtime, Required Analysis Compatibility/CodeQL, native Windows/Ubuntu/macOS validation, bounded-pilot confidence, signed materialization, expected-head Squash, and zero unresolved review-thread gates passed before publication. Read-only post-publication verification independently confirmed the exact tag, release body, latest/immutable release state, and prior-tag preservation.

The release incorporates Prime Directive / Lifecycle V2, completed runtime refoundation milestones AR-0 through AR-2, Scribe Specialist Upgrade (SSU), the complete architecture governance program OR-GOV-1 through OR-GOV-10, Registry O7, Cloak CUIR reference intelligence, and expanded deterministic validation.

No AR-3/AR-4 implementation, deployment, production mutation, policy activation, installed-integration refresh, destructive cleanup, force push, or history rewrite was performed. Later `main` changes are post-release maintenance and do not move the immutable v1.8.0 identity.

See `docs/validation/V1_8_0_PUBLICATION_CLOSEOUT.md`.

## v1.7.0 Adaptive Intelligence, Portable Memory & Design Fidelity Publication

Orchestra `v1.7.0` is `PUBLISHED_VERIFIED`. Immutable GitHub Release id `376713145` and lightweight tag `v1.7.0` resolve to exact signed canonical release commit `e5305ef3e160209a0345bd2c7843c923940e62c5` with tree `7b7a0f6d5dd5376a62125ed1c6b037284e519c69` and sole parent `664079b5fb9e149ea0689ff08bc2d9c039780290`. Canonical Governance, validate/runtime, Required Analysis Compatibility/CodeQL, native Windows/Ubuntu/macOS validation, Cosmic Ray confidence, signed materialization, expected-head Squash, and zero unresolved review-thread gates passed before publication. Read-only post-publication verification run `32898750932` independently confirmed the exact tag, release body, latest/immutable release state, and prior-tag preservation.

The release includes governed adaptive intelligence through bounded shadow maturity, optional storage-agnostic portable adaptive memory, Registry O1-O6 adaptive consumption, and governed UI design fidelity through UIX-9A repository proof preparation. A5 topology benefit and repeatable Murmurs efficiency benefit were not established, so neither was promoted to default execution authority.

No live UIX-9 model/provider proof, deployment, production mutation, policy activation, installed-integration refresh, destructive cleanup, force push, or history rewrite was performed. Later `main` changes are post-release maintenance and do not move the immutable v1.7.0 identity.

See `docs/validation/V1_7_0_PUBLICATION_CLOSEOUT.md`.

## v1.5.0 Machine-Verifiable Control Plane and Murmurs Publication

The post-v1.4.0 control-plane re-foundation is complete through `LEGACY_RETIRED`. Forward governance stabilization requires both `mergeable=true` and a current `mergeable_state=clean` for ordinary governed merge progression. Murmurs is canonical as an additive opt-in presentation layer with `NORMAL` as the default and hard-required explanation for authority, human-action, failure, blocker, governance-stop, handoff, and terminal events.

Package/version metadata is `1.5.0` across all 11 release surfaces without changing public command identity, specialist identity, supported/scaffold host maturity, marketplace publication state, deployment state, or installed integrations. Compatibility evidence supported a minor release rather than an intentional breaking major release.

The final published candidate passed the release campaign's exact-head runtime, statement/branch coverage, critical-module, workflow-sanity, P9 conformance, Mutmut, integrated Cosmic Ray, native Windows/Ubuntu/macOS, CodeQL, governance, package/version, Registry compatibility, signed canonical merge, tag-identity, and GitHub Release identity gates. The immutable GitHub Release was published from exact signed canonical release commit `b0a56cc7af8ad78234754bcb29ed07f6ab54d920` and independently verified.

```text
CURRENT_PUBLIC_RELEASE=v1.5.0
TARGET_VERSION=1.5.0
TARGET_TAG=v1.5.0
V1_5_0_RELEASE_STATE=PUBLISHED_VERIFIED
V1_5_0_RELEASE_COMMIT=b0a56cc7af8ad78234754bcb29ed07f6ab54d920
V1_5_0_GITHUB_RELEASE_ID=371314544
CONTROL_PLANE_STAGE=LEGACY_RETIRED
MURMURS_DEFAULT=NORMAL
MURMURS_TOKEN_PERCENT_CLAIM=UNAVAILABLE_WITHOUT_COMPARABLE_HOST_COUNTERS
MCP_IMPLEMENTATION=NOT_INCLUDED_IN_V1_5_0
```

The v1.5.0 release tag is fixed. Post-publication documentation or later implementation may advance `main`, but must not move the immutable release identity. MCP publication dependency is satisfied, but no MCP implementation is implied or authorized by publication alone. It remains subject to a fresh post-v1.5 dependency/risk/value and design decision.

See `docs/releases/v1.5.0-machine-verifiable-control-plane-murmurs-release-candidate.md`, `docs/validation/V1_5_0_RELEASE_READINESS_EVIDENCE.md`, and `docs/validation/V1_5_0_PUBLICATION_CLOSEOUT.md`.

## v1.4.0 Governance and Compliance Registry Cross-Integration Publication

The v1.4.0 governance upgrade is `PUBLISHED_VERIFIED`. The public GitHub Release `Orchestra v1.4.0: Governance & Compliance Registry Cross-Integration` was published under separate explicit authority as release id `370658917` at `2026-08-14T15:21:25Z`. Lightweight tag `v1.4.0` resolves directly to exact signed canonical release commit `93dd51c0fbe1b10affc58e6fadd5fb0bc2927a50` with tree `1ef60b00e3ac6deba5da57c47d2a0850872d41a9`. The release is non-draft, non-prerelease, immutable, and independently verified as latest at its publication checkpoint.

The trusted Registry dependency is also complete: immutable `registry-v0.1.0` targets Registry canonical `3821bcb55125b4d8864f28b6423650e6e17ac67b`, and Orchestra network-provenance run `31811353512` / job `94802485762` passed exact release identity, real bundle integrity, `CURRENT` freshness, PH source query, project pinning, update-check, and idempotent re-sync. Final Orchestra PR #271 then passed the full exact-head matrix and merged as the signed release commit above; its canonical post-merge matrix passed Governance, validate, 568 runtime tests at 94.31% coverage, CodeQL actions/Python, and native Ubuntu/macOS/Windows.

```text
CURRENT_PUBLIC_RELEASE_AT_CHECKPOINT=v1.4.0
V1_4_0_RELEASE_STATE=PUBLISHED_VERIFIED
V1_4_0_TAG_REF_TYPE=commit
V1_4_0_TAG_TARGET=93dd51c0fbe1b10affc58e6fadd5fb0bc2927a50
V1_4_0_RELEASE_COMMIT_SIGNATURE=VERIFIED_VALID
V1_4_0_GITHUB_RELEASE_ID=370658917
V1_4_0_GITHUB_RELEASE_IMMUTABLE=true
V1_4_0_PUBLICATION=COMPLETE_VERIFIED
```

No marketplace publication, installed-integration refresh, deployment/production mutation, policy activation, destructive cleanup, branch deletion, force push, or history rewrite was performed.

See `docs/validation/V1_4_0_PUBLICATION_CLOSEOUT.md`.

## v1.3.0 Specialist Intelligence Publication

The SK1-SK10 Specialist Knowledge Layer campaign is `MERGED_VERIFIED`. The bounded v1.3.0 package/version preparation was reviewed through PR #255 at signed head `f63daf49add4887d7fbd1b581959ebf8654150db` and Squash-merged with an expected-head guard as canonical commit `32257723d6ca72847e4581d8b927c7b14c77039e`.

Revision-bound readiness was reviewed through PR #257 and merged as signed canonical commit `db351796684789987eb5bce85e641ce31c91993b`. README alignment was then reviewed through PR #259 at signed head `b7b8bfeced7c0719558eb95c0797f0685f0c98f2`, passed all nine exact-head checks, and Squash-merged with an expected-head guard as exact release commit `3c6155c111981632649a3c3207fac8ac1edcea74` with tree `5ae72f6ab9ddf5284afdc3d8675f67fc23c24281`.

The current runtime suite at the v1.3.0 release checkpoint was 542 passing tests at 94.33% coverage, including deterministic `1.3.0` parity across all 11 live package/version surfaces.

The first candidate PR #253 is preserved as fail-closed evidence: Stage 1 Strict Governance correctly rejected the 13-file candidate because significant package/test changes lacked a matching changelog update. The corrected tree added the focused changelog entry, restored historical wording, discarded stale validation, and reran the full exact-head matrix through PR #255.

Publication completed under separate explicit maintainer authority:

```text
CURRENT_PUBLIC_RELEASE_AT_CHECKPOINT=v1.3.0
TARGET_VERSION=1.3.0
TARGET_TAG=v1.3.0
V1_3_0_RELEASE_STATE=PUBLISHED_VERIFIED
V1_3_0_TAG_OBJECT=c66afec49990036d9deb2f07e3363cd664e2dcb1
V1_3_0_TAG_TARGET=3c6155c111981632649a3c3207fac8ac1edcea74
V1_3_0_TAG_OBJECT_SIGNATURE=UNSIGNED
V1_3_0_RELEASE_COMMIT_SIGNATURE=VERIFIED_VALID
V1_3_0_GITHUB_RELEASE_IMMUTABLE=true
V1_3_0_PUBLICATION=COMPLETE_VERIFIED
```

The unsigned annotated-tag-object state is recorded accurately and is consistent with the prior v1.2.0 annotated tag pattern. Trust remains anchored to the exact tag target and the GitHub-verified signed release commit.

No deployment, marketplace publication, installed-integration refresh, policy activation, destructive cleanup, branch deletion, force push, or history rewrite was performed.

See `docs/releases/v1.3.0-specialist-intelligence-release-candidate.md`, `docs/validation/V1_3_0_RELEASE_READINESS_EVIDENCE.md`, and `docs/validation/V1_3_0_PUBLICATION_CLOSEOUT.md`.

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

### README Direct-Main Governance Incident - 2026-08-10

Canonical commit `807bda608d65cb10bf65cdf313916d9d0fd62320` contains the accepted public-facing README refinement and changes only `README.md`. Exact local validation is green: the behavior suite passed, 541 runtime tests passed at 94.31% coverage, and strict governance passed with 0 errors and 0 warnings.

Post-validation commit verification reported the canonical commit as unsigned. The README transition also occurred directly on `main` rather than through the repository's required pull-request path.

Maintainer disposition is forward-only:

```text
PRESERVE_CURRENT_CANONICAL_HISTORY=true
HISTORY_REWRITE=false
FORCE_PUSH=false
UNSIGNED_DIRECT_MAIN_RESULT_IS_NOT_FUTURE_PRECEDENT=true
```

No README reversal is required because the content itself validated successfully. Governance closeout requires a separate normal PR from `807bda608d65cb10bf65cdf313916d9d0fd62320`, fresh exact-head checks, Squash-only merge, a signature-verified canonical result, and independent post-merge verification. KB reconciliation remains pending until that closeout is `MERGED_VERIFIED`.

See `docs/validation/README_DIRECT_MAIN_GOVERNANCE_RECONCILIATION_2026_08_10.md`.

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

No profile creates authority. Claude Code remains `SCAFFOLD_ONLY`; runtime authority, plugin manifests, versions, host fixtures, and installed integrations are unchanged by the autonomy-profile implementation itself.

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
- **Issue #215:** `CLOSED_VERIFIED` after the published v1.2.0 release, Orchestra post-publication PR #236, KB publication-closeout PR #32, and the evidence-backed completion comment were independently verified.
- **R6 Repository State:** Release-candidate preparation completed with version surfaces normalized to `1.2.0`.
- **R7 State:** R7 and R7R are `MERGED_VERIFIED`; PR #230 incident history is preserved forward-only and PR #231 is the signed Squash trust anchor.
- **Governed Autonomy Modes:** GA-0 through GA-7 are `MERGED_VERIFIED` through PR #232 and signed canonical Squash commit `900f88d7a3ed480ae8b910e6ba204008a72d2784`.
- **Pre-R8 Repository Hygiene:** README provenance/host/release state and complete conservative file/branch classifications are `MERGED_VERIFIED` through PR #234 and signed canonical Squash commit `8cca62109b10aa06abaf25fc4c9982a02160bcbf`. No tracked file or branch was deleted.
- **v1.2.0 Publication State:** Annotated tag `v1.2.0` and the immutable, non-draft, non-prerelease GitHub Release are historical `PUBLISHED_VERIFIED` evidence at release commit `4f3c45f6d1e5f290aca108ddf5810c1b18f1dc76`.
- **v1.3.0 Preparation:** SK1-SK10 are `MERGED_VERIFIED`; package/version preparation is canonical through PR #255 at signed Squash `32257723d6ca72847e4581d8b927c7b14c77039e`, with 542 runtime tests at 94.33% coverage and all 9 observed exact-head checks passing.
- **v1.3.0 Publication State:** Annotated tag `v1.3.0` targets exact signed release commit `3c6155c111981632649a3c3207fac8ac1edcea74`; the immutable, non-draft, non-prerelease GitHub Release `Orchestra v1.3.0: Specialist Intelligence` is `PUBLISHED_VERIFIED`. No deployment, marketplace publication, installed-integration refresh, or policy activation was performed.
- **v1.4.0 Publication State:** Lightweight tag `v1.4.0` resolves directly to exact signed release commit `93dd51c0fbe1b10affc58e6fadd5fb0bc2927a50`; GitHub Release id `370658917`, `Orchestra v1.4.0: Governance & Compliance Registry Cross-Integration`, is immutable, non-draft, non-prerelease, and `PUBLISHED_VERIFIED`. No marketplace publication, installed-integration refresh, deployment, or policy activation was performed.
- **v1.5.0 Publication State:** Lightweight tag `v1.5.0` resolves directly to exact signed release commit `b0a56cc7af8ad78234754bcb29ed07f6ab54d920`; GitHub Release id `371314544`, `Orchestra v1.5.0: Machine-Verifiable Control Plane and Murmurs`, is immutable, non-draft, non-prerelease, and `PUBLISHED_VERIFIED`. MCP remains unimplemented and requires a fresh post-release priority/design gate.

## Local Startup Verification

```powershell
git switch main
git fetch origin --prune
git pull --ff-only origin main
python scripts\preflight_sync_check.py
```

This file records stable current state. Historical decisions remain in `DECISION_LOG.md`, `CHANGELOG.md`, the archived autonomous-run branch, and immutable handoff evidence.
