# CI/CD Governance Plan

This document outlines the governance validation foundation for the Orchestra repository. These checks will later be enforced by CI/CD (e.g., GitHub Actions) to act as quality and release gates before merging.

## Phase 1 Objectives
* Define required governance checks.
* Implement a non-destructive validation script (`scripts/governance_check.py`).
* Document critical security gaps (e.g., Dagger runtime guardrail).

## Phase 2 Objectives
* Add a script-level Dagger runtime guardrail (`scripts/dagger_guardrail.py`).
* Keep Dagger in simulation-only mode.
* Produce a structured guardrail report for humans and future CI artifacts.
* Preserve the manifest warning until CI/CD wiring exists.

## Phase 3 Objectives
* Create `.github/workflows/governance-check.yml`.
* Configure workflow triggers (`pull_request`, `push` to `main`, `workflow_dispatch`).
* Execute existing validation scripts inside CI.
* Generate and upload a governance report artifact.
* Maintain advisory mode (no deployments, no releases).

## Required Governance Checks

The following checks are part of the initial governance validation plan. In Phase 1-3, they are evaluated in advisory mode (non-blocking for deployments, though safe technical failures will fail the CI check).

### 1. Code & Quality Gates
* **Tests:** Required tests must pass.
* **Documentation:** Required documentation must exist.
* **Changelog:** Changelog or context tracker must be updated when relevant.
* **Local Sync Preflight:** Before starting a new local development phase or repository-editing session, run the preflight sync check against `origin/main`. Do not begin edits if the local branch is behind, diverged, dirty, or unverifiable. Ahead-only state may proceed, but the unpublished commits must be reported.

### 2. Security & Compliance Gates
* **Secrets:** No secrets or forbidden files should be committed.
* **Security Scans:** Security/dependency scan must pass.
* **Optional GESF Audit:** An optional GESF audit score threshold can be enforced as a future enhancement.

### 3. Architecture & Structure Gates
* **Metadata Consistency:** Plugin and manifest metadata (`plugin.json`) must remain consistent and syntactically valid.
* **Skill Structure:** Skill folders must follow the expected structure (`skills/<skill_name>/SKILL.md`).
* **Commands:** Command files must match registered skills.
* **Output Templates:** Output templates must exist for applicable specialists.
* **Output Formats:** Specialist output format must be followed.

## Execution
Validation is currently performed via the non-destructive `scripts/governance_check.py` script plus the simulation-only `scripts/dagger_guardrail.py` validator and `scripts/test_dagger_guardrail.py`.

For local development sessions, run `scripts/preflight_sync_check.py` before editing repository files. This preflight is validation-only: it fetches remote refs, reports sync state, and blocks unsafe local starts, but it does not pull, rebase, reset, merge, stash, or push automatically.

Phase 3 has successfully wired these scripts into an automated GitHub Actions CI workflow (`.github/workflows/governance-check.yml`). The workflow is purely advisory, runs all validation gates on push/PR, and generates a unified report artifact (`governance-validation-report`). Strict release enforcement (Phase 4) and live Dagger promotion are still deferred until Arbiter calibration is complete.
