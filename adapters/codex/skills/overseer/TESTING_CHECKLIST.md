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

## Contract and End-to-End Testing
- [ ] Contract evidence names provider/consumer version, schema or protocol revision, compatibility direction, and negative cases.
- [ ] E2E coverage is limited to critical cross-boundary journeys and does not duplicate cheaper evidence without reason.
- [ ] Test doubles preserve the behavior relevant to the risk and do not hide serialization, transaction, auth, or network semantics.

## Property, Mutation, and Coverage
- [ ] Property tests state the invariant, generator domain, bounds, seed/replay method, and minimized counterexample behavior.
- [ ] Mutation testing targets risk-bearing logic and reports survived, killed, invalid, timeout, and uncovered mutants distinctly.
- [ ] Coverage type, exclusions, generated code, changed lines, critical untested behavior, and residual risk are interpreted with the percentage.

## Flaky Tests and Isolation
- [ ] Failure signature, frequency, first failing attempt, environment, timing, seed, ordering, and shared-state evidence are captured.
- [ ] Retries do not erase the initial failure and quarantine has owner, issue, expiry, and visible non-passing status.
- [ ] Time, randomness, concurrency, locale, network, ports, queues, caches, database state, and parallel-worker identifiers are controlled where relevant.

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
- [ ] Data provenance, factory/fixture version, uniqueness, setup/reset, retention, redaction, and disposal are defined.
- [ ] Synthetic data preserves required relationships and distributions without copying sensitive credentials or personal records.

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
- [ ] Job dependencies, matrix dimensions, shard identity, cache keys, artifact retention, cancellation, and skipped-cell visibility are explicit.
- [ ] Supported OS/runtime/browser/device combinations are covered by risk or documented as residual gaps.

## Performance Acceptance
- [ ] Workload, warm-up, steady window, sample size, percentiles, throughput/error constraints, environment, baseline tolerance, and stop conditions are explicit.
- [ ] Generator saturation, background noise, caching state, and regression significance are interpreted before pass/fail.

## Release Readiness
- [ ] Required gates passed with evidence or have approved waivers.
- [ ] Blockers, not-run checks, residual risks, and approval ownership are explicit.
