# UI/UX Foundations Guide

## UI vs Backend Security Boundaries
- **UI is not a security boundary**: Hidden buttons, disabled fields, hidden routes, and client-side validation are usability tools, not enforcement.
- **Frontend validation**: Improves user experience but does not replace backend validation.
- **Role-aware UI**: Improves usability by hiding inaccessible options but does not replace backend authorization.
- **Data Exposure**: Sensitive data should not be overexposed in UI, logs, screenshots, exported views, notifications, or browser-visible artifacts.
- **Error Messages**: Must be helpful without leaking system details, account existence, secrets, stack traces, or internal state.
- **Destructive Actions**: Should use clear confirmation, review, and recovery affordances.
- **Secure UX**: Must reduce accidental disclosure and user mistakes.

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
- **Session State Indicators**: Make it clear if the user is logged in, and as which role.

## Forms & Validation
- **Form Usability**: Keep forms concise. Group related inputs.
- **Validation Messaging**: Provide clear, inline, and actionable validation messaging before and after submission.
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
- **Secure Error Message UX**: Avoid giving attackers hints (e.g., "Invalid password" vs "User not found").
- **Secure Onboarding/Recovery**: Provide safe, clear flows for login, onboarding, and password recovery.
- **Audit Clarity**: Ensure actions that generate an audit log are clear to the user if relevant.
