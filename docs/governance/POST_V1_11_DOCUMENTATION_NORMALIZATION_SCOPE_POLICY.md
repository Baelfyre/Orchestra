# Post-v1.11 Documentation Normalization Assurance Scope

Decision ID: `ORCHESTRA_POST_V1_11_DOCUMENTATION_NORMALIZATION_SCOPE_HUMAN_POLICY_20260911`

Authority class: `HUMAN_POLICY`

## Decision

The maintainer authorizes one deterministic exact-set assurance-scope lane for the post-publication normalization of Orchestra v1.11.0 documentation.

Historical PRAI, AQ5, and AQ7 implementation inventories are `NOT_APPLICABLE` only when the candidate diff is exactly the registered documentation inventory enforced by `scripts/validation/classify_adaptive_assurance_scope.py`.

Partial, mixed, superset, runtime, protected-governance, provider, telemetry, production, deployment, and unknown changes remain fail-closed and do not inherit this classification.

## Preserved authority boundaries

This decision does not authorize runtime behavior changes, provider/model activation, telemetry, production mutation, deployment, whitelist mutation, protected-policy self-amendment, AQ15, AR3 implementation, or CritiQual CUD10 admission. Ordinary Governance, validate, Required Analysis, Cross-platform, Cosmic Ray/CodeQL when applicable, signed materialization, canonical promotion, and post-merge validation remain governed by their existing contracts.

## Execution separation

This governance amendment is canonicalized separately. The documentation-normalization candidate must be created only after this policy is canonical and must match the exact registered path inventory.
