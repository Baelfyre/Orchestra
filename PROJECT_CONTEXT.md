# Orchestra Project Context

## Project Name
Orchestra

## Project Purpose
A governance-first specialist skill framework that routes complex AI-assisted software work through focused, auditable specialist skills, designed for compatibility across multiple IDEs and coding hosts.

## Project Type
Open-source developer tooling and AI orchestration framework

## Current Stage
v1.1.0 (Specialist Governance & Boundary Standard), publicly released, actively maintained

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
- `main` is already governed by required pull-request review, required status checks (`governance-check`, `validate`, `Analyze (actions)`, `Analyze (python)`), and signed-commit expectations per `docs/CONTRIBUTING.md`, which is consistent with Recommended-tier coordination needs.
- Maintainers may raise this to Strict-Governed later if adoption, write scope, or release criticality increases.

## Safety Boundaries
- Dagger guardrail system enforces warning-first, then blocking, behavior for governance-sensitive actions, per `docs/CONTRIBUTING.md`.
- State-lock mechanism guards against concurrent write collisions.
- Scaffold-only adapters (Cursor, Windsurf, JetBrains, Zed, Neovim) must not be represented as production-ready or marketplace-published until formally graduated per `docs/project/SCAFFOLD_ADAPTER_GRADUATION_CRITERIA.md`.
- No vendoring of external plugin code, and no claiming unsupported compatibility or compliance, per `docs/CONTRIBUTING.md`.

## Validation Requirements
- `pytest tests/runtime` must pass with `--cov-fail-under=90` as enforced in CI via `validate.yml`.
- `python tests/behavior/run_tests.py` must pass.
- `python scripts/governance_check.py --strict` must pass as enforced in CI via `governance-check.yml`.
- Manifest and packaging validators (`validate_claude_plugin.py`, `validate_ide_packaging.py`, `validate_manifest.py`, `validate_structure.py`) must pass.
- `python scripts/preflight_sync_check.py` must be run against `origin/main` before starting a new local editing session, per `docs/CONTRIBUTING.md`.

## Known Constraints
- Cursor, Windsurf, JetBrains, Zed, and Neovim adapters are scaffold-only and not yet published to their respective marketplaces.
- `tests/behavior/run-tests.ps1` is intentionally maintained in parallel with `run_tests.py` as the primary validation path for Windows environments, per `docs/MATURITY.md`.
- Direct pushes to `main` are not part of the normal workflow; changes go through a branch and pull request except for documented maintainer bypass recovery cases.

## Known Non-Goals
- Orchestra does not store, process, or transmit end-user or client data itself.
- Orchestra does not aim to make `PROJECT_CONTEXT.md` universally mandatory for every project that adopts it, per `docs/governance/PROJECT_CONTEXT_ENFORCEMENT_POLICY.md`.
- This document does not modify CI enforcement on its own; wiring `validate_project_context.py` into a workflow is a separate, explicit step.

## Maintainer Approval Rules
- Changes to governance level, scaffold graduation status, or CI enforcement gates require pull-request review and at least one approval before merge, per `docs/CONTRIBUTING.md`.
- Maintainer bypass is a recovery path for urgent ruleset repair, CI repair, or access recovery only, not a default development path, and must be documented afterward if it changes governance or CI behavior.

## User or Maintainer Preferences
Not yet decided. No project-specific maintainer preferences beyond `docs/CONTRIBUTING.md` are currently documented for this field.

## Last Reviewed
2026-07-10
