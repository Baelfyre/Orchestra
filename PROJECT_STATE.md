# Project State

- **Project Name:** Conductor
- **Active Repo:** `C:\+conductor`
- **Current Branch:** `audit/artificer-internal-architecture`
- **Base Branch:** `main`
- **Current Release:** `v1.1.1`
- **Target Patch:** `v1.1.2`
- **Current Stable State:** `Wave 5B merged`
- **Related but Forbidden Repo for this task:** `C:\+AA`
- **Latest Validation:** Structure, manifest, stale-reference, strict governance, Codex export, behavior, focused prompt-load regression, runtime, and checker validations passed; runtime: 43 tests passed with 95.51% coverage; prompt-load checker exited `0`.
- **Active Governance Gates:**
  - Workspace Boundary Gate
  - Session Isolation Gate
  - Audit Mode / No-Edit Gate
  - Record Accuracy Gate
  - Caveman Public-Content Exclusion
  - Ponytail Handoff Restriction
  - Acme Readiness Gate Expansion
- **Current Risks:** Prompt-load thresholds remain advisory and current observed Groups A, B, C, and Grand Total exceed soft limits; no re-baselining decision exists.
- **Do-Not-Touch Areas:** Do not edit website repo files from this task (`C:\+AA`).
- **Current Task:** Artificer internal architecture audit and specification
- **Pending Next Steps:** Create the Artificer audit-first branch
- **Most Recent Checkpoint:** 2026-07-11 - Post-Wave 5B main realignment.

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
