# Project State

* **Project Name:** Conductor
* **Active Repo:** `C:\+conductor`
* **Canonical Branch:** `main`
* **Base Branch:** `main`
* **Current Release:** `v1.1.1`
* **Target Patch:** `v1.1.2`
* **Current Stable State:** Artificer Phase 5B-B completed through PR #170
* **Current Task:** Issue #171 governance, prompt-load, and routing recalibration before Phase 5C
* **Mode:** Governed implementation and validation audit
* **Latest Validation:** Complete Issue #171 validation chain passed locally, including integrated behavior, strict governance with 0 errors and 0 warnings, and 43 runtime tests
* **Pending Next Steps:** Maintainer review of the exact unstaged 31-file Issue #171 scope; do not stage, commit, push, create a PR, merge, or begin Phase 5C
* **Most Recent Checkpoint:** 2026-07-12 - Issue #171 canonical governance protocol, routing contracts, and prompt-load baseline implemented locally
* **Related but Forbidden Repo for this task:** `C:\+AA`
* **Active Governance Gates:**

  * Workspace Boundary Gate
  * Session Isolation Gate
  * Audit Mode / No-Edit Gate
  * Record Accuracy Gate
  * Caveman Public-Content Exclusion
  * Ponytail Handoff Restriction
  * Acme Readiness Gate Expansion
* **Current Risks:** Static routing contracts prove policy consistency, not actual model routing accuracy; manual or model-driven routing evidence remains separate.
* **Do-Not-Touch Areas:** Do not edit website repo files from this task (`C:\+AA`).


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
