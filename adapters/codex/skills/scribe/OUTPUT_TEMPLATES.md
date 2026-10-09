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
- [Domain Glossary](#domain-glossary)
- [Problem-to-Objective Matrix](#problem-to-objective-matrix)
- [Requirements Traceability Matrix](#requirements-traceability-matrix)
- [As-Built System Reconstruction](#as-built-system-reconstruction)
- [Documentation Reconciliation Report](#documentation-reconciliation-report)
- [Research-to-System Traceability Matrix](#research-to-system-traceability-matrix)
- [Capstone Evidence Map](#capstone-evidence-map)
- [Implementation-to-Claim Matrix](#implementation-to-claim-matrix)
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
[Short verified summary and link to maintained architecture evidence.]

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

```markdown
# Domain Narrative

## Context
## Vocabulary
## Stakeholders and Actors
## Processes
## Business Rules
## Events and State Changes
## Candidate Concepts
## Relationships
## Assumptions and Constraints
## External Systems
## Scope Boundaries
## Evidence and Traceability
## Unresolved Questions
```

Use only supported sections. Candidate concepts are discovery notes, not automatically classes, entities, tables, services, or components.

## Domain Glossary

```markdown
# Domain Glossary

| Term | Preferred Meaning | Synonyms / Ambiguity | Status | Evidence / Source |
|---|---|---|---|---|
| | | | | |
```

## Problem-to-Objective Matrix

```markdown
# Problem-to-Objective Matrix

| Problem ID | Problem Statement | Objective ID | Objective | Status | Evidence |
|---|---|---|---|---|---|
| | | | | | |
```

## Requirements Traceability Matrix

```markdown
# Requirements Traceability Matrix

| Requirement | Objective / Goal | Domain / Use Case | Design / Architecture | Implementation | Test / Evaluation | Evidence | Status |
|---|---|---|---|---|---|---|---|
| | | | | | | | |
```

Use `NOT_APPLICABLE`, `MISSING_EVIDENCE`, or `UNRESOLVED` instead of inventing missing links.

## As-Built System Reconstruction

```markdown
# As-Built System Reconstruction

## Source Revision and Environment
## Evidence Reviewed
## Observed Behavior
## Current Implementation
## Validated Behavior
## Inferred Purpose
## Historical Intent
## Supported Requirements / Capabilities
## Verified Technical Description
## Known Limitations
## Unresolved Assumptions
## Specialist Verification Needed
## Evidence Map
```

Do not merge inferred purpose, historical intent, and current implementation into one statement.

## Documentation Reconciliation Report

```markdown
# Documentation Reconciliation Report

## Scope and Compared Revisions
## Evidence Inventory
| Item | Intended / Approved | Current Implementation | Validation Evidence | Documentation | Disposition | Owner |
|---|---|---|---|---|---|---|
| | | | | | | |

## Documentation Drift
## Implementation Drift
## Missing Evidence
## Specialist Re-entry Required
## Governance Decisions Required
## Corrections Completed
## Remaining Unresolved Items
## Final Reconciliation Status
```

## Research-to-System Traceability Matrix

```markdown
# Research-to-System Traceability Matrix

| Research Question / Business Goal | Objective | Requirement | Implementation Evidence | Evaluation | Result / Evidence | Documented Claim | Limitation |
|---|---|---|---|---|---|---|---|
| | | | | | | | |
```

## Capstone Evidence Map

```markdown
# Capstone Evidence Map

| Research / System Item | Status | Evidence | Owner / Source | Claim Allowed? | Limitation |
|---|---|---|---|---|---|
| Problem | | | | | |
| Objective | | | | | |
| Requirement | | | | | |
| Implementation | | | | | |
| Evaluation | | | | | |
| Result | | | | | |
| Documented Claim | | | | | |
```

Delete irrelevant rows instead of filling them with generic content.

## Implementation-to-Claim Matrix

```markdown
# Implementation-to-Claim Matrix

| Claim ID | Documented Claim | Implementation Evidence | Test / Evaluation Evidence | Evidence Status | Claim Disposition |
|---|---|---|---|---|---|
| | | | | | |
```

Claim dispositions may include `SUPPORTED`, `PARTIALLY_SUPPORTED`, `MISSING_EVIDENCE`, `SUPERSEDED`, `NOT_APPLICABLE`, or `UNRESOLVED`.

## Documentation Drift Report

```markdown
# Documentation Drift Report

## Scope
## Compared Revision / Environment
| Item | Documentation Says | Verified Evidence Says | Drift Type | Severity / Impact | Required Owner | Disposition |
|---|---|---|---|---|---|---|
| | | | | | | |

## Summary
## Documentation Corrections
## Implementation Review Required
## Missing Validation
## Unresolved Items
```

Drift identification is evidence comparison, not implementation or governance authority.
