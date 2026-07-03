# Session Handoff

- **Current Task:** Codex adapter governance export validation fix
- **Current Repo:** `C:\conductor`
- **Mode:** Implementation with targeted adapter, validation, guardrail, and repo-memory updates
- **Allowed Files:**
  - `adapters/codex/export-codex-skills.ps1`
  - `adapters/codex/validate_codex_export.py`
  - `scripts/refresh-installed-integrations.ps1`
  - `scripts/runtime_guardrail.py`
  - `scripts/governance_check.py`
  - `scripts/test_governance_check.py`
  - `SESSION_HANDOFF.md`
  - `PROJECT_STATE.md`
  - `DECISION_LOG.md`
- **Forbidden Repo:** `C:\+AA`
- **Last Validation:** Preflight passed on branch `fix/codex-governance-export-validation`; full validation pending after implementation.
- **Known Risks:** Potential context drift if previous session history is long.
- **Next Step:** Regenerate Codex adapter export, run required validation matrix, and review git diff.
- **Fresh-Session Warning:** If the current conversation has long prior history from another repository, enter safe mode and request user confirmation before proceeding with implementation.

## Token Control Note

Use this file to avoid rebuilding context from scratch. Read only what is needed to confirm the active repo, current mode, allowed files, forbidden repos, latest validation, known risks, and next step.

Do not load raw transcripts unless the task specifically requires history debugging.
