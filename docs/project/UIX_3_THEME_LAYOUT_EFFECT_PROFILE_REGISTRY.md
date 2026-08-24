# UIX-3 Theme, Layout, and Effect Profile Registry

Status: `UIX_3_PROFILE_REGISTRY_IMPLEMENTED_PENDING_CANONICAL_VALIDATION`

Recorded: 2026-08-24

Entry baseline: `8e4f3bb5e878131e8c038ea195311c92ca08cfde`

## Purpose

UIX-3 defines a versioned, library-neutral registry for composing a foundation, layout, complete theme/design system, and optional visual effect. The registry prevents models from treating every visual idea as a peer theme or mixing unrelated systems without a deterministic rejection rule.

The registry is metadata and evidence. It does not prescribe CSS values, select a frontend stack, authorize implementation, authorize dependency adoption, make an external tool authoritative, or authorize Figma mutation.

## Canonical machine surface

- Schema: `machine/schemas/ui-profile-registry.schema.json`
- Registry: `machine/ui/ui-profile-registry.v1.json`
- Valid composition fixture: `tests/fixtures/ui/uix3-valid-profile-composition.json`
- Invalid composition fixture: `tests/fixtures/ui/uix3-invalid-full-system-mix.json`
- Deterministic validation: `tests/runtime/test_ui_profile_registry.py`

Schema version: `orchestra.ui-profile-registry.v1`

## Taxonomy

The initial registry deliberately keeps categories distinct:

- Foundation: `minimalist`
- Layout: `bento_grid`
- Full theme or system: `dark_cyberpunk`, `neo_brutalism`, `material_3`, `retro_web_90s`
- Optional effect: `glassmorphism`, `neumorphism`, `claymorphism`, `aurora`

`bento_grid` is a layout profile, not a theme. `material_3` is a complete system and is not a casual mix-in with another complete system.

## Composition rules

- Exactly one foundation and one layout are required.
- At most one full theme or system may be selected.
- At most one optional effect may be selected in v1.
- Unknown profiles, category mismatches, duplicate selections, and incompatibilities reject the composition.
- Optional effects must not weaken interaction-critical contrast or focus.
- Existing project design systems take precedence over generated profile defaults.
- Profile names do not authorize arbitrary CSS values.

## Accessibility invariants

Semantic structure and names, keyboard and focus behavior, interaction-critical contrast, target size and error states, reduced-motion behavior, and forced-colors behavior remain active for every profile composition. These are requirements for later implementation and rendered evidence, not claims that a registry entry has passed accessibility validation.

## Authority boundary

The registry grants no implementation, CSS, validation, dependency-adoption, external-tool, or Figma-mutation authority. Figma, Code Connect, Storybook, Playwright, axe, and frontend component libraries remain optional capabilities outside this phase.

## Ownership and exit

Cloak owns the profile semantics and accessibility invariants. Clockwork owns any later host-neutral composition boundary. Ponytail owns only authorized project-native implementation. Overseer owns rendered/accessibility evidence. Conductor and Arbiter retain routing and transition ownership.

UIX-3 exits only after the exact source tree passes focused and repository validation, fresh protected-main checks, signed materialization, canonical promotion, and independent tree/signature readback.
