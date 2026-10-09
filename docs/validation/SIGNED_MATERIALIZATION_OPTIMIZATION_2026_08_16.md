# Signed Materialization Optimization

## Status

`SUPERSEDED_BY_TREE_ATTESTED_PROMOTION_ASSURANCE`

This document preserves the historical 2026-08-16 two-PR signing optimization. The current machine policy is `machine/governance/policy.v1.json`, and the current human-readable promotion contract is `docs/governance/TREE_ATTESTED_PROMOTION_ASSURANCE.md`.

## Historical role

The original optimization reduced an earlier three-PR pattern to two PRs:

```text
unsigned authored tree
    -> materialization PR targeting materialize/**
    -> bounded signed-materialization workflow
    -> GitHub Squash creates a signed materialized commit
    -> canonical PR from the signed materialized head to main
    -> full exact-head protected-main validation matrix
    -> protected Squash merge
    -> independent canonical readback
```

The materialization PR acted as both review surface and signing transport. It intentionally did not run the full behavior/runtime matrix, mutation campaigns, or Cosmic Ray. Full canonical validation therefore still had to run on the signed head.

## Why it was superseded

AQ8 closeout exposed that the historical model repeatedly validated identical repository content because signing and canonical squash created new commit SHAs even when the Git tree was unchanged.

The current tree-attested model separates content qualification from promotion assurance:

1. a dedicated source PR to `main` receives the full applicable assurance matrix on the exact unsigned source SHA and tree;
2. a bounded materialization PR signs that already-qualified tree without repeating the content matrix;
3. a canonical PR preserves all required status-context identities but verifies the exact source -> carrier -> canonical provenance and tree chain instead of re-running full content assurance solely because the SHA changed;
4. any content mismatch, missing source assurance, invalid signature, wrong base/parent, wrong changed-path set, or unproven promotion identity fails closed.

This intentionally restores a separate source qualification PR. The additional PR is the evidence anchor that makes later validation reuse safe and deterministic.

## Preserved protections

The superseding model does not weaken the `Protect main` ruleset, required status contexts, signed-commit requirement, linear-history rule, squash-only merge policy, mergeability checks, conversation resolution, force-push/deletion protections, human-only whitelist authority, PRAI semantics, or independent protected-action authority.

Materialization and tree-attestation evidence remain non-authorizing. They do not create release, deployment, provider, credential, telemetry, production, whitelist, policy, or bypass authority.

## Current reference

See `docs/governance/TREE_ATTESTED_PROMOTION_ASSURANCE.md` and the current `repository_change_transport.api_authored_unsigned_tree` object in `machine/governance/policy.v1.json`.
