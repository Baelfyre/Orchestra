# Branch Protection Setup Guide

## Purpose

This guide records the current GitHub `Protect main` ruleset baseline for Orchestra's `main` branch and the validation signals that the automation layer must mirror.

It is aligned with `REQUIRED_STATUS_CHECKS_REVIEW.md` and `AUTONOMOUS_MERGE_READINESS_PROTOCOL.md`.

## Scope

This guide is documentation-only. It does not configure GitHub settings automatically.

The existence of this file must never be treated as evidence that protection is active. Repository settings must be inspected and tested separately through the live GitHub configuration.

## Protected Branch

Protect:

- `main`

## Current Required Validation Signals

Require the active GitHub check contexts corresponding to these jobs before merging into `main`:

- Governance Check / `governance-check`;
- validate / `validate`;
- validate / `runtime-tests`;
- Cross-platform Validation / `native-windows-latest`;
- Cross-platform Validation / `native-ubuntu-latest`;
- Cross-platform Validation / `native-macos-latest`;
- CodeQL / `Analyze (actions)`;
- CodeQL / `Analyze (python)`.

Workflow and job names are distinct concepts in GitHub. When configuring rules, select the actual check contexts presented by a current pull request rather than assuming the human-readable workflow title is the exact stored context.

## Current Solo-Maintainer Protection Profile

The accepted `Protect main` settings are:

```text
Restrict creations: OFF
Restrict updates: OFF
Restrict deletions: ON
Require linear history: ON
Require deployments to succeed: OFF
Require signed commits: ON
Require a pull request before merging: ON
Required approvals: 0
Dismiss stale approvals when new commits are pushed: ON
Require review from specific teams: OFF
Require review from Code Owners: OFF
Require approval of the most recent reviewable push: OFF
Require conversation resolution before merging: ON
Allowed merge methods: Squash only
Require status checks to pass: ON
Require branches to be up to date before merging: ON
Do not require status checks on creation: OFF
Block force pushes: ON
Require code scanning results: OFF
Require code quality results: OFF
Restrict code coverage: OFF
Automatically request Copilot code review: OFF
```

The bypass list is intentionally retained for operational access by trusted roles/apps. Do not treat membership in that list as governance authorization.

```text
BYPASS_CAPABILITY != GOVERNANCE_AUTHORIZATION
```

Ordinary governed autonomous execution must still use the pull-request path, exact-head evidence, Squash merge, and independent post-merge verification. Any deliberate bypass is a separate authority decision.

## Why Squash Only

The ruleset requires linear history and signed commits. Orchestra therefore standardizes autonomous merging on Squash for this repository.

A squash merge creates a new canonical commit SHA. Post-merge verification must validate the canonical squash result rather than require the reviewed PR head SHA to remain in `main` ancestry.

Required post-merge proof includes:

- reviewed head SHA and tree;
- exact pre-merge base;
- canonical squash commit and parent;
- canonical tree equals reviewed tree;
- reviewed-to-canonical content diff is empty;
- canonical squash commit signature is verified;
- independent canonical remote read.

Rebase is not an allowed merge method under the current ruleset. Merge commits are incompatible with the current linear-history requirement.

## Setup / Review Steps

1. Open the Orchestra repository on GitHub.
2. Open `Settings` -> `Rules` -> `Rulesets` -> `Protect main`.
3. Confirm the rule targets `main` and is Active.
4. Confirm the solo-maintainer protection profile above.
5. Confirm Allowed merge methods is `Squash` only.
6. Confirm all eight required check contexts are present.
7. Confirm required approvals remains `0` while the repository has no independent maintainer reviewer.
8. Confirm conversation resolution, signed commits, linear history, branch-up-to-date, restricted deletion, and blocked force pushes remain enabled.
9. Leave the current bypass list unchanged unless a separate repository-hardening decision explicitly changes it.
10. Save changes and use a current PR to verify enforcement behavior.

## Mandatory Verification After Setup

Use a safe controlled PR and prove all of the following from live GitHub behavior:

1. The PR cannot ordinarily merge while a required check is queued or in progress.
2. The PR cannot ordinarily merge when `governance-check` fails.
3. The PR cannot ordinarily merge when `runtime-tests` fails.
4. The PR cannot ordinarily merge when any native Windows, Ubuntu, or macOS job fails.
5. The PR cannot ordinarily merge when either required CodeQL Analyze job fails or is missing.
6. The PR cannot ordinarily merge with unresolved review conversations.
7. The branch must be up to date before merge.
8. Squash is the only ordinary merge method offered by the ruleset.
9. The resulting canonical squash commit has a verified signature.
10. Direct force pushes and deletion of `main` are blocked for non-bypass operation.
11. The existence of bypass-capable actors does not cause Orchestra's client-side controller to skip evidence or record a bypassed transition as governance-ready.

Do not mark branch protection verified solely from a screenshot or rule name. Live merge behavior and independent canonical reads are stronger evidence.

## Client-Side Protocol Still Applies

Server-side protection is defense in depth. Autonomous execution must still follow `AUTONOMOUS_MERGE_READINESS_PROTOCOL.md`.

```text
missing checks -> WAIT_FOR_EVIDENCE
pending checks -> WAIT_FOR_EVIDENCE
failed required check -> BLOCK
stale head -> STALE_EVIDENCE
red main baseline -> REMEDIATE_BASELINE_FIRST
ruleset drift -> BLOCK
non-Squash merge -> BLOCK
unauthorized bypass -> BLOCK
```

`mergeable: true`, a bypass-capable actor, and a merge API that would accept the request do not override those results.

## Workflow Migration Notes

Do not retire or rename a required validation workflow/job until:

- the replacement signal is visible and green on `main` and pull requests;
- the live ruleset is updated;
- the autonomous merge-readiness inventory is updated;
- the migration is documented in `CHANGELOG.md`;
- the new signal has been proven on a controlled pull request.

## Current Recommendation

Keep the current `Protect main` profile unchanged unless a separately reviewed repository-policy change is required. Keep all eight required checks active and keep Squash as the only allowed merge method.
