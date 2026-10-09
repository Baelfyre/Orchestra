# Output Formats

## Caveman

```markdown
# Chronicler Quick DB Review

## Database Objective
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

## Normalization Output

```markdown
# Chronicler Database Review

## Scope Reviewed
- Project:
- Database Objective:
- Source of Truth:
- Evidence Reviewed:
- Review Mode:

## Review Confidence
Confidence Level: High / Medium / Low
Reason:

## Executive Summary

## Confirmed Schema Strengths

## Data Integrity Issues

## Referential Integrity Issues

## Constraint Issues

## Normalization Issues

## Index and Performance Notes

## Seed Data Issues

## Migration Risks

## Integration Notes

## Auditability Notes

## Data Dictionary Gaps

## Recommended Fixes

## SQL or Documentation Guidance
Provide SQL only when supported by evidence. Mark SQL as draft unless tested.

## Missing Evidence

## Final Recommendation
```

## Migration Risk Contract section

This is a structured section inside **Caveman** or **Normalization Output**, not
a new frontmatter output format. Use the canonical schema and keep unknown
production facts explicit.

```text
CONTRACT: MigrationRiskContract
SCHEMA: orchestra.migration-risk-contract.v1
OWNER: chronicler
REVISION: [revision]
DATABASE_ENGINE: [confirmed engine]
DATABASE_VERSION: [confirmed version or UNKNOWN]
SCHEMA_REVISION: [revision]
MIGRATION_TOOL: [tool or UNKNOWN]
PRODUCTION_DATA: [true | false; unknown => MIGRATION_RISK_SCHEMA_GAP]
AFFECTED_RECORDS: [observed value | UNKNOWN | TO_BE_MEASURED]
READ_TRAFFIC: [observed value | UNKNOWN | TO_BE_MEASURED]
WRITE_TRAFFIC: [observed value | UNKNOWN | TO_BE_MEASURED]
LOCKING_IMPLICATIONS: [evidence-bound description]
COMPATIBILITY_REQUIRED: [true | false]
BACKFILL_REQUIRED: [true | false]
INDEX_OPERATION: [operation or none]
MIGRATION_PATTERN: [canonical pattern]
DEPLOYMENT_SEQUENCE: [ordered conceptual steps]
ROLLBACK_BOUNDARY: [explicit boundary]
FAILURE_RECOVERY: [bounded recovery guidance]
OBSERVABILITY: [applicable signals]
COMPLETION_CRITERIA: [proof conditions]
RISK: [LOW | MEDIUM | HIGH | CRITICAL | UNKNOWN]
HUMAN_GATE_REQUIRED: [true | false]
EVIDENCE_REFS: [supporting references]
```

An unknown production-presence input returns
`MIGRATION_RISK_SCHEMA_GAP: UNKNOWN_PRODUCTION_STATE_NOT_REPRESENTABLE` and
does not emit a v1 contract. Missing engine/version evidence blocks
dialect-specific claims as `ENGINE_SPECIFIC_CLAIM_BLOCKED`. This section is a
planning and Ponytail handoff contract, never migration execution or release
readiness.
