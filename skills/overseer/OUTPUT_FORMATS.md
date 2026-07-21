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

### ExecutionEvidencePacket

Use this format when producing or verifying focused validation evidence for a delegated internal unit.

```markdown
- schema_version:
- evidence_id:
- envelope_id:
- phase_id:
- unit_id:
- repository_identity:
- branch:
- approved_base_sha:
- current_commit_sha:
- working_tree_fingerprint:
- changed_paths:
- implementation_summary:
- validation_commands:
- validation_results:
- skipped_checks:
- known_limitations:
- scope_audit_result: PASS | FAIL
- protected_repository_result: PASS | FAIL
- security_and_secret_result: PASS | FAIL
- design_contradiction_state: NONE | PENDING
- evidence_producer:
- evidence_timestamp:
- freshness_reference:
```
