# Project State

* **Project Name:** Conductor
* **Active Repo:** `C:\+conductor`
* **Canonical Branch:** `main`
* **Base Branch:** `main`
* **Current Release:** `v1.1.1`
* **Target Patch:** `v1.1.2`
* **Current Stable State:** Artificer Phase 2 completed through PR #160.
* **Current Task:** Artificer Phase 3 source-intake and pattern-record instance validation.
* **Latest Validation:** Pending corrected Phase 3 baseline and CI validation.
* **Pending Next Steps:** Complete Phase 3 validation coverage, open the pull request, and verify all GitHub Actions checks.
* **Most Recent Checkpoint:** 2026-07-11 - Initial Phase 3 implementation committed; review identified cross-platform and regression-coverage gaps.
* **Related but Forbidden Repo for this task:** `C:\+AA`
* **Active Governance Gates:**

  * Workspace Boundary Gate
  * Session Isolation Gate
  * Audit Mode / No-Edit Gate
  * Record Accuracy Gate
  * Caveman Public-Content Exclusion
  * Ponytail Handoff Restriction
  * Acme Readiness Gate Expansion
* **Current Risks:** Prompt-load thresholds remain advisory and current observed Groups A, B, C, and Grand Total exceed soft limits; no re-baselining decision exists.
* **Do-Not-Touch Areas:** Do not edit website repo files from this task (`C:\+AA`).
* **Pending Next Steps:** Merge Phase 3 branch `feat/artificer-record-instance-validation` into main.
* **Most Recent Checkpoint:** 2026-07-11 - Phase 3 instance validator completed.

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
