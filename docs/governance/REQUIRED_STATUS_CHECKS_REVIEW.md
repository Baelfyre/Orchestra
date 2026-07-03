# Required Status Checks Review

## Purpose

This document defines the recommended required GitHub status checks for Orchestra before merging changes into `main`.

It follows the CI workflow consolidation review and keeps validation policy explicit before any workflow is retired, renamed, or converted to manual-only execution.

## Current Validation Workflows

| Workflow | Recommended requirement status | Reason |
|---|---|---|
| Governance Check | Required | Primary strict governance and release-readiness gate |
| Cross-platform Validation | Required | Confirms native Ubuntu and macOS validation coverage |
| validate | Temporarily required or compatibility-only | Legacy/simple behavior validation check; keep until branch-protection dependencies are confirmed |

## Recommended Required Checks

The following checks should be required for pull requests targeting `main`:

1. `Governance Check`
2. `Cross-platform Validation`

If GitHub branch protection currently requires `validate`, keep it enabled until a separate branch-protection update confirms it can be safely removed.

## Policy

Do not remove or rename a workflow that may be configured as a required status check unless one of the following is true:

1. Branch protection has been reviewed and updated.
2. The replacement workflow is already passing on `main`.
3. The migration is documented in `CHANGELOG.md`.
4. A PR confirms the old and new check names are both visible before removing the old one.

## Migration Path

### Step 1: Keep all checks active

Current safe state:

- `Governance Check`: active
- `Cross-platform Validation`: active
- `validate`: active

### Step 2: Confirm branch protection

Confirm whether `validate` is configured as a required status check in GitHub repository settings.

### Step 3: Decide future treatment for `validate`

Choose one:

1. Keep `validate` as a lightweight compatibility workflow.
2. Convert `validate` to manual-only after required status checks are updated.
3. Retire `validate` after confirming no required protection depends on it.

## Current Recommendation

Require `Governance Check` and `Cross-platform Validation`.

Keep `validate` active until branch protection is confirmed.