# Orchestra Routing Plan

## Project Detection
- Detected Project Type: Application documentation update
- Evidence: `README.md`, `docs/`, design log, diagrams, and a submission rubric
- Confidence: High

## User Goal
- Stated Goal: Make the README and design log submission-ready.
- Implied Goal: Keep documentation consistent with the implemented project and rubric.
- Missing Information: Whether architecture diagrams also require revision.

## Recommended Skill Stack
### Scribe
- Skill: `scribe`.
- Why this skill is needed: Align structure, setup instructions, evidence, and rubric coverage.
- When to use it: After technical claims are verified.
- Expected output: Focused README and design-log edits.

### Weaver
- Skill: `weaver`, only if diagrams are in scope.
- Why this skill is needed: Check diagram notation, clarity, and consistency with the documented architecture.
- When to use it: Only for named diagrams.
- Expected output: Diagram findings or corrected guidance.

## Execution Sequence
### Step 1
- Skill: Domain specialist or direct read-only inspection
- Task: Verify commands, architecture claims, and current features against source.
- Output: Fact checklist.

### Step 2
- Skill: `scribe`
- Task: Update only rubric-relevant sections using verified facts.
- Output: Concise documentation diff.

### Step 3
- Skill: `weaver`, if required
- Task: Review named diagrams against confirmed architecture.
- Output: Diagram corrections.

## Risks and Conflicts
- Overlapping skills: Documentation owns prose; domain review owns factual verification.
- Missing project context: Diagram submission requirement.
- Possible unsafe actions: Publishing credentials, private paths, or local configuration.
- Areas requiring user approval: New documentation files, tracked agent instructions, commit, push, or PR.

## Local and Git Safety
- Skill and routing-file location: Keep local prompts and routing notes outside the repository.
- Repository impact: Only approved README, design-log, or diagram changes.
- Git status: Show untracked, ignored, modified, and staged files before commit advice.
- Approval required: Adding `AGENTS.md`, `.codex`, `.agents`, skill files, staging, commit, push, or PR.

## Commands or Prompts to Run
`Review README.md, the design log, and the submission rubric. Verify every technical claim against the current project, edit only required sections, and do not add local Codex instructions or new auxiliary documentation.`

## Final Recommendation
Use `scribe` after factual verification; add diagram review only if the rubric requires it.
