# UI/UX Foundations Guide

## UI vs Backend Security Boundaries
- **UI is not a security boundary**: Hidden buttons, disabled fields, hidden routes, and client-side validation are usability tools, not enforcement.
- **Frontend validation**: Improves user experience but does not replace backend validation.
- **Role-aware UI**: Improves usability by hiding inaccessible options but does not replace backend authorization.
- **Data Exposure**: Sensitive data should not be overexposed in UI, logs, screenshots, exported views, notifications, or browser-visible artifacts.
- **Error Messages**: Must be helpful without leaking system details, account existence, secrets, stack traces, or internal state.
- **Destructive Actions**: Should use clear confirmation, review, and recovery affordances.
- **Secure UX**: Must reduce accidental disclosure and user mistakes.

## Design-System Evidence Review
- **Evidence First**: Review the supplied artifact evidence before recommending changes.
- **Figma Evidence**: Tokens, components, variants, annotations, and linked docs are valid evidence when provided.
- **Canva Evidence**: Brand guidance, templates, comments, and approvals are valid evidence when provided.
- **GitHub Evidence**: Docs, stories, screenshots, issue context, PR context, and design-system references are valid evidence when provided.
- **Missing Inputs**: If a referenced artifact was not supplied, mark it as `NEEDS EVIDENCE` instead of inferring behavior.
- **Review vs Ownership**: Cloak reviews the user-visible evidence and constraints; it does not take ownership of implementation, CI/CD, telemetry, or release rollout.

## Information Architecture & Layout
- **Information Architecture**: Organize content logically so users can find what they need. Use clear navigation structures.
- **Layout Structure**: Use grids, alignment, and whitespace to create an organized, readable interface.
- **Responsive Behavior**: Ensure interfaces scale across desktop, tablet, and mobile breakpoints without breaking workflows.

## Visual Hierarchy & Typography
- **Visual Hierarchy**: Guide the user's eye to the most important elements first using size, color, and contrast.
- **Typography and Spacing**: Use legible fonts, consistent line heights, and rhythmic spacing.

## Interaction Design & Feedback
- **Interaction Design**: Controls should look clickable and behave predictably.
- **User Feedback States**: Always provide visual feedback for interactions (e.g., hover, active, focus).
- **State Management**: Account for empty, loading, error, and success states so the user is never left guessing.
- **Extended State Review**: Cover retry and permission-denied states when they exist in the flow.
- **Session State Indicators**: Make it clear if the user is logged in, and as which role.

## Forms & Validation
- **Form Usability**: Keep forms concise. Group related inputs.
- **Validation Messaging**: Provide clear, inline, and actionable validation messaging before and after submission.
- **Validation Recovery**: Validation failures should preserve user input and make the recovery path obvious.
- **Message Quality**: Errors should identify the problem, the affected field or action, and the next safe step.
- **Safe Defaults**: Use default values that minimize risk and user effort.

## Accessibility Basics
- **Keyboard Navigation**: Ensure all interactive elements are reachable and operable via keyboard.
- **Focus States**: Every interactive element must have a highly visible focus state.
- **Color Contrast**: Maintain minimum contrast ratios (WCAG) for text and interactive components.
- **Readable Labels**: Inputs and icons must have descriptive, readable labels (or aria-labels).
- **Microcopy & Progressive Disclosure**: Use concise microcopy and reveal complex information progressively.

## Privacy & Role Awareness
- **Privacy-Aware Displays**: Mask or hide high-risk identifiers, authentication values, and confidential fields by default.
- **Sensitive-Data Masking**: Provide toggle visibility for sensitive inputs.
- **Role-Aware UI Visibility**: Only show controls the user has permission to use.
- **Permission-Aware Navigation**: Do not display navigation links to unauthorized areas.
- **Permission-State Messaging**: When access is limited, make the user-visible reason and recovery path clear without exposing sensitive policy details.
- **Secure Error Message UX**: Avoid giving attackers hints (e.g., "Invalid password" vs "User not found").
- **Secure Onboarding/Recovery**: Provide safe, clear flows for login, onboarding, and password recovery.
- **Audit Clarity**: Ensure actions that generate an audit log are clear to the user if relevant.

## Deep Reference Loading

Use the base guide for broad UI review, then load only the specialized reference needed by the evidence:

- `SEMANTIC_HTML_ARIA_KEYBOARD_GUIDE.md` for semantic structure, accessible names/descriptions, ARIA states, keyboard patterns, dialogs, or focus movement.
- `RESPONSIVE_CSS_LAYOUT_GUIDE.md` for flex/grid containment, intrinsic sizing, overflow/clipping, responsive reflow, fixed/sticky UI, or data-heavy surfaces.
- `FORM_FOCUS_VALIDATION_GUIDE.md` for field identity, validation timing, error recovery, focus after submission, duplicate submission, multi-step forms, or destructive confirmations.
- `DESIGN_TOKENS_COMPONENT_STATES_GUIDE.md` for tokens, themes, reusable component variants, and state matrices.
- `FRONTEND_ROUTING_COMPONENT_BOUNDARIES_GUIDE.md` for route orientation, deep links, focus transitions, history/recovery, responsive navigation, or component-boundary review.

Do not load all five by default. Progressive disclosure remains the context-efficiency rule.
## Handoff Blueprint Requirements
- **Blueprint over Code**: Cloak hands off semantic structure, component intent, visible state expectations, and review findings, not production code.
- **Design-System Constraints**: Name the token, component, and variant constraints that the implementation should preserve.
- **State Coverage**: Call out loading, empty, error, success, retry, and permission states when relevant.
- **Routing Boundaries**: Route implementation to Ponytail, architecture to Clockwork, security policy to Cipher, persistence to Chronicler, validation gates to Overseer, long-form docs to Scribe, and diagrams to Weaver.
