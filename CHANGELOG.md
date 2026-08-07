# Changelog

This changelog records release-level Orchestra history. Detailed implementation chronology remains available in Git history, merged pull requests, `DECISION_LOG.md`, `PROJECT_STATE.md`, and immutable handoff records.

## v1.2.0 Release Candidate - NOT RELEASED

`v1.2.0` is prepared as a minor release candidate. Repository manifests are normalized to `1.2.0`, but the latest published GitHub Release remains `v1.1.2` until R7 live installed-host evidence is reconciled and the separately governed R8 publication gate completes.

### Added

- Delegated Phase B instruction-level autonomous progression with approved execution envelopes, six transition dispositions, checkpoints, bounded remediation, capacity handoff, current evidence requirements, and default-deny external-action authority.
- The Tuner cross-specialist coordination stack through Phases 1-4: contract assembly, missing-owner and contradiction detection, semantic invalidation, evidence continuity, typed in-memory coordination records, deterministic transitions/rejections, minimal specialist re-entry, and bounded Conductor-owned runtime integration.
- Spec Kitty-derived governed phase execution contracts: `OrchestraRuntimeEnvelope`, `OrchestraCorrelationID`, `OrchestraPhaseRetrospective`, the 15-field `ApprovedUnitPlan` extension, `OrchestraStatusProjection`, and `OrchestraWorktreeContract`.
- Cross-layer integrity audit profiles for frontend-to-backend synchronicity, backend-to-persistence integrity, and language-neutral cross-module logical flow using the existing Conductor -> Tuner -> specialist -> Overseer -> Arbiter ownership model.
- Delegated Phase C repository host-reliability contracts and deterministic adversarial fixtures covering reset/resume, active-host handoff, capacity waits, stale identity, incomplete checkpoints, scaffold-only hosts, authority expansion, and duplicate replay.
- Fail-closed autonomous merge-readiness protocol, machine-readable evaluation fixtures, and runtime regressions requiring green canonical baseline, exact-head evidence, complete successful required checks, changelog freshness, expected-head merge guards where supported, and independent post-merge verification.
- `docs/releases/v1.2.0-governed-orchestration-release-candidate.md` as the source-backed candidate release note and publication-boundary record.

### Changed

- Reconciled Delegated Phase D against the existing trusted runtime. PR #226 concluded `NO_DUPLICATE_RUNTIME_EXTENSION_REQUIRED` for `v1.2.0`; no competing runtime model was added.
- Reconciled canonical delegated-governance state so stale Phase C/D not-started claims and false live-host promotion are rejected by executable consistency validation.
- Normalized the root, Claude Code, Codex, and scaffold adapter version surfaces to `1.2.0` without changing adapter maturity or publishing any IDE marketplace package.
- Updated README, project context/state, session handoff, roadmap, compatibility, installation, and Codex adapter documentation to distinguish release-candidate metadata from the current public release.
- Consolidated the previously fragmented post-`v1.1.2` unreleased changelog entries into this release-candidate record while preserving detailed implementation evidence in Git and pull-request history.

### Clean Replay and Governance Hardening

The first autonomous finalization experiment was rolled back to the verified recovery point and preserved as audit evidence. The accepted clean replay and hardening sequence is:

- R1 / PR #223 - Spec Kitty Phase 3 and roadmap reconciliation.
- R2 / PR #224 - backend-to-persistence and cross-module logical-flow integrity.
- R3 / PR #225 - delegated Phase C repository host-reliability contract after bounded fixture remediation and a fully fresh exact-head matrix.
- R4 / PR #226 - Phase D runtime-overlap reconciliation with no duplicate runtime extension required.
- R5 / PR #227 - autonomous merge-readiness hardening.
- R5B / PR #228 - delegated-governance current-state reconciliation, merged at `fbe4532ba2083feaa7ed9fcda2988843f1237a78` and independently verified on canonical `main`.
- R6 - `v1.2.0` release-candidate metadata, public documentation, changelog, and release-note preparation.

Historical fail-open merge behavior from the first experiment is not successful validation precedent.

### Capability Merge Map

Key post-`v1.1.2` canonical milestones include:

- PR #190 - Delegated Phase B instruction-level progression.
- PR #191 - Phase B post-merge synchronization.
- PR #197 - The Tuner Phase 2 evidence identity and continuity.
- PR #198 - The Tuner Phase 3 typed in-memory coordination runtime.
- PR #200 - The Tuner Phase 4 scenario validation and runtime integration.
- PR #201 - Tuner Phase 4 post-merge continuity state.
- PR #208 - Spec Kitty-derived Phase 2 governed execution contracts.
- PR #210 - Spec Kitty-derived Phase 3A design and ownership package.
- PR #212 - `OrchestraStatusProjection`.
- PR #214 - `OrchestraWorktreeContract` and Phase 3 completion.
- PR #216 - frontend-to-backend synchronicity contract.
- PR #223 - clean replay roadmap/state closeout.
- PR #224 - backend-to-persistence and cross-module logical-flow profiles.
- PR #225 - Delegated Phase C repository host-reliability contract.
- PR #226 - Delegated Phase D overlap reconciliation.
- PR #227 - autonomous merge-readiness hardening.
- PR #228 - delegated-governance current-state reconciliation.

### Compatibility and Authority Boundaries

- Codex, Claude Code, and Antigravity retain supported integration surfaces; version normalization does not by itself prove live installed-host continuity.
- Cursor, Windsurf, VS Code/VSCodium, JetBrains, Zed, and Neovim remain scaffold-only. No scaffold is graduated or marketplace-published by R6.
- Existing authority, immutable run-scoped capabilities, bounded delegation, lifecycle, coordination ownership, evidence identity, and default-deny external-action controls remain unchanged.
- No persistent collaboration storage, SQLite, migrations, RPC, network daemon, remote worker, background agent, production deployment, or automatic policy activation is added by the release candidate.

### Evidence Boundary

Repository CI proves deterministic repository behavior for the exact candidate revision. It does not prove an installed Codex reset/resume, installed Antigravity reset/resume, real live cross-host continuation, or active Claude Code runtime continuity.

```text
REPOSITORY_SIMULATION != LIVE_HOST_EVIDENCE
LIVE_INSTALLED_HOST_VALIDATION=PENDING_LOCAL_HOST_VALIDATION
```

R7 host-derived evidence remains a publication gate.

### Publication Boundary

R6 does **not** create or publish `v1.2.0`. It performs no tag creation, GitHub Release publication, deployment, marketplace graduation, installed-host mutation, policy activation, force push, or history rewrite.

Publication requires a separately authorized R8 gate after R6 is merged and independently verified and R7 live-host evidence is reconciled.

---

## v1.1.2 - Trusted Runtime Authority

Published July 14, 2026.

### Added

- Trusted runtime composition with explicit finite `ACTIVE` and `COMPATIBILITY` authority modes.
- Immutable run-scoped runtime capability manifests and fail-closed authority/capability enforcement before governance.
- Bounded in-process specialist delegation with authority and capability subset enforcement, depth limits, specialist identity checks, and explicit context minimization.
- Structured lifecycle control with deterministic terminal replay, conflict rejection, and exact state transitions.
- `RuntimeExecutor` integration with authority and capability checks before governance and adapter execution.
- Adversarial validation for initialization, escalation, provenance, binding ownership, delegation, lifecycle, execution ordering, replay, and audit-sink failure paths.
- Deterministic non-authorizing audit events.
- Four governed Artificer promotions finalized as `IMPLEMENTED` with synchronized Pattern Catalog records and preserved provenance/attribution boundaries.

### Changed

- Normalized approved plugin and scaffold-package metadata to `1.1.2` without changing scaffold maturity.
- Refreshed release, setup, compatibility, runtime, project-state, Codex, roadmap, architecture, and handoff documentation for the trusted runtime authority baseline.

See [v1.1.2 release notes](docs/releases/v1.1.2-trusted-runtime-authority.md).

---

## v1.1.1 - Post-Release Hardening

### Changed

- Hardened release-surface and startup-state validation, including Codex metadata and structured branch/version claims.
- Converted PowerShell and shell validation entrypoints into thin wrappers around canonical Python validators to reduce cross-platform drift.
- Hardened update and rollback guidance with fast-forward-only pulls, canonical post-update validation, and recovery-branch guidance.
- Fixed runtime context assembly so adapter-provided `ContextPackage` metadata is preserved and enriched rather than bypassed.

---

## v1.1.0 - Specialist Governance & Boundary Standard

### Added

- Added the shared `docs/project/SPECIALIST_AUTHORING_STANDARD.md` and normalized specialist authoring expectations.

### Changed

- Clarified governance, specialist, routing, validation, local-safety, and handoff boundaries across the public specialist set and Codex exports without changing trusted runtime behavior.
- Strengthened Cloak, Conductor, Ponytail, Clockwork, Cipher, Overseer, Chronicler, Scribe, Weaver, Governor, and Steward documentation consistency.

---

## v1.0.0 - Portable Runtime

### Release Highlights

- Added `orchestra_runtime/` as the shared runtime core for routing, manifest parsing, skill loading, governance validation, execution flow, and audit logging.
- Added `PRAP v1` as the stable Portable Runtime Adapter Protocol for host metadata, capabilities, compatibility, and validation.
- Added thin adapter support for Codex, Claude Code, Antigravity, Cursor, Windsurf, VS Code/VSCodium compatibility, JetBrains, Zed, and Neovim.
- Added scaffold-only packaging surfaces for Cursor, Windsurf, VS Code, JetBrains, Zed, and Neovim.
- Normalized release-facing documentation, compatibility guidance, and manifest metadata for the Portable Runtime baseline.

---

## Earlier Repository History

Pre-`v1.0.0` implementation detail, router-first evolution, Artificer phases, governance calibration, prompt-load work, cross-platform validation changes, and specialist foundation history remain preserved in Git history and the repository's decision, roadmap, governance, and handoff records. The changelog is intentionally release-oriented rather than a duplicate of every commit.
