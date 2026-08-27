# Governed Autonomous Execution Protocol

## Purpose

This protocol applies a selected Governance Profile to Orchestra's existing delegated execution, Arbiter, evidence, host-continuity, candidate-maturity, and autonomous merge-readiness contracts.

It does not replace authority evaluation. It decides whether an already-valid transition may proceed without another human checkpoint.

## Required inputs

Before each transition, resolve and re-read:

1. exact repository, branch, base, head, and worktree/index state;
2. selected Governance Profile and its revision-bound grant;
3. parent profile/grant for child execution;
4. repository and project policy;
5. current phase/path/action scope;
6. host capability;
7. exact-current-state validation evidence;
8. unresolved blockers and review threads;
9. requested action and hard-boundary classification;
10. current Candidate Maturity and Feature Freeze identity when a development-candidate transition is requested;
11. current admission/promotion, qualification, merge, readback, or closeout evidence required by that candidate transition.

Missing or stale required input is not approval.

## Evaluation order

```text
validate profile and grant identity
-> enforce child <= parent
-> enforce authority and scope
-> enforce repository/project policy
-> enforce hard boundaries
-> enforce evidence freshness
-> validate candidate-maturity prerequisite when applicable
-> apply profile action/transition ceiling
-> issue canonical disposition
```

The first restrictive result wins.

## Canonical dispositions

- `AUTO_CONTINUE`: action or candidate transition is within the effective grant/profile ceiling and all required prerequisite evidence is current.
- `AUTO_REMEDIATE_AND_REVALIDATE`: defect was caused by the current authorized change and correction remains inside the exact remediation boundary.
- `WAIT_FOR_EVIDENCE`: required identity, policy, check, write result, continuity, candidate freeze, qualification evidence, or canonical read is missing, pending, stale, or unverifiable.
- `WAIT_FOR_CAPACITY`: resumable host capacity limit; preserve the exact profile and grant in the checkpoint.
- `ESCALATE_HUMAN`: the action is valid in principle but the selected profile, explicit grant, repository/project policy, adoption judgment, major-phase gate, or hard boundary requires a human decision.
- `STOP`: malformed state, invalid authority, unauthorized bypass, invalid candidate transition, non-remediable governance violation, unrelated red baseline, or prohibited action.

Unknown dispositions fail closed.

## Transition loop

For every automatic transition:

1. re-read the current head and authoritative policy;
2. collect exact-head evidence;
3. resolve the current candidate identity and maturity when applicable;
4. evaluate effective authority and transition prerequisites;
5. execute at most the requested transition/action;
6. independently read the resulting canonical state;
7. record the result only after verification;
8. invalidate all earlier evidence if state changed;
9. continue only when the next transition independently evaluates to `AUTO_CONTINUE`.

API success is not verified state.

## Candidate-maturity integration

The [Governed Autonomy Candidate Lifecycle Integration](GOVERNED_AUTONOMY_CANDIDATE_LIFECYCLE_INTEGRATION.md) is a thin bridge over this protocol. It does not replace this protocol or the existing autonomy evaluator.

It consumes only the forward Candidate Maturity path:

```text
PROPOSED
-> IMPLEMENTING
-> FROZEN_CANDIDATE
-> ACCEPTED
-> MERGE_READY
-> MERGE_APPLIED_UNVERIFIED
-> MERGED_VERIFIED
-> RETIRED
```

The integration preserves these boundaries:

```text
FULL_AUTONOMOUS != FEATURE_ADOPTION_AUTHORITY
MERGE_READY != MERGE_AUTHORITY
CANDIDATE_TRANSITION != PERSISTENCE_AUTHORITY
RETIRED != BRANCH_DELETION_AUTHORITY
```

A human-owned acceptance/promotion decision must already exist before `FROZEN_CANDIDATE -> ACCEPTED` may proceed without another checkpoint. Full Autonomous cannot manufacture that decision.

For `MERGE_READY -> MERGE_APPLIED_UNVERIFIED`, Full Autonomous requires an exact candidate/PR merge grant and must still receive `AUTO_CONTINUE` from the existing merge evaluator on the same exact state. Human-Governed and Semi-Autonomous stop before initiating merge. If a human/external merge is already independently observed, the transition may record that fact without retroactively authorizing the merge.

`MERGE_APPLIED_UNVERIFIED -> MERGED_VERIFIED` requires independent canonical readback. `MERGED_VERIFIED -> RETIRED` closes the candidate record only and never implies branch deletion.

If recording a candidate transition requires stage, commit, push, PR mutation, merge, or another repository write, that persistence action is independently evaluated by the normal autonomy action contract.

## Bounded remediation

Automatic remediation requires all of:

- the current authorized change caused the defect;
- the correction stays within the allowed paths and behavior;
- no authority, runtime, fixture, validator, manifest, dependency, CI, security, release, or deployment boundary expands;
- accepted evidence identities and hard boundaries remain unchanged;
- focused and consolidated validation are rerun against the new exact state.

Every remediation commit invalidates CI and immutable-review evidence for the prior head. For a frozen development candidate, any source remediation also creates a new candidate identity under the Candidate Maturity and Feature Freeze contract.

## Merge integration

An automatic merge is allowed only for `FULL_AUTONOMOUS`, only when merge is explicitly granted to the exact current candidate/PR, and only after the Autonomous Merge Readiness Protocol passes on the exact reviewed head.

For Orchestra's current `Protect main` profile:

- Squash is the only allowed method;
- bypass use is prohibited unless separately authorized;
- all required checks must be completed/successful on the exact head;
- unresolved review threads must be zero;
- expected-head protection is used when supported;
- canonical parent must equal the pre-merge base;
- canonical tree must equal the reviewed-head tree;
- reviewed-to-canonical content diff must be empty;
- the canonical Squash commit must have a verified signature;
- a canonical remote read must verify the result.

Reviewed-head ancestry is not required after a valid Squash merge.

## Profile-specific stopping points

- `HUMAN_GOVERNED`: stop before every material Git/remote transition and unapproved major phase progression. Mechanical candidate-state recording may continue only after the required human decision/evidence already exists.
- `SEMI_AUTONOMOUS`: may reach exact-head `MERGE_READY` automatically when qualification evidence is current, then stop before merge. Major progression outside the explicit candidate-transition contract remains human-gated.
- `FULL_AUTONOMOUS`: may continue through an exactly granted merge and subsequent candidate verification/closeout while evidence remains green; stop at the first hard boundary, adoption judgment, or authority gap.

## Audit and provenance

Material decisions record:

- run/correlation/grant identity;
- selected and prior profile;
- parent profile for children;
- requested action or candidate transition;
- exact candidate id/head/tree/base when applicable;
- exact pre-state and post-state;
- repository-policy identity;
- evidence identity;
- acceptance/promotion decision identity when applicable;
- merge method and bypass-used state when applicable;
- exact candidate/PR merge-grant identity when applicable;
- disposition and reason;
- human authorization for any profile increase;
- remediation attempt identity.

## Continuity and recovery

Same-host resume, portable handoff, and context reset must preserve:

- exact profile and grant;
- parent/child relationship;
- repository/base/head;
- current candidate identity and maturity when applicable;
- current phase/action;
- hard boundaries;
- evidence freshness state;
- repository policy and merge method evidence.

Mismatch, omission, or unverifiable continuity returns `WAIT_FOR_EVIDENCE`. A resumed run never defaults upward.

## Release and R8 boundary

Governed Autonomy Modes is part of the `v1.2.0` candidate, but no profile authorizes R8.

Tag creation, GitHub Release publication, deployment, marketplace publication, installed-integration refresh, and policy activation require separate human authority. Full Autonomous must stop before R8 when that authority is absent.

## Protocol result

`GOVERNED_AUTONOMOUS_EXECUTION_DEFINED`
