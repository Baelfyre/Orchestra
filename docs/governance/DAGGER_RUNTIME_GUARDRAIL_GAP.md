# Dagger Runtime Guardrail Gap

## Important Dagger Governance Gap
The current `plugin.json` includes a safety note stating that the destructive Dagger skill (and `resilience-check` command) does not yet have a fully enforced automated runtime guardrail. Phase 2 adds a script-level guardrail, but the manifest warning remains in place until CI/CD and runtime integration are completed.

## Impact
This creates a weak point if Dagger is promoted for broader use. Destructive actions (e.g., negative, fuzz, adversarial QA, and failure-mode testing) should not rely exclusively on manual compliance. Without an automated guardrail, unauthorized or accidentally broad destructive actions could impact project files or environments.

## Required Future Remediation
Before Dagger is promoted or enabled in higher-risk workflows, Orchestra must add CI/CD and runtime wiring around the automated safety gate so destructive operations cannot bypass validation.

## Recommended Future Controls
* Require explicit destructive-action confirmation before execution.
* Require file/path scope validation.
* Block deletion or overwrite outside approved project paths.
* Require dry-run mode before destructive execution.
* Require rollback or backup instructions.
* Log all destructive-action requests and approvals.
* Fail closed when approval or scope is missing.

## Phase 2 Implementation Status
Phase 2 now provides a hardened guardrail in `scripts/dagger_guardrail.py`.

Current behavior:
* resolves the project root dynamically and also accepts `--project-root`
* validates repository-relative target scope
* blocks protected directories and parent traversal
* requires explicit confirmation
* requires rollback instructions
* requires `--dry-run`
* writes a structured JSON report to `artifacts/dagger_guardrail_report.json` by default
* prints a human-readable `DAGGER_GUARDRAIL_RESULT` summary
* blocks live destructive execution

This script is validation-only. It does not execute destructive operations.

**Note:** The safety note in `plugin.json` has NOT been removed. Dagger will remain un-promoted until this automated guardrail is officially wired into the CI/CD pipeline and validated end-to-end.
