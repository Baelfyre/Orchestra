# Orchestra Project Context

## Project Name
Orchestra

## Project Purpose
A governance-first specialist skill framework that routes complex AI-assisted software work through focused, auditable specialist skills, designed for compatibility across multiple IDEs and coding hosts.

## Project Type
Open-source developer tooling and AI orchestration framework

## Current Stage
Release-candidate metadata `v1.2.0` (`PREPARED_NOT_RELEASED`). The current public GitHub Release remains `v1.1.2` until the separate publication gate completes. Canonical `main` includes R7/R7R and Governed Autonomy Modes through signed Squash commit `900f88d7a3ed480ae8b910e6ba204008a72d2784` from PR #232. GA-0 concluded `NO_DUPLICATE_AUTHORITY_MODEL`; GA-1 through GA-7 are `MERGED_VERIFIED`, and invalidated release evidence is refreshed and independently green. No release, deployment, installed-integration refresh, or policy activation has occurred. R8 remains separately human-authorized.

## Primary Users
Developers and maintainers who install Orchestra as a plugin, skill set, or runtime package inside a supported or scaffold-only IDE or coding host (Claude Code, Codex, Antigravity, Cursor, Windsurf, JetBrains, Zed, Neovim)

## Data Sensitivity
Not applicable by default. Orchestra itself does not store, process, or transmit end-user or client data. Data sensitivity depends on the downstream project a maintainer applies Orchestra to, per `docs/CONTRIBUTING.md` instructions to exclude private projects, personal data, and client details from the repository itself.

## Runtime or Deployment Context
Distributed via GitHub as a plugin or marketplace package (`.claude-plugin/`, `.codex-plugin/`) and as a Python runtime package (`orchestra_runtime/`). Consumed locally inside a developer's IDE or coding host; not deployed as a hosted service.

## Governance Level
Recommended

Guidance used for this classification:
- Orchestra is a public, multi-agent development repository with write-permission automation surfaces such as Dagger guardrails and state-lock scripts, which is a listed risk signal above pure Advisory.
- Orchestra does not itself handle real end-user data, client data, production business data, or destructive-by-default operations, so automatic Strict-Governed classification is not required.
- `main` is governed by pull-request review and required status checks, which is consistent with Recommended-tier coordination needs.
- Maintainers may raise this to Strict-Governed later if adoption, write scope, or release criticality increases.

## Safety Boundaries
- Dagger guardrail system enforces warning-first, then blocking, behavior for governance-sensitive actions, per `docs/CONTRIBUTING.md`.
- State-lock mechanism guards against concurrent write collisions.
- Scaffold-only adapters (Cursor, Windsurf, JetBrains, Zed, Neovim) must not be represented as production-ready or marketplace-published until formally graduated per `docs/project/SCAFFOLD_ADAPTER_GRADUATION_CRITERIA.md`.
- Runtime envelopes are transport metadata, not execution authority. Correlation IDs are observational identifiers. Retrospectives are supplementary audit records. `ApprovedUnitPlan` governance decision references do not replace execution-envelope authority.
- `OrchestraStatusProjection` is read-only and derived; it does not mutate repository state, Git refs, or governance policy. It is not a source of truth. Missing or conflicting data reports UNKNOWN. Exit codes report command execution success only and do not create governance authority.
- `OrchestraWorktreeContract` is optional and host-capability-dependent. Worktree isolation must not be mandatory for single-agent or lightweight execution. Cleanup is `EXPLICIT_HOST_ACTION_ONLY`; no automatic deletion of dirty, unrelated, or user-owned worktrees is permitted.
- The cross-module audit protocol coordinates specialist-owned findings and evidence; it creates no implementation, Git, merge, release, deployment, or policy authority.
- Repository simulation and GitHub CI are not live installed-host evidence. Accepted R7 evidence is recorded separately for installed Codex and Antigravity continuity and Claude Code packaging compatibility; Claude Code active runtime continuity remains unclaimed under `SCAFFOLD_ONLY` maturity.
- Governed Autonomy Profiles are reduction-only workflow gates. `HUMAN_GOVERNED` is the safe default, children cannot exceed parents, and no profile creates release, deployment, policy, destructive, force-push, history-rewrite, or authority-expansion permission.
- No vendoring of external plugin code, and no claiming unsupported compatibility or compliance, per `docs/CONTRIBUTING.md`.

## Validation Requirements
- `pytest tests/runtime` must pass with `--cov-fail-under=90` as enforced in CI via `validate.yml`.
- `python tests/behavior/run_tests.py` must pass.
- `python scripts/governance_check.py --strict` must pass as enforced in CI via `governance-check.yml`.
- Manifest and packaging validators (`validate_claude_plugin.py`, `validate_ide_packaging.py`, `validate_manifest.py`, `validate_structure.py`) must pass.
- Cross-layer contract validators and their behavior tests must pass for affected revisions.
- `python scripts/validate_governed_autonomy_modes_contract.py` and its focused runtime tests must pass when autonomy-profile contracts change.
- `python scripts/preflight_sync_check.py` must be run against `origin/main` before starting a new local editing session, per `docs/CONTRIBUTING.md`.

## Known Constraints
- Cursor, Windsurf, JetBrains, Zed, and Neovim adapters are scaffold-only and not yet published to their respective marketplaces.
- `tests/behavior/run-tests.ps1` is intentionally maintained in parallel with `run_tests.py` as the primary validation path for Windows environments, per `docs/MATURITY.md`.
- Direct pushes to `main` are not part of the normal workflow; changes go through a branch and pull request except for documented maintainer bypass recovery cases.
- Installed Codex and Antigravity parity, host context-reset behavior, and Windows filesystem-specific behavior require host-local evidence in addition to repository CI.
- `v1.2.0` metadata in the repository is release-candidate state, not evidence of a published tag or GitHub Release.

## Known Non-Goals
- Orchestra does not store, process, or transmit end-user or client data itself.
- Orchestra does not aim to make `PROJECT_CONTEXT.md` universally mandatory for every project that adopts it, per `docs/governance/PROJECT_CONTEXT_ENFORCEMENT_POLICY.md`.
- This document does not modify CI enforcement on its own.
- A merged implementation or version bump is not a released capability until the separate tag and GitHub Release gates complete.

## Maintainer Approval Rules
- Changes to governance level, scaffold graduation status, CI enforcement gates, merge state, or release state require their applicable pull-request and human-authorization gates.
- Maintainer bypass is a recovery path for urgent ruleset repair, CI repair, or access recovery only, not a default development path, and must be documented afterward if it changes governance or CI behavior.

## User or Maintainer Preferences
Not yet decided. No project-specific maintainer preferences beyond `docs/CONTRIBUTING.md` are currently documented for this field.

## Last Reviewed
2026-08-09
