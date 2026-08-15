# Third-Party Provenance and Acknowledgements

This document records external projects, tools, standards, and repositories used or consulted during Orchestra development so that implementation provenance is transparent to maintainers, reviewers, users, and automated repository-analysis tools.

## Provenance policy

Every external item used by Orchestra must be classified as one of the following:

- **TEST_TOOL_DEPENDENCY** — installed only for development, validation, CI, or release-confidence work; not shipped as Orchestra runtime code.
- **REFERENCE_ONLY** — documentation, architecture, protocol, or implementation ideas were consulted, but the project is not incorporated as a dependency and its source is not copied into Orchestra.
- **INTEGRATED_RUNTIME_DEPENDENCY** — a third-party package or component is required by Orchestra at runtime.
- **VENDORED_OR_COPIED_CODE** — third-party source is copied, adapted, or vendored into the repository. This classification requires an explicit source reference, applicable license/notice preservation, and a clear description of modifications.

The absence of an item from this file must not be interpreted as permission to copy or vendor its source. New third-party incorporation should update this document and the machine-readable registry in the same change.

## Current re-foundation tooling

### mutmut 3.6.0

- Classification: **TEST_TOOL_DEPENDENCY**
- Purpose: bounded mutation testing of Orchestra trust-boundary modules during release-confidence hardening.
- Upstream project: `boxed/mutmut`
- Installed version: `3.6.0`
- License: BSD-3-Clause
- Runtime incorporation: **No**
- Source copied or vendored into Orchestra: **No**
- Adapted upstream source: **No**
- Orchestra integration surface: `.github/workflows/mutation-confidence.yml`, `setup.cfg`, and Orchestra-owned mutation evidence tooling.
- Notes: Orchestra invokes the published package as an external CI tool. Current mutation-confidence work also records tool failures as evidence rather than treating workflow completion as a mutation-quality PASS.

### Hypothesis 6.163.0

- Classification: **TEST_TOOL_DEPENDENCY**
- Purpose: property-based testing of machine-contract and governance invariants.
- Upstream project: `HypothesisWorks/hypothesis`
- Installed version in the mutation-confidence workflow: `6.163.0`
- License: MPL-2.0
- Runtime incorporation: **No**
- Source copied or vendored into Orchestra: **No**
- Adapted upstream source: **No**
- Orchestra integration surface: property-based tests under `tests/runtime/` and CI test environments.

## Evaluated but not incorporated

The re-foundation architecture has also evaluated external technologies and standards for potential future use. Evaluation does not make them Orchestra dependencies or authority sources. Examples include policy engines, sandbox technologies, MCP transport patterns, structured-output frameworks, and schema tooling discussed in architecture records. Any future incorporation must be promoted into the machine-readable provenance registry with an exact role, version or revision where applicable, and license/provenance review.

## Source-use rule

Orchestra's current re-foundation implementation is Orchestra-authored code. No source from the external projects listed above has been copied or vendored into the repository as part of this work. When external documentation or behavior informs an Orchestra design decision, the external project remains a reference/tool unless the repository explicitly records otherwise.

## Machine-readable counterpart

Canonical machine-readable third-party provenance is stored at:

`machine/provenance/third-party.v1.json`

Its schema is:

`machine/schemas/third-party-provenance.schema.json`
