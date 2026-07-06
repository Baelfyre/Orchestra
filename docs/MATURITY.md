# Orchestra Project Maturity

This document classifies the current maturity level of Orchestra's features and infrastructure. It helps contributors and users understand the stability of different components and what is planned for the future.

## Stable

* **Skill Structure**: The standard `SKILL.md` format, folder layout, and required metadata are well-defined and validated.
* **Manifest Validation**: The `plugin.json` manifest acts as the single source of truth and is strictly validated against skill contents.
* **Stale-Reference Checks**: Automatic scanning for deprecated naming, legacy roles, and disallowed references.
* **Guardrail Scanning**: Runtime checks for secrets, PII, destructive operations, copyleft licenses, and unsafe expressions.
* **Workspace Locking**: Collision protection and state locking mechanisms via `.amalgam/lock.json`.
* **PowerShell Validation**: The legacy PowerShell `run-tests.ps1` validation suite provides a robust, primary validation path for Windows environments.

## Beta

* **Governance Instruction Conformance Checks**: Static evaluation of `SKILL.md` instructions against behavioral expectation fixtures (e.g., verifying `BLOCKED`, `HOLD` states are documented).
* **Project Context Governance Validator**: Validates `PROJECT_CONTEXT.md` presence and required sections against advisory, recommended, and strict-governed governance levels. Advisory and recommended paths remain non-blocking by default; strict-governed remains blocking when declared or explicitly requested.
* **Codex Export Validation**: Alignment checks for exports specifically intended for the Codex adapter framework.

## Experimental

* **Python Cross-Platform Validation Runner**: A native Python port of the validation suite intended to provide true cross-platform parity without requiring PowerShell Core. This remains experimental until CI processes prove parity across Windows, Linux, and macOS.

## Planned

* **CI Matrix Validation**: Implement continuous integration tests across major platforms (Windows, Linux, macOS) for both the PowerShell and Python validation runners.
* **Deeper Runtime Behavioral Simulation**: Expand static governance checks into true end-to-end routing simulation to prove real runtime governance decisions.
* **Host-Integrated Enforcement**: Transition from instruction-level and standalone script enforcement to direct host integration blocking capabilities (where feasible).
