# Frontend Review Guide

1. Identify the artifact sources reviewed, target user, primary task, supported viewport range, themes, and available rendered states.
2. Inspect the smallest relevant component, semantic structure, style/layout owner, current design tokens, route context, and design-system evidence before recommending changes.
3. Review native HTML semantics, accessible names, ARIA state relationships, keyboard behavior, and focus movement when the surface contains interactive web UI.
4. Review layout mechanics that can affect task completion: source order, flex/grid containment, intrinsic sizing, wrapping, overflow, clipping, fixed/sticky overlays, and narrow-width reflow.
5. Review form usability, validation timing and messaging, submission ownership, focus after errors, and visible loading, empty, error, success, retry, permission, disabled, and read-only states that affect the task.
6. Review client-side navigation at the user-visible contract level: current-location indication, deep links, Back/Forward behavior, route focus, not-found/permission states, and responsive navigation. Route internal state or architecture ownership to Clockwork.
7. Review component-state and token consistency across supported themes. Reuse current tokens/components before proposing variants or dependencies.
8. Report confirmed task, accessibility, containment, consistency, recovery, and design-system issues by severity. Separate confirmed evidence from assumptions and `NEEDS EVIDENCE`.
9. Produce a frontend handoff blueprint that names semantic structure, affected components, token/state constraints, responsive rules, accessibility/focus requirements, route expectations, and downstream ownership without writing production code.
10. Require current rendered evidence for visual correctness and route readiness testing to Overseer when the user asks for a readiness conclusion.

Load deeper references only when the task needs them:

- `SEMANTIC_HTML_ARIA_KEYBOARD_GUIDE.md`
- `RESPONSIVE_CSS_LAYOUT_GUIDE.md`
- `FORM_FOCUS_VALIDATION_GUIDE.md`
- `DESIGN_TOKENS_COMPONENT_STATES_GUIDE.md`
- `FRONTEND_ROUTING_COMPONENT_BOUNDARIES_GUIDE.md`

Route implementation to `ponytail`, architecture and shared-state ownership to `clockwork`, security policy to `cipher`, database semantics to `chronicler`, normal QA and validation gates to `overseer`, project documentation to `scribe`, system diagrams to `weaver`, and destructive guardrail pressure testing to gated `dagger`.