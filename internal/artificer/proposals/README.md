# Artificer Evolution Proposals Registry

## Purpose
This registry stores design artifacts proposing how governed patterns should be evolved or adapted into Orchestra.

## Layout and Filenames
Files must be named using their unique proposal ID:
`internal/artificer/proposals/<proposal-id>.json`

## Requirements
*   **Traceability**: Every proposal must trace back to governance decisions and audit reports.
*   **Manual Creation**: Records are manually created and reviewed.
*   **Validation**: Phase 4B deterministically validates this registry, approved decisions, and cross-record integrity.
*   **No Approval Authority**: No record in this registry grants Artificer approval or implementation authority. The proposal is a design artifact only.
*   **No External Modifications**: No registry may modify an external repository.
*   **Empty State**: An empty registry is valid.
