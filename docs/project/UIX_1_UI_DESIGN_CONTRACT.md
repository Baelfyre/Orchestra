# UIX-1 UI Design Contract

Status: `UIX_1_SCHEMA_IMPLEMENTED_PENDING_CANONICAL_VALIDATION`

Recorded: 2026-08-24

Entry baseline: `de8fa50fe6b379deb491667d5ca913c23c55b616`

UIX-0 authority: `docs/project/UIX_0_ACTIVATION_OVERLAP_AUDIT.md`

## Purpose

UIX-1 defines the first library-neutral machine-readable UI Design Contract for Orchestra. The contract records design intent and evidence so downstream specialists can preserve an existing design system, reuse project-native components and tokens, identify unresolved design evidence, and bind later rendered validation to the same reference identity.

The contract is evidence. It does not itself authorize implementation, dependency adoption, Figma mutation, validation bypass, release, deployment, or production mutation.

## Canonical schema surface

- Schema: `machine/schemas/ui-design-contract.schema.json`
- Valid example: `tests/fixtures/ui/uix1-valid-contract.json`
- Invalid inference fixture: `tests/fixtures/ui/uix1-invalid-inferred-without-approval.json`
- Invalid unknown-field fixture: `tests/fixtures/ui/uix1-invalid-unknown-field.json`
- Deterministic validation: `tests/runtime/test_ui_design_contract.py`

Schema version:

```text
orchestra.ui-design-contract.v1
```

JSON Schema dialect:

```text
https://json-schema.org/draft/2020-12/schema
```

## Contract sections

The top-level contract contains exactly these sections:

```text
schema_version
contract_id
source
design_system
components
layouts
theme
assets
accessibility
fidelity
validation
authority
```

Unknown top-level fields are rejected. Nested contract records also use closed object shapes where the schema defines deterministic fields.

## Source evidence

Supported source-provider classifications are:

```text
FIGMA
PROJECT_NATIVE
STORYBOOK
SCREENSHOT
REFERENCE_IMAGE
OTHER_STRUCTURED
NONE
```

This deliberately keeps Figma optional. A project-native design system can produce a valid contract without Figma or Code Connect.

Capability markers are evidence only:

```text
STRUCTURED_CONTEXT
CODE_CONNECT
COMPONENT_DOCS
DESIGN_TOKENS
EXACT_ASSETS
RENDERED_REFERENCE
```

Their presence does not grant authority or force a target project to adopt a tool.

## Evidence confidence

Evidence-bearing fields use these confidence states:

```text
CONFIRMED
MISSING
INFERRED_WITH_EXPLICIT_APPROVAL
UNRESOLVED
```

`INFERRED_WITH_EXPLICIT_APPROVAL` is fail-closed: an `approval_ref` is required. A model cannot label an inference as approved merely by choosing the enum value.

The intended downstream behavior is:

- `CONFIRMED`: sourced design evidence exists.
- `MISSING`: required evidence is known to be absent.
- `INFERRED_WITH_EXPLICIT_APPROVAL`: a bounded inference was explicitly approved and is traceable to that approval.
- `UNRESOLVED`: evidence is insufficient and implementation should not silently guess.

## Design-system model

The schema keeps implementation tools out of the contract. It records evidence-bound token sets for:

- primitive tokens;
- semantic tokens;
- component tokens;
- typography roles;
- spacing scale;
- radii;
- borders;
- shadows;
- motion;
- breakpoints.

Token values are deliberately limited to scalar JSON values in v1. Composite token structures should be represented through stable named records rather than arbitrary nested objects until a later schema version proves that richer value types are necessary.

## Components and project reuse

Each component records:

- canonical component identity;
- source mapping;
- variants;
- states;
- slots;
- accessibility contract;
- project component mapping.

Project mappings use:

```text
EXACT
ADAPTED
NONE
UNRESOLVED
```

`EXACT` and `ADAPTED` require a concrete target component identity. This supports the UIX rule that existing target-project components should be resolved before a model generates a one-off substitute.

## Layouts and themes

Layout records capture pattern, regions, responsive ordering, containment, overflow, and source identity without prescribing CSS, React, JavaFX, or another frontend implementation mechanism.

Theme fields remain compositional and nullable:

- foundation;
- layout profile;
- theme profile;
- optional effects.

The initial style taxonomy is not hard-coded into the v1 schema. UIX-3 owns the profile registry and compatibility rules. UIX-1 therefore allows stable profile identifiers without prematurely making one aesthetic taxonomy part of the schema vocabulary.

## Assets

Asset records cover:

```text
FONT
ICON
IMAGE
LOGO
ILLUSTRATION
```

Each asset records semantic role, source identity, provenance state, license/source review state, and substitution policy.

Substitution policies are:

```text
EXACT_REQUIRED
PROJECT_MATCH_ALLOWED
APPROVAL_REQUIRED
NO_SUBSTITUTION
```

This contract prevents a known asset from being silently replaced merely because a model can generate or locate a visually similar alternative.

## Accessibility invariants

Accessibility requirements are first-class contract data for both the whole design and individual components:

- semantics;
- keyboard behavior;
- focus behavior;
- names and descriptions;
- contrast;
- target size;
- reduced motion;
- error state behavior.

The schema records requirements; it does not claim they have passed. Rendered accessibility evidence remains Overseer-owned downstream validation.

## Fidelity dispositions

Every tracked fidelity item uses exactly one disposition:

```text
PRESERVED
INTENTIONALLY_ADAPTED
UNRESOLVED
DIVERGENT
```

Rules:

- `PRESERVED` requires a source reference.
- `INTENTIONALLY_ADAPTED` requires both a reason and an explicit `approval_ref`.
- `UNRESOLVED` requires a reason and must not be silently treated as preserved.
- `DIVERGENT` requires a reason and remains visible to downstream review.

This prevents implementation convenience from silently becoming design truth.

## Validation state

The contract can exist before implementation. Validation status is therefore explicit:

```text
PRE_IMPLEMENTATION
IMPLEMENTATION_BOUND
VALIDATED
BLOCKED
```

Comparison state is independently explicit:

```text
NOT_RUN
PASS
FAIL
INCONCLUSIVE
```

The reference identity is always retained. Before implementation, the implementation revision may be `null` and rendered/accessibility evidence arrays may be empty. Later UIX phases must bind evidence to the actual implementation revision instead of rewriting the design reference to erase a failure.

## Authority boundary

Three authority fields are schema constants and can never be set to `true`:

```text
contract_grants_implementation_authority = false
external_tools_grant_authority = false
validation_grants_authority = false
```

The contract may record whether dependency adoption or Figma mutation has separately been authorized, but setting those booleans records external authority; it does not create it.

The schema therefore preserves:

```text
DESIGN_EVIDENCE != IMPLEMENTATION_AUTHORITY
TOOL_CAPABILITY != AUTHORITY
VALIDATION_PASS != AUTHORITY
FIGMA_CONTEXT != PROJECT_STACK_SELECTION
```

## Deterministic tests

The UIX-1 test suite proves that:

1. the Draft 2020-12 schema is itself valid;
2. the reference contract validates;
3. stored invalid fixtures are rejected;
4. inferred evidence without approval is rejected;
5. the same inference becomes valid only with an explicit approval reference;
6. intentional adaptation requires both reason and approval;
7. project-native evidence validates without Figma or Code Connect;
8. exact/adapted project component mappings require an actual target;
9. contract, tool, or validation evidence cannot be converted into authority by setting an authority flag;
10. a pre-implementation contract cannot masquerade as rendered validation evidence.

## Ownership

UIX-1 does not change the UIX-0 ownership model:

- Cloak owns design intent and static fidelity requirements.
- Clockwork owns UI engineering/component boundaries.
- Ponytail owns authorized implementation.
- Overseer owns rendered/browser/accessibility evidence.
- Conductor owns routing.
- Arbiter owns transition disposition.
- Governor owns licensing/IP review when adoption or asset use creates that need.

## Non-goals

UIX-1 does not:

- implement Figma ingestion;
- write Code Connect mappings;
- install or require Storybook, Playwright, axe-core, shadcn/ui, Radix, Material, or token tooling;
- modify Cloak, Clockwork, Ponytail, Overseer, or Conductor behavior yet;
- create runtime UI generation authority;
- create a visual style registry;
- perform target-project UI implementation;
- perform rendered comparison;
- authorize UIX-2 or later phases by itself.

## Exit condition

UIX-1 is ready for canonicalization only when the exact source head passes Orchestra governance, runtime/schema tests, required analysis, and cross-platform validation. After canonical readback, the next planned unit is UIX-2, the Cloak design-source preservation workflow, under a separately bounded continuation decision.
