# Signed Materialization Optimization

## Role of this document

This file is a human-readable explanation of the machine policy in `machine/governance/policy.v1.json` under `repository_change_transport.api_authored_unsigned_tree`. The JSON policy is the machine representation. This Markdown file does not override or reconstruct machine state.

## Problem

Some repository mutations performed through file/API tooling create an unsigned source head. Orchestra's protected `main` requires signed commits, so that unsigned head cannot be used directly for ordinary canonical progression.

The post-v1.5 documentation closeout demonstrated a three-PR pattern:

1. source PR for the unsigned authored tree;
2. auxiliary PR that squashed the reviewed tree onto an isolated branch to obtain a GitHub-signed commit;
3. canonical PR from the signed commit to `main`, followed by a fresh exact-head validation matrix.

That pattern was safe but duplicated the review surface. The source PR and materialization PR represented the same authored content before the final protected PR.

## Canonical optimized pattern

The machine policy now selects a two-PR pattern for API-authored unsigned trees:

```text
unsigned authored tree
    -> materialization PR targeting materialize/**
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

## Why workflow routing is unchanged in this phase

This first optimization removes the redundant source PR without changing workflow trigger semantics. That gives a measurable reduction in PR and validation duplication while keeping the current CI behavior intact.

If later evidence shows that intermediate `materialize/**` validation itself remains materially wasteful, workflow routing can be optimized as a separate bounded change. Such a change must still preserve full exact-head validation on the final signed PR to `main` and must not weaken the live ruleset.
