# Artificer Evolution Proposals Registry

## Purpose
This registry stores design artifacts proposing how governed patterns should be evolved or adapted into Orchestra.

## Layout and Filenames
Files must be named using their unique proposal ID:
`internal/artificer/proposals/<proposal-id>.json`

## Requirements
*   **Traceability**: Every proposal must trace back to governance decisions and audit reports.
*   **Schema**: Proposal records use `EVOLUTION_PROPOSAL_SCHEMA.json` version `1.1`.
*   **Manual Creation**: Records are created manually. Artificer cannot create, approve, or advance a proposal on its own.
*   **Lifecycle**: Allowed states are `DRAFT`, `UNDER_REVIEW`, `APPROVED`, `REVISION_REQUIRED`, `DEFERRED`, `REJECTED`, and `BLOCKED`.
*   **Structured Reviews**: Arbiter, Governor, and Steward records each contain a status, rationale, and review date. The Maintainer disposition is recorded separately.
*   **Approval**: Final approval requires Arbiter and Steward approval, Maintainer approval, and Governor approval whenever a referenced audit requires Governor review. A proposal cannot self-approve.
*   **Validation**: Phase 4B deterministically validates this registry, approved decisions, and cross-record integrity.
*   **Promotion Boundary**: No proposal is eligible for promotion before final `APPROVED` disposition. Approval still does not create a promotion or Catalog entry.
*   **No Approval Authority**: Proposal records are design artifacts and grant no implementation authority.
*   **Phase Separation**: Phase 5C-A hardens the contract and creates an `UNDER_REVIEW` draft. Independent Arbiter, Governor, Steward, and Maintainer disposition occurs only in Phase 5C-B.
*   **No External Modifications**: No registry may modify an external repository.
*   **Empty State**: An empty registry is valid.
