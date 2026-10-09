# Routing Plan

## Detected task
- Evidence:
- Goal:

## Minimal skill stack
1. Skill:
   - Owned output:

## Sequence
## Overlap removed
## Approval boundaries
## Copy-paste prompt

## Specialist Reroute

Use this format when a specialist receives a request outside its documented scope. The specialist must not execute the out-of-scope task.

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

### Contract Rules

- Use when the requested specialist is clearly not the right owner.
- The wrong specialist must not perform the out-of-scope task.
- The wrong specialist may provide only routing, clarification, or handoff guidance.
- If the correct specialist is unclear, route to Conductor.
- If the task is multi-specialist, identify the primary specialist and supporting specialist.
- If the task is safety-sensitive or destructive, route through Dagger guardrail requirements and Arbiter review.
