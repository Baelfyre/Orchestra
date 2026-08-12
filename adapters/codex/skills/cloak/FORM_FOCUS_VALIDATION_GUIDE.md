# Form, Focus, and Validation Guide

Use this guide for forms, multi-step flows, authentication inputs, destructive confirmations, and other interactions where errors or state transitions can block task completion.

## Field identity and grouping

- Provide a persistent visible label for each field unless the control pattern has an equally clear native accessible name.
- Group related controls with meaningful structure and instructions.
- Distinguish required and optional fields consistently before submission.
- Use input purpose, autocomplete, and platform-native control behavior when they reduce user effort and do not conflict with product requirements.
- Do not use placeholder text as the only label or instruction.

## Validation timing

- Prevent avoidable errors before submission when the rule can be explained without interrupting normal entry.
- Avoid aggressive validation that marks incomplete fields invalid while the user is still entering a reasonable value.
- Revalidate authoritative constraints after submission or server response. Client-side validation improves UX but is not an enforcement boundary.
- Async validation needs a visible pending state and must avoid racing older responses into the current field state.

## Error communication

A useful error tells the user what happened, where it happened, and how to recover.

- Associate field-specific messages with their field.
- Use `aria-invalid` and an accessible description relationship when appropriate to the implemented pattern.
- Keep error text specific enough to guide correction without exposing sensitive backend or account-existence information.
- Preserve the user's valid input after a failed submission.
- For forms with multiple errors, provide an error summary when it materially improves navigation and recovery.
- Do not rely on color, icon shape, or placement alone to communicate invalid state.

## Focus after submission

- On failed submission, move focus only when it improves recovery. Common destinations are the error summary or first invalid field according to the established product pattern.
- Ensure the focused error target is not hidden behind sticky or fixed UI.
- On successful submission, move or restore focus according to the resulting context. Do not leave focus on a removed control.
- If a modal form closes, return focus to the logical invoking control when it still exists.

## Submission ownership

- Provide one authoritative submit path for the action.
- Prevent accidental duplicate submission while an in-flight mutation owns completion.
- A disabled control must still leave the reason and recovery path understandable. Do not strand users behind an unexplained disabled primary action.
- Distinguish disabled, read-only, loading, and permission-restricted states. They have different user meanings and should not be styled as interchangeable.

## Multi-step flows

- Show current position and what remains when the sequence is long enough to need orientation.
- Preserve completed valid data when users move backward or recover from errors.
- Avoid forcing redundant entry of information already supplied unless a current safety or verification reason requires it.
- Warn before abandoning unsaved work when loss would be meaningful, and provide a clear safe alternative.

## Sensitive and destructive actions

- Explain consequence before confirmation.
- Avoid preselecting the destructive choice or using visual pressure to make cancellation harder.
- Use additional confirmation only when the risk justifies the friction.
- Authentication and recovery forms should not disclose whether an account exists unless product security policy explicitly allows that distinction.
- Route security-policy decisions to Cipher and backend validation ownership to the appropriate engineering specialist.

## Mobile and assistive-technology review

- Verify the on-screen keyboard does not hide the active field, validation message, or primary action.
- Verify zoom, reflow, text resizing, and orientation changes preserve labels and error relationships.
- Verify dynamic submission status is perceivable without repeatedly stealing focus.
- Verify touch targets and spacing support users with limited precision.

## Evidence boundary

Cloak defines form usability, focus, and user-visible validation requirements. Ponytail implements them, Cipher owns security policy, Clockwork owns state and architecture boundaries, and Overseer owns readiness testing.

## Primary references

- HTML forms: https://html.spec.whatwg.org/multipage/forms.html
- WCAG 2.2: https://www.w3.org/TR/WCAG22/
- WAI-ARIA Authoring Practices Guide: https://www.w3.org/WAI/ARIA/apg/