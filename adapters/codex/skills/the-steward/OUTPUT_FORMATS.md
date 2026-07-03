# Output Formats

## Governance Review

### Compact
Use this default compact format for general governance reviews.

```text
REVIEWER: the-steward
PROJECT_CONTEXT: [project type] | [risk level]
DECISION: [APPROVED | ADVISORY_ONLY | REVISION_REQUIRED | BLOCKED | NOT_APPLICABLE]
REASON: [one-line assessment]
RISKS: [identified risks or "none"]
REQUIRED_ACTIONS: [actions needed or "none"]
```

### Expanded
Use this expanded format when significant findings or risks exist.

```text
REVIEWER: the-steward
PROJECT_CONTEXT: [project type] | [risk level]
DECISION: [APPROVED | ADVISORY_ONLY | REVISION_REQUIRED | BLOCKED | NOT_APPLICABLE]
SUMMARY: [one-line assessment]
ALIGNMENT: [status]
SCOPE: [within scope | scope drift risk | out of scope]
REQUIREMENTS: [covered | partial | missing]
ACCEPTANCE_CRITERIA: [defined | undefined | not needed]
SDLC_DOCS: [sufficient | gaps found | missing]
FINDINGS: [list]
RISKS: [list]
REQUIRED_ACTIONS: [list]
DOCUMENTATION_GAPS: [list]
TIMESTAMP: [ISO 8601]
```
