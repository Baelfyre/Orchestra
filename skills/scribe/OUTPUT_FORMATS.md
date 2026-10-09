# Output Formats

## Mode 1

Use for final documentation or detailed audits.

```markdown
# Scribe Documentation Audit

## Scope Reviewed
- Project:
- Objective:
- Documentation Type:
- Intended Reader:
- Evidence Reviewed:

## Review Confidence
Confidence Level: High / Medium / Low
Reason:

## Executive Summary

## Confirmed Documentation Strengths

## Missing Documentation

## Accuracy Issues

## Objective Alignment Issues

## Traceability Issues

## Technical Clarity Issues

## Submission Readiness

## Recommended Documentation Structure

## Priority Fix List

## Copy-Ready Revision Notes

## Missing Evidence

## Final Recommendation
```

## Mode 2

Use for standard documentation audits.

```markdown
# Scribe Documentation Audit

## Objective
-

## Review Confidence
Confidence Level: High / Medium / Low

## Executive Summary

## Accuracy Issues

## Priority Fix List

## Copy-Ready Revision Notes

## Next Action
-
```

## Mode 3

Use for quick audits.

```markdown
# Scribe Quick Audit

## Objective
-

## Documentation Status
- Complete:
- Missing:
- Risk:

## Priority Fixes
1.
2.
3.

## Next Action
-
```

## GOVERNANCE_DOCUMENTATION_RECONCILIATION

Use for auditing and reconciling documentation against governance reality, specialist contracts, and exact-head commit/tree lineage.

```markdown
# Governance Documentation Reconciliation Report

## Target Surface
- Document Path:
- Lineage Binding (Commit / Tree):
- Specialist Contracts Reviewed:

## Evidence Evaluation
- Verified Source Evidence:
- Missing Evidence / Gaps:
- Prohibited Silent Promotions Detected: None / [List]

## Drift & Contradiction Analysis
- Documentation Drift: None / [Details]
- Implementation Drift: None / [Details]
- Contract Contradictions: None / [Details]

## Disposition & Handoff
- Reconciliation Status: RECONCILED / DRIFT_DETECTED / MISSING_EVIDENCE
- Specialist Handoffs Required:
```
