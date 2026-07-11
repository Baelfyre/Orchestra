# Project State

- **Project Name:** Conductor
- **Active Repo:** `C:\+conductor`
- **Current Branch:** `fix/wave5b-prompt-load-alignment`
- **Base Branch:** `main`
- **Current Release:** `v1.1.1`
- **Target Patch:** `v1.1.2`
- **Current Stable State:** `v1.1.1` tagged and published; Wave 5A implementation and Wave 5B audit merged; Wave 5B reporting alignment completed and pushed for review.
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
- **Pending Next Steps:** Open the Wave 5B pull request, verify GitHub Actions, merge after required review, then realign startup-state files on main before beginning Artificer.
- **Most Recent Checkpoint:** 2026-07-11 - Wave 5B implementation committed and pushed at 03e6abd.

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
