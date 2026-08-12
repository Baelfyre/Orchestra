# Cloak Review Checklist

Use only the sections relevant to the selected review mode. Unchecked items are inspection prompts, not automatic defects.

## General UX
- [ ] Identify the primary user, task, entry point, and success state.
- [ ] Identify which artifact sources were actually reviewed before drawing conclusions.
- [ ] Confirm the main action is discoverable and uses familiar language.
- [ ] Check feedback, cancellation, recovery, loading, empty, and error states.
- [ ] Check success, retry, and permission-denied states when the feature has them.
- [ ] Remove steps and choices that do not support the task.

## Artifact Evidence
- [ ] Distinguish inspected evidence from assumptions and missing artifacts.
- [ ] For Figma evidence, inspect tokens, components, variants, annotations, and linked guidance when available.
- [ ] For Canva evidence, inspect brand guidance, templates, comments, or approvals only when they are relevant to the review.
- [ ] For GitHub evidence, inspect screenshots, docs, stories, examples, issues, or PR context instead of inferring behavior from filenames alone.
- [ ] Mark missing required artifacts as `NEEDS EVIDENCE`.

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
- [ ] Confirm visual inspection was performed for the changed screen or component, not inferred from functional test success alone.
- [ ] Confirm supported themes preserve the same visual hierarchy and state meaning.

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
- [ ] Confirm theme changes do not obscure chart marks, labels, units, legends, tooltips, or accessible summaries.

## Forms
- [ ] Use persistent labels and logical field groups.
- [ ] Mark required and optional fields clearly.
- [ ] Validate without erasing input.
- [ ] Associate specific errors with affected fields.
- [ ] Review user-facing validation copy, timing, placement, and recovery path.
- [ ] Prevent duplicate submission and confirm destructive actions.
- [ ] Confirm each user action has one authoritative interaction path after the change.
- [ ] Flag duplicate or conflicting controls unless a staged migration is explicitly documented.

## Design Systems and Component Consistency
- [ ] Reuse existing tokens and components before adding variants.
- [ ] Cover default, hover, focus, active, disabled, loading, error, and empty states.
- [ ] Keep naming, spacing, typography, color, and motion systematic.
- [ ] Avoid cosmetic variants without a product need.
- [ ] Confirm new UI elements use existing theme tokens, component patterns, and state styles before adding variants.

## Frontend Architecture
- [ ] Align component boundaries with behavior and ownership.
- [ ] Maintain one clear source of truth for shared state.
- [ ] Avoid duplicated business logic and unnecessary state synchronization.
- [ ] Reuse framework features and project utilities.
- [ ] Keep the review at user-visible behavior and handoff level unless Conductor routes architecture ownership elsewhere.

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
- [ ] Success, retry, and permission states are designed and handled when the feature has them.
- [ ] Error messaging is secure and does not leak system details.
- [ ] Sensitive-data display is masked or privacy-aware.
- [ ] Role-aware UI hides unauthorized actions (but relies on backend for enforcement).
- [ ] Destructive actions require explicit confirmation and provide recovery affordances.
- [ ] Responsive layout checks pass across all expected breakpoints.

## Design Debt
- [ ] Identify duplicated patterns, inconsistent variants, workarounds, and stale styles.
- [ ] Separate intentional tradeoffs from accidental drift.
- [ ] Prioritize debt affecting tasks, accessibility, responsiveness, or change cost.

## Handoff Blueprint
- [ ] Define the semantic structure and affected components clearly enough for implementation without writing code.
- [ ] State design-system constraints, form and validation expectations, and visible state coverage.
- [ ] Name the downstream owner for implementation, security, architecture, persistence, validation, diagrams, or long-form docs when those concerns appear.

## SK4 Deep-Dive Checks

### Semantic HTML, ARIA, Keyboard, and Focus
- [ ] Native semantic elements are used when they already provide the required role and keyboard behavior.
- [ ] Accessible names align with visible labels; descriptions and errors are connected only when they add supporting information.
- [ ] ARIA state such as expanded, current, selected, pressed, or invalid matches the visible state.
- [ ] Composite widgets follow a recognized keyboard model and do not use positive tabindex to manufacture order.
- [ ] Dialogs establish initial focus, contain focus while modal, support safe cancellation, and return focus appropriately.
- [ ] Route/view changes, form failures, and dynamic updates move focus only when the context change requires it.
- [ ] Sticky/fixed/overlay UI does not obscure the focused element.

### Responsive CSS Containment
- [ ] Flex/grid choice matches the dimensional layout need and preserves semantic source order.
- [ ] Intrinsic sizing, long content, media, and nested containers cannot force accidental page-level horizontal overflow.
- [ ] Overflow/clipping cannot hide actions, focus rings, errors, menus, or required content.
- [ ] Breakpoints preserve task order under intermediate widths, zoom, text enlargement, orientation, and localization pressure.
- [ ] Fixed/sticky surfaces account for safe areas, on-screen keyboards, and focused content.

### Form, Validation, and Submission State
- [ ] Validation timing does not punish reasonable incomplete input while authoritative constraints are still checked on submission/server response.
- [ ] Error summaries and field errors provide an explicit recovery path and preserve valid input.
- [ ] Failed submission has a deliberate focus target; successful state does not leave focus on removed content.
- [ ] One authoritative submission path owns an in-flight mutation and duplicate activation is prevented.
- [ ] Disabled, read-only, loading, and permission-restricted states remain visually and semantically distinct.

### Tokens, Themes, and Component States
- [ ] Primitive, semantic, and component token responsibilities are not mixed without evidence.
- [ ] Default, hover, focus-visible, active, selected/current, disabled, loading, error, and success states are covered when the component can enter them.
- [ ] Supported themes preserve semantic meaning, contrast, hierarchy, focus visibility, and chart/state legibility.
- [ ] New variants represent a reusable product need rather than page-specific cosmetic drift.

### Frontend Routes and Component Boundaries
- [ ] Direct links, menu navigation, Back/Forward, permission, not-found, loading, and error states preserve route orientation.
- [ ] Client-side navigation provides a predictable focus/context destination when the prior focused element disappears.
- [ ] Permission-aware navigation is treated as UX only, not authorization enforcement.
- [ ] Cloak limits component-boundary advice to the user-visible contract and routes state/data architecture to Clockwork.
## Specialist Handoff
- [ ] Route diagram semantics and modeling to `weaver`.
- [ ] Route database design and SQL to `chronicler`.
- [ ] Route project documentation audits to `scribe`.
- [ ] Use `conductor` when the smallest specialist stack is unclear.
