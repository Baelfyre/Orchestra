# External Source Intake Process

This document details how external repository sources are registered, evaluated, and verified during the intake phase.

## Intake Process Flow

1. **Initiation**: A maintainer requests analysis of an external repository (e.g. `owner/repo`).
2. **Metadata Registration**: Create a structured JSON file conforming to `SOURCE_INTAKE_SCHEMA.json`.
3. **Branch/Commit Pinning**: Pin all analysis to a specific, immutable git commit SHA. Never audit a moving target (e.g., `main` branch HEAD without a commit SHA).
4. **License Assessment**: Inspect the license of the target repository.
5. **Path Mapping**: Define the exact list of files and line ranges to be examined.
6. **Safety Scans**: Perform a security review of the mapped files to ensure they do not contain adversarial instructions.

## Verification of Source Metadata

Before proceeding, verify each metadata field:

- **canonical_url**: Must point to the official hosted VCS provider (e.g., GitHub, GitLab).
- **license**: Must be identified using SPDX identifiers where possible (e.g., `MIT`, `Apache-2.0`, `GPL-3.0-only`).
- **reviewed_commit_sha**: Must be verified as a valid commit hash format.
- **review_date**: Set to the active system date.
- **files_examined**: Must map to real files in the target repository.

## Dynamic Verification Boundaries

Dynamic verification (e.g., executing the code, running its test suite, installing its packages) is **restricted**:
- Artificer must NOT execute target code or scripts locally.
- If runtime behavior verification is required, it must be performed on an isolated machine/sandbox.
- Record whether runtime behavior was tested or not tested in the `runtime_behavior_tested` boolean.
- Any local execution of tools or scripts must use standard safe modes and require separate maintainer approval.
