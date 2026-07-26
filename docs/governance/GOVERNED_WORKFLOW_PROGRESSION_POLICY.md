# Governed Workflow Progression Policy

## Status

```text
POLICY_STATUS=ACCEPTED
EFFECTIVE_DATE=2026-07-26
SCOPE=AUTHORIZED_ORCHESTRA_REPOSITORY_WORKFLOWS
```

## Purpose

This policy defines when an already-authorized Orchestra repository workflow may progress without a separate human approval message at every internal gate.

It does not weaken validation, governance, scope control, evidence requirements, or fail-closed behavior. It replaces repeated approval prompts with standing authorization only while every required control remains satisfied.

## Standing governed authorization

After the user has established the task objective and authorized scope, the workflow may continue through the following repository-local actions without requesting a new approval at every step:

- implementation and exact-scope corrections;
- focused and consolidated validation;
- exact-scope staging;
- commit creation;
- non-force push to the same authorized branch;
- draft pull-request creation and metadata maintenance;
- draft-to-ready transition;
- merge when the exact reviewed head is mergeable and all required validation, governance, CI, review, and guardrail conditions pass;
- post-merge verification and repository/knowledge-base state synchronization.

Each action remains conditional. Standing authorization is not permission to bypass a failed or missing gate.

## Mandatory progression gates

Before advancing, the workflow must verify all controls relevant to the action, including:

- exact repository, branch, base, head, parent, tree, path, and blob identity;
- no unauthorized paths, unrelated refactors, or hidden scope expansion;
- clean working tree and index where local Git state is involved;
- focused tests and the complete required validation suite;
- strict governance and repository guardrails;
- canonical-to-adapter or generated-reference parity when applicable;
- non-force remote updates and exact remote-head verification;
- current pull-request metadata, changed-file scope, mergeability, CI, review submissions, and unresolved review threads;
- durable evidence and knowledge-base updates at each material gate.

A workflow must stop and report a blocker when any required control fails, becomes unavailable, contradicts the approved scope, or produces uncertain evidence.

## Actions outside standing authorization

The following remain separate unless they are explicitly included in the task's approved purpose:

- release, tagging, package publication, marketplace publication, or deployment;
- production configuration or production-resource changes;
- destructive data or repository operations;
- force push, history rewriting, or branch-protection/ruleset changes;
- branch deletion;
- secrets, credentials, billing, external accounts, or expanded external-action authority;
- unrelated consumer-repository changes;
- expansion beyond the authorized issue, phase, paths, or stated objective.

## Documentation requirement

The repository record and the external project knowledge base must remain consistent.

At minimum, continuity records must capture:

- the approved scope and applicable standing authorization;
- base, implementation, correction, merge, and state-sync commit identities;
- pull-request numbers and final state;
- changed-path counts and any exact correction scope;
- validation and CI results;
- blockers and corrections;
- remaining boundaries and excluded authority.

Transient wording such as `unstaged`, `uncommitted`, or `awaiting approval` must not remain in durable post-action records after the corresponding state has changed.

## Issue #195 application

The Tuner Phase 4 workflow applied this policy after the user established standing authorization to continue while validation, governance, and guardrails remained satisfied.

```text
ISSUE=195
IMPLEMENTATION_PR=200
IMPLEMENTATION_HEAD=455f5272734f6091ab686bc0aa56094b684511eb
IMPLEMENTATION_MERGE=32fb67f8b2fd5c3436a1f2738e13e7903fda5328
PHASE_4_STATUS=MERGED
```

The merge does not authorize persistence, SQLite, migrations, RPC, host orchestration, release, deployment, consumer-repository mutation, Dagger authority expansion, or expanded external-action authority.
