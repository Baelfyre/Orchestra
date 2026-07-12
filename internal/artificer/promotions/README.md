# Artificer Pattern Catalog Promotion Records Registry

## Purpose
This registry tracks the promotion of approved patterns into the Pattern Catalog and their implementation lifecycle.

## Layout and Filenames
Files must be named using their catalog pattern ID:
`internal/artificer/promotions/<catalog-pattern-id>.json`

## Requirements
*   **Traceability**: Every promotion record must trace to a proposal ID, decision ID, source bundle, commit SHA, file, and line range.
*   **Manual Creation**: Records are manually created and reviewed.
*   **Catalog Projection**: Every validated promotion record must project to exactly one Catalog index row and exactly one Catalog entry in `docs/internal/PATTERN_CATALOG.md`.
*   **Manual Synchronization**: The Pattern Catalog is synchronized manually; automatic Catalog writes are prohibited.
*   **Validation**: Run `python scripts/validate_artificer_pattern_catalog.py` to enforce synchronization, or `python scripts/validate_artificer_pattern_catalog.py --print-expected` to preview the canonical projection without writing files.
*   **No Approval Authority**: No record in this registry grants Artificer approval or implementation authority.
*   **No External Modifications**: No registry may modify an external repository.
*   **Empty State**: An empty registry is valid.
