# Required Status Checks Review

## Purpose

This document defines Orchestra's current minimum validation evidence for pull requests targeting `main` and the recommended GitHub protection that should mirror it.

The first autonomous finalization experiment demonstrated that GitHub may technically accept a merge while repository validation is red. Therefore required-check policy is fail-closed at both the automation layer and, where configured, the GitHub branch-protection/ruleset layer.

Canonical rule:

```text
GITHUB_CAN_MERGE != GOVERNANCE_READY_TO_MERGE
```

## Current Validation Workflows and Minimum Jobs

| Workflow | Required job | Requirement | Reason |
| --- | --- | --- | --- |
| Governance Check | `governance-check` | Required | Strict governance, changelog freshness, routing, prompt-load, packaging, and repository policy evidence |
| validate | `validate` | Required | Canonical behavior validation suite |
| validate | `runtime-tests` | Required | Runtime regression and coverage gate |
| Cross-platform Validation | `native-windows-latest` | Required | Native Windows repository/runtime validation |
| Cross-platform Validation | `native-ubuntu-latest` | Required | Native Ubuntu repository/runtime validation |
| Cross-platform Validation | `native-macos-latest` | Required | Native macOS repository/runtime validation |

Additional checks required by repository rules, security tooling, CodeQL, or a specific phase remain additive. This table is the minimum autonomous merge evidence inventory, not a bypass list.

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
- missing changelog update when strict governance classifies changed paths as significant.

Missing or pending evidence maps to `WAIT_FOR_EVIDENCE`. Failed required evidence maps to `BLOCK` or bounded remediation followed by complete revalidation.

## Exact-Head Requirement

A remediation commit invalidates prior check evidence. The complete minimum matrix must be collected again on the new head.

Immediately before merge:

1. Re-read the PR and confirm its exact head SHA.
2. Re-read every required workflow/job for that SHA.
3. Require all minimum jobs and any additional repository-required checks to be completed and successful.
4. Use `expected_head_sha` or the platform's equivalent compare-and-swap guard where supported.
5. After the merge write, independently re-read the PR and canonical `main` before recording `MERGED_VERIFIED`.

`mergeable: true` is informational only. It means Git can construct a merge; it does not prove validation or governance readiness.

The executable companion contract is `docs/governance/AUTONOMOUS_MERGE_READINESS_PROTOCOL.md` with `scripts/validate_autonomous_merge_readiness_contract.py` and its regression fixtures/tests.

## GitHub Protection Recommendation

GitHub branch protection or rulesets for `main` should require the active check contexts corresponding to the minimum jobs above and should apply to administrators and automation identities where practical.

Do not infer that repository protection is configured merely because this document exists. The live repository settings must be inspected and tested separately.

The automation-side fail-closed protocol remains mandatory even when GitHub protection is configured, because governance must not rely on a platform merge button or API call as its only safety boundary.

## Workflow Migration Policy

Do not remove, rename, consolidate, or convert a workflow to manual-only while it supplies a required merge signal unless all of the following are true:

1. The replacement workflow/job is already running successfully on `main` and pull requests.
2. Branch protection/rulesets have been reviewed and updated.
3. The autonomous merge-readiness inventory has been updated.
4. The migration is recorded in `CHANGELOG.md`.
5. A PR proves the old and new check names are observable before the old check disappears.

## Current Recommendation

Keep all three workflow families active:

- Governance Check;
- validate;
- Cross-platform Validation.

Treat all six minimum jobs listed above as required autonomous merge evidence until a separately validated CI consolidation changes this contract.
