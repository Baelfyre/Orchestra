# Output Formats

## Caveman

```markdown
# Overseer Quick QA Review

## Quality Objective
-

## Evidence Reviewed
-

## Confirmed Issues
1.
2.
3.

## Highest-Risk Gap
-

## Recommended Next Action
-
```

## Full QA Review

```markdown
# Overseer Quality Review

## Scope Reviewed
- Project:
- Quality Objective:
- Review Mode:
- Evidence Reviewed:

## Review Confidence
Confidence Level: High / Medium / Low
Reason:

## Executive Summary

## Confirmed Quality Strengths

## Requirements Testability Issues

## Test Coverage Issues

## Test Case Quality Issues

## Defect and Risk Issues

## Regression Readiness

## Verification and Validation Notes

## Release Readiness

## Missing Evidence

## Priority Fixes

## Recommended Test or QA Actions

## Final Recommendation
```

## Delegated Unit Evidence

Use this format when producing or verifying focused validation evidence for a delegated internal unit.

```markdown
## Execution Evidence Packet
- Envelope ID:
- Phase ID:
- Unit ID:
- Repository:
- Branch:
- Approved Base SHA:
- Current Commit SHA:
- Working Tree Fingerprint:
- Changed Paths:
- Implementation Summary:
- Validation Commands:
- Validation Results:
- Skipped Checks:
- Known Limitations:
- Scope Audit Result: PASS | FAIL
- Protected Repository Result: PASS | FAIL
- Security and Secret Result: PASS | FAIL
- Design Contradiction State: NONE | PENDING
- Evidence Producer:
- Evidence Timestamp:
- Freshness Reference:
```
