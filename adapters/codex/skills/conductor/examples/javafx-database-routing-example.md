# Orchestra Routing Plan

## Project Detection
- Detected Project Type: JavaFX + Maven + relational database application
- Evidence: `pom.xml`, `src/main/java`, JavaFX views and controllers, repository classes, and SQL schema files
- Confidence: High

## User Goal
- Stated Goal: Fix employee-editor layout and verify employment-status persistence.
- Implied Goal: Preserve existing UI structure and database behavior outside the two defects.
- Missing Information: Whether live-database mutation is approved for verification.

## Recommended Skill Stack
### Cloak
- Skill: `cloak`
- Why this skill is needed: Review the JavaFX field layout and focus behavior.
- When to use it: First, limited to the employee editor.
- Expected output: Confirmed UI findings and the smallest layout correction.

### Java/OOP specialist
- Skill: Use the installed Java/OOP reviewer.
- Why this skill is needed: Trace the update path through controller, service, and repository.
- When to use it: After the UI scope is fixed.
- Expected output: Evidence-backed persistence finding or bounded patch.

### Overseer
- Skill: `overseer`.
- Why this skill is needed: Compile and run focused UI or persistence checks.
- When to use it: After implementation.
- Expected output: Build and smoke-test evidence.

## Execution Sequence
### Step 1
- Skill: `cloak`
- Task: Review only the employee editor layout and accessibility.
- Output: Scoped layout recommendation.

### Step 2
- Skill: Java/OOP specialist
- Task: Trace and repair employment-status persistence without schema changes.
- Output: Minimal code change with evidence.

### Step 3
- Skill: `overseer`
- Task: Compile and run the narrowest existing persistence smoke test.
- Output: Pass/fail results and remaining risk.

## Risks and Conflicts
- Overlapping skills: Keep UX findings separate from persistence ownership.
- Missing project context: Live database state is not yet confirmed.
- Possible unsafe actions: Updating live employee records.
- Areas requiring user approval: Any live-data mutation or schema change.

## Local and Git Safety
- Skill and routing-file location: Keep under `~/.codex/skills`, outside the repository.
- Repository impact: No routing or skill files added.
- Git status: Check before recommending a project commit.
- Approval required: Staging, commit, push, PR, or live-data mutation.

## Commands or Prompts to Run
`Use $cloak to review only the EmployeeEditorDialog contact and employment-status layout. Preserve the existing JavaFX theme and report confirmed findings before editing.`

`Review the employment-status update path from controller through repository. Make the smallest safe fix, do not change schema or seed files, then compile and run the existing focused smoke test.`

## Final Recommendation
Use three bounded phases: UI review, persistence implementation, then focused verification.
