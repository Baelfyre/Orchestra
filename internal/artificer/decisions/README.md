# Artificer Governance Decisions Registry

## Purpose
This registry stores governance decisions determining whether a pattern from an audit report is approved, rejected, deferred, or blocked.

## Layout and Filenames
Files must be placed in a directory corresponding to the source bundle ID, and named after the pattern slug:
`internal/artificer/decisions/<bundle-id>/<pattern-slug>.json`

## Requirements
*   **Traceability**: Every decision must reference a specific pattern record and an audit report.
*   **Manual Creation**: Records are manually created and reviewed by Arbiter, Governor, and Steward before a Maintainer decision.
*   **Validation**: Phase 4B will introduce deterministic validation for these records.
*   **No Approval Authority**: No record in this registry grants Artificer approval or implementation authority automatically.
*   **No External Modifications**: No registry may modify an external repository.
*   **Empty State**: An empty registry is valid.
