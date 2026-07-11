# Session Handoff

- **Current Task:** Wave 5B prompt-load reporting pull-request review and merge
- **Current Repo:** `C:\+conductor`
- **Current Branch:** `fix/wave5b-prompt-load-alignment`
- **Base Branch:** `main`
- **Current Release:** `v1.1.1`
- **Target Patch:** `v1.1.2`
- **Mode:** Wave 5B implementation completed and pushed; awaiting pull-request validation
- **Allowed Files:**
  - `scripts/check_prompt_load_thresholds.py`
  - `docs/performance/PROMPT_LOAD_THRESHOLD_POLICY.md`
  - `docs/performance/PROMPT_LOAD_THRESHOLD_CHECKER.md`
  - `docs/testing/PROMPT_LOAD_THRESHOLD_AUDIT.md`
  - `tests/behavior/test_prompt_load_thresholds.py`
  - `tests/behavior/run_tests.py`
  - `PROJECT_STATE.md`
  - `SESSION_HANDOFF.md`
  - `PROJECT_CONTEXT.md`
  - `docs/MATURITY.md`
  - `docs/project/MANIFEST_SCHEMA.md`
  - `CHANGELOG.md`
- **Forbidden Repo:** `C:\+AA`
- **Last Validation:** All required local validators passed; runtime 43/43 at 95.51% coverage; checker exited `0`; branch is clean and pushed.
- **Known Risks:** Groups A, B, C, and Grand Total exceed documented soft limits; observations are not approved replacement baselines.
- **Next Step:** Open the pull request, verify Validate, Governance Check, and Cross-platform Validation, then merge after review.
- **Fresh-Session Warning:** If the current conversation has long prior history from another repository, enter safe mode and request user confirmation before proceeding with implementation.

## Token Control Note

Use this file to avoid rebuilding context from scratch. Read only what is needed to confirm the active repo, current mode, allowed files, forbidden repos, latest validation, known risks, and next step.

Do not load raw transcripts unless the task specifically requires history debugging.
