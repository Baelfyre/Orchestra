# Output Formats

## Governance Review

### Compact
Use this default compact format for general governance reviews.

```text
REVIEWER: the-governor
PROJECT_CONTEXT: [project type] | [risk level]
DECISION: [APPROVED | ADVISORY_ONLY | REVISION_REQUIRED | BLOCKED | NOT_APPLICABLE]
HUMAN_REVIEW_REQUIRED: [true | false]
REASON: [one-line assessment]
RISKS: [identified risks or "none"]
REQUIRED_ACTIONS: [actions needed or "none"]
```

### Expanded
Use this expanded format when significant findings or risks exist.

```text
REVIEWER: the-governor
PROJECT_CONTEXT: [project type] | [risk level]
DECISION: [APPROVED | ADVISORY_ONLY | REVISION_REQUIRED | BLOCKED | NOT_APPLICABLE]
HUMAN_REVIEW_REQUIRED: [true | false]
SUMMARY: [one-line assessment]
COMPLIANCE: [compliant | concerns found | non-compliant]
LEGAL_RISK: [none | low | medium | high]
PRIVACY_RISK: [none | low | medium | high]
TOS_IMPACT: [none | update required]
PRIVACY_POLICY_IMPACT: [none | update required]
IP_COPYRIGHT: [clear | concerns found | requires review]
LICENSING: [compatible | incompatible | requires review]
SECURITY_GOVERNANCE: [sufficient | gaps found]
AUDIT_DOCS: [sufficient | gaps found | missing]
FINDINGS: [list]
RISKS: [list]
REQUIRED_ACTIONS: [list]
REQUIRED_REMEDIATION: [list]
DOCUMENTATION_GAPS: [list]
EVIDENCE_REFERENCES: [list]
TIMESTAMP: [ISO 8601]
```
