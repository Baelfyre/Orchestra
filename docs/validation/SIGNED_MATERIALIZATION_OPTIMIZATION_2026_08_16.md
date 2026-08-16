# Signed Materialization Optimization

## Role of this document

This file is a human-readable explanation of the machine policy in `machine/governance/policy.v1.json` under `repository_change_transport.api_authored_unsigned_tree`. The JSON policy is the machine representation. This Markdown file does not override or reconstruct machine state.

## Problem

Some repository mutations performed through file/API tooling create an unsigned source head. Orchestra's protected `main` requires signed commits, so that unsigned head cannot be used directly for ordinary canonical progression.

The post-v1.5 documentation closeout demonstrated a three-PR pattern:

1. source PR for the unsigned authored tree;
2. auxiliary PR that squashed the reviewed tree onto an isolated branch to obtain a GitHub-signed commit;
3. canonical PR from the signed commit to `main`, followed by a fresh exact-head validation matrix.

That pattern was safe but duplicated both the review surface and validation work.

## Canonical optimized pattern

The machine policy selects a two-PR pattern for API-authored unsigned trees:

```text
unsigned authored tree
    -> materialization PR targeting materialize/**
    -> bounded signed-materialization workflow emits machine evidence
    -> review exact source tree
    -> GitHub Squash creates signed materialized commit
    -> verify materialized signature, parent, and exact tree equivalence
    -> canonical PR from signed materialized head to main
    -> full exact-head protected-main validation matrix
    -> require mergeable=true and mergeable_state=clean
    -> protected Squash merge with expected-head guard
    -> independent canonical readback
```

The materialization PR is both the review surface and the signing transport. A separate source PR is not required.

## Bounded materialization validation

Pull requests whose base branch matches `materialize/**` run `.github/workflows/signed-materialization.yml`. That workflow intentionally does not run the full behavior/runtime matrix, Mutmut, or Cosmic Ray. It checks the exact pull-request source head, verified materialization target identity, repository-relative changed paths, `git diff --check`, and the machine transport policy, then emits `signed-materialization-evidence` using `machine/schemas/signed-materialization-evidence.schema.json`.

The evidence disposition is `REVIEWED_UNSIGNED_SOURCE_READY_FOR_GITHUB_SQUASH_MATERIALIZATION`. It explicitly records that the materialization PR has no canonical merge-readiness, project-state promotion, release, or bypass authority.

The normal `validate`, `mutation-confidence`, and `cosmic-ray-confidence` pull-request workflows are scoped to `main`. Existing Governance Check, CodeQL, and cross-platform protected-main behavior remains unchanged.

## What is not optimized away

The final signed PR to `main` still requires the complete canonical evidence matrix. Materialization evidence is not reusable as canonical exact-head validation and tree equivalence is not a substitute for protected-main checks.

The current `Protect main` requirements remain unchanged, including signed commits, linear history, Squash-only merging, required status checks, up-to-date branch state, conversation resolution, and force-push/deletion protections.

## Authority boundaries

A materialization PR or branch:

- is not canonical merge readiness;
- does not promote project state;
- does not create release authority;
- does not create bypass authority;
- does not authorize policy activation, deployment, installed-integration refresh, destructive cleanup, branch deletion, force push, or history rewrite.

The signed materialized commit must preserve the exact reviewed tree and verified canonical base relationship before it may become the head of the canonical PR.

## Validation sequence

For API-authored unsigned changes, use this sequence:

1. create the unsigned source branch from a freshly verified canonical base;
2. create an isolated `materialize/**` branch from that same base;
3. open the source branch directly against the isolated materialization branch;
4. require the `signed-materialization` workflow to pass and review its exact machine evidence;
5. Squash the materialization PR without bypass;
6. verify the resulting commit signature, exact reviewed tree, and exact canonical parent;
7. open that signed materialized commit against `main`;
8. run the complete protected-main validation matrix on the exact signed head;
9. require current `mergeable=true`, `mergeable_state=clean`, zero unresolved review threads, and unchanged base/head identities;
10. Squash with the expected-head guard and independently verify the canonical result.

This optimization reduces duplicate signing/review validation without changing what evidence is required for canonical progression.
