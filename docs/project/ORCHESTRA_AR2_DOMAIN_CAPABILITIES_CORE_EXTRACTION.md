# Orchestra AR-2 Domain Capabilities Core Extraction

Status: `AR_2_DOMAIN_CAPABILITIES_CORE_CANDIDATE`

Phase boundary: AR-2 remains active. AR-3 is not started.

## Objective

Move only the capability value objects and deterministic capability-decision semantics into the inward domain layer without pulling run identity, filesystem policy loading, application ports, or runtime audit projection into the domain.

## Canonical inward ownership in this candidate

`orchestra_runtime/domain/capabilities/core.py` owns:

- `CapabilityReasonCode`;
- `RuntimeCapability`;
- `RuntimeCapabilityGrant`;
- `CapabilityDecision`;
- capability identifier/text normalization used by those domain objects;
- deterministic grant evaluation;
- fail-closed decision enforcement; and
- restrictive delegated grant intersection.

The domain capability core imports only standard-library value-object support, `orchestra_runtime.domain.governance.authority`, and `orchestra_runtime.shared.errors`.

## Transitional legacy ownership retained

`orchestra_runtime/capabilities.py` deliberately continues to own:

- `RuntimeCapabilityManifest`, because it is run-bound through legacy `RunIdentity`;
- `CapabilityResolver` application-port inheritance and run-bound manifest construction;
- `load_trusted_capability_manifest`, because trusted policy loading performs filesystem I/O;
- `capability_manifest_event` and `capability_decision_event`, because runtime audit projection remains outside the pure domain core.

`RunIdentity` is not moved by this unit. Its current correlation validation dependency is coupled to a module that also owns UUID, clock, and entropy-backed correlation generation, so that boundary requires a separate classification and extraction rather than implicit migration here.

## Compatibility contract

Existing imports from `orchestra_runtime.capabilities` remain valid. The legacy module re-exports the same canonical class and enum objects for:

- `RuntimeCapability`;
- `RuntimeCapabilityGrant`;
- `CapabilityDecision`; and
- `CapabilityReasonCode`.

The transitional `CapabilityResolver` delegates deterministic evaluation, enforcement, and grant intersection to the inward capability core while preserving its existing public method behavior and run-bound manifest construction.

## Dependency direction

The intended dependency direction for this unit is:

`legacy/application transition -> domain.capabilities -> domain.governance + shared.errors`

The domain capability core does not import `pathlib`, host/provider surfaces, MCP, application interfaces, legacy models, audit projections, persistence, or repository `internal/` modules.

## Validation

`tests/runtime/test_domain_capabilities_core.py` verifies:

- legacy-to-domain symbol identity;
- normalized allow/deny evaluation semantics;
- fail-closed operation and constraint denial;
- restrictive delegated grant intersection; and
- inward-only import boundaries.

The existing runtime capability, delegation, authority-integration, adversarial, and correlation tests remain the broader compatibility regression surface.

## Non-goals

This bounded AR-2 unit does not:

- move `RunIdentity` or correlation generation/validation;
- move filesystem-backed trusted policy loading;
- move application ports or start AR-3;
- move infrastructure concerns or start AR-4;
- alter provider or MCP execution behavior;
- retire legacy public imports;
- change release, deployment, policy/ruleset, destructive-operation, installed-integration, or publication authority.
