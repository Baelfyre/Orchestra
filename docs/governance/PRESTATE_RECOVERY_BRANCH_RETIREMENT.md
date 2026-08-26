# Pre-state, Forward Recovery, and Branch Retirement

**Contract:** `ORCHESTRA_PRESTATE_RECOVERY_BRANCH_RETIREMENT_V1`
**Machine record:** `RepositoryRecoveryRetirementPlan`
**Machine schema:** `machine/schemas/repository-recovery-retirement-plan.v1.schema.json`
**Authority class:** evidence planning, retention classification, and dry-run eligibility are machine-validatable; ref creation, merge, recovery execution, branch deletion, destructive cleanup, force push, and history rewrite remain separately governed

## Purpose

Campaign 5 defines a recoverable merge boundary and a conservative branch-retirement policy without creating a cleanup bot or a rollback mechanism that rewrites canonical history.

```text
PRESTATE_EVIDENCE != RECOVERY_AUTHORITY
RECOVERY_PLAN != RECOVERY_EXECUTION_AUTHORITY
RETIREMENT_ELIGIBLE != BRANCH_DELETION_AUTHORITY
ANCESTRY != SAFE_DELETION_PROOF
DRY_RUN != DESTRUCTIVE_ACTION
```

This campaign is **dry-run only**. Its machine contract may classify and recommend; it must not create/delete refs, reset `main`, force-push, rewrite history, or execute a recovery.

## Pre-state evidence

Every merge candidate records the immutable canonical pre-state immediately before merge:

- repository identity;
- canonical branch;
- exact pre-merge commit SHA;
- exact pre-merge tree SHA;
- observation/evidence identity.

Exact SHA/tree evidence is the durable historical record.

### Materialized pre-state ref

A temporary pre-state ref is not universal. It is required only when repository/project policy or the candidate's risk classification requires one.

Default policy:

- `LOW` / lightweight bounded changes: exact SHA/tree evidence is sufficient unless another policy requires a ref;
- `MODERATE`: policy may require a temporary ref;
- `HIGH` / `CRITICAL`, material trust-boundary, recovery automation, destructive automation, or other policy-triggered change: temporary pre-state ref required.

Suggested naming:

```text
prestate/main/<candidate-id>-<YYYYMMDD>-<prestate-short-sha>
```

When a temporary ref is required it must:

- point exactly to the recorded pre-merge canonical SHA;
- be created immediately before the merge operation;
- never be reused for another candidate;
- never be force-updated;
- retain the same evidence identity as the pre-state record;
- default to a 30-day retention window after `MERGED_VERIFIED`, subject to policy extension.

A pre-state ref is a recovery convenience, not a permission grant and not the canonical historical record.

## Forward-only recovery

Canonical recovery is forward-only:

```text
verified incident / failed canonical outcome
    -> new recovery or revert candidate
    -> exact scope and acceptance criteria
    -> qualification and validation
    -> governed pull request
    -> separately authorized merge
    -> independent canonical readback
```

The recovery process must not:

- reset `main` backward;
- force-update canonical history;
- reuse stale readiness evidence;
- treat the existence of a pre-state ref as recovery authority;
- skip qualification/validation because the target content existed previously.

```text
RECOVERY != RESET_MAIN_BACKWARD
PREVIOUSLY_CANONICAL != CURRENTLY_VALIDATED
```

Emergency procedures may have separate policy, but Campaign 5 does not create one.

## Branch retirement classifications

The canonical retirement vocabulary is:

```text
ACTIVE
OPEN_PR
CANONICAL_EQUIVALENT
SUPERSEDED
RECOVERY_EXPIRED
HISTORICAL_EVIDENCE
UNMERGED_UNIQUE
UNKNOWN
```

### ACTIVE

Current work, active worktree, explicitly active campaign, current canonical branch, or another current execution role.

Disposition: `KEEP`.

### OPEN_PR

Head of an open pull request.

Disposition: `KEEP` regardless of ancestry or apparent equivalence.

### CANONICAL_EQUIVALENT

No unique content remains after squash/materialization/reconciliation, and durable PR/commit evidence preserves the history.

Disposition: `ELIGIBLE_FOR_SEPARATE_AUTHORIZATION` only after the default 7-day cooling period and sealed evidence.

Git ancestry alone is not sufficient because valid Squash and signed-materialization workflows can make a branch non-ancestor while its reviewed tree is already canonical.

### SUPERSEDED

A newer explicit candidate replaces this branch and the older branch has no remaining active role.

Disposition: `QUARANTINE`; default 14 days before any separate deletion adjudication.

### RECOVERY_EXPIRED

A temporary `prestate/*` or recovery ref has passed its policy retention window and all required canonical/readback evidence is sealed.

Disposition: `ELIGIBLE_FOR_SEPARATE_AUTHORIZATION`; default retention is 30 days after `MERGED_VERIFIED` unless policy extends it.

### HISTORICAL_EVIDENCE

The ref preserves evidence not durably recoverable from an immutable PR, tag, release, signed canonical commit, or another approved evidence artifact.

Disposition: `KEEP`. This classification requires a positive preservation reason; it is not a generic exemption for old branches.

### UNMERGED_UNIQUE

The branch contains unique work/content not proven incorporated or superseded.

Disposition: `KEEP`. It is never automatically deletion-eligible.

### UNKNOWN

Evidence is missing, stale, contradictory, or insufficient to classify safely.

Disposition: `QUARANTINE`; default 30 days, then refresh evidence or escalate. `UNKNOWN` never becomes deletion eligibility merely because time elapsed.

## Retirement evidence

Before a branch may even be labeled `ELIGIBLE_FOR_SEPARATE_AUTHORIZATION`, current evidence must establish the applicable facts, including:

- exact ref and tip identity;
- canonical `main` identity;
- open-PR status;
- active-worktree/current-campaign status when available;
- whether unique content/commits remain;
- canonical tree/content equivalence when ancestry is insufficient;
- materialization/squash provenance where relevant;
- release/recovery/pre-state role;
- historical-evidence reason, if any;
- age/retention boundary;
- evidence freshness.

Missing or stale evidence yields `UNKNOWN` or `KEEP`, never automatic deletion eligibility.

## Default retention policy

```text
ACTIVE                         KEEP
OPEN_PR                        KEEP
CANONICAL_EQUIVALENT           7 days + sealed evidence before eligibility
SUPERSEDED                     quarantine 14 days
RECOVERY_EXPIRED               temporary prestate/recovery refs: 30-day default
HISTORICAL_EVIDENCE            KEEP while positive preservation reason remains
UNMERGED_UNIQUE                KEEP
UNKNOWN                        quarantine 30 days, then refresh/escalate
```

Retention expiry is only an eligibility input. It does not authorize deletion.

## Dry-run action vocabulary

Campaign 5 may derive only:

```text
KEEP
QUARANTINE
ELIGIBLE_FOR_SEPARATE_AUTHORIZATION
```

It may never derive `DELETE` or perform a ref mutation.

The machine record is structurally required to state:

```text
DRY_RUN = true
REF_CREATION_PERFORMED = false
RECOVERY_EXECUTION_PERFORMED = false
BRANCH_DELETION_PERFORMED = false
FORCE_PUSH_PERFORMED = false
HISTORY_REWRITE_PERFORMED = false
```

## Relationship to the lifecycle

Pre-state capture belongs immediately before a separately authorized merge.

After merge:

```text
MERGE_APPLIED_UNVERIFIED
    -> independent canonical readback
    -> MERGED_VERIFIED
    -> retention clocks may begin where policy allows
```

`RETIRED` closes the candidate record. It does not delete its source branch.

## Explicit exclusions

Campaign 5 does not:

- create a pre-state branch automatically;
- execute recovery;
- reset or rewind `main`;
- merge a recovery candidate;
- delete or archive branches;
- force push or rewrite history;
- alter repository rulesets;
- release, deploy, or activate policy;
- make live model/provider calls.

Any later destructive cleanup remains a separately authorized action against a fresh exact repository read.
