# Worked Example: Governed Analytics Export Change

This is a planning-only example. It records governance method, not a legal conclusion or implementation authorization.

## Proposed Change

Add a customer analytics export to an existing internal service.

## Steward Traceability

- Objective: enable approved operations analysis.
- Requirement `REQ-EXPORT-01`: authorized analysts can request a bounded export.
- Acceptance criterion `AC-01`: authorized and unauthorized personas have observable allow/deny evidence.
- Acceptance criterion `AC-02`: exported fields match the approved data dictionary and exclude undeclared fields.
- Implementation: `NOT_STARTED`.
- Evidence: `NOT_FOUND`.
- Status: `APPROVED_REQUIREMENT_IMPLEMENTATION_UNVERIFIED`.

Scope additions such as external sharing, a new data category, or automated delivery are `SCOPE_CHANGE`, not implementation detail. They require updated criteria and owner review.

## Governor Source and Issue Record

- Intended users, data fields, recipients, retention, and jurisdictions: `PARTIAL_CONTEXT`.
- Applicable customer agreements and privacy notices: `SOURCE_NOT_FOUND`.
- Jurisdiction/effective-date verification: `NOT_PERFORMED`.
- License or third-party dataset impact: `NOT_APPLICABLE` only after inventory confirms none.
- Legal/compliance conclusion: `NOT_MADE`.

Operational question: may the proposed fields be exported to the named analyst role under the governing agreements and applicable privacy obligations?

Disposition: `REVISION_REQUIRED`, `human_review_required: true`. Product and data owners must complete the facts; a qualified privacy/legal owner must resolve the material applicability question. Technical privacy/security controls route to Cipher after obligations are defined.

## Protected State

No implementation, data access, policy activation, notice publication, release, or production change occurred. Passing future tests cannot replace the unresolved governance decision.
