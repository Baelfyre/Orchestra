# Governed Autonomy Candidate Lifecycle Integration

**Contract:** `ORCHESTRA_GOVERNED_AUTONOMY_CANDIDATE_LIFECYCLE_V1`
**Consumes:** Governed Autonomy Modes, Governed Autonomous Execution Protocol, Candidate Maturity and Feature Freeze, Qualification Gates/Evaluation/Independent Audit
**Authority class:** deterministic pause/transition evaluation only; this contract creates no execution, merge, release, deployment, policy, destructive-action, or branch-deletion authority

## Purpose

Campaign 3 integrates development-candidate maturity with Orchestra's existing Governed Autonomy Modes. Campaign 4 supplies the qualification evidence that must be satisfied before the human-owned promotion/acceptance decision.

The integration answers one narrow question:

> When the prerequisite decision, authority, identity, and evidence already exist, does the selected Governance Profile require another human checkpoint before recording or carrying out the next candidate-maturity transition?

```text
AUTONOMY_CHANGES_PAUSES_NOT_PREREQUISITES
CANDIDATE_TRANSITION != PERSISTENCE_AUTHORITY
FULL_AUTONOMOUS != FEATURE_ADOPTION_AUTHORITY
MERGE_READY != MERGE_AUTHORITY
RETIRED != BRANCH_DELETION_AUTHORITY
```

The existing governed-autonomy evaluator remains the action ceiling. Candidate Maturity remains the state/evidence contract. Qualification Gates define proportional evidence obligations. This integration is only the deterministic bridge between them.

## Separation of responsibilities

```text
Feature Admission / human ownership judgment
        -> whether a capability should be investigated or adopted

Candidate Maturity / Feature Freeze
        -> what exact development state and frozen identity exist

Qualification Gates / Evaluation / Audit
        -> what evidence this frozen candidate must satisfy

Governed Autonomy Modes
        -> whether an otherwise-valid action needs another human pause

Candidate Lifecycle Integration
        -> whether an otherwise-valid maturity transition needs another human pause
```

None of these layers may infer authority from another.

## Forward candidate path

```text
PROPOSED -> IMPLEMENTING
IMPLEMENTING -> FROZEN_CANDIDATE
FROZEN_CANDIDATE -> ACCEPTED
ACCEPTED -> MERGE_READY
MERGE_READY -> MERGE_APPLIED_UNVERIFIED
MERGE_APPLIED_UNVERIFIED -> MERGED_VERIFIED
MERGED_VERIFIED -> RETIRED
```

Skipped or backward transitions fail closed.

## Profile behavior

### PROPOSED -> IMPLEMENTING

All profiles may mechanically continue only when the admission basis is current and implementation authority already exists.

Missing admission evidence returns `WAIT_FOR_EVIDENCE`. Missing implementation authority returns `ESCALATE_HUMAN`.

### IMPLEMENTING -> FROZEN_CANDIDATE

All profiles may record the freeze without another approval only when the exact candidate identity is current and the Feature Freeze is complete.

Freeze completion does not prove qualification, acceptance, or merge readiness.

### FROZEN_CANDIDATE -> ACCEPTED

Qualification occurs **before** product/adoption acceptance.

The transition may be recorded only when:

1. exact-current qualification evidence exists;
2. its derived disposition is `QUALIFIED`; and
3. a current human-owned acceptance/promotion decision exists.

`QUALIFICATION_PENDING` returns `WAIT_FOR_EVIDENCE`. `BLOCKED` returns `STOP`. No Governance Profile may convert either state into acceptance.

```text
FULL_AUTONOMOUS + GREEN_TESTS != ACCEPTANCE_DECISION
QUALIFIED != ACCEPTED
```

Full Autonomous may automate evidence collection and recording, but cannot self-adopt a capability.

### ACCEPTED -> MERGE_READY

This transition consumes **merge-readiness evidence**, not qualification evidence that was already completed before acceptance.

- `HUMAN_GOVERNED`: requires an explicit major-phase progression authorization before the transition is recorded.
- `SEMI_AUTONOMOUS`: may record `MERGE_READY` when exact-current merge-readiness evidence is complete.
- `FULL_AUTONOMOUS`: may record `MERGE_READY` when exact-current merge-readiness evidence is complete.

This is readiness evidence only. It does not authorize merge.

### MERGE_READY -> MERGE_APPLIED_UNVERIFIED

Recording an already-observed human/external merge does not authorize that merge.

If the merge has not yet occurred:

- `HUMAN_GOVERNED`: `ESCALATE_HUMAN`.
- `SEMI_AUTONOMOUS`: `ESCALATE_HUMAN`.
- `FULL_AUTONOMOUS`: may proceed only when an `EXACT_CANDIDATE_PR_MERGE_GRANT` is current and the existing governed-autonomy `merge` evaluator independently returns `AUTO_CONTINUE` for the same exact candidate state.

The integration does not duplicate Squash, required-check, ruleset, evidence, host, bypass, or write-readback checks.

### MERGE_APPLIED_UNVERIFIED -> MERGED_VERIFIED

All profiles may record verification automatically only after independent canonical readback is current and verified.

API success, GitHub merge response, or local state alone is insufficient.

### MERGED_VERIFIED -> RETIRED

All profiles may record candidate retirement after closeout evidence is current.

Retirement closes the candidate record. It does not delete a branch, tag, recovery reference, artifact, or historical evidence.

```text
RETIRED != BRANCH_DELETION_AUTHORITY
```

## Candidate identity and freshness

Every candidate transition is evaluated against the exact current candidate identity. If the frozen head/tree/base/policy/acceptance identity is stale or mismatched, the result is `WAIT_FOR_EVIDENCE`.

A remediation-generated replacement candidate must be evaluated under its new identity. Old exact-head evidence remains historical only.

## Persistence boundary

A transition disposition answers whether another human checkpoint is needed for the maturity transition. It does not grant the Git mutation needed to persist a record.

If persistence requires stage, commit, push, pull-request mutation, merge, or another repository write, that action is evaluated separately by the existing Governed Autonomy Modes contract.

```text
AUTO_CONTINUE(candidate_transition)
    !=
AUTO_CONTINUE(commit_or_push)
```

## Protected actions

Candidate maturity never absorbs the separately controlled boundaries for release/publication, deployment/production mutation, policy activation, installed-integration refresh, destructive operations, branch deletion, force push/history rewrite, or authority expansion.

## Fail-closed rule

Unknown profile, malformed candidate transition, invalid authority, bypass use, stale continuity, stale repository policy, stale candidate identity, missing required qualification/readiness evidence, or unsupported transition never becomes automatic permission.

## Contract result

`GOVERNED_AUTONOMY_CANDIDATE_LIFECYCLE_INTEGRATION_DEFINED`
