# Orchestra AR-2 Domain Capability Manifest Extraction

Status: `AR_2_DOMAIN_CAPABILITY_MANIFEST_IMPLEMENTATION_CANDIDATE`

Phase: `AR-2`

Canonical source baseline: `1081ce3ba0e32b63f0ffab8380b211755f8b27f2`.

## Purpose

Move the immutable run-bound capability manifest inward now that its dependencies are canonical domain contracts, without moving application-port resolution, repository-policy loading, or runtime audit projection into the domain.

## Canonical domain surface

`orchestra_runtime/domain/capabilities/manifest.py` owns `RuntimeCapabilityManifest`.

The manifest binds:

- canonical manifest identity;
- `RunIdentity`;
- policy version;
- an immutable ordered set of `RuntimeCapabilityGrant` values;
- `AuthorityProvenance`.

It preserves the existing fail-closed rules for empty manifests and case-insensitive capability identity collisions.

## Compatibility surface

`orchestra_runtime/capabilities.py` imports and re-exports the same `RuntimeCapabilityManifest` class object. Existing top-level `orchestra_runtime.RuntimeCapabilityManifest` therefore remains identity-compatible.

## Deliberately retained outside the domain

The transitional legacy capability module continues to own:

- `CapabilityResolver(ICapabilityResolver)`;
- trusted repository-policy filesystem loading;
- `RunIdentity` construction at the application boundary;
- runtime audit-event projection.

These concerns remain candidates for AR-3 application extraction or AR-4 infrastructure extraction. They are not pulled inward merely to reduce legacy code volume.

## Validation

Focused regression coverage verifies:

- domain, legacy, and public object identity;
- normalization, deterministic grant ordering, and serialization;
- empty-manifest rejection;
- duplicate capability collision rejection;
- inward-only dependency purity with no direct I/O.

Repository qualification remains authoritative. Validation success does not grant later-phase or protected-action authority.

## Non-goals

This unit does not:

- move `ICapabilityResolver` or `CapabilityResolver` into the domain;
- move repository policy loading;
- move runtime audit events;
- alter capability evaluation/intersection behavior;
- alter provider, MCP, runtime routing, or governance behavior;
- retire `orchestra_runtime.capabilities`;
- start AR-3 or AR-4;
- authorize release, deployment, production mutation, policy activation, provider routing/fallback, installed-integration refresh, destructive cleanup, branch deletion, force push, or history rewrite.

## Sequencing

After canonicalization and post-merge verification, AR-2 remains active for the residual pure governance, policy, and workflow contracts identified by the live dependency audit.
