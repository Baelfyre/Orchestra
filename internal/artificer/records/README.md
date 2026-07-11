# Artificer Pattern Records Registry

This directory contains the canonical records of external source intake and pattern evaluations.

## Directory Structure

Records are organized into "bundle" directories. Each bundle represents the evaluation of a specific repository at a specific commit.

The bundle directory name is derived from the repository owner, repository name, and the first 12 characters of the reviewed commit SHA:
`<owner-slug>__<repo-slug>__<sha12>`

### Bundle Layout

Inside each bundle directory:
*   `source-intake.json`: Contains the repository metadata, license, and the list of examined files and line ranges. Must conform to `SOURCE_INTAKE_SCHEMA.json`.
*   `patterns/`: A directory containing individual pattern evaluation records.
    *   `*.json`: Each pattern instance. The filename must be the slugified pattern name. Must conform to `PATTERN_SCHEMA.json`.

## Validation

Record instances are validated strictly by the Phase 3 instance validator (`scripts/validate_artificer_records.py`).
The validator ensures schema compliance, semantic validity (e.g., proper slug derivation, line range coverage), and cross-record integrity.
