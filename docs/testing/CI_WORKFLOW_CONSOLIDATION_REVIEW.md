# CI Workflow Consolidation Review

## Status

Orchestra currently has three validation workflows:

| Workflow | File | Current role |
|---|---|---|
| validate | `.github/workflows/validate.yml` | Legacy/simple Ubuntu behavior validation entry point |
| Governance Check | `.github/workflows/governance-check.yml` | Primary strict governance and release-readiness gate |
| Cross-platform Validation | `.github/workflows/cross-platform-validation.yml` | Native Ubuntu/macOS validation coverage |

## Findings

### 1. `validate.yml`

`validate.yml` runs the PowerShell behavior validation wrapper on `ubuntu-latest`.

This is useful as a small compatibility check, but it overlaps with the broader behavior validation already executed by the governance and cross-platform workflows.

### 2. `governance-check.yml`

`governance-check.yml` is the strongest governance gate. It runs strict governance, router benchmark validation, negative benchmark validation, prompt load checks, Dagger simulation tests, governance behavior tests, general behavior tests, plugin syntax validation, and artifact upload.

This workflow should remain a required gate.

### 3. `cross-platform-validation.yml`

`cross-platform-validation.yml` provides native runner coverage across Ubuntu and macOS. It verifies POSIX helper scripts, runs core validators, executes behavior tests, checks runtime guardrails, validates prompt-load thresholds, validates `plugin.json`, and runs whitespace checks.

This workflow should remain a required gate for portability.

## Consolidation Decision

Do not remove or weaken any workflow yet.

The next safe consolidation step is to classify `validate.yml` as a legacy compatibility workflow until repository branch-protection requirements are confirmed. Removing it immediately may break expected check names if GitHub branch protection or external status expectations depend on `validate`.

## Recommended Future Change

After branch-protection requirements are confirmed, choose one of these options:

1. Keep `validate.yml` as a fast legacy compatibility check.
2. Convert `validate.yml` to `workflow_dispatch` only.
3. Retire `validate.yml` after confirming no required status check depends on it.

## Current Recommendation

Keep all three workflows active for now.

Treat `Governance Check` and `Cross-platform Validation` as the primary gates. Treat `validate` as a lightweight compatibility check pending a branch-protection review.