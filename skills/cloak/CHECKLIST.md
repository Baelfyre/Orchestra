# Cloak Review Checklist

Use only the sections relevant to the selected review mode. Unchecked items are inspection prompts, not automatic defects.

## General UX
- [ ] Identify the primary user, task, entry point, and success state.
- [ ] Confirm the main action is discoverable and uses familiar language.
- [ ] Check feedback, cancellation, recovery, loading, empty, and error states.
- [ ] Remove steps and choices that do not support the task.

## Cognitive Load
- [ ] Prefer recognition over recall.
- [ ] Group related controls using proximity and common region.
- [ ] Reveal advanced choices only when needed.
- [ ] Keep instructions near the action they govern.

## Visual Hierarchy
- [ ] Make the primary task dominant without hiding alternatives.
- [ ] Use typography, spacing, contrast, and alignment consistently.
- [ ] Avoid competing calls to action.
- [ ] Ensure grouping reflects content relationships.

## Accessibility
- [ ] Check text and non-text contrast.
- [ ] Verify keyboard access, visible focus, logical order, and no keyboard trap.
- [ ] Provide names, roles, values, labels, instructions, and useful errors.
- [ ] Do not rely on color, position, sound, or motion alone.
- [ ] Support zoom, reflow, text resizing, and adequate targets.
- [ ] Expose dynamic updates to assistive technology.

## Information Architecture
- [ ] Organize content around user tasks and domain concepts.
- [ ] Use distinct, predictable, consistently scoped labels.
- [ ] Separate global, local, contextual, and utility navigation.
- [ ] Provide location, orientation, search, and recovery cues when needed.

## Responsive Layout
- [ ] Avoid clipping and horizontal scrolling at supported widths.
- [ ] Preserve source order, hierarchy, and task completion during reflow.
- [ ] Check text scaling, orientation, safe areas, and virtual-keyboard behavior.
- [ ] Use content-driven breakpoints when current architecture supports them.

## Dashboard Layout
- [ ] Match each metric and visualization to a decision.
- [ ] Show units, range, freshness, filters, and comparison baseline.
- [ ] Prioritize exceptions and actions over decorative metrics.
- [ ] Provide accessible summaries and data alternatives for charts.

## Forms
- [ ] Use persistent labels and logical field groups.
- [ ] Mark required and optional fields clearly.
- [ ] Validate without erasing input.
- [ ] Associate specific errors with affected fields.
- [ ] Prevent duplicate submission and confirm destructive actions.

## Design Systems and Component Consistency
- [ ] Reuse existing tokens and components before adding variants.
- [ ] Cover default, hover, focus, active, disabled, loading, error, and empty states.
- [ ] Keep naming, spacing, typography, color, and motion systematic.
- [ ] Avoid cosmetic variants without a product need.

## Frontend Architecture
- [ ] Align component boundaries with behavior and ownership.
- [ ] Maintain one clear source of truth for shared state.
- [ ] Avoid duplicated business logic and unnecessary state synchronization.
- [ ] Reuse framework features and project utilities.

## JavaFX Screens
- [ ] Use layout panes and constraints that survive resize and localization.
- [ ] Check labels, mnemonics, focus traversal, keyboard operation, and validation.
- [ ] Avoid blocking the JavaFX Application Thread.
- [ ] Verify modal ownership, window state, minimum sizes, and scene transitions.

## React / HTML / CSS Components
- [ ] Prefer semantic HTML and native controls.
- [ ] Verify source order, focus management, and accessible names after updates.
- [ ] Avoid duplicate state, unnecessary effects, and unstable keys.
- [ ] Reuse existing components and CSS tokens.

## Interaction Design and User Flow
- [ ] Make triggers, current state, next action, and success outcome clear.
- [ ] Preserve user control, cancellation, undo, and error recovery.
- [ ] Check interruptions, retries, and destructive actions.
- [ ] Use familiar platform conventions where appropriate.

## Performance
- [ ] Require measurements before naming a bottleneck.
- [ ] Check rendering, network, media, startup, and thread costs relevant to the artifact.
- [ ] Avoid optimization that adds complexity without demonstrated benefit.

## Secure UX and Foundational Checks
- [ ] Accessible labels are present on all inputs and icons.
- [ ] Highly visible focus states exist for interactive elements.
- [ ] Full keyboard navigation is supported.
- [ ] Loading, error, and empty states are designed and handled.
- [ ] Error messaging is secure and does not leak system details.
- [ ] Sensitive-data display is masked or privacy-aware.
- [ ] Role-aware UI hides unauthorized actions (but relies on backend for enforcement).
- [ ] Destructive actions require explicit confirmation and provide recovery affordances.
- [ ] Responsive layout checks pass across all expected breakpoints.

## Design Debt
- [ ] Identify duplicated patterns, inconsistent variants, workarounds, and stale styles.
- [ ] Separate intentional tradeoffs from accidental drift.
- [ ] Prioritize debt affecting tasks, accessibility, responsiveness, or change cost.

## Specialist Handoff
- [ ] Route diagram semantics and modeling to `weaver`.
- [ ] Route database design and SQL to `chronicler`.
- [ ] Route project documentation audits to `scribe`.
- [ ] Use `conductor` when the smallest specialist stack is unclear.
