# Requirements Traceability and Acceptance Guide

Load this guide when reviewing whether intended outcomes, acceptance criteria, implementation, and evidence remain connected.

## Evidence Layers

Keep these layers distinct:

1. `OBJECTIVE`: the business outcome and target users.
2. `REQUIREMENT`: a testable capability or constraint.
3. `ACCEPTANCE_CRITERION`: observable conditions for accepting the requirement.
4. `IMPLEMENTATION`: exact components, documents, schemas, or workflows intended to satisfy it.
5. `EVIDENCE`: current tests, reviews, commands, or canonical reads that demonstrate the criterion.

An implementation reference is not evidence by itself. A test result supports only the criterion exercised on the exact state identified by that result.

## Traceability Record

For material requirements, record:

| Field | Required content |
| --- | --- |
| Requirement ID | Stable identifier, not a mutable list position |
| Source | User decision, accepted plan, issue, ADR, or contract revision |
| Objective | Business outcome served |
| Acceptance criteria | Observable behavior, boundary, and failure/recovery condition |
| Implementation references | Exact owned paths or components |
| Evidence references | Test/check name, state identity, result, and timestamp when material |
| Status | `PROPOSED`, `APPROVED`, `IMPLEMENTED_UNVERIFIED`, `VERIFIED`, `DEFERRED`, or `REJECTED` |
| Owner | One accountable decision owner |

Bidirectional traceability means every in-scope requirement maps forward to acceptance and evidence, and every implementation change maps back to an authorized requirement or defect.

## Acceptance-Criteria Quality

Criteria should state:

- precondition and actor;
- observable success;
- relevant denial or failure behavior;
- recovery behavior when failure is material;
- security, privacy, accessibility, or data boundary when applicable;
- evidence type and environment;
- exclusions that prevent accidental scope growth.

Avoid criteria such as "works correctly", "is secure", or "passes tests" without a measurable behavior and evidence boundary.

## Coverage Review

Classify each requirement:

- `COVERED`: criteria and current evidence exist.
- `PARTIAL`: some criteria or evidence are missing.
- `ORPHAN_REQUIREMENT`: no owned implementation or evidence.
- `ORPHAN_CHANGE`: implementation has no authorized requirement or defect.
- `STALE_EVIDENCE`: evidence targets an earlier state or contract revision.
- `CONTRADICTED`: sources or criteria cannot all be satisfied as written.

`PARTIAL`, `ORPHAN_REQUIREMENT`, `ORPHAN_CHANGE`, `STALE_EVIDENCE`, or `CONTRADICTED` must be visible in the decision. Do not manufacture linkage to make a matrix look complete.

## Invalidation

Re-evaluate affected traceability when objectives, requirements, criteria, implementation identity, environment, or evidence state changes. Preserve historical decisions; add a superseding record rather than silently rewriting prior evidence.
