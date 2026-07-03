# Cloak Review

## Scope Reviewed
- Artifact Type: Employee onboarding form with validation result
- Primary User Goal: Add a new employee record
- Target User: HR administrator
- Review Mode: Form Review
- Evidence Reviewed: Default and validation states plus observed submission behavior

## Review Confidence
Confidence Level: High

Reason:
- Default and validation states available
- Submission behavior observed

## Scoring Matrix
- Task Completion: 48/100
- Accessibility: 55/100
- Cognitive Load: 72/100
- Discoverability: 76/100
- Visual Hierarchy: 80/100
- Consistency: 78/100
- Maintainability: 65/100
- Responsiveness: 68/100
- Performance: 78/100
- Overall Score: 66/100

## Executive Summary
The form groups employee data clearly, but recoverable validation clears entered values and errors are not associated with fields.

## Confirmed Findings
- Submitting an invalid employee ID reloads the form with all fields empty.
- A generic `Invalid input` message appears only at the top.

## Assumptions
None.

## Critical Issues
### Recoverable errors clear the form
- Severity: Critical
- Principle Applied: Nielsen - error prevention and recovery; user control and freedom
- Finding: Validation failure removes all entered values.
- Impact: Users lose work and may create duplicate or inaccurate records when re-entering data.
- Recommendation: Preserve values and focus the first invalid field after showing an error summary.
- Implementation Notes: Return structured errors without resetting form state.

## Major Issues
### Error messages are detached from fields
- Severity: Major
- Principle Applied: WCAG - understandable; Nielsen - help users recover from errors
- Finding: The generic message does not identify the invalid field or correction.
- Impact: Users cannot recover efficiently, especially with assistive technology.
- Recommendation: Add specific inline errors and programmatic field associations.
- Implementation Notes: Use `aria-describedby` and `aria-invalid` on the web, or equivalent relationships in the target toolkit.

## Minor Issues
None confirmed.

## Strengths
- Field groups match the HR workflow.
- Required fields are identified in labels.

## Quick Wins
- Replace the generic error with field-specific text.
- Move focus to the first invalid field.

## Long-Term Improvements
- Add draft preservation only if interrupted completion is a demonstrated need.

## Accessibility Notes
Verify keyboard submission, visible focus, required-state exposure, and announcement of the error summary and inline errors.

## Information Architecture Notes
Personal and employment sections match the task; keep errors inside the section that owns each field.

## Design Debt
The submission path treats validation failure like a fresh form load, coupling error handling to destructive state reset.

## Frontend Implementation Notes
Preserve form state on validation failure and associate structured errors with existing fields.

## Performance Notes
No performance problem was observed.

## Missing Evidence
- Screen-reader output
- Backend validation rules
- Duplicate-submission behavior
- Network failure behavior

## Final Recommendation
Needs major revision to error handling before use.
