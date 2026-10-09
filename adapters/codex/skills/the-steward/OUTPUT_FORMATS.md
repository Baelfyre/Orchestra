# Output Formats

## Governance Review

### Compact
```text
REVIEWER: the-steward
PROJECT_CONTEXT: [project type] | [risk level]
DECISION: [APPROVED | ADVISORY_ONLY | REVISION_REQUIRED | BLOCKED | NOT_APPLICABLE]
REASON: [one-line assessment]
RISKS: [identified risks or "none"]
REQUIRED_ACTIONS: [actions needed or "none"]
```

### Expanded
```text
REVIEWER: the-steward
PROJECT_CONTEXT: [project type] | [risk level]
DECISION: [APPROVED | ADVISORY_ONLY | REVISION_REQUIRED | BLOCKED | NOT_APPLICABLE]
SUMMARY: [assessment]
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

## Delegated Governance Review
```text
REVIEWER: the-steward
ENVELOPE_ID: [envelope_id]
PHASE_ID: [phase_id]
UNIT_ID: [unit_id]
DECISION: [decision]
HUMAN_REVIEW_REQUIRED: [false | true]
REASON_CODE: [code]
CONSTRAINTS: [list or "none"]
REQUIRED_ACTIONS: [actions or "none"]
EVIDENCE_REFERENCES: [list or "none"]
```

## Product Intent Contract
```text
CONTRACT: ProductIntentContract
OWNER: the-steward
REVISION: [revision]
PROBLEM: [verified problem friction]
EVIDENCE: [tickets/quotes/telemetry]
USERS: [personas/roles]
WORKAROUND: [current handling]
REQUESTED: [proposed solution]
ALIGNMENT: [strategic alignment]
ALTERNATIVES_REQUIRED: [true | false]
OVERLAP: [overlap or "none"]
OBSOLESCENCE: [assessment]
MAINTENANCE: [assessment]
DECISION: [decision enum]
RATIONALE: [justification]
CRITERIA: [acceptance criteria]
REFS: [evidence references]
```

## Capacity Envelope
```text
CONTRACT: CapacityEnvelope
OWNER: the-steward
REVISION: [revision]
STAGE: [stage enum]
HORIZON: [target horizon]
METRICS: [metric: status, value, basis, confidence]
KNOWN: [known metrics]
ASSUMED: [assumed metrics]
UNKNOWN: [unknown metrics]
DISPOSITION: [disposition enum]
REFS: [evidence references]
```
