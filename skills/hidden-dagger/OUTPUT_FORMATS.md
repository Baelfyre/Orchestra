# Output Formats

## Caveman

You must output using this strict Caveman format. Keep it concise, focused, and free of unnecessary essays.

```text
TASK TYPE:
RISK LEVEL:
TARGET BOUNDARY:
FAILURE SCENARIO:
CONTROLLED TEST INPUT / FAILURE TRIGGER:
EXPECTED FAILURE OR BEHAVIOR:
SAFETY GATE:
ACME HANDOFF:
CIPHER HANDOFF:
PONYTAIL HANDOFF:
```

### Review and Planning Guidance

For planning, report safety status, target, highest-risk areas, proposed tests, approval required, and next action.

For a full review, report:

1. Safety gate and approved scope
2. System purpose, critical workflows, evidence, and exclusions
3. Confidence and reason
4. Each test: target, condition, expected guardrail, actual result, severity, evidence, fix, and retest
5. Resilience scorecard
6. Confirmed failures, suspected weaknesses, assumptions, missing evidence, and untested areas
7. Highest-risk findings, fix priority, retest plan, and final recommendation

Use Critical, Major, Minor, or Cleanup severity. Never mark a test passed unless it ran and evidence is available.

### Risk Scoring Guidance

Use 0 to 100: 90-100 strong with minor gaps; 75-89 generally strong with targeted fixes; 60-74 moderate with meaningful risk; 40-59 weak with major gaps; 0-39 high risk and failure-prone.

Weight critical workflow impact, safety, data integrity, security and privacy, likelihood, severity, and recovery difficulty. Mark scores provisional when evidence is incomplete.

