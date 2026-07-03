# Output Formats

## Routing Plan

### Full Orchestration
Use this structure for comprehensive planning. Keep it compact for simple tasks.

```markdown
# Orchestra Routing Plan

## Project Detection
- Detected Project Type:
- Evidence:
- Confidence:

## User Goal
- Stated Goal:
- Implied Goal:
- Missing Information:

## Recommended Skill Stack
### [Skill name or capability]
- Skill:
- Why this skill is needed:
- When to use it:
- Expected output:

## Execution Sequence
### Step 1
- Skill:
- Task:
- Output:

### Step 2
- Skill:
- Task:
- Output:

## Risks and Conflicts
- Overlapping skills:
- Missing project context:
- Possible unsafe actions:
- Areas requiring user approval:

## Local and Git Safety
- Skill and routing-file location:
- Repository impact:
- Git status:
- Approval required:

## Final Recommendation
State the shortest effective workflow.
```

### Compact Routing
For a simple route, use `# Conductor Quick Route` followed by project signal, selected skill, reason, exclusions, approval boundary, and one copy-paste prompt.

## Prompts

Provide copy-paste-ready Codex prompts to execute the defined Routing Plan. Do not include commit, push, PR, install, or destructive commands unless explicitly approved.

## Specialist Reroute

When a specialist refuses out-of-scope work, Conductor must classify the `SPECIALIST_REROUTE_REQUIRED` response and route the task to the correct specialist.

```text
SPECIALIST_REROUTE_REQUIRED

Requested specialist:
Detected task type:
Reason for mismatch:
Recommended specialist:
Supporting specialist:
Required handoff:
Can current specialist proceed: No
Evidence:
Next action:
```
