# Project State

- **Project Name:** Conductor
- **Active Repo:** `C:\conductor`
- **Current Branch:** `chore/readme-release-snapshot-metrics`
- **Base Branch:** `main`
- **Current Release:** `v1.1.0`
- **Target Patch:** `v1.1.1`
- **Current Stable State:** `v1.1.0` tagged and published; `main` is clean and aligned; post-release hardening in progress
- **Related but Forbidden Repo for this task:** `C:\+AA`
- **Latest Validation:**
  - `python scripts/preflight_sync_check.py` passed with `PROCEED` on `main` at `v1.1.0`
  - Runtime: 42 tests passed, 95.51% coverage
  - Behavior: passed
  - Governance strict: passed
  - All metadata validators: passed
- **Active Governance Gates:**
  - Workspace Boundary Gate
  - Session Isolation Gate
  - Audit Mode / No-Edit Gate
  - Record Accuracy Gate
  - Caveman Public-Content Exclusion
  - Ponytail Handoff Restriction
  - Acme Readiness Gate Expansion
- **Current Risks:** Release-surface and startup-state drift identified in post-release audit.
- **Do-Not-Touch Areas:** Do not edit website repo files from this task (`C:\+AA`).
- **Pending Next Steps:** Complete Wave 1 remediation (release-surface alignment, startup-state refresh, governance hardening), validate, and prepare PR.
- **Most Recent Checkpoint:** 2026-07-10 - Wave 1 release-surface and startup-state drift remediation.

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
