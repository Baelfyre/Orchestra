# Documentation Output Templates

Replace placeholders with verified project facts. Delete irrelevant sections instead of filling them with generic text.

## Contents

- [README](#readme)
- [System Readiness Report](#system-readiness-report)
- [Final Submission Report](#final-submission-report)
- [Implementation Summary](#implementation-summary)
- [Testing Summary](#testing-summary)
- [Documentation Audit Report](#documentation-audit-report)
- [Known Issues Log](#known-issues-log)
- [Decision Log](#decision-log)
- [Domain Narrative](#domain-narrative)
- [Requirements Traceability Matrix](#requirements-traceability-matrix)
- [As-Built System Reconstruction](#as-built-system-reconstruction)
- [Documentation Reconciliation Report](#documentation-reconciliation-report)
- [Research-to-System Traceability](#research-to-system-traceability)
- [Capstone Evidence Map](#capstone-evidence-map)
- [Documentation Drift Report](#documentation-drift-report)

## README

```markdown
# [Project Name]

[One-sentence objective and intended user.]

## Status
[Current milestone, supported scope, and important limitations.]

## Features
- [Verified capability]

## Requirements
- [Tool and verified version]

## Setup
1. [Verified step]

## Run
`[verified command]`

## Test
`[verified command]`

## Architecture
[Short summary and link to maintained diagram.]

## Known Issues
- [Issue, impact, workaround]
```

## System Readiness Report

```markdown
# System Readiness Report

## Objective and Scope
## Environment
## Readiness Criteria
| Criterion | Status | Evidence | Blocker |
|---|---|---|---|
## Build and Test Results
## Data and Integration Status
## Security and Accessibility Status
## Documentation Status
## Blockers and Next Actions
## Recommendation
```

## Final Submission Report

```markdown
# Final Submission Report

## Project Objective
## Required Deliverables
| Deliverable | Status | Evidence |
|---|---|---|
## Implemented Scope
## Excluded or Incomplete Scope
## Verification Summary
## Known Issues
## Submission File Checklist
## Final Readiness Decision
```

## Implementation Summary

```markdown
# Implementation Summary

## Objective
## Changed Components
## Behavior Added or Corrected
## Important Decisions
## Validation Performed
## Known Limitations
## Follow-up Work
```

## Testing Summary

```markdown
# Testing Summary

## Scope and Environment
## Commands Run
| Check | Result | Evidence |
|---|---|---|
## Failures or Skipped Checks
## Regression Risk
## Final Assessment
```

## Documentation Audit Report

```markdown
# Documentation Audit Report

## Objective and Audience
## Evidence Reviewed
## Confirmed Strengths
## Missing or Stale Content
## Accuracy and Traceability Issues
## Priority Fixes
## Missing Evidence
## Recommendation
```

## Known Issues Log

```markdown
# Known Issues

| ID | Issue | Impact | Workaround | Status | Evidence |
|---|---|---|---|---|---|
| KI-001 | | | | | |
```

## Decision Log

```markdown
# Decision: [Title]

- Status: Proposed / Accepted / Superseded
- Date:
- Context:
- Decision:
- Alternatives:
- Rationale:
- Consequences:
- Evidence or links:
```

## Domain Narrative

Use only the sections that fit the project.

```markdown
# Domain Narrative

## Context and Problem
## Stakeholders and Actors
## Vocabulary / Glossary
| Term | Meaning | Evidence / Source | Ambiguity |
|---|---|---|---|
## Rules and Processes
## Events and States
## Candidate Concepts
| Candidate | Evidence | Possible Classification | Relationships | Open Questions | Validation Owner |
|---|---|---|---|---|---|
## Assumptions and Constraints
## Scope Boundaries
## Requirement Links
## Unresolved Questions
```

## Requirements Traceability Matrix

```markdown
| Requirement | Source | Rationale | Status | Design / Model | Implementation | Verification | Evidence | Drift / Gap |
|---|---|---|---|---|---|---|---|---|
```

Do not populate implementation or validation fields without supporting evidence.

## As-Built System Reconstruction

```markdown
# As-Built System Reconstruction

## Scope and Exact Revision
## Evidence Reviewed
## Demonstrated Capabilities
| Capability / Behavior | Observed Evidence | Requirement / Intent Evidence | Validation Evidence | State | Documentation Action |
|---|---|---|---|---|---|
## Inferred Purpose
## Historical Intent Evidence
## Missing or Conflicting Documentation
## Unresolved Assumptions
## Specialist Verification Needed
```

## Documentation Reconciliation Report

```markdown
# Documentation-System Reconciliation Report

## Direction
SPEC_TO_SYSTEM / SYSTEM_TO_DOCS / RECONCILE

## Scope
## Evidence Reviewed
## Current Authoritative Inputs
## Confirmed Matches
## Drift and Gaps
| ID | Type | Documented State | Observed State | Evidence | Owner | Required Action | Status |
|---|---|---|---|---|---|---|---|
## Unsupported or Unresolved Claims
## Superseded / Obsolete References
## Traceability Updates
## Remaining Validation Gaps
## Recommendation
```

## Research-to-System Traceability

```markdown
| Research Question / Goal | Objective | Requirement / Capability | Implementation Evidence | Evaluation Method | Evidence / Result | Supported Claim | Status |
|---|---|---|---|---|---|---|---|
```

## Capstone Evidence Map

```markdown
| Deliverable / Rubric Item | Required Evidence | Current Artifact | State | Gap / Next Action |
|---|---|---|---|---|
```

Institutional headings and rubrics remain authoritative. Adapt this map to the actual submission requirements.

## Documentation Drift Report

```markdown
| Drift ID | Type | Source Artifact | Conflicting Artifact | Evidence | Impact | Owner | Disposition |
|---|---|---|---|---|---|---|---|
```

Use drift classifications only when the compared artifacts and their revisions are identifiable.
