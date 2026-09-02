# Scribe `SPEC_TO_SYSTEM` Example

## Request

Turn an approved problem statement about missed customer order updates into implementation-ready documentation without making architecture or database decisions.

## Direction

`SPEC_TO_SYSTEM`

## Domain Narrative

- `PROVIDED`: Customers and staff need reliable visibility of order status.
- `PROVIDED`: Missed or inconsistent updates create support work and reduce trust.
- `CANDIDATE`: `Order Status` is a domain concept that may have lifecycle states.
- `UNRESOLVED`: The technical source of truth for status has not been designed.

Noun discovery does not make `Order Status`, `Customer`, or `Staff` a software class, database table, or aggregate.

## Problem-to-Objective Mapping

| Problem / Need | Objective | Requirement |
|---|---|---|
| Order status is not reliably visible | Provide a consistent status view to authorized users | `ORD-STATUS-001` |

## Requirement Record

- ID: `ORD-STATUS-001`
- Status: `APPROVED`
- Statement: Authorized users must be able to view the current order status.
- Source: Approved project problem statement.
- Acceptance criteria: Current status is visible for an existing order to an authorized user; unauthorized visibility is not assumed by this documentation.
- Architecture: `UNRESOLVED`, route to Clockwork.
- Persistence semantics: `UNRESOLVED`, route to Chronicler if stored state is required.
- Security rules: `UNRESOLVED`, route to Cipher.
- Formal state/model diagram: optional, route to Weaver if required.
- Implementation: `PLANNED`, not yet claimed as implemented.
- Validation: `MISSING_EVIDENCE` until Overseer-owned evidence exists.

## Handoff

Scribe preserves the requirement and traceability. Conductor routes the unresolved technical decisions to the minimum required owners, then routes implementation. After validation, Scribe updates the as-built record without changing `IMPLEMENTED` to `VALIDATED` until qualifying evidence exists.
