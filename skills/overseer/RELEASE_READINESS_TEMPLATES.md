# QA and Release Readiness Templates

Replace placeholders only with verified evidence.

## Contents
- [Test Plan Review](#test-plan-review)
- [Test Case Audit](#test-case-audit)
- [Regression Readiness Checklist](#regression-readiness-checklist)
- [Defect Triage Note](#defect-triage-note)
- [Release Readiness Report](#release-readiness-report)
- [Final Quality Gate Summary](#final-quality-gate-summary)

## Test Plan Review

```markdown
# Test Plan Review
## Objective and Scope
## Evidence Reviewed
## Risks and Priorities
## Test Levels and Types
## Environment and Data
## Entry and Exit Criteria
## Coverage Gaps
## Assumptions
## Missing Evidence
## Recommendation
```

## Test Case Audit

```markdown
# Test Case Audit
| Case | Requirement | Preconditions | Data | Expected Result | Actual Result | Outcome | Gap |
|---|---|---|---|---|---|---|---|
## Duplicate or Missing Coverage
## Assumptions
## Missing Evidence
## Priority Fixes
```

## Regression Readiness Checklist

```markdown
# Regression Readiness
- Change surface:
- Critical workflows:
- Dependency impact:
- Prior defect areas:
- Selected regression checks:
- Evidence status:
- Residual risk:
- Assumptions:
- Missing evidence:
- Decision:
```

## Defect Triage Note

```markdown
# Defect Triage Note
- Summary:
- Environment and revision:
- Preconditions:
- Reproduction steps:
- Expected behavior:
- Actual behavior:
- Evidence:
- Frequency:
- Impact and severity rationale:
- Scope and regression risk:
- Workaround:
- Assumptions:
- Missing evidence:
- Next action:
```

## Release Readiness Report

```markdown
# Release Readiness Report
## Release Objective and Revision
## Required Gates
| Gate | Status | Evidence | Blocker or Waiver |
|---|---|---|---|
## Test Results
## Defects and Residual Risk
## Verification and Validation Evidence
## Documentation and Operational Readiness
## Assumptions
## Missing Evidence
## Release Recommendation
```

## Final Quality Gate Summary

```markdown
# Final Quality Gate Summary
- Quality objective:
- Revision:
- Passed gates:
- Failed gates:
- Blocked or not-run gates:
- Approved waivers:
- Residual risk owner:
- Evidence reviewed:
- Missing evidence:
- Final decision:
```
