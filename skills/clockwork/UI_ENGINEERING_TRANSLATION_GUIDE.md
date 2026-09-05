# Clockwork UI Engineering Translation Guide

Status: UIEF-5 ADDITIVE GUIDANCE

Purpose: translate an accepted Cloak `UIFidelityHandoff` into maintainable engineering boundaries without redesigning the visible experience.

Core rule:

```text
DESIGN_COMPLEXITY != ARCHITECTURAL_COMPLEXITY
```

Clockwork may simplify engineering structure only when accepted visible-layer fidelity is unchanged.

## Ownership

Clockwork owns:
- component boundaries;
- state ownership and lifecycle boundaries;
- responsive engineering structure;
- composition/container ownership;
- overlay and stacking-context ownership;
- data-flow boundaries;
- reusable component strategy;
- integration and dependency boundaries.

Clockwork does not own:
- visible design intent, hierarchy, spacing, typography, interaction design, or accessibility requirements -> Cloak;
- implementation -> Ponytail;
- dependency adoption authority -> applicable human/governance gate;
- security policy -> Cipher;
- persistence mechanics -> Chronicler;
- QA strategy or rendered evidence -> Overseer;
- cross-specialist integration sequencing -> Conductor / UIEF-6.

## Required translation order

1. Validate the accepted `UIFidelityHandoff` identity and ownership.
2. Inventory project-native components, state owners, layout containers, and integration boundaries.
3. Map every required macro-composition item to a composition/container owner.
4. Map visible component roles to cohesive component boundaries without inventing visual requirements.
5. Assign mutable UI state to explicit owners and lifecycle scopes.
6. Translate responsive transformations into engineering rules while preserving the accepted transformation.
7. Define overlay, portal, z-index, focus-trap, scroll-lock, and stacking-context ownership when applicable.
8. Define data-flow inputs/outputs without moving visible-layer decisions into data or service layers.
9. Prefer reusable project-native components when they preserve the accepted design contract.
10. Define dependency direction and integration boundaries with the smallest sufficient architecture.
11. Record unresolved engineering questions and route non-Clockwork decisions to their owner.
12. Return an implementation-ready engineering boundary to Ponytail without writing application code.

## Fidelity preservation rules

- Do not remove, merge, flatten, or reorder accepted visible regions merely to simplify component architecture.
- Do not replace deliberate asymmetry with a generic equal-card or equal-column architecture.
- Do not convert an accepted responsive transformation into generic stacking unless the handoff permits it.
- Do not invent modals, drawers, navigation, interactions, motion, breakpoints, or design tokens.
- Do not treat a large component count as evidence that the visible design should be simplified.
- Prefer fewer engineering abstractions when the same visible contract can be preserved.
- Preserve project-native component/token/asset precedence.

## Fail-closed boundaries

Return to Cloak when a visible-layer ambiguity must be resolved before architecture can be defined.

Route to the owning specialist when the translation requires:
- security or privacy control decisions -> Cipher;
- schema, migration, transaction, or persistence mechanics -> Chronicler;
- QA scope or rendered proof -> Overseer;
- ambiguous specialist sequencing -> Conductor.

UIEF-5 must not initiate UIEF-6, authorize implementation, adopt dependencies, release, deploy, or rewrite the accepted Cloak handoff.

## Output

Use the `UI_ENGINEERING_TRANSLATION` format in `OUTPUT_FORMATS.md`.

The machine-readable reference contract is:
`machine/ui/ui-engineering-translation.v1.json`

Schema:
`machine/schemas/ui-engineering-translation.v1.schema.json`
