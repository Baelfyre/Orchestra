# Artificer Records Registry

This registry stores immutable snapshot records of external source intake and pattern extraction.

## Bundle Layout

The registry is organized into bundles. An empty registry is valid. Each bundle must strictly follow this layout:

```text
internal/artificer/records/<bundle-id>/
├── source-intake.json
└── patterns/
    ├── <pattern-slug-1>.json
    └── <pattern-slug-2>.json
```

### Derivations

* **Bundle ID**: Derived precisely as `<owner-slug>__<repo-slug>__<12-char-commit-sha>`.
* **Pattern Filenames**: The `name` field in the pattern JSON is converted to lowercase, slugified, and appended with `.json`. No directory traversal or nesting is permitted.

## Validation Constraints and Boundaries

Artificer local validation is strictly a structural metadata check against the internal schemas (`internal/artificer/SOURCE_INTAKE_SCHEMA.json` and `internal/artificer/PATTERN_SCHEMA.json`).

Validation **does not**:
* Perform network requests, repository cloning, or package installation.
* Execute or compile external source code.
* Prove factual evidence or verify that external source files and line ranges actually exist remotely.
* Approve licensing terms or bypass governance review.
* Promote patterns to the global Pattern Catalog automatically.

All records remain subject to manual maintainer and governance review.

## Schema Paths

Validation enforces the JSON schema subsets located at:
* `internal/artificer/SOURCE_INTAKE_SCHEMA.json`
* `internal/artificer/PATTERN_SCHEMA.json`

## Examples

### Valid `source-intake.json`

```json
{
  "repository": "example/project",
  "repository_owner": "example",
  "canonical_url": "https://github.com/example/project",
  "license": "MIT",
  "reviewed_commit_sha": "a1b2c3d4e5f678901234567890abcdef12345678",
  "review_date": "2026-07-11",
  "default_branch": "main",
  "files_examined": [
    {
      "file_path": "src/main.py",
      "line_ranges": ["10-50"]
    }
  ],
  "runtime_behavior_tested": true,
  "source_confidence": "HIGH"
}
```

### Valid `pattern.json`

```json
{
  "name": "Init Sequence",
  "description": "Example initialization pattern",
  "source_file": "src/main.py",
  "line_range": "15-25",
  "classification": "REFERENCE_ONLY",
  "assigned_specialist": "cloak",
  "license_implications": "MIT license requires standard copyright preservation."
}
```

*Note: The pattern's `source_file` must map exactly to an entry in the intake's `files_examined`, and its `line_range` must fall completely within the examined line ranges.*

The required `default_branch` records the source repository's declared default branch. A `runtime_behavior_tested` value of `true` records only separately authorized isolated external validation; it never indicates execution by Artificer in the Orchestra workspace.
