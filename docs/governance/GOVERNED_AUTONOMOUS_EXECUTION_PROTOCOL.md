# Governed Autonomous Execution Protocol

## Purpose

This protocol applies a selected Governance Profile to Orchestra's existing delegated execution, Arbiter, evidence, host-continuity, and autonomous merge-readiness contracts.

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
9. requested action and hard-boundary classification.

Missing or stale required input is not approval.

## Evaluation order

```text
validate profile and grant identity
-> enforce child <= parent
-> enforce authority and scope
-> enforce repository/project policy
-> enforce hard boundaries
-> enforce evidence freshness
-> apply profile action ceiling
-> issue canonical disposition
```

The first restrictive result wins.

## Canonical dispositions

- `AUTO_CONTINUE`: action is within the effective grant and all required evidence is current and green.
- `AUTO_REMEDIATE_AND_REVALIDATE`: defect was caused by the current authorized change and correction remains inside the exact remediation boundary.
- `WAIT_FOR_EVIDENCE`: required identity, policy, check, write result, continuity, or canonical read is missing, pending, stale, or unverifiable.
- `WAIT_FOR_CAPACITY`: resumable host capacity limit; preserve the exact profile and grant in the checkpoint.
- `ESCALATE_HUMAN`: the action is valid in principle but the selected profile, explicit grant, repository/project policy, or hard boundary requires a human decision.
- `STOP`: malformed state, invalid authority, unauthorized bypass, non-remediable governance violation, unrelated red baseline, or prohibited action.

Unknown dispositions fail closed.

## Transition loop

For every automatic transition:

1. re-read the current head and authoritative policy;
2. collect exact-head evidence;
3. evaluate effective authority;
4. execute at most the requested transition;
5. independently read the resulting canonical state;
6. record the result only after verification;
7. invalidate all earlier evidence if state changed;
8. continue only when the next transition independently evaluates to `AUTO_CONTINUE`.

API success is not verified state.

## Bounded remediation

Automatic remediation requires all of:

- the current authorized change caused the defect;
- the correction stays within the allowed paths and behavior;
- no authority, runtime, fixture, validator, manifest, dependency, CI, security, release, or deployment boundary expands;
- accepted evidence identities and hard boundaries remain unchanged;
- focused and consolidated validation are rerun against the new exact state.

Every remediation commit invalidates CI and immutable-review evidence for the prior head.

## Merge integration

An automatic merge is allowed only for `FULL_AUTONOMOUS`, only when merge is explicitly granted, and only after the Autonomous Merge Readiness Protocol passes on the exact reviewed head.

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

- `HUMAN_GOVERNED`: stop before every material Git/remote transition and major phase progression.
- `SEMI_AUTONOMOUS`: stop after exact-head PR/CI readiness and before merge; stop before major phase progression.
- `FULL_AUTONOMOUS`: continue through granted merge and phase transitions while evidence remains green; stop at the first hard boundary or authority gap.

## Audit and provenance

Material decisions record:

- run/correlation/grant identity;
- selected and prior profile;
- parent profile for children;
- requested action;
- exact pre-state and post-state;
- repository-policy identity;
- evidence identity;
- merge method and bypass-used state when applicable;
- disposition and reason;
- human authorization for any profile increase;
- remediation attempt identity.

## Continuity and recovery

Same-host resume, portable handoff, and context reset must preserve:

- exact profile and grant;
- parent/child relationship;
- repository/base/head;
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
