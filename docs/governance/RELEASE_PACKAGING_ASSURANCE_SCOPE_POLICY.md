# Release Packaging Assurance Scope Policy

Status: **HUMAN_POLICY — APPROVED 2026-09-11**

## Decision

A narrowly bounded `RELEASE_PACKAGING` scope may be classified as `NOT_APPLICABLE` to the historical AQ5, AQ6, and PRAI exact implementation inventories when, and only when, the complete changed-path set matches the deterministic release-packaging inventory defined by the protected scope classifier.

This authority was granted by the human maintainer on 2026-09-11 after the v1.11.0 release candidate demonstrated that AQ5, AQ6, and PRAI runtime/contract checks passed while their historical exact-scope jobs could not represent ordinary release packaging.

## Required properties

The release-packaging scope is exact-set and fail-closed:

- all fixed release/version/documentation/test surfaces must be present;
- exactly one versioned release-candidate document must be present;
- exactly one matching versioned release-readiness evidence document must be present;
- the two version identities must match;
- partial inventories are `APPLICABLE`;
- supersets are `APPLICABLE`;
- runtime, governance, security, provider, telemetry, production/deployment, or unknown additions are `APPLICABLE`;
- duplicate, unsafe, or malformed paths are rejected;
- this classification does not skip Governance, validate, Required Analysis, Cross-platform Validation, Cosmic Ray, CodeQL, version-surface tests, host-update tests, signed materialization, canonical promotion, or post-merge verification.

## Non-authority

This policy does not:

- lower AQ5, AQ6, PRAI, mutation, coverage, or governance thresholds;
- authorize AQ15 or any later unregistered ADAPT-QA phase;
- authorize provider/routing, telemetry, production, deployment, secret, or protected-policy mutation;
- authorize CritiQual CUD10;
- allow release publication when any mandatory release gate fails.

Any future release whose packaging inventory differs from the deterministic registered shape fails closed and requires a fresh human-policy decision before the classifier may be broadened.
