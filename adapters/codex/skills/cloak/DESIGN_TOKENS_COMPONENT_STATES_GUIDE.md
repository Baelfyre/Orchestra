# Design Tokens and Component States Guide

Use this guide when reviewing a design system, Figma library, theme implementation, or reusable component contract.

## Token layers

Distinguish the purpose of tokens before recommending new ones.

- Primitive tokens hold raw design values such as a color step, spacing step, radius, or typography value.
- Semantic tokens express intent such as surface, text, border, danger, success, focus, or interactive emphasis.
- Component tokens are appropriate only when a reusable component needs a stable local contract that semantic tokens cannot express clearly.
- Prefer semantic reuse over duplicating near-identical raw values across components.

Cloak does not prescribe a specific token tool or file format unless the project already uses one.

## Theme parity

- A light-theme token and dark-theme token should preserve the same semantic purpose even when their raw values differ.
- Contrast, hierarchy, disabled-state clarity, focus visibility, chart legibility, and error/success meaning must survive each supported theme.
- Do not encode meaning through hue alone.
- Avoid theme-specific exceptions that silently bypass the design-system token layer unless the exception is documented and evidence-backed.

## Required state model

Review the states that the component can actually enter. Typical states include:

- default
- hover when a hover-capable pointer exists
- focus-visible
- active or pressed
- selected or current
- disabled
- read-only where applicable
- loading or pending
- empty where applicable
- error or invalid
- success or complete
- permission-restricted where applicable

Not every component needs every state. Missing states are findings only when the component can actually enter that condition.

## State consistency

- Visual state, accessibility state, and product state must describe the same condition.
- Focus-visible treatment must not disappear merely because hover styling is active.
- Disabled appearance must not be reused for read-only or permission-denied content when the user meaning differs.
- Loading state should preserve enough layout and context to avoid confusing movement or duplicate action.
- Error and success treatments need text or another perceivable cue in addition to color.

## Variant discipline

- Add a variant for a product or interaction need, not merely a one-off cosmetic preference.
- Reuse the existing component before creating a near-duplicate component with different naming.
- Keep variant names tied to purpose or state rather than page-specific styling.
- If two variants behave differently, their interaction and accessibility contract must make that difference explicit.

## Typography, spacing, and density

- Typography tokens should preserve readable hierarchy and line spacing across responsive conditions.
- Spacing should communicate grouping and separation consistently rather than act as arbitrary pixel tuning.
- Dense modes must retain target size, focus visibility, readable labels, and error communication.
- Localization and longer content must not break the component contract.

## Motion tokens and transitions

- Reuse established duration/easing conventions when motion serves a state transition.
- Respect reduced-motion preferences.
- Motion should clarify change, not become the only indication that state changed.

## Evidence review

For Figma or another design-system artifact, inspect available variables/tokens, component variants, properties, descriptions, annotations, and state coverage. Mark unavailable evidence as `NEEDS EVIDENCE` rather than inventing a token structure.

## Handoff

Cloak defines the design-system and state requirements. Ponytail owns implementation. Clockwork owns architecture or shared-state design when the component contract crosses system boundaries. Overseer owns state-matrix and visual-regression readiness evidence.