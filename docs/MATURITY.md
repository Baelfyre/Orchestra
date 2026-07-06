# Orchestra Project Maturity

This document classifies the current maturity level of Orchestra's features and infrastructure. It helps contributors and users understand the stability of different components and what is planned for the future.

## Stable

* **Skill Structure**: The standard `SKILL.md` format, folder layout, and required metadata are well-defined and validated.
* **Manifest Validation**: The `plugin.json` manifest acts as the single source of truth and is strictly validated against skill contents.
* **Stale-Reference Checks**: Automatic scanning for deprecated naming, legacy roles, and disallowed references.
* **Guardrail Scanning**: Runtime checks for secrets, PII, destructive operations, copyleft licenses, and unsafe expressions.
* **Workspace Locking**: Collision protection and state locking mechanisms via `.amalgam/lock.json`.
* **Python Behavior Validation**: `tests/behavior/run_tests.py` is the primary cross-platform behavior validation runner used by CI.
* **Runtime Coverage Enforcement**: `tests/runtime` is enforced in CI with `pytest-cov` and `--cov-fail-under=90`.

## Beta

* **Governance Instruction Conformance Checks**: Static evaluation of `SKILL.md` instructions against behavioral expectation fixtures (e.g., verifying `BLOCKED`, `HOLD` states are documented).
* **Project Context Governance Validator**: Validates `PROJECT_CONTEXT.md` presence and required sections against advisory, recommended, and strict-governed governance levels. Advisory and recommended paths remain non-blocking by default; strict-governed remains blocking when declared or explicitly requested.
* **Codex Export Validation**: Alignment checks for exports specifically intended for the Codex adapter framework.

## Experimental

* **PowerShell Validation Wrapper**: The legacy `run-tests.ps1` wrapper remains available for Windows-oriented compatibility flows, but it is no longer the primary CI entry point.

## Planned

* **CI Matrix Validation**: Implement continuous integration tests across major platforms (Windows, Linux, macOS) for the Python behavior runner, the runtime coverage gate, and any remaining compatibility wrapper coverage that still matters.
* **Deeper Runtime Behavioral Simulation**: Expand static governance checks into true end-to-end routing simulation to prove real runtime governance decisions.
* **Host-Integrated Enforcement**: Transition from instruction-level and standalone script enforcement to direct host integration blocking capabilities (where feasible).
