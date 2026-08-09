# Autonomous Merge Readiness Protocol

## Purpose

This protocol defines Orchestra's fail-closed evidence gate for autonomous or delegated pull-request merges. It exists because GitHub may technically accept a merge even when repository validation is missing, red, stale, or bypassable. Platform capability is not governance readiness.

Canonical merge rules:

```text
GITHUB_CAN_MERGE != GOVERNANCE_READY_TO_MERGE
BYPASS_CAPABILITY != GOVERNANCE_AUTHORIZATION
```

This protocol does not grant merge authority. It constrains how already-authorized merge authority may be exercised.

## Parent Governing Rule

This protocol is the merge-specific specialization of Orchestra's Evidence-Bound Governed Transition Rule.

```text
PLATFORM_CAN_EXECUTE != GOVERNANCE_READY_TO_TRANSITION
GITHUB_CAN_MERGE != GOVERNANCE_READY_TO_MERGE
API_SUCCESS != VERIFIED_STATE
NO_EVIDENCE != APPROVAL
BYPASS_CAPABILITY != GOVERNANCE_AUTHORIZATION
```

The parent rule applies to governed phase advancement and other material state transitions, including merge, release, deployment, policy activation, protected-state mutation, destructive operations, permanent deletion, and history rewrite. Missing, pending, stale, contradictory, or failed required evidence never grants permission. Evidence belongs to the exact current state and becomes invalid when that state changes. A red canonical baseline blocks ordinary progression except for explicitly authorized bounded remediation. A successful write is not a completed transition until an independent canonical read verifies the resulting state.

Neither this protocol nor its parent rule creates or widens authority.

## Canonical `Protect main` Profile

The current Orchestra repository policy is a solo-maintainer profile. The ruleset may expose operational bypass capability to trusted roles/apps, but autonomous governance does not treat that capability as permission to skip this protocol.

The canonical profile is:

```text
Required approving reviews: 0
Dismiss stale approvals after new reviewable commits: ON
Require review from specific teams: OFF
Require Code Owner review: OFF
Require approval of most recent reviewable push: OFF
Require conversation resolution: ON

Allowed merge methods: Squash only

Restrict deletions: ON
Require linear history: ON
Require signed commits: ON
Require pull request before merging: ON
Require status checks to pass: ON
Require branches to be up to date before merging: ON
Block force pushes: ON
```

The bypass list is intentionally retained as repository-operational capability. It is non-authorizing for governed autonomous progression unless a separate explicit bypass authority is granted. Ordinary autonomous merge execution records `bypass_used=false`.

A live ruleset that is stricter than this profile may constrain progression further. A live ruleset that materially weakens this profile is policy drift and blocks autonomous merge until reviewed.

## Required Evidence Snapshot

A pre-merge snapshot must bind all evidence to one exact current PR head SHA and record:

- canonical base health;
- current PR head SHA;
- whether that head was re-read immediately before merge;
- the live `Protect main` profile;
- selected merge method;
- whether bypass was used;
- changelog freshness when significant paths changed;
- unresolved blocking findings;
- unresolved review-thread count;
- Git mergeability state;
- every required workflow/job result with its exact head SHA, status, and conclusion.

The canonical exact required-check inventory is:

| Workflow | Required job |
| --- | --- |
| Governance Check | `governance-check` |
| validate | `validate` |
| validate | `runtime-tests` |
| Cross-platform Validation | `native-windows-latest` |
| Cross-platform Validation | `native-ubuntu-latest` |
| Cross-platform Validation | `native-macos-latest` |
| CodeQL | `Analyze (actions)` |
| CodeQL | `Analyze (python)` |

Repository rules may become stricter and require additional checks. Additional required checks must also pass; this table is a minimum exact profile for the current Orchestra ruleset, not a bypass list.

## Fail-Closed Interpretation

```text
NO_CHECK_DATA = WAIT_FOR_EVIDENCE
MISSING_REQUIRED_CHECK = WAIT_FOR_EVIDENCE
QUEUED_REQUIRED_CHECK = WAIT_FOR_EVIDENCE
IN_PROGRESS_REQUIRED_CHECK = WAIT_FOR_EVIDENCE
STALE_HEAD_EVIDENCE = STALE_EVIDENCE
FAILED_REQUIRED_CHECK = BLOCK
CANCELLED_REQUIRED_CHECK = BLOCK
TIMED_OUT_REQUIRED_CHECK = BLOCK
SKIPPED_REQUIRED_CHECK = BLOCK
RED_CANONICAL_BASELINE = REMEDIATE_BASELINE_FIRST
UNRESOLVED_BLOCKER = BLOCK
UNRESOLVED_REVIEW_THREAD = BLOCK
REQUIRED_CHANGELOG_MISSING = BLOCK
RULESET_PROFILE_DRIFT = BLOCK
MERGE_METHOD_NOT_SQUASH = BLOCK
BYPASS_USED_WITHOUT_SEPARATE_AUTHORITY = BLOCK
```

A high passing-test count, passing coverage threshold, `mergeable: true`, a bypass-capable actor, or a successful merge API call cannot override a failed or missing required check.

`mergeable: true` is informational only: it means Git can construct a merge. It never proves governance readiness.

`mergeable: false` blocks because the PR has a technical merge conflict.

## Exact-Head Rule

Validation evidence is revision-specific.

Before merge:

1. Read the PR and capture the current head SHA.
2. Read the live ruleset and verify the effective policy remains compatible with the canonical profile.
3. Require `Squash` as the selected merge method.
4. Require ordinary governed execution to use no bypass.
5. Fetch fresh required workflow/job state for that exact head.
6. Require every required job to exist.
7. Require every required job status to be `completed`.
8. Require every required job conclusion to be `success`.
9. Require every job's evidence head SHA to equal the current PR head SHA.
10. Require zero unresolved review threads.
11. Re-read the PR immediately before merge.
12. If the head changed, discard prior evidence and return `STALE_EVIDENCE`.
13. Use `expected_head_sha` or the platform's equivalent compare-and-swap guard when issuing the merge.

Any remediation commit invalidates all earlier check evidence. The complete required matrix must be collected again for the new head.

## Canonical Baseline Rule

A new autonomous phase must not begin from a red canonical baseline.

```text
red canonical baseline -> REMEDIATE_BASELINE_FIRST
```

A low-risk documentation-only next phase cannot bypass a failure inherited from an earlier merge.

## Changelog Freshness

When repository governance classifies changed paths as significant, `CHANGELOG.md` must be updated in the same change set. A later release consolidation does not satisfy a current strict changelog gate unless the gate itself explicitly permits that behavior.

## Squash-Merge Verification

The Orchestra ruleset permits Squash only. A squash merge intentionally creates a new canonical commit SHA, so successful post-merge verification must not require the reviewed PR head SHA itself to remain in canonical `main` ancestry.

Instead, the controller must prove that the canonical squash result is the exact reviewed change applied to the exact pre-merge base.

Required evidence:

- exact reviewed PR head SHA;
- exact pre-merge base SHA;
- exact reviewed head tree SHA;
- exact canonical main SHA after merge;
- exact canonical main parent SHA;
- exact canonical tree SHA after merge;
- empty content diff between the reviewed head tree and canonical result;
- verified signature on the canonical squash commit;
- independent canonical remote read.

Required equivalence:

```text
canonical_tree == reviewed_tree
canonical_parent == pre_merge_base
content_diff_empty == true
canonical_signature_verified == true
```

Tree/content equivalence is not a substitute for pre-merge exact-head CI. It is the post-write proof that the newly created squash commit contains exactly the already-reviewed result.

A rebase merge is not valid under the current ruleset. A merge commit is not valid while linear history is required.

## Post-Merge Verification

A merge write is not complete merely because an API returned success.

The controller must perform a canonical remote read after the write and verify:

- the PR now reports `merged == true`;
- the observed merge method is `squash`;
- the exact canonical main SHA is resolved from the remote;
- the canonical parent equals the exact pre-merge base;
- the canonical tree equals the reviewed head tree;
- the reviewed-head-to-canonical content diff is empty;
- the canonical squash commit has a verified signature;
- the remote read corresponds to the intended repository and PR.

Only then may state advance to:

```text
MERGED_VERIFIED
```

Otherwise:

```text
MERGE_STATE_UNVERIFIED
```

An intended action, attempted action, successful API response, or actor bypass capability must not be recorded as executed governance fact without this independent canonical remote read.

## PR #230 Historical Incident Boundary

PR #230 exposed the previous ancestry-only post-merge assumption. Its reviewed head `f49a03c929be7df7c10c457a227a46532ef47854` and canonical rebase result `80f9bc71f00cc86c0021fd9da258f2eec596d7e0` have equivalent trees/content, but the reviewed head is not in canonical ancestry and the platform-generated canonical commit is unsigned.

The repository history must not be rewritten merely to satisfy the old validator. That incident requires an explicit human canonical-history disposition and forward-only governance remediation. It is not successful precedent for future unsigned or rebase merges.

## Server-Side Protection

Repository rulesets should independently enforce the current profile and required checks where practical. The client-side protocol remains mandatory even when server-side protection exists or an actor is present on the bypass list.

The existence of this protocol must not be used to claim a ruleset is configured. Repository settings must be verified separately.

## Repository Simulation vs Live Evidence

This merge protocol governs repository evidence only. It must not convert repository simulation into installed-host evidence. Host-specific validation remains subject to its own protocol and evidence boundary.

## Machine-Readable Contract

The executable contract is:

- `scripts/validate_autonomous_merge_readiness_contract.py`
- `tests/behavior/autonomous-merge-readiness-fixtures.json`
- `tests/runtime/test_autonomous_merge_readiness_contract.py`

The fixtures intentionally cover missing check data, pending jobs, failed governance/runtime/cross-platform/CodeQL checks, stale heads, red baseline progression, changelog omission, mergeability misuse, ruleset drift, unauthorized bypass use, non-Squash merge selection, unresolved review threads, tree mismatch, parent drift, unsigned canonical commits, and unverified post-merge state.
