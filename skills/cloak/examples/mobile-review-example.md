# Cloak Review

## Scope Reviewed
- Artifact Type: Mobile banking transfer mockup
- Primary User Goal: Send money to a saved recipient
- Target User: Mobile banking customer
- Review Mode: Mobile UX Review
- Evidence Reviewed: Static mobile mockup

## Review Confidence
Confidence Level: Medium

Reason:
- Full primary screen available
- Device behavior and code unavailable

## Scoring Matrix
- Task Completion: 72/100
- Accessibility: 66/100
- Cognitive Load: 78/100
- Discoverability: 74/100
- Visual Hierarchy: 80/100
- Consistency: 82/100
- Maintainability: 72/100
- Responsiveness: 70/100
- Performance: 75/100
- Overall Score: 74/100

## Executive Summary
The transfer fields follow the task sequence, but the bottom action may be hidden by the keyboard and the amount lacks visible currency context.

## Confirmed Findings
- The fixed `Continue` button sits below the active amount field at the viewport bottom.
- The amount field displays `0.00` without a currency label.

## Assumptions
- The layout does not reposition when the virtual keyboard opens; confirm on supported devices.

## Critical Issues
None confirmed.

## Major Issues
### Submit action may be hidden by the keyboard
- Severity: Major
- Principle Applied: Task completion; mobile usability
- Finding: The only progression action occupies the bottom edge below the active field.
- Impact: The virtual keyboard may hide the action on smaller screens.
- Recommendation: Keep the action above the keyboard or use a keyboard-aware scroll container.
- Implementation Notes: Test the smallest supported viewport with text scaling enabled.

## Minor Issues
### Currency is not identified
- Severity: Minor
- Principle Applied: Nielsen - match between system and the real world
- Finding: The amount field shows only `0.00`.
- Impact: Multi-currency users may enter an amount under the wrong assumption.
- Recommendation: Show the account currency as a persistent prefix or adjacent label.
- Implementation Notes: Use account data already supplied to the screen; do not infer currency from locale.

## Strengths
- Recipient, amount, note, and review follow a logical order.
- The recipient remains visible while the amount is entered.

## Quick Wins
- Add the currency label.
- Verify safe-area padding and keyboard avoidance.

## Long-Term Improvements
- Add a confirmation step showing recipient, amount, fee, and total if one does not already exist.

## Accessibility Notes
Verify target spacing, screen-reader labels, focus order, dynamic-type reflow, and error announcements in the running app.

## Information Architecture Notes
The field order matches the transfer task. Keep fee and exchange-rate information adjacent to the amount when applicable.

## Design Debt
No confirmed structural debt; keyboard handling is an implementation risk requiring verification.

## Frontend Implementation Notes
Use the platform's existing keyboard-avoidance and safe-area behavior before introducing custom positioning logic.

## Performance Notes
No performance evidence was supplied.

## Missing Evidence
- Keyboard-open state
- Error and loading states
- Review or confirmation screen
- Screen-reader behavior
- Supported device sizes

## Final Recommendation
Needs revision and device testing before release.
