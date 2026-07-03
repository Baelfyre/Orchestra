# Testing Checklist

## Requirements Testability
- [ ] Requirement is specific, observable, bounded, and linked to an objective.
- [ ] Dependencies and error behavior are explicit.

## Acceptance Criteria
- [ ] Criteria state conditions, action, and expected outcome.
- [ ] Boundary, permission, failure, and recovery behavior are included when relevant.

## Unit Testing
- [ ] Critical branches, boundaries, and errors are covered at the smallest useful scope.
- [ ] Tests avoid unnecessary implementation coupling.

## Integration Testing
- [ ] Interfaces, data contracts, transactions, and dependency failures are covered.

## System Testing
- [ ] Critical end-to-end workflows run in a representative environment.

## User Testing and UAT
- [ ] Participant roles match intended user groups.
- [ ] Task scenarios map to user goals and acceptance criteria.
- [ ] Observed behavior, issues, severity, and evidence are recorded without inventing feedback.
- [ ] Stakeholder acceptance is tied to explicit criteria and approval authority.

## Smoke Testing
- [ ] Critical availability paths are short, stable, and run after relevant builds or deployments.

## Regression Testing
- [ ] Coverage maps to changed code, dependencies, defect history, and critical workflows.
- [ ] Residual risk is documented.

## Test Case Structure
- [ ] Identifier, objective, requirement link, level, priority, and owner are present when useful.

## Preconditions
- [ ] Required state, permissions, dependencies, and setup are explicit.

## Test Data
- [ ] Data covers valid, invalid, boundary, and permission scenarios without exposing sensitive information.

## Test Environment
- [ ] Revision, platform, configuration, services, and database state are identifiable.

## Expected Results
- [ ] Expected behavior is observable and unambiguous.

## Actual Results
- [ ] Actual behavior and evidence are captured only after execution.

## Pass/Fail Criteria
- [ ] Outcome rules are objective and applied consistently.

## Defect Reproducibility
- [ ] Steps, frequency, environment, expected and actual behavior, and evidence are actionable.

## Evidence Capture
- [ ] Logs, reports, screenshots, or traces support the conclusion and exclude secrets.

## CI Checks
- [ ] Trigger, scope, environment, failure visibility, retry behavior, and required status are understood.

## Release Readiness
- [ ] Required gates passed with evidence or have approved waivers.
- [ ] Blockers, not-run checks, residual risks, and approval ownership are explicit.
