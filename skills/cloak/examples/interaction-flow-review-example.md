# Cloak Interaction-Flow Review

## Scope Reviewed
- Artifact: Account-deletion modal interaction and destructive-action copy
- User goal: Understand consequences, cancel safely, or deliberately confirm deletion
- Evidence: Dialog markup, focus order, button states, confirmation copy, and supplied keyboard recording

## Confirmed Findings

### Critical - Initial focus favors the destructive action
When the modal opens, focus is placed directly on Delete account. The destructive action is also the strongest visual button. This makes an irreversible action the default keyboard continuation instead of prioritizing comprehension and safe cancellation.

### High - Dialog description is not connected to the interaction
The consequence text is visually present but is not included in the dialog's accessible description relationship. A screen-reader user can reach the controls without receiving the same consequence context.

### Medium - Focus return is undefined
The supplied flow closes the modal after Cancel, but the evidence does not establish where focus returns. Losing focus context after cancellation would make the interaction harder to recover from.

## Recommendations

1. Give the dialog a stable accessible name and connect the consequence text as supporting description.
2. Place initial focus on a comprehension target or safe action according to the established product pattern, not automatically on the destructive action.
3. Keep Tab and Shift+Tab inside the modal while it is active and provide a safe cancel path, including Escape when product requirements permit it.
4. Return focus to the invoking Delete account control after cancellation when it still exists.
5. Keep the irreversible consequence explicit and avoid styling or wording that pressures the user toward confirmation.
6. After confirmed deletion, move focus to the resulting stable context rather than attempting to restore focus to removed account controls.

## Keyboard and State Matrix

| Event | Expected user-visible behavior |
|---|---|
| Open dialog | Focus enters the modal and consequence context is available. |
| Tab / Shift+Tab | Focus remains within the active modal. |
| Cancel | Dialog closes and focus returns to the logical invoker. |
| Confirm while pending | One authoritative submission path owns completion; duplicate activation is blocked. |
| Failure | Dialog remains recoverable with a clear error and safe retry/cancel path. |
| Success | User is taken to a stable post-deletion context. |

## Handoff

- Cloak: dialog semantics, focus, hierarchy, destructive UX requirements
- Cipher: security/re-authentication policy if deletion requires identity confirmation
- Ponytail: implementation
- Overseer: keyboard, screen-reader, and current rendered evidence

## Missing Evidence
- Assistive-technology announcement of the current dialog
- Re-authentication policy
- Post-confirmation destination
- Failure/retry behavior