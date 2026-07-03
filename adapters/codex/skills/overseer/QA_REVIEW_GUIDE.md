# QA Review Guide

## Review a Test Plan

1. Confirm objective, scope, exclusions, quality risks, test levels, environment, data, responsibilities, schedule, entry and exit criteria, and evidence strategy.
2. Map planned tests to requirements and high-risk changes.
3. Flag unsupported coverage claims and missing dependencies.

## Review Test Cases

1. Confirm purpose, requirement link, preconditions, data, steps, expected result, and pass/fail criteria.
2. Check positive, negative, boundary, permission, recovery, and state-transition cases only where relevant.
3. Remove duplicate cases that do not add risk coverage.

## Review Acceptance Criteria

- Require observable outcomes and one clear obligation per criterion.
- Resolve vague terms, hidden assumptions, and conflicting conditions.
- Include critical failure and permission behavior.

## Review Regression Risk

- Trace the changed surface through callers, dependencies, data, configurations, and user workflows.
- Prioritize critical paths and prior defect areas.
- Record omitted coverage and residual risk.

## Triage Defects

- Confirm reproducibility, evidence, impact, affected scope, frequency, environment, and workaround.
- Separate severity from scheduling priority.
- Do not assign root cause without supporting evidence.

## Evaluate Release Readiness

- Compare required gates with actual evidence.
- Distinguish passed, failed, blocked, skipped, waived, and not run.
- Identify release blockers and the owner authorized to accept residual risk.

## Avoid Unsupported Test Claims

- Never infer a pass from test existence, compilation, screenshots without context, or absent failures.
- State the exact evidence and revision supporting each result.
- Mark stale or mismatched reports.

## Ask for Missing Evidence

Ask only when the missing requirement, environment, result, defect evidence, or gate definition materially changes the decision. Otherwise, document the gap and proceed with limited confidence.

## Stop and Require Approval

Require approval before editing test files, changing CI or release configuration, running costly or destructive tests, mutating production data, deploying, publishing a release, or waiving a gate.
