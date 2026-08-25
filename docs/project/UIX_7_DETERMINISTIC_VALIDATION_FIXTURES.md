# UIX-7 Deterministic Validation Fixtures

Status: `UIX_7_DETERMINISTIC_VALIDATION_FIXTURES_IMPLEMENTED_PENDING_CANONICAL_VALIDATION`

Recorded: 2026-08-24

Entry baseline: `67af42002a18ac3b58811cb2877d285bc8604ce0`

## Purpose

UIX-7 converts the UI fidelity requirements accumulated in UIX-1 through UIX-6 into deterministic pass and fail-closed fixtures. The phase validates objective contract behavior without adding a frontend stack, browser dependency, runtime adapter, external service, model judgment, or implementation authority.

## Required coverage

The fixture suite contains one passing and one fail-closed case for each required category:

1. component reuse;
2. token preservation;
3. arbitrary-value drift;
4. state completeness;
5. profile conflicts;
6. asset provenance;
7. responsive containment;
8. accessibility invariants;
9. reference identity; and
10. unauthorized visual-baseline replacement.

The visual-baseline case is deliberately strict: an existing failing comparison cannot be erased by replacing the baseline, even when a nominal approval reference is present. A baseline refresh after a passing comparison still requires explicit approval and a reason.

## Validation-only surfaces

- Fixture schema: `tests/fixtures/ui/uix7-deterministic-validation-fixtures.schema.json`
- Deterministic suite: `tests/fixtures/ui/uix7-deterministic-validation-suite.json`
- Runtime-test harness: `tests/runtime/test_deterministic_ui_validation_fixtures.py`
- Profile-conflict source: `machine/ui/ui-profile-registry.v1.json`
- Component and asset source: `machine/ui/component-asset-preservation-contract.v1.json`
- UI design source: `machine/schemas/ui-design-contract.schema.json`
- Optional-adapter boundary source: `machine/ui/optional-adapter-boundaries.v1.json`

Schema version: `orchestra.ui-deterministic-validation-fixtures.v1`

## Deterministic dispositions

Every fixture resolves to exactly one of:

- `PASS`
- `FAIL_CLOSED`

Fail-closed cases carry a stable failure code. The test harness recomputes the expected disposition from fixture inputs rather than trusting the fixture's declared result. Profile composition is evaluated against the canonical UIX-3 registry.

## Authority boundaries

UIX-7 is validation evidence only. Fixture results do not grant implementation, adoption, baseline, external-tool, Figma, release, deployment, or policy authority. The evaluator exists only in the test surface and does not alter Orchestra runtime behavior.

No dependency installation, runtime integration, external call, Figma mutation, installed-integration refresh, release, deployment, policy activation, branch deletion, force push, or history rewrite is part of this phase.

## Exit gate

UIX-7 exits only after the exact fixture suite and test harness pass the fresh protected-main validation matrix, the reviewed tree is GitHub-signed through the repository's API-authored signed-materialization transport, canonical promotion uses an exact-head guard, and the resulting canonical commit is independently read back.

Stop before UIX-8 until that canonical readback is complete.
