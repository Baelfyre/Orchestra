# Candidate Maturity and Feature Freeze

**Contract:** `ORCHESTRA_CANDIDATE_MATURITY_FEATURE_FREEZE_V1`
**Machine record:** `CandidateMaturityRecord`
**Machine schema:** `machine/schemas/candidate-maturity-record.v1.schema.json`
**Authority class:** maturity and freeze completeness are machine-validated; transition intent, acceptance, merge authorization, release, deployment, policy activation, and destructive actions remain governed by their existing authorities

## Purpose

Campaign 2 adds a thin development-candidate maturity contract on top of the Prime Directive and Feature Admission. It does not replace Orchestra's runtime lifecycle controller, governance kernel, authority model, merge-readiness protocol, remediation circuit, or autonomy profiles.

The contract answers two questions:

1. What maturity state does a development candidate currently occupy?
2. Once a candidate is frozen, what exact identity, scope, acceptance revision, and remediation boundary must remain stable for later evidence to be meaningful?

```text
RUNTIME_LIFECYCLE != DEVELOPMENT_CANDIDATE_MATURITY
FROZEN_CANDIDATE != ACCEPTED
ACCEPTED != MERGE_READY
MERGE_READY != MERGE_AUTHORITY
MERGE_APPLIED != MERGED_VERIFIED
FREEZE != AUTHORITY
```

## Maturity states

The normative maturity vocabulary is:

```text
PROPOSED
IMPLEMENTING
FROZEN_CANDIDATE
ACCEPTED
MERGE_READY
MERGE_APPLIED_UNVERIFIED
MERGED_VERIFIED
RETIRED
```

The ordinary forward path is:

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

Campaign 2 validates recorded state and transition shape only. It does not execute transitions or infer that their prerequisites are satisfied.

### Operational overlays remain separate

Operational conditions do not become maturity states:

```text
NONE
WAITING_FOR_EVIDENCE
WAITING_FOR_CAPACITY
REMEDIATING
ESCALATED
STOPPED
```

Likewise, lifecycle dispositions remain separate from maturity:

```text
ACTIVE
DEFERRED
REJECTED
SUPERSEDED
```

A candidate can therefore remain `FROZEN_CANDIDATE` while `WAITING_FOR_EVIDENCE`, or become `SUPERSEDED` without pretending that `SUPERSEDED` is the next maturity stage.

## Feature Freeze

Before a candidate may be represented as `FROZEN_CANDIDATE` or any later maturity state, its freeze must bind:

- repository identity;
- exact candidate head SHA and tree SHA;
- exact base SHA and base tree;
- allowed and prohibited paths;
- allowed and prohibited behavior-change boundaries;
- acceptance revision and deterministic acceptance digest;
- the governing admission basis;
- current authority reference;
- optional future gate-applicability and evaluation-disposition references;
- artifact-lifecycle references when applicable.

The gate-applicability and evaluation-disposition references are deliberately nullable in Campaign 2. Their policy is defined in the later qualification-gate campaign rather than duplicated here.

```text
FROZEN_IDENTITY = HEAD_SHA + TREE_SHA + BASE_SHA + BASE_TREE
FROZEN_SCOPE != PERMISSION_TO_EXPAND_SCOPE
FREEZE_COMPLETENESS != VALIDATION_SUCCESS
FREEZE_COMPLETENESS != MERGE_READINESS
```

## Candidate identity rule

Any source change after freeze creates a new candidate identity.

A bounded remediation may supersede the frozen candidate, but it must not reuse the old candidate identifier or old exact-head evidence.

```text
FROZEN_SOURCE_CHANGE
    -> NEW_HEAD_OR_TREE
    -> NEW_CANDIDATE_IDENTITY
    -> OLD_EXACT_HEAD_EVIDENCE_STALE
```

The prior candidate remains preserved as historical evidence and may be marked `SUPERSEDED`.

## Allowed bounded remediation classes

The following classes may be treated as bounded remediation only when they preserve the original objective, scope, dependency posture, architecture decision, and acceptance criteria:

```text
BUG_FIX
TEST_REMEDIATION
SECURITY_REMEDIATION
GOVERNANCE_REMEDIATION
PROTOCOL_CORRECTION
EVIDENCE_CORRECTION
DOCUMENTATION_TRUTH_CORRECTION
ACCEPTANCE_CRITERIA_REMEDIATION
```

For a frozen candidate, an allowed remediation still requires a new candidate identity. The deterministic classifier returns `BOUNDED_REMEDIATION_NEW_IDENTITY_REQUIRED` for that case.

`ACCEPTANCE_CRITERIA_REMEDIATION` means changing the implementation or evidence to satisfy already-frozen acceptance criteria. It does not authorize rewriting the acceptance criteria.

## Forbidden remediation expansion

The following are not valid bounded remediation:

```text
NEW_FEATURE
UNRELATED_OPTIMIZATION
ARCHITECTURAL_EXPANSION
NICE_TO_HAVE
NEW_INTEGRATION
NEW_SCOPE
DEPENDENCY_OR_POLICY_EXPANSION
VALIDATOR_WEAKENING
```

They require a return to the applicable admission/implementation process or are prohibited under the current candidate.

The same is true when the proposed change materially alters any of these frozen dimensions:

```text
OBJECTIVE
SCOPE
DEPENDENCY_POSTURE
ARCHITECTURE_DECISION
ACCEPTANCE_CRITERIA
```

Changing those dimensions cannot be relabeled as remediation merely because a candidate already exists.

## Recorded transition validation

The machine contract may validate that a recorded `previous_state -> state` pair is an allowed forward pair and that the required freeze shape is present. This is record validation, not a transition engine.

Examples:

```text
PROPOSED -> IMPLEMENTING                      VALID_PAIR
IMPLEMENTING -> FROZEN_CANDIDATE             VALID_PAIR
FROZEN_CANDIDATE -> ACCEPTED                 VALID_PAIR
ACCEPTED -> MERGE_READY                      VALID_PAIR
MERGE_READY -> MERGE_APPLIED_UNVERIFIED      VALID_PAIR
MERGE_APPLIED_UNVERIFIED -> MERGED_VERIFIED  VALID_PAIR
MERGED_VERIFIED -> RETIRED                   VALID_PAIR
```

Skipped stages, backward transitions, and same-identity self-transitions are rejected by the Campaign 2 validator.

## Evidence freshness

Evidence remains bound to the exact candidate identity it validated.

- a head or tree change invalidates exact-head evidence for the old candidate;
- a base or base-tree change invalidates merge-readiness claims that depended on the prior base;
- a policy, ruleset, acceptance, or scope identity change invalidates the evidence that was bound to it;
- a superseded candidate's evidence remains historical evidence but cannot be reused as current readiness evidence for its replacement.

Campaign 2 records these identities but does not replace the existing evidence system.

## Authority boundary

`CandidateMaturityRecord` is a state/evidence contract, not a permission grant.

```text
CANDIDATE_RECORD != EXECUTION_AUTHORITY
FROZEN_CANDIDATE != IMPLEMENTATION_AUTHORITY
ACCEPTED != MERGE_AUTHORITY
MERGE_READY != MERGE_AUTHORITY
MERGE_APPLIED_UNVERIFIED != MERGED_VERIFIED
MERGED_VERIFIED != RELEASE_AUTHORITY
RETIRED != BRANCH_DELETION_AUTHORITY
```

Merge, release/publication, deployment/production mutation, policy activation, installed-integration refresh, destructive cleanup, branch deletion, force push, history rewrite, and authority expansion remain separately governed.

## Relationship to Campaign 1

A candidate must reference its admission basis:

- a `FeatureDecisionRecord`; or
- an explicitly eligible `INLINE_RATIONALE_ALLOWED` basis from Feature Admission.

Campaign 2 does not decide whether Orchestra should own a capability. It consumes the already-recorded admission basis and constrains candidate maturity after implementation begins.

## Explicit exclusions

Campaign 2 does **not** add:

- a second runtime lifecycle controller;
- a second governance kernel;
- a new authority engine;
- automatic qualification-gate selection;
- experiment-policy or independent-audit policy;
- autonomy-profile changes;
- automatic merge;
- pre-state branch creation;
- branch deletion or cleanup;
- release/deployment/policy activation;
- live model/provider calls.

Those remain existing mechanisms or later separately authorized campaigns.
