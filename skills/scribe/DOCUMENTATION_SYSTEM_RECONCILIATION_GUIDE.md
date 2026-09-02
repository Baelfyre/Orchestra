# Documentation-System Reconciliation Guide

## Purpose

Use this guide when Scribe must keep documented intent, specification, implementation, validation, and research claims aligned over time.

The reconciliation model is bidirectional. Documentation can become stale, but implementation can also diverge from approved requirements or design. Neither side is automatically authoritative without context and evidence.

## Documentation Directions

Scribe supports three explicit directions.

### SPEC_TO_SYSTEM

Use when documented intent and approved requirements guide future implementation.

```text
Problem / Opportunity
  -> Domain Narrative
  -> Objectives
  -> Stakeholders
  -> Scope / Constraints
  -> Requirements
  -> Acceptance Criteria
  -> Specialist Design / Models
  -> Implementation
  -> Verification / Validation
  -> As-Built Documentation
```

Scribe structures intent and traceability. Architecture, persistence, formal modeling, security, UI, implementation, and QA decisions remain with their owning specialists.

### SYSTEM_TO_DOCS

Use when a system already exists but documentation is incomplete or stale.

```text
Repository / Runtime / Existing Docs
  -> Code, Config, Schemas, Tests, UI, Git History, Evidence
  -> Specialist Verification
  -> Scribe Reconstruction
  -> Domain Narrative
  -> Supported Requirements / Capabilities
  -> Technical and Research Documentation
  -> As-Built Record
```

Reconstruct only what evidence supports. Distinguish:

- observed behavior;
- current implementation;
- validated behavior;
- inferred purpose;
- historical intent;
- unresolved assumptions.

Do not present inferred intent as an approved historical requirement.

### RECONCILE

Use for continuous comparison across lifecycle artifacts.

```text
INTENT
  <-> SPECIFICATION
  <-> IMPLEMENTATION
  <-> VALIDATION
  <-> DOCUMENTATION / RESEARCH CLAIMS
```

The objective is not to make every artifact identical. The objective is to make differences explicit, classified, traceable, and routed to the correct owner.

## Documentation State Model

Use existing project/governance states where they already exist. When a local documentation status is needed, these semantic states are recommended:

- `PROPOSED`: idea exists but is not approved.
- `APPROVED`: intent or requirement has been accepted by the relevant authority.
- `PLANNED`: scheduled or authorized for implementation.
- `IMPLEMENTED`: repository or runtime evidence establishes implementation.
- `VALIDATED`: qualifying verification/evaluation evidence demonstrates the expected behavior under stated conditions.
- `DEPRECATED`: still present but intentionally being retired.
- `SUPERSEDED`: replaced by a newer decision, requirement, model, or artifact.
- `DOC_DRIFT`: documentation no longer matches reviewed implementation or approved current truth.
- `IMPLEMENTATION_DRIFT`: implementation diverges from an approved requirement, design, or policy.
- `MISSING_EVIDENCE`: a claim or state cannot currently be verified.
- `UNRESOLVED`: evidence is contradictory or insufficient to determine the correct state.

Do not create a new lifecycle vocabulary when an authoritative project vocabulary already covers the same meaning.

## Reconciliation Procedure

### 1. Establish the Comparison Scope

Identify the exact artifacts and revisions being compared, such as:

- requirements/specification;
- domain narrative or glossary;
- architecture decision or model;
- source files and configuration;
- schema or migration;
- tests and validation evidence;
- README or technical documentation;
- research/capstone manuscript;
- release notes or changelog.

### 2. Identify Claimed State

Extract material claims from the documentation or approved specification. Examples:

- feature exists;
- requirement is implemented;
- behavior is validated;
- architecture has a stated responsibility;
- dataset/evaluation supports a research conclusion;
- version, command, path, endpoint, or compatibility statement is current.

### 3. Identify Observed State

Use repository, runtime, specialist, and validation evidence to determine what can actually be established.

### 4. Compare and Classify

Classify differences rather than editing them away silently.

| Condition | Classification |
|---|---|
| Documentation is stale relative to verified current implementation | `DOC_DRIFT` |
| Implementation diverges from approved current specification/design | `IMPLEMENTATION_DRIFT` |
| Required documentation is absent | `MISSING_DOCUMENTATION` |
| Implementation has no traceable requirement/decision where one is expected | `UNDOCUMENTED_IMPLEMENTATION` |
| Requirement has no realization, deferral, or disposition | `ORPHANED_REQUIREMENT` |
| Claim lacks qualifying evidence | `UNSUPPORTED_CLAIM` or `MISSING_EVIDENCE` |
| Model or reference was replaced but is still presented as current | `OBSOLETE_MODEL` / `SUPERSEDED_REFERENCE` |
| Validation state is asserted without qualifying evidence | `VALIDATION_GAP` |
| Research conclusion exceeds collected evidence | `STALE_OR_UNSUPPORTED_RESEARCH_CLAIM` |
| Evidence conflicts and authority cannot be established | `UNRESOLVED` |

### 5. Determine the Correct Owner

Scribe may correct prose when the underlying truth is already established. If the discrepancy requires a technical, governance, or validation decision, route it first:

- Clockwork for architecture and technical boundaries;
- Chronicler for persistence/data semantics;
- Weaver for formal model consistency;
- Cipher for security/privacy controls;
- Cloak for UX/UI behavior;
- Overseer for validation conclusions;
- The Steward or The Governor for their governance domains;
- implementation specialist for source changes;
- Conductor when ownership or sequencing is ambiguous.

### 6. Update Traceability

After the owning decision is established, update the relevant documentation links, statuses, evidence references, and supersession relationships.

## Documentation Reconciliation Report

Use this adaptable structure:

```markdown
# Documentation-System Reconciliation Report

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

## As-Built Reconstruction Record

For `SYSTEM_TO_DOCS`, use a concise evidence table when useful:

```markdown
| Capability / Behavior | Observed Evidence | Requirement / Intent Evidence | Validation Evidence | Confidence / State | Documentation Action |
|---|---|---|---|---|---|
```

Do not use confidence language to promote a state beyond the underlying evidence.

## Drift Report

```markdown
| Drift ID | Type | Source Artifact | Conflicting Artifact | Evidence | Impact | Owner | Disposition |
|---|---|---|---|---|---|---|---|
```

## Safeguards

- Do not rewrite history to make old documentation appear current.
- Preserve superseded decisions and link them to their replacements when history matters.
- Do not treat code as proof of original intent.
- Do not treat an approved specification as proof that implementation matches it.
- Do not treat tests as passed unless the relevant execution evidence exists.
- Do not convert implementation evidence into research-effectiveness claims.
- Do not auto-resolve a conflict when the owning specialist has not established the correct truth.

## Completion Rule

A reconciliation is complete only when every material mismatch has one of these outcomes:

1. documentation corrected against verified truth;
2. implementation remediation routed to the proper owner;
3. specification/design correction routed to the proper owner;
4. explicit deferral or supersession recorded;
5. unresolved state preserved with the missing evidence identified.

Silently ignoring a known mismatch is not a valid reconciliation outcome.
