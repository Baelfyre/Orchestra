# Session Handoff

- **Current Task:** Add lightweight project memory files
- **Current Repo:** `C:\conductor`
- **Mode:** Implementation with limited file creation
- **Allowed Files:**
  - `PROJECT_STATE.md`
  - `SESSION_HANDOFF.md`
  - `DECISION_LOG.md`
  - `.amalgam/state.json`
  - `skills/amalgam-conductor/SKILL.md`
- **Forbidden Repo:** `C:\+AA`
- **Last Validation:** Manifest and structure validation passed prior to memory file implementation.
- **Known Risks:** Potential context drift if previous session history is long.
- **Next Step:** Validate structure and manifest after changes.
- **Fresh-Session Warning:** If the current conversation has long prior history from another repository, enter safe mode and request user confirmation before proceeding with implementation.

## Token Control Note

Use this file to avoid rebuilding context from scratch. Read only what is needed to confirm the active repo, current mode, allowed files, forbidden repos, latest validation, known risks, and next step.

Do not load raw transcripts unless the task specifically requires history debugging.
