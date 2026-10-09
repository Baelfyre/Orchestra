# Orchestra Routing Plan

## Project Detection
- Detected Project Type: Full-stack AI collaboration platform
- Evidence: Agent orchestration modules, conversation APIs, web client, authentication middleware, and model-provider configuration
- Confidence: Medium

## User Goal
- Stated Goal: Add shared agent workspaces with role-based access.
- Implied Goal: Preserve tenant isolation and provide understandable collaboration state.
- Missing Information: Tenant model, real-time transport, and existing authorization policy.

## Recommended Skill Stack
### Architecture specialist
- Skill: Use the installed system-architecture specialist.
- Why this skill is needed: Define workspace ownership, agent state, events, and trust boundaries.
- When to use it: Before implementation.
- Expected output: Confirmed component and authorization boundaries.

### Cipher
- Skill: `cipher`; add Codex Security only for source-level vulnerability analysis.
- Why this skill is needed: Review tenant isolation, RBAC evidence, prompt inputs, privacy, and secrets handling.
- When to use it: On the affected design and evidence; use a scanner on the affected diff only when requested.
- Expected output: Evidence-based risks and defensive remediation.

### Cloak
- Skill: `cloak`
- Why this skill is needed: Review workspace roles, agent status, errors, and collaboration flow.
- When to use it: After boundaries are known and before UI implementation.
- Expected output: UX flow and architecture-diagram review.

## Execution Sequence
### Step 1
- Skill: Architecture specialist
- Task: Map workspace, tenant, agent, and event ownership from current code.
- Output: Current-state architecture and required decisions.

### Step 2
- Skill: `cipher`
- Task: Review authorization, tenant isolation, secrets, and privacy evidence in the affected scope.
- Output: Validated security requirements.

### Step 3
- Skill: `cloak`
- Task: Review the collaboration flow using confirmed roles and states.
- Output: Prioritized UX findings.

### Step 4
- Skill: `overseer`
- Task: Define tenant-isolation, concurrency, failure, and cancellation checks.
- Output: Focused verification plan.

## Risks and Conflicts
- Overlapping skills: Architecture defines ownership; security validates abuse paths; UX owns interaction clarity.
- Missing project context: Current authorization and real-time architecture.
- Possible unsafe actions: Production provider calls or tenant-data mutation.
- Areas requiring user approval: New dependencies, schema changes, deployments, and production testing.

## Local and Git Safety
- Skill and routing-file location: Keep prompts and routing notes under the local Codex environment.
- Repository impact: Add only approved product code or documentation.
- Git status: Show before any commit recommendation.
- Approval required: Staging, commit, push, PR, deployment, or local Codex files in Git.

## Commands or Prompts to Run
`Inspect the current workspace, tenant, agent, and event boundaries. Produce a current-state architecture review only; do not implement or add dependencies.`

`Use $cipher to review RBAC, tenant-isolation, secrets, and privacy evidence. Add a scoped Codex Security scan only if source-level vulnerability analysis is required.`

## Final Recommendation
Resolve ownership and authorization first, then review UX and tests; do not start with UI implementation.
