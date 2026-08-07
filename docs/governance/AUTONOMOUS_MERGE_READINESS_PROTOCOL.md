# Autonomous Merge Readiness Protocol

## Purpose

This protocol defines Orchestra's fail-closed evidence gate for autonomous or delegated pull-request merges. It exists because GitHub may technically accept a merge even when repository validation is missing or red. Platform capability is not governance readiness.

Canonical merge rule:

```text
GITHUB_CAN_MERGE != GOVERNANCE_READY_TO_MERGE
```

This protocol does not grant merge authority. It constrains how already-authorized merge authority may be exercised.

## Parent Governing Rule

This protocol is the merge-specific specialization of Orchestra's Evidence-Bound Governed Transition Rule.

```text
PLATFORM_CAN_EXECUTE != GOVERNANCE_READY_TO_TRANSITION
GITHUB_CAN_MERGE != GOVERNANCE_READY_TO_MERGE
API_SUCCESS != VERIFIED_STATE
NO_EVIDENCE != APPROVAL
```

The parent rule applies to governed phase advancement and other material state transitions, including merge, release, deployment, policy activation, protected-state mutation, destructive operations, permanent deletion, and history rewrite. Missing, pending, stale, contradictory, or failed required evidence never grants permission. Evidence belongs to the exact current state and becomes invalid when that state changes. A red canonical baseline blocks ordinary progression except for explicitly authorized bounded remediation. A successful write is not a completed transition until an independent canonical read verifies the resulting state.

Neither this protocol nor its parent rule creates or widens authority.

## Required Evidence Snapshot

A pre-merge snapshot must bind all evidence to one exact current PR head SHA and record:

- canonical base health;
- current PR head SHA;
- whether that head was re-read immediately before merge;
- changelog freshness when significant paths changed;
- unresolved blocking findings;
- Git mergeability state;
- every required workflow/job result with its exact head SHA, status, and conclusion.

The canonical minimum check inventory is:

| Workflow | Required job |
| --- | --- |
| Governance Check | `governance-check` |
| validate | `validate` |
| validate | `runtime-tests` |
| Cross-platform Validation | `native-windows-latest` |
| Cross-platform Validation | `native-ubuntu-latest` |
| Cross-platform Validation | `native-macos-latest` |

Repository rules may require additional checks. Additional required checks must also pass; this table is a minimum, not a bypass list.

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
REQUIRED_CHANGELOG_MISSING = BLOCK
```

A high passing-test count, passing coverage threshold, `mergeable: true`, or a successful merge API call cannot override a failed or missing required check.

`mergeable: true` is informational only: it means Git can construct a merge. It never proves governance readiness.

`mergeable: false` blocks because the PR has a technical merge conflict.

## Exact-Head Rule

Validation evidence is revision-specific.

Before merge:

1. Read the PR and capture the current head SHA.
2. Fetch fresh required workflow/job state for that exact head.
3. Require every required job to exist.
4. Require every required job status to be `completed`.
5. Require every required job conclusion to be `success`.
6. Require every job's evidence head SHA to equal the current PR head SHA.
7. Re-read the PR immediately before merge.
8. If the head changed, discard prior evidence and return `STALE_EVIDENCE`.
9. Use `expected_head_sha` or the platform's equivalent compare-and-swap guard when issuing the merge.

Any remediation commit invalidates all earlier check evidence. The complete required matrix must be collected again for the new head.

## Canonical Baseline Rule

A new autonomous phase must not begin from a red canonical baseline.

```text
red canonical baseline -> REMEDIATE_BASELINE_FIRST
```

A low-risk documentation-only next phase cannot bypass a failure inherited from an earlier merge.

## Changelog Freshness

When repository governance classifies changed paths as significant, `CHANGELOG.md` must be updated in the same change set. A later release consolidation does not satisfy a current strict changelog gate unless the gate itself explicitly permits that behavior.

## Post-Merge Verification

A merge write is not complete merely because an API returned success.

The controller must perform a canonical remote read after the write and verify:

- the PR now reports `merged == true`;
- the reviewed head is contained in canonical `main`;
- the canonical main SHA is resolved from the remote;
- the remote read corresponds to the intended repository and PR.

Only then may state advance to:

```text
MERGED_VERIFIED
```

Otherwise:

```text
MERGE_STATE_UNVERIFIED
```

An intended action, attempted action, or successful API response must not be recorded as executed fact without this independent canonical remote read.

## Server-Side Protection

Repository branch protection or rulesets should independently require the same current checks and should apply to administrators/automation where practical. The client-side protocol remains mandatory even when server-side protection exists.

The existence of this protocol must not be used to claim that GitHub branch protection is configured. Repository settings must be verified separately.

## Repository Simulation vs Live Evidence

This merge protocol governs repository evidence only. It must not convert repository simulation into installed-host evidence. Host-specific validation remains subject to its own protocol and evidence boundary.

## Machine-Readable Contract

The executable contract is:

- `scripts/validate_autonomous_merge_readiness_contract.py`
- `tests/behavior/autonomous-merge-readiness-fixtures.json`
- `tests/runtime/test_autonomous_merge_readiness_contract.py`

The fixtures intentionally cover the failure modes observed during the first autonomous finalization experiment, including missing check data, pending jobs, failed governance/runtime/cross-platform checks, stale heads, red baseline progression, changelog omission, mergeability misuse, and unverified post-merge state.