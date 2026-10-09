# AQ9 Assurance Scope Policy

## Purpose

This policy separates the future AQ9 deep-assurance implementation from the historical PRAI, AQ5, and AQ7 exact implementation inventories without weakening those historical gates.

AQ9 is an assurance-depth phase. Its approved purpose is to expand mutation, property, metamorphic, and bounded fuzz coverage over existing deterministic assurance logic. It does not create a second QA engine, runtime authority, provider behavior, deployment behavior, or production behavior.

The policy is grounded in the primary maintainer's explicit `HUMAN_POLICY` decision recorded in Padayon at canonical commit `959369ec84140198c2cb1cf86743a6e368830f71` under decision ID `ORCHESTRA_AQ9_ASSURANCE_SCOPE_CLASSIFIER_HUMAN_POLICY_20260911`.

## Exact future AQ9 implementation inventory

Only the following exact nine-path set may be classified as a complete AQ9 implementation for historical-scope separation:

1. `CHANGELOG.md`
2. `README.json`
3. `cosmic-ray.toml`
4. `docs/architecture/ADAPTIVE_ASSURANCE_AQ9.md`
5. `machine/adaptive/aq9-deep-assurance.v1.json`
6. `machine/schemas/aq9-deep-assurance.v1.schema.json`
7. `scripts/validation/validate_aq9.py`
8. `tests/behavior/run_tests.py`
9. `tests/runtime/test_adaptive_assurance_aq9.py`

This inventory deliberately reuses the existing runtime and assurance architecture. AQ9 does not require a new production runtime module. `cosmic-ray.toml` is part of the exact set because mutation evidence is truthful only when AQ9-relevant existing assurance code is an actual mutation target. `tests/behavior/run_tests.py` is included only to register the AQ9 validator in the existing behavior-validation surface.

## AQ9 anchors

The following AQ9-identifying paths are anchors:

- `docs/architecture/ADAPTIVE_ASSURANCE_AQ9.md`
- `machine/adaptive/aq9-deep-assurance.v1.json`
- `machine/schemas/aq9-deep-assurance.v1.schema.json`
- `scripts/validation/validate_aq9.py`
- `tests/runtime/test_adaptive_assurance_aq9.py`

If any AQ9 anchor appears without the complete nine-path inventory, historical PRAI/AQ5/AQ7 applicability remains fail-closed `APPLICABLE`.

## Deterministic classification

```text
EXACT_COMPLETE_AQ9_IMPLEMENTATION_SET
    => NOT_APPLICABLE to historical exact implementation inventories

PARTIAL_AQ9_SET
    => APPLICABLE

MIXED_AQ9_SET
    => APPLICABLE

AQ9_SUPERSET_WITH_UNKNOWN_PATH
    => APPLICABLE

UNREGISTERED_FUTURE_AQ_PHASE_PATH
    => APPLICABLE
```

The classifier compares normalized exact repository paths. Duplicate or unsafe paths remain invalid.

## Not a whitelist

This policy is an assurance-phase taxonomy rule, not a lifecycle whitelist.

```text
AQ9_SCOPE_POLICY != WHITELIST
AQ9_SCOPE_SEPARATION != ASSURANCE_BYPASS
AQ9_SCOPE_SEPARATION != AUTHORITY_EXPANSION
```

The existing human-only whitelist boundary remains unchanged. This policy cannot create, modify, broaden, narrow, reinterpret, remove, or consume a whitelist.

## Preserved controls

The following remain unchanged:

- PRAI protected-policy handling;
- Covenant and specialist authority boundaries;
- Overseer validation ownership;
- Arbiter transition ownership;
- historical PRAI, AQ5, AQ6, AQ7, and AQ8 implementation inventories;
- statement and branch coverage thresholds;
- mutation evidence truthfulness requirements;
- repository required checks and rulesets;
- signed-materialization and tree-attested promotion controls;
- release, deployment, provider, credential, telemetry, and production authority.

AQ10 through AQ14 are not admitted by this policy. Any later phase needing historical-scope separation requires its own evidence and, where protected policy is implicated, its own human decision.

## Sequencing

This policy amendment must itself complete normal governed qualification, signed materialization when required, canonical promotion, and post-merge verification before the fresh AQ9 implementation begins. Historical source candidates may not consume an unmerged version of this policy as authority.
