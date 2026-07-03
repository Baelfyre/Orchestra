# Project State

- **Project Name:** Conductor
- **Active Repo:** `C:\conductor`
- **Current Branch:** `fix/codex-governance-export-validation`
- **Current Stable State:** Local branch synced with `origin/main`; Codex adapter export validation fix in progress
- **Related but Forbidden Repo for this task:** `C:\+AA`
- **Latest Validation:**
  - `python scripts/preflight_sync_check.py` passed with `PROCEED`
  - Full post-change validation pending
- **Active Governance Gates:**
  - Workspace Boundary Gate
  - Session Isolation Gate
  - Audit Mode / No-Edit Gate
  - Record Accuracy Gate
  - Caveman Public-Content Exclusion
  - Ponytail Handoff Restriction
  - Acme Readiness Gate Expansion
- **Current Risks:** Cross-repo context drift from long-running sessions.
- **Do-Not-Touch Areas:** Do not edit website repo files from this task (`C:\+AA`).
- **Pending Next Steps:** Regenerate Codex adapter export and run the required validation matrix.
- **Most Recent Checkpoint:** 2026-07-03 - Started Codex adapter governance export validation fix.

## Token Efficiency Rationale

These project memory files are intended to reduce token waste by avoiding repeated prompts, repeated context reconstruction, and repeated correction cycles.

The goal is not to store full conversation history. The goal is to preserve only the latest validated project state, active constraints, approved decisions, known risks, and next steps.

A small curated state file should help future chats, agents, and plugin sessions:

* confirm the active repository faster
* avoid cross-repo drift
* avoid stale assumptions
* reduce repeated explanations
* reduce accidental edits
* improve factual and implementation accuracy

These files must remain concise. If they become raw transcript logs or long historical dumps, they will increase token usage instead of reducing it.
