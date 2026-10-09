# CI Workflow Consolidation Review

> [!IMPORTANT]
> Historical note: this document originally reviewed the workflow layout before `validate.yml` moved to the Python behavior runner plus a separate runtime coverage job. The workflow inventory below has been updated to match the current repo state.

## Status

Orchestra currently has three validation workflows:

| Workflow | File | Current role |
|---|---|---|
| validate | `.github/workflows/validate.yml` | Ubuntu validation workflow running the Python behavior suite plus a separate runtime coverage gate |
| Governance Check | `.github/workflows/governance-check.yml` | Primary strict governance and release-readiness gate |
| Cross-platform Validation | `.github/workflows/cross-platform-validation.yml` | Native Ubuntu/macOS validation coverage |

## Findings

### 1. `validate.yml`

`validate.yml` now runs two Python-based jobs on `ubuntu-latest`.

The `validate` job runs `python tests/behavior/run_tests.py`. The `runtime-tests` job runs `python -m pytest tests/runtime --cov=orchestra_runtime --cov-report=term-missing --cov-fail-under=90`.

This workflow is no longer a PowerShell compatibility-only path. It is the narrow Ubuntu validation entry point for behavior checks plus runtime coverage enforcement.

### 2. `governance-check.yml`

`governance-check.yml` is the strongest governance gate. It runs strict governance, router benchmark validation, negative benchmark validation, prompt load checks, Dagger simulation tests, governance behavior tests, general behavior tests, plugin syntax validation, and artifact upload.

This workflow should remain a required gate.

### 3. `cross-platform-validation.yml`

`cross-platform-validation.yml` provides native runner coverage across Ubuntu and macOS. It verifies POSIX helper scripts, runs core validators, executes behavior tests, checks runtime guardrails, validates prompt-load thresholds, validates `plugin.json`, and runs whitespace checks.

This workflow should remain a required gate for portability.

## Consolidation Decision

Do not remove or weaken any workflow yet.

The next safe consolidation step is to treat this document as a historical consolidation snapshot and re-evaluate workflow overlap against the current Python-based `validate.yml` behavior. Removing or renaming workflows may still affect required status checks.

## Recommended Future Change

After branch-protection requirements are confirmed, choose one of these options:

1. Keep `validate.yml` as the focused Ubuntu behavior-plus-runtime workflow.
2. Narrow duplication with other workflows only after confirming required status check names and release expectations.
3. Retire or rename `validate.yml` only after branch-protection requirements are confirmed.

## Current Recommendation

Keep all three workflows active for now.

Treat `Governance Check` and `Cross-platform Validation` as the broader governance and portability gates. Treat `validate` as the focused Ubuntu behavior and runtime coverage workflow, not as a legacy PowerShell compatibility check.
