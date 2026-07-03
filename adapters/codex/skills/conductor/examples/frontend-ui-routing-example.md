# Orchestra Routing Plan

## Project Detection
- Detected Project Type: React + TypeScript + Vite portfolio frontend
- Evidence: `package.json`, `vite.config.ts`, `tsconfig.json`, `.tsx` components, and shared theme CSS
- Confidence: High

## User Goal
- Stated Goal: Improve navbar reveal behavior on desktop and mobile.
- Implied Goal: Preserve links, page structure, and visual theme.
- Missing Information: Supported mobile breakpoint and desired reduced-motion behavior.

## Recommended Skill Stack
### Cloak
- Skill: `cloak`
- Why this skill is needed: Define discoverability, keyboard, motion, and responsive expectations.
- When to use it: First, scoped to navbar behavior.
- Expected output: Small set of evidence-backed interaction requirements.

### Frontend specialist
- Skill: Use the installed frontend or React specialist.
- Why this skill is needed: Implement the approved behavior in existing components and CSS.
- When to use it: After UX requirements are fixed.
- Expected output: Minimal component and style diff.

## Execution Sequence
### Step 1
- Skill: `cloak`
- Task: Review navbar hide and reveal behavior only.
- Output: Interaction, accessibility, and mobile requirements.

### Step 2
- Skill: Frontend specialist
- Task: Implement the smallest change in the existing navbar and shared theme files.
- Output: Scoped patch.

### Step 3
- Skill: `overseer` when QA evidence is required, otherwise direct project checks
- Task: Run the existing build and inspect representative desktop and mobile widths.
- Output: Build and behavior evidence.

## Risks and Conflicts
- Overlapping skills: UX specifies behavior; frontend owns code.
- Missing project context: Exact supported breakpoints.
- Possible unsafe actions: None beyond unintended layout regression.
- Areas requiring user approval: New dependencies or redesign outside navbar scope.

## Local and Git Safety
- Skill and routing-file location: Global local Codex skills directory.
- Repository impact: Only approved navbar source changes; no skill files.
- Git status: Check before recommending a commit.
- Approval required: Staging, commit, push, or PR.

## Commands or Prompts to Run
`Use $cloak to review the navbar hide and top-edge reveal behavior across desktop and mobile. Preserve existing links and layout; return only confirmed issues and implementation guidance.`

`Implement the approved navbar behavior using existing React and CSS patterns. Do not add dependencies or change unrelated components. Run the repository build afterward.`

## Final Recommendation
Use one UX pass, one bounded frontend change, and existing build plus responsive checks.
