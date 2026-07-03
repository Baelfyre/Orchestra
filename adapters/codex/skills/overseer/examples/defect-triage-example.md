# Defect Triage Note

Fictional example.

- Summary: Saving an edited phone number shows success but the old value returns after reopening.
- Environment and revision: Fictional desktop test build `r42`, local test database.
- Preconditions: Existing employee record and editor access.
- Reproduction steps: Edit phone, save, close editor, reopen employee.
- Expected behavior: Reopened editor shows the saved phone number.
- Actual behavior: Success message appears; reopened editor shows the old number.
- Evidence Reviewed: Screen recording and before/after read-only query supplied in the example.
- Frequency: 3 of 3 supplied attempts.
- Impact and severity rationale: Major data-persistence defect in a primary workflow.
- Scope and regression risk: Contact repository mapping and employee-update transaction.
- Workaround: None confirmed.
- Assumptions: UI and query use the same employee identifier.
- Missing evidence: Service logs and repository test.
- Next action: Trace the update mapping and add a focused persistence regression check before editing code.
