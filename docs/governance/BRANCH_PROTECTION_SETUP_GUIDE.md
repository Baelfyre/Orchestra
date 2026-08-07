# Branch Protection Setup Guide

## Purpose

This guide provides the recommended GitHub branch protection or ruleset setup for Orchestra's `main` branch.

It mirrors the fail-closed merge evidence defined by `REQUIRED_STATUS_CHECKS_REVIEW.md` and `AUTONOMOUS_MERGE_READINESS_PROTOCOL.md`.

## Scope

This guide is documentation-only. It does not configure GitHub settings automatically.

The existence of this file must never be treated as evidence that protection is active. Repository settings must be inspected and tested separately by an administrator with access to the live configuration.

## Protected Branch

Protect:

- `main`

## Minimum Required Validation Signals

Require the active GitHub check contexts corresponding to these minimum jobs before merging into `main`:

- Governance Check / `governance-check`;
- validate / `validate`;
- validate / `runtime-tests`;
- Cross-platform Validation / `native-windows-latest`;
- Cross-platform Validation / `native-ubuntu-latest`;
- Cross-platform Validation / `native-macos-latest`.

Additional security, CodeQL, or repository-specific required checks remain additive.

Workflow and job names are distinct concepts in GitHub. When configuring rules, select the actual check contexts presented by a current pull request rather than assuming the human-readable workflow title is the exact stored context.

## Recommended Protection Settings

Enable, where supported by the repository plan:

1. Require a pull request before merging.
2. Require status checks to pass before merging.
3. Require the minimum validation signals above.
4. Require branches to be up to date before merging when that does not conflict with the repository's merge strategy.
5. Require conversation resolution before merging.
6. Block force pushes to `main`.
7. Block deletion of `main`.
8. Apply protection to administrators and automation/bot identities where practical so privileged credentials do not silently bypass red checks.

Optional according to maintainer policy:

- signed commits;
- linear history;
- independent review approval;
- merge queue.

A merge queue is preferable for high-concurrency development because GitHub can validate the final merge candidate instead of relying only on an earlier head snapshot.

## Setup Steps

1. Open the Orchestra repository on GitHub.
2. Open `Settings` and the repository's branch-protection or ruleset controls.
3. Create or edit the rule targeting `main`.
4. Enable pull-request and required-status-check enforcement.
5. Use a current test PR to identify the actual check contexts for:
   - `governance-check`;
   - `validate`;
   - `runtime-tests`;
   - `native-windows-latest`;
   - `native-ubuntu-latest`;
   - `native-macos-latest`.
6. Add those contexts as required.
7. Configure administrator/automation bypass policy deliberately; avoid broad bypass for autonomous development credentials.
8. Block force pushes and branch deletion for `main`.
9. Save the rule.

## Mandatory Verification After Setup

Use a disposable test PR or another safe controlled change and prove all of the following from the live GitHub UI/settings behavior:

1. The PR cannot merge while a required check is queued or in progress.
2. The PR cannot merge when `governance-check` fails.
3. The PR cannot merge when `runtime-tests` fails even if coverage remains above threshold.
4. The PR cannot merge when any native Windows, Ubuntu, or macOS job fails.
5. The PR cannot merge when a required check is missing.
6. The PR can merge only after all required checks pass.
7. The automation identity used for autonomous development cannot bypass these failures unless a separately governed emergency path explicitly permits it.
8. Direct pushes, force pushes, and deletion of `main` behave exactly as the documented policy expects.

Do not mark branch protection verified until these behaviors are observed. A settings screenshot or configured rule name alone is weaker evidence than an actual blocked-merge test.

## Client-Side Protocol Still Applies

Server-side protection is defense in depth. Autonomous execution must still follow `AUTONOMOUS_MERGE_READINESS_PROTOCOL.md`.

In particular:

```text
missing checks -> WAIT_FOR_EVIDENCE
pending checks -> WAIT_FOR_EVIDENCE
failed required check -> BLOCK
stale head -> STALE_EVIDENCE
red main baseline -> REMEDIATE_BASELINE_FIRST
```

`mergeable: true` and a merge API that would accept the request do not override those results.

## Workflow Migration Notes

Do not retire or rename a validation workflow/job until:

- the replacement signal is visible and green on `main` and pull requests;
- the live branch protection/ruleset is updated;
- the autonomous merge-readiness inventory is updated;
- the migration is documented in `CHANGELOG.md`;
- the new signal has been proven to block a deliberately failing test PR.

## Current Recommendation

Keep Governance Check, validate, and Cross-platform Validation active. Require their six minimum jobs as merge evidence until a separately validated CI consolidation replaces this contract.
