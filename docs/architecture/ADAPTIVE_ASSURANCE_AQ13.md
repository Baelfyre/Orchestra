# ADAPTIVE ASSURANCE AQ13 — Staged Non-Production Rollout Evaluation

AQ13 implements a deterministic `EVIDENCE_ONLY_NON_AUTHORIZING` evaluation of staged rollout evidence. It does **not** deploy Orchestra, change routing, activate a provider, alter protected policy, or create lifecycle authority.

## Boundary

The evaluation is bound to Orchestra canonical AQ12 closeout `2fc2d9ce9fc263813981e4dc8c88d1e4f604f036` and mode `CONTROLLED_NON_PRODUCTION_STAGED_ROLLOUT_EVALUATION`. Its environment scope is `NON_PRODUCTION_ONLY`.

The required progression is ordered:

1. `SHADOW`
2. `CANARY`
3. `LIMITED`
4. `EXPANDED`

These names describe evidence stages only. They do not authorize real production rollout.

## Evidence policy

Each stage requires at least 10 observations, independent evidence, deterministic replay parity, and explicit rollback-signal recording. Across the four stages AQ13 requires at least 40 observations.

The aggregate regression ceiling is 500 basis points (5%). Any critical violation forces `REVISION_REQUIRED`. Aggregate regression above the ceiling also forces `REVISION_REQUIRED`. An explicit rollback signal forces `HOLD` even when other measurements are acceptable. Insufficient, non-independent, or non-deterministic evidence yields `WAIT_FOR_EVIDENCE`.

A `PASS` means only that the controlled non-production evidence satisfied the AQ13 evaluation contract. It is not a production-readiness claim.

## Disposition precedence

AQ13 uses deterministic precedence:

`REVISION_REQUIRED` → `HOLD` → `WAIT_FOR_EVIDENCE` → `PASS`

This ordering prevents a favorable metric from averaging away a critical violation or rollback signal.

## Prime Directive alignment

Under the Prime Directive, remediation may proceed only when it preserves source truth, the registered AQ13 inventory, existing authority ownership, and all assurance thresholds. A failure may not be repaired by lowering the regression ceiling, ignoring a rollback signal, inventing evidence, weakening validation, or changing the protected phase registry.

## Authority boundary

AQ13 preserves all existing controls:

- Arbiter remains lifecycle-transition owner.
- The human-owned ADAPT-QA phase registry remains protected policy.
- Whitelist mutation remains human-only.
- Provider and telemetry activation remain unauthorized.
- Production mutation and release/deployment remain unauthorized.
- CritiQual `CUD10` remains `READY_NOT_STARTED_HELD_BY_CURRENT_USER`.
- AQ13 `PASS` grants no transition, release, production, provider, whitelist, protected-policy, or CUD10 admission authority.

AQ14 remains a separately registered phase and requires AQ13 canonical closeout plus Padayon reconciliation before activation.
