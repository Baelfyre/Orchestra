# Promotion Record: Optional Unit Worktree Standard (OrchestraWorktreeContract)

```text
Record ID: PROM-SPEC-KITTY-005
External source: https://github.com/Priivacy-ai/spec-kitty
External source commit: 8466727ebbbc01fcaf43575657c9b1b9553784d9 (v3.2.6)
External source paths reviewed: src/kernel/, .worktrees/
Concept name: Optional Unit Worktree Standard (OrchestraWorktreeContract)
External observation: Spec Kitty automatically isolates each work package in a dedicated git worktree (`.worktrees/<wp_id>`) to enable parallel execution and clean branch isolation.
Verified Orchestra gap: Orchestra lacks a standard host/adapter contract for creating, verifying, and tearing down temporary git worktrees during parallel unit execution.
Why the current Orchestra contract is insufficient: When multi-agent hosts run units concurrently on the same workspace directory, uncommitted edits can pollute parallel unit execution paths.
Proposed Orchestra-native adaptation: Define `OrchestraWorktreeContract` as an optional host/adapter capability (`HOST_CAPABILITY_DEPENDENT` / `OPTIONAL`) specifying workspace creation (`git worktree add`), base SHA verification, clean status checks, and cleanup hooks (`git worktree remove`).
Canonical Orchestra owner: Ponytail (implementation), Host Adapters
Affected specialists: Conductor, Arbiter, Overseer
Authority implications: None. Worktree isolation is a local workspace management mechanism.
Capability implications: Allows multi-agent host adapters (e.g. Codex/Claude orchestrators) to run parallel units safely without branch drift.
Governance implications: Worktree base SHA must match the approved plan base SHA; dirty worktrees are prohibited before unit completion.
Delegation implications: Adapters declare `worktree_supported: true/false` in adapter metadata.
Coordination implications: Isolates specialist file access per execution unit.
Lifecycle implications: Executed during unit initialization and unit cleanup.
Validation implications: Preflight check `python scripts/preflight_sync_check.py` must run clean inside worktrees.
Audit and evidence implications: Include `worktree_path` and `worktree_base_sha` in `ExecutionEvidencePacket`.
Privacy and retention implications: Worktrees must be located inside repo root or git ignored paths (`.orchestra/worktrees/`) to prevent leaking code to untracked surfaces.
Compatibility implications: Optional contract; single-workspace executions continue to operate normally.
Migration requirements: None; optional capability.
Rejected copied elements: Mandating worktree creation for all execution units (rejected as overly restrictive for simple local runs).
License and attribution requirements: Conceptual adaptation; no code copied.
Risks: Stale worktree accumulation if cleanup hooks fail.
Non-goals: Making worktrees mandatory for single-agent execution.
Recommended next phase: Candidate Phase 1A (Architecture Ownership & Contract Placement)
Promotion recommendation: ADAPT_LATER
Confidence: Medium (85%)
Open questions: Should worktree management be implemented in host adapters or Python scripts in `scripts/`?
```
