# Session Handoff

- **Current Task:** Artificer Phase 2 internal boundary and contract validation
- **Current Repo:** `C:\+conductor`
- **Canonical Branch:** `main`
- **Base Branch:** `main`
- **Current Release:** `v1.1.1`
- **Target Patch:** `v1.1.2`
- **Mode:** Deterministic internal contract enforcement
- **Allowed Files:**
  - `scripts/validate_artificer_internal.py`
  - `tests/behavior/test_artificer_internal.py`
  - `scripts/governance_check.py`
  - `tests/behavior/run_tests.py`
  - `CHANGELOG.md`
  - `DECISION_LOG.md`
  - `PROJECT_STATE.md`
  - `SESSION_HANDOFF.md`
- **Forbidden Repo:** `C:\+AA`
- **Last Validation:** Behavior suite and runtime pytest suite passed locally.
- **Known Risks:** Prompt-load thresholds remain advisory and current observed Groups A, B, C, and Grand Total exceed documented soft limits; no replacement baseline has been approved.
- **Next Step:** Run the full baseline and merge feat/artificer-internal-boundary-validator
- **Fresh-Session Warning:** If the current conversation has long prior history from another repository, enter safe mode and request user confirmation before proceeding with implementation.

## Token Control Note

Use this file to avoid rebuilding context from scratch. Read only what is needed to confirm the active repo, current mode, allowed files, forbidden repos, latest validation, known risks, and next step.

Do not load raw transcripts unless the task specifically requires history debugging.