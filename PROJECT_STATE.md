# Project State

* **Project Name:** Conductor
* **Active Repo:** `C:\+conductor`
* **Canonical Branch:** `main`
* **Base Branch:** `main`
* **Current Release:** `v1.1.1`
* **Target Patch:** `v1.1.2`
* **Current Stable State:** Phase 3 Artificer Source-Intake and Pattern-Record Instance Validator implemented successfully and behavior-tested.
* **Current Task:** Awaiting Phase 3 merge and transition to next development sequence.
* **Related but Forbidden Repo for this task:** `C:\+AA`
* **Latest Validation:** Passed `validate_artificer_records.py` with 50 tests via `tests/behavior/run_tests.py` and strict governance.
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
