# Artificer Audit Reports Registry

## Purpose
This registry stores governed audit reports generated during Artificer's Phase 4 lifecycle. It records security reviews, license compatibility assessments, and specific findings with recommendations.

## Layout and Filenames
Files must be placed in a directory corresponding to the source bundle ID:
`internal/artificer/reviews/<bundle-id>/audit-report.json`

## Requirements
*   **Traceability**: Every report must trace back to a specific `source-intake.json` record via `source_intake_path` and `source_bundle_id`.
*   **Manual Creation**: Records are manually created and reviewed.
*   **Validation**: Phase 4B deterministically validates this registry, source traceability, and cross-record integrity.
*   **No Approval Authority**: No record in this registry grants Artificer approval or implementation authority.
*   **No External Modifications**: No registry may modify an external repository.
*   **Empty State**: An empty registry is valid.

## Phase 4C-A Read-Only Rendering

Render one validated audit report to standard output:

```powershell
python scripts/render_artificer_audit_report.py `
  --audit internal/artificer/reviews/<bundle-id>/audit-report.json
```

Use `--repo-root <path>` only when invoking the renderer outside the repository
root. The renderer creates no file and never updates governance records or
`docs/internal/PATTERN_CATALOG.md`. Rendered Markdown is a human-readable view,
not governance authority; validated JSON records remain canonical.
