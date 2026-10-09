# Required Status Checks Review

## Purpose

This document defines Orchestra's current validation evidence for pull requests targeting `main` and the live GitHub `Protect main` ruleset that mirrors it.

The autonomous finalization incidents demonstrated that GitHub may technically accept a merge while repository validation is red, while a privileged actor has bypass capability, or while the selected merge method does not preserve the evidence assumptions used by the controller. Required-check policy is therefore fail-closed at both the automation layer and the GitHub ruleset layer.

Canonical rules:

```text
GITHUB_CAN_MERGE != GOVERNANCE_READY_TO_MERGE
BYPASS_CAPABILITY != GOVERNANCE_AUTHORIZATION
```

## Current Required Validation Signals

| Workflow | Required job | Requirement | Reason |
| --- | --- | --- | --- |
| Governance Check | `governance-check` | Required | Strict governance, changelog freshness, routing, prompt-load, packaging, and repository policy evidence |
| validate | `validate` | Required | Canonical behavior validation suite |
| validate | `runtime-tests` | Required | Runtime regression and coverage gate |
| Cross-platform Validation | `native-windows-latest` | Required | Native Windows repository/runtime validation |
| Cross-platform Validation | `native-ubuntu-latest` | Required | Native Ubuntu repository/runtime validation |
| Cross-platform Validation | `native-macos-latest` | Required | Native macOS repository/runtime validation |
| CodeQL | `Analyze (actions)` | Required | GitHub Actions security/code-analysis signal required by the live ruleset |
| CodeQL | `Analyze (python)` | Required | Python security/code-analysis signal required by the live ruleset |

Additional checks required by a stricter future repository rule or a specific phase remain additive. This table is the current exact autonomous merge evidence inventory, not a bypass list.

## Current `Protect main` Ruleset Baseline

The live Orchestra ruleset is intentionally configured for a solo maintainer:

```text
Required approvals: 0
Dismiss stale PR approvals when new commits are pushed: ON
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

The repository bypass list remains available for operational access by trusted roles/apps. Its existence does not grant Orchestra governance authority and does not make a bypassed transition valid. Ordinary governed automation records and requires `bypass_used=false`; any future deliberate bypass requires separate explicit authority and evidence.

## Fail-Closed Interpretation

Every required job must be positively present for the exact current PR head SHA and must satisfy:

```text
status == completed
conclusion == success
```

The following states do not authorize merge:

- check data absent or unavailable;
- required job missing;
- queued or in-progress job;
- failed, cancelled, timed-out, action-required, or skipped required job;
- check evidence tied to an earlier PR head;
- red canonical `main` baseline;
- unresolved blocking finding;
- unresolved review thread;
- missing changelog update when strict governance classifies changed paths as significant;
- live ruleset drift from the accepted protection profile;
- merge method other than Squash;
- use of bypass without separate explicit authority.

Missing or pending evidence maps to `WAIT_FOR_EVIDENCE`. Failed required evidence maps to `BLOCK` or bounded remediation followed by complete revalidation.

## Exact-Head Requirement

A remediation commit invalidates prior check evidence. The complete required matrix must be collected again on the new head.

Immediately before merge:

1. Re-read the PR and confirm its exact head SHA.
2. Re-read the live ruleset and selected merge method.
3. Require all eight current required jobs and any additional repository-required checks to be completed and successful for that exact head.
4. Require zero unresolved review threads.
5. Require Squash as the selected merge method.
6. Require no bypass for ordinary governed execution.
7. Use `expected_head_sha` or the platform's equivalent compare-and-swap guard where supported.
8. After the merge write, independently re-read the PR and canonical `main` before recording `MERGED_VERIFIED`.

`mergeable: true` is informational only. It means Git can construct a merge; it does not prove validation or governance readiness.

Because Squash creates a new canonical commit identity, post-merge verification follows `AUTONOMOUS_MERGE_READINESS_PROTOCOL.md`: verify the exact canonical parent, tree/content equivalence to the reviewed head, and verified signature on the canonical squash commit rather than requiring the reviewed head SHA itself to remain in `main` ancestry.

The executable companion contract is `docs/governance/AUTONOMOUS_MERGE_READINESS_PROTOCOL.md` with `scripts/validate_autonomous_merge_readiness_contract.py` and its regression fixtures/tests.

## GitHub Protection Alignment

The live `Protect main` ruleset should continue to require the active contexts listed above, Squash-only merging, signed and linear canonical history, current-base testing, conversation resolution, pull-request flow, restricted deletion, and blocked force pushes.

The current bypass list is an operational repository setting. The automation-side fail-closed protocol remains mandatory even for actors technically capable of bypassing the ruleset.

Do not infer that the repository settings still match this document merely because the document exists. The live ruleset must be re-read before an autonomous merge.

## Workflow Migration Policy

Do not remove, rename, consolidate, or convert a workflow to manual-only while it supplies a required merge signal unless all of the following are true:

1. The replacement workflow/job is already running successfully on `main` and pull requests.
2. The live ruleset has been reviewed and updated.
3. The autonomous merge-readiness inventory has been updated.
4. The migration is recorded in `CHANGELOG.md`.
5. A PR proves the old and new check names are observable before the old check disappears.

## Current Recommendation

Keep Governance Check, validate, Cross-platform Validation, and the two CodeQL Analyze jobs active. Treat all eight jobs listed above as required autonomous merge evidence until a separately validated CI or ruleset change replaces this contract.
