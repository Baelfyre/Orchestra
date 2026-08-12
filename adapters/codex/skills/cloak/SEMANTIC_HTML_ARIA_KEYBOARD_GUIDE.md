# Semantic HTML, ARIA, and Keyboard Interaction Guide

Use this guide when a web UI review requires more depth than the base accessibility checklist. Cloak defines user-visible requirements and review criteria. Ponytail owns implementation code.

## Native semantics first

- Prefer native HTML elements whose built-in role and keyboard behavior match the interaction.
- Treat ARIA as a semantic supplement, not a replacement for native behavior.
- A custom role creates an interaction contract. If a component uses an ARIA widget role, its keyboard behavior, focus behavior, states, and accessible name must match that role.
- Do not add redundant roles to native elements when the native semantics already express the requirement.
- Do not place `aria-hidden="true"` on an element that contains focusable or interactive content.

## Landmarks and document structure

Review the page structure before individual widgets.

- Require one clear main content region for the page task.
- Use landmarks such as header, nav, main, aside, and footer when they represent the actual region purpose.
- Preserve a logical heading hierarchy that communicates document structure rather than visual size alone.
- Use section or article only when the content has a meaningful structural identity.
- Keep DOM/source order aligned with reading order and keyboard order. Visual reordering must not create a different interaction sequence.

## Accessible names and descriptions

Every interactive control needs a stable accessible name.

- Prefer visible text or an associated `label` for form controls.
- Use `aria-labelledby` when another visible element already provides the correct name.
- Use `aria-describedby` for supporting instructions, constraints, or error details that are useful in addition to the name.
- Keep the visible label and accessible name aligned so voice-input and screen-reader users receive the same control identity.
- Icon-only controls require an accessible name that communicates the action, not the icon shape.
- Placeholder text is not a substitute for a persistent label.

## ARIA state literacy

Cloak should recognize common state relationships and verify that user-visible state and accessibility state do not diverge.

- `aria-expanded` should reflect whether a controlled disclosure, menu, or region is currently expanded.
- `aria-controls` may express a relationship when it materially helps identify the controlled region, but it does not create behavior by itself.
- `aria-current` identifies the current item in a set such as navigation or a step sequence.
- `aria-selected` represents selection in widgets whose role defines selectable items.
- `aria-pressed` represents the state of a toggle button, not a generic selected style.
- `aria-invalid` identifies a form value that is currently invalid and should be paired with useful correction guidance.
- Live-region techniques such as `aria-live` should be reserved for dynamic information users need to perceive without moving focus. Avoid repeated or noisy announcements.

## Keyboard interaction review

- All interactive functionality must be reachable and operable without a pointer.
- Preserve predictable Tab and Shift+Tab movement between components.
- Avoid positive `tabindex` values used to manually reorder focus. Prefer a logical DOM order.
- Native buttons activate with their platform/browser keyboard behavior. A custom button-like control must provide equivalent behavior if a native button cannot be used.
- Composite widgets such as tabs, menus, listboxes, and grids require their pattern-specific keyboard model. Do not invent a novel arrow-key model when a recognized platform pattern applies.
- Keyboard shortcuts must not conflict with text entry or create inaccessible single-character traps.

## Focus management

Focus should move only when doing so helps users understand a real context change.

- When a modal dialog opens, move focus into the dialog and contain keyboard focus while it is modal.
- Initial dialog focus should support comprehension and safe action. Do not automatically focus a destructive primary action merely because it is visually prominent.
- When a dialog closes, return focus to the invoking control when that control still exists and remains the logical continuation point.
- After client-side route or major view changes, provide a predictable focus destination such as the page heading or main content start when users otherwise lose context.
- After failed form submission, focus an error summary or the first invalid field according to the product pattern, while preserving entered values.
- Do not move focus for passive status messages that can be communicated through a live region.
- Ensure sticky headers, overlays, and fixed controls do not visually obscure the focused element.

## Dialog and disclosure review

For dialogs, disclosures, tabs, menus, and other rich patterns:

1. Confirm a native element or simpler pattern cannot meet the need first.
2. Identify the expected role, state, accessible name, and keyboard model.
3. Verify visible state and accessibility state stay synchronized.
4. Verify initial focus, contained focus where required, Escape/cancel behavior when safe, and focus return.
5. Verify the component remains understandable under zoom, reflow, high contrast, and reduced-motion conditions.

## Evidence boundary

A source-level review can identify probable semantic and focus defects, but it is not a rendered accessibility pass. Cloak must state what was inspected and route browser, assistive-technology, or formal conformance testing to Overseer when readiness evidence is required.

## Primary references

- WCAG 2.2: https://www.w3.org/TR/WCAG22/
- WAI-ARIA Authoring Practices Guide: https://www.w3.org/WAI/ARIA/apg/
- APG keyboard interface practice: https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/
- HTML Living Standard: https://html.spec.whatwg.org/