# Branch Protection Setup Guide

## Purpose

This guide provides the recommended GitHub branch protection setup for Orchestra's `main` branch.

It follows the required status checks review and translates the documented policy into practical repository settings.

## Scope

This guide is documentation-only.

It does not configure GitHub settings automatically. Branch protection must be configured manually in GitHub repository settings by a repository administrator.

## Recommended Protected Branch

Protect:

- `main`

## Recommended Required Status Checks

Require the following checks before merging into `main`:

- `Governance Check`
- `Cross-platform Validation`

Keep `validate` active until branch-protection dependencies are confirmed.

If `validate` is already configured as a required status check, do not remove it until a separate branch-protection update confirms that it can be safely retired or converted to manual-only execution.

## Recommended Branch Protection Settings

Enable:

1. Require a pull request before merging.
2. Require status checks to pass before merging.
3. Require branches to be up to date before merging, if the project prefers stricter merge safety.
4. Require conversation resolution before merging.
5. Block force pushes.
6. Block branch deletion.

Optional, depending on maintainer preference:

1. Require signed commits.
2. Require linear history.
3. Require review approval before merging.
4. Apply rules to administrators.

## Setup Steps

1. Open the repository on GitHub.
2. Go to `Settings`.
3. Go to `Branches`.
4. Under branch protection rules, create or edit the rule for `main`.
5. Enable required status checks.
6. Add:
   - `Governance Check`
   - `Cross-platform Validation`
7. Keep `validate` if it is already required.
8. Save the branch protection rule.

## Validation After Setup

After branch protection is configured:

1. Open a test pull request.
2. Confirm required checks appear in the merge box.
3. Confirm the PR cannot merge while required checks are pending or failing.
4. Confirm the PR can merge after required checks pass.
5. Confirm direct pushes to `main` are blocked unless intentionally allowed.

## Migration Notes

Do not retire, rename, or convert `validate.yml` to manual-only until branch protection confirms it is not required.

If a workflow is renamed, GitHub may treat it as a new status check. Keep old and new checks running together long enough to confirm the new check appears reliably on pull requests.

## Current Recommendation

Required:

- `Governance Check`
- `Cross-platform Validation`

Temporary compatibility:

- `validate`

Keep all three workflows active until branch protection has been manually reviewed.