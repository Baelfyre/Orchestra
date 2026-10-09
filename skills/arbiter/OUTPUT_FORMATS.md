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

## TransitionDecisionRecord

Use this format when emitting a transition disposition at a delegated phase unit boundary.

```markdown
- schema_version:
- transition_id:
- envelope_id:
- phase_id:
- unit_id:
- governance_decision: APPROVED | ADVISORY_ONLY | REVISION_REQUIRED | BLOCKED | NOT_APPLICABLE
- continuity_result: READY | READY_WITH_MINOR_FIXES | HOLD | BLOCKED
- transition_disposition: AUTO_CONTINUE | AUTO_REMEDIATE_AND_REVALIDATE | WAIT_FOR_EVIDENCE | WAIT_FOR_CAPACITY | ESCALATE_HUMAN | STOP
- reason_code:
- evidence_references:
- remediation_authority:
- remediation_attempt_count:
- next_eligible_unit:
- resume_requirements:
- decision_producer:
- decision_timestamp:
```

## CheckpointRecord

Use this format when creating a checkpoint after an accepted unit.

```markdown
- envelope_id:
- phase_id:
- last_completed_unit:
- next_eligible_unit:
- branch:
- approved_base_sha:
- current_execution_sha:
- working_tree_state: clean | changed
- changed_paths:
- validation_completed:
- validation_remaining:
- known_limitations:
- next_exact_action:
```

## CapacityHandoffRecord

Use this format when recording a resumable capacity wait state.

```markdown
- envelope_validity: VALID | INVALID
- last_completed_unit:
- current_incomplete_unit:
- current_branch:
- current_sha:
- working_tree_state: clean | changed
- uncommitted_changes:
- validation_completed:
- validation_remaining:
- exact_next_action:
- known_blockers:
- resume_prerequisites:
```
