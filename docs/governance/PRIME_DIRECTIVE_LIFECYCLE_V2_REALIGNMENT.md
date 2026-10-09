# Prime Directive and Development Lifecycle V2 Realignment

Status: `MERGED_VERIFIED`

Recorded: 2026-08-27

Canonical closeout: 2026-08-28

## Canonical closeout

The realigned source was reviewed and promoted through PR #592 using the repository's signed-materialization path and Squash-only canonical merge discipline.

- canonical merge commit: `a04dafe75fc52ecc1fedcc17a73b14b8a31f548a`
- canonical tree: `854ebfb01b05226304f36d2c35420658c5c8e91f`
- sole parent: `11c255c3e0efa158b5df9fe4832c60f9ae401948`
- canonical signature: `VERIFIED_VALID`
- reviewed tree equals canonical tree: `true`
- post-merge validation: `PASS`
- public release remains: `v1.7.0`

The active `Protect main` ruleset `17927422` was separately corrected under explicit ruleset-mutation authority before the canonical merge. The unintended duplicate `native-ubuntu-latest` required-status entry was removed while the rest of the ruleset profile remained preserved. Ruleset correction and validation evidence did not create merge authority; PR #592 merged only after separate explicit merge authorization.

## Historical starting boundary

This realignment started from Orchestra canonical `main` at:

- commit: `11c255c3e0efa158b5df9fe4832c60f9ae401948`
- tree: `0a4d80e2a1c46e62a2599bef4626f81c21f8dc4f`
- latest published release: `v1.7.0`
- UIX-9C V3 controlled-study result: `NO_BENEFIT_ESTABLISHED`

The UIX-9C result records six valid observations, three corrected valid pairs, 39 primary governed-versus-baseline comparisons, zero improvements, and zero regressions. It establishes neither benefit nor harm and is retained as negative evidence.

## Purpose

The August 27 Campaign 0-5 stack was prepared from an earlier `main`. Its historical exact-head CI is evidence about those exact candidates, not current merge-readiness evidence. This realignment reconstructs only the still-valid constitutional and lifecycle work on current canonical `main`, preserving newer runtime, adaptive, UIX, documentation, and release work.

The reconstruction must not introduce a second governance kernel, autonomy engine, lifecycle controller, Arbiter, merge-readiness engine, or generic workflow platform.

## Campaign reconciliation

| Campaign | Source PR | Source head | Disposition | Current treatment |
| --- | ---: | --- | --- | --- |
| Campaign 0 - policy-source reconciliation | #573 | `838179da05bb638ffde165f628813a3b850901fa` | `KEEP_WITH_REALIGNMENT` | Preserve repository-side unique required-check parity and fail-closed drift detection. At candidate construction, the live `Protect main` ruleset contained a duplicate `native-ubuntu-latest` entry. That external policy drift was separately reconciled under explicit ruleset authority before PR #592 merged; the source candidate itself did not mutate the live ruleset. |
| Campaign 1 - Prime Directive + Feature Admission | #574 | `4f922ff8e94572ccfe778cb5a3bbaab66d747664` | `KEEP_WITH_REALIGNMENT` | Promote the constitutional Prime Directive and feature-admission/value boundary onto current `main`; retain existing governance as subordinate implementation. |
| Campaign 2 - Candidate Maturity + Feature Freeze | #576 | `59ac8db4f0d9e0b131ed14e6ff7f44811b05b5d5` | `KEEP_WITH_REALIGNMENT` | Keep development-candidate maturity separate from runtime execution lifecycle; exact identity and evidence staleness remain explicit. |
| Campaign 3 - Governed Autonomy lifecycle integration | #578 | `258a46553ad8529e41ed89552a731cf70e74cdd2` | `KEEP_WITH_REALIGNMENT` | Reuse the existing autonomy evaluator and authority envelope. `AUTONOMY_CHANGES_PAUSES_NOT_PREREQUISITES`. Full Autonomous cannot self-adopt permanent capability. |
| Campaign 4 - Qualification, evaluation, audit | #580 | `3a1e9beef4b63dbd078ac31fd8a3f2833bf5930e` | `KEEP_WITH_REALIGNMENT` | Preserve risk-proportional qualification, preregistered controlled evaluation, negative-evidence retention, and read-only first independent audit. UIX-9C is the canonical example that valid implementation plus valid experiment does not imply promotion when repeatable benefit is not established. |
| Campaign 5 - pre-state, recovery, retirement | #582 | `090d362b05b9bcdaff73b8bf01950c2420be1fe8` | `KEEP_WITH_REALIGNMENT` | Preserve forward-only recovery and conservative branch-retirement classification. Eligibility remains evidence, never deletion authority. |

## Constitutional boundary

The realigned Prime Directive remains implementation-neutral:

> Orchestra shall permit an AI-assisted action or lifecycle transition only within explicit, reduction-only authority and current applicable evidence. It shall never infer permission from capability, routing, confidence, learned state, validation success, mergeability, or prior success. A permanent capability shall be promoted only when proportional evidence shows that it solves an Orchestra-owned problem whose benefit justifies its complexity and risk without weakening these boundaries.

Key semantic separations remain controlling:

```text
CAPABILITY != AUTHORITY
ROUTING != AUTHORITY
VALIDATION_SUCCESS != AUTHORITY
MERGEABILITY != MERGE_AUTHORITY
ADMISSION != PROMOTION
PROMOTION != MERGE_AUTHORITY
MERGE_READY != MERGE_AUTHORITY
ADOPTION != RELEASE_OR_ACTIVATION_AUTHORITY
```

## Development Lifecycle V2

The development lifecycle is a governance overlay for candidate maturity and promotion, not a replacement for Orchestra's runtime execution lifecycle:

```text
Feature Admission
-> Baseline + Implementation
-> Candidate Declaration / Feature Freeze
-> Qualification Gate Set
-> Promotion Adjudication
-> Merge Preparation
-> Merge + Independent Verification
-> Closeout + Retirement
```

Candidate maturity is recorded separately as:

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

Implementation correctness, validation, evidence support, adoption value, merge readiness, merge authority, and release/activation authority remain distinct decisions.

## UIX-9C negative-evidence integration

The completed UIX-9C V3 study is retained as a concrete feature-admission and promotion example:

```text
VALID_IMPLEMENTATION
+
VALID_EXPERIMENT
+
NO_REPEATABLE_MEASURABLE_ADVANTAGE
=
NO_AUTOMATIC_PROMOTION
```

`NO_BENEFIT_ESTABLISHED` does not mean harm was established. The evidence must not be discarded, selectively retried, or rewritten into a positive claim.

## Evidence and authority rules

- Historical Campaign 0-5 exact-head CI remains historical evidence only.
- Current readiness requires fresh validation on the reconstructed exact head.
- Any source change invalidates earlier exact-head readiness evidence.
- Experiment plans do not grant live model/provider call authority.
- Qualification does not grant acceptance.
- Acceptance does not grant merge authority.
- Retirement eligibility does not grant branch-deletion authority.
- A state-changing action is incomplete until canonical state is independently read back.

## Current live ruleset state

A post-correction read-only GitHub ruleset read for active `Protect main` ruleset `17927422` reports the required-status profile with each context exactly once:

- `governance-check`
- `validate`
- `native-windows-latest`
- `native-ubuntu-latest`
- `native-macos-latest`
- `runtime-tests`
- `Compatibility CodeQL (python)`

The same live read preserves strict required-status enforcement, Squash-only merging, required linear history, required signatures, pull-request requirements, deletion/non-fast-forward protection, default-branch targeting, and the pre-existing bypass actors. `RULESET_PROFILE_DRIFT = FALSE` at the PR #592 closeout checkpoint.

This is external repository configuration and must be re-read for future merge decisions. Its current validity does not create future merge, release, policy, or bypass authority.

## Protected boundaries

This realignment grants no authority for:

- future canonical merge;
- release/tag publication;
- deployment or production mutation;
- policy activation;
- live GitHub ruleset mutation;
- installed-integration refresh;
- branch deletion or destructive cleanup;
- force push or history rewrite;
- live model/provider experiments;
- autonomous amendment of the Prime Directive.

## Completion disposition

PR #592 satisfied the realignment completion condition and is `MERGED_VERIFIED`. The reviewed source tree was canonically materialized without content drift, the ruleset profile was separately reconciled before merge, the exact candidate passed the required pre-merge matrix, and the canonical post-merge workflow matrix passed on `a04dafe75fc52ecc1fedcc17a73b14b8a31f548a`.

This closeout is historical evidence for that transition only. Any future candidate must establish its own current baseline, exact-head validation, live ruleset parity, zero unresolved review blockers, and separately applicable merge authority.