# Tree-Attested Promotion Assurance

## Purpose

Orchestra binds full content assurance to the exact qualified repository tree. When an API-authored source tree has already completed its applicable source-candidate assurance, later signed-materialization and canonical-promotion stages verify identity, provenance, and tree continuity instead of repeating the complete content suite solely because GitHub created a new commit SHA.

This control is evidence-only and non-authorizing. It does not create merge, release, deployment, provider, production, whitelist, or policy authority.

## Core invariant

```text
NO_CONTENT_CHANGE => REUSE_CONTENT_ASSURANCE_THROUGH_VERIFIED_TREE_ATTESTATION
CONTENT_CHANGE_OR_UNPROVEN_ATTESTATION => FULL_ASSURANCE_REQUIRED_OR BLOCK
```

A commit SHA is part of provenance, but content assurance is bound to the Git tree. Reuse is permitted only when the complete source-to-carrier-to-canonical chain is independently verified.

## API-authored unsigned transport

The current transport is deliberately three-stage and three-PR:

```text
unsigned source branch
    -> source PR to main
    -> full exact-source assurance
    -> isolated materialization PR
    -> bounded signing validation
    -> GitHub-signed identical-tree carrier
    -> canonical PR to main
    -> tree/provenance attestation through required contexts
    -> protected squash merge
    -> canonical tree/provenance readback
```

The extra source PR is the qualification surface. It is not merged directly. Its role is to establish full assurance on the exact content tree before signing and promotion. The materialization PR is signing transport only, and the canonical PR is the promotion surface.

This replaces the earlier two-PR transport documented in `docs/validation/SIGNED_MATERIALIZATION_OPTIMIZATION_2026_08_16.md`, because a two-PR flow does not provide an independently full-qualified unsigned source tree to which later promotion assurance can be safely bound.

## Assurance stages

### 1. Source candidate

The source branch opens a dedicated PR to `main`. It remains a full-assurance candidate. The existing required checks and any applicable specialized assurance workflows execute normally against the exact source SHA and tree.

The promotion validator does not classify ordinary source branches as tree-attested promotions. Source qualification must be complete before materialization may support assurance reuse.

### 2. Signed materialization

The `materialize/**` signing transport remains bounded and non-authorizing. GitHub Squash produces a signed carrier whose parent must equal the verified canonical base and whose tree must equal the qualified source tree.

Materialization does not repeat the source content matrix and does not independently grant canonical readiness.

### 3. Canonical promotion

A pull request to `main` whose head is a `materialize/**` branch may use tree-attested promotion assurance only when the validator independently proves all of the following:

- the signed carrier commit is GitHub-verified with reason `valid`;
- the carrier has exactly one parent and it equals the canonical PR base;
- exactly one merged materialization PR produced that carrier on the expected materialization branch and canonical base;
- the materialization source SHA resolves to exactly one source PR against the same canonical base;
- the qualified source tree equals the signed carrier tree;
- source and canonical promotion changed-path sets are identical;
- every required source check context is terminal `success`;
- every pull-request workflow observed on the exact source SHA is terminal-success, neutral, or intentionally skipped;
- any observed GitHub CodeQL security check is terminal-success, neutral, or intentionally skipped.

If a branch is an ordinary source candidate, full assurance runs. If a branch presents itself as a signed promotion but any required attestation fails, the promotion fails closed rather than silently falling back and discarding the signed-provenance requirement.

### 4. Canonical post-merge state

For a `main` push produced by a recognized signed canonical promotion, the validator additionally proves:

- the canonical SHA resolves to exactly one merged PR to `main`;
- the canonical commit is GitHub-verified with reason `valid`;
- the canonical parent equals the push `before` SHA and canonical PR base;
- the canonical tree equals both the signed carrier tree and qualified source tree;
- the complete source assurance and promotion provenance chain remains valid.

A `main` push that is not a recognized signed promotion continues through ordinary full assurance.

## Required check compatibility

The active `Protect main` ruleset remains authoritative. The required contexts are not removed, renamed, bypassed, or weakened:

- `governance-check`
- `validate`
- `runtime-tests`
- `native-windows-latest`
- `native-ubuntu-latest`
- `native-macos-latest`
- `Compatibility CodeQL (python)`

For an independently verified tree-identical signed promotion, these contexts execute the bounded promotion attestation instead of repeating the source content suite. For an ordinary source candidate, they execute their existing full logic.

## Historical assurance classifiers

`validate.yml`, `cross-platform-validation.yml`, `signed-materialization.yml`, the signed-materialization validator/tests, and the historical signed-materialization transport document are governance-control surfaces because they define or verify repository promotion and required-assurance transport. They are classified as governance paths for historical exact-scope compatibility.

This is a control-surface classification, not a one-off lifecycle whitelist. It does not create a path-set exception for application/runtime changes and does not alter the exact AQ8 canonical-closeout whitelist.

## Fail-closed rules

Tree-attested reuse is rejected when source identity, source checks, source workflows, tree equality, changed-path continuity, materialization identity, carrier signature, canonical base, canonical parent, or canonical signature cannot be proven exactly.

The following remain unchanged:

- human-only whitelist authority;
- PRAI protected-policy self-modification handling;
- Covenant and specialist authority boundaries;
- coverage and mutation thresholds;
- repository ruleset enforcement;
- signed materialization requirements;
- no force push, rebase, amend, or history rewrite;
- independent release, deployment, provider, credential, telemetry, and production authority.

## Human authority

This realignment is grounded in Padayon decision `ORCHESTRA_AQ8_TREE_ATTESTED_PROMOTION_ASSURANCE_20260911`, canonicalized at Padayon commit `03d60fb5c8df4527bd13f4d09251ae57bd89cead`.

The decision was made after AQ8 canonical content completion and does not authorize AQ9 by itself.
