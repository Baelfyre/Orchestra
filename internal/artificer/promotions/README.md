# Artificer Pattern Catalog Promotion Records Registry

## Purpose
This registry tracks the promotion of approved patterns into the Pattern Catalog and their implementation lifecycle.

## Layout and Filenames
Files must be named using their catalog pattern ID:
`internal/artificer/promotions/<catalog-pattern-id>.json`

## Requirements
*   **Traceability**: Every promotion record must trace to a proposal ID, decision ID, source bundle, commit SHA, file, and line range.
*   **Manual Creation**: Records are manually created and reviewed.
*   **Validation**: Phase 4B deterministically validates this registry and does not mutate the Pattern Catalog; Phase 4C owns catalog rendering and gating.
*   **No Approval Authority**: No record in this registry grants Artificer approval or implementation authority.
*   **No External Modifications**: No registry may modify an external repository.
*   **Empty State**: An empty registry is valid.
