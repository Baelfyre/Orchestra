# Output Formats

## Continuity Review

Use this format for handoff, branch, merge, interruption, workspace-transition, source-of-truth, and validation-state reviews.

```markdown
## Workflow Status
- Current Phase:
- Current Milestone:
- Overall Status:

## Completed
- Verified completed work:

## In Progress
- Active work:

## Remaining
- Next tasks:

## Risks
- Technical:
- Merge:
- Architecture:
- Validation:
- Workflow:

## Validation Summary
- Build Status:
- Test Status:
- Documentation Status:
- Branch Status:
- Configuration Status:
- Merge Readiness:

## Continuation Package
- Current Objective:
- Current Implementation Point:
- Source of Truth:
- Next Recommended Task:
- Known Blockers:
- Dependencies:
- Important Notes:

## Access / Visibility Closeout (Optional)
- Expected Actor:
- Expected Authority Source:
- Actual Authority Source Found:
- Positive Persona Proof:
- Negative Persona Proof:
- Edge-Case Persona Proof:
- Navigation Visibility:
- Direct Route / Screen Switching:
- Backend / Service Authorization:
- Gap Type: policy | data | validation | mixed
- Workaround or Durable Fix:
- Unsupported Cases:
- Final Closeout Decision:

## Final Verdict
READY | READY_WITH_MINOR_FIXES | HOLD | BLOCKED

Justification:
```

Keep entries evidence-based. Use `NOT FOUND` when expected evidence is absent and `NEEDS VERIFICATION` when evidence is unclear.

## Governance Effectiveness Review

Use this format for governance layer calibration, CI governance report interpretation, advisory workflow review, and governance-readiness reviews.

```markdown
Result:
READY | READY_WITH_MINOR_FIXES | READY_WITH_REQUIRED_FIXES | BLOCKED

Critical findings:
- Severity:
- File path:
- Function/component:
- Evidence:
- Reason:
- Minimal remediation:

Major findings:
- Severity:
- File path:
- Function/component:
- Evidence:
- Reason:
- Minimal remediation:

Minor findings:
- Severity:
- File path:
- Function/component:
- Evidence:
- Reason:
- Minimal remediation:

Cleanup findings:
- Severity:
- File path:
- Function/component:
- Evidence:
- Reason:
- Minimal remediation:

Validation run:
- Command:
- Result:

Final recommendation:
- Merge readiness:
- CI readiness:
- Dagger safety status:
- Next action:
```

Rules:

- Use `READY_WITH_REQUIRED_FIXES` for major advisory governance gaps that should be corrected before stricter enforcement, but do not currently justify a hard block.
- Use `BLOCKED` only for unsafe destructive behavior, missing or bypassed critical guardrails, or broken governance execution that prevents review.
- Keep Dagger safety conclusions evidence-based and do not report live execution risk when the runtime guardrail is still simulation-only and fail-closed.
- Do not describe advisory CI output as unconditional success when warnings, deferred checks, or non-blocking findings exist.
