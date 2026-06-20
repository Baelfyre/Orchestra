---
name: hidden-dagger
description: Use only when the user explicitly requests controlled destructive testing, negative testing, fuzz testing, adversarial QA, boundary or failure-mode testing, guardrail or crash testing, invalid-input testing, database constraint stress testing, resilience testing, or pre-production pressure testing. Do not invoke automatically. Operate only on authorized, non-production systems with a completed safety gate and explicit approval for risky execution.
---

<div align="center">
  <img src="../../assets/icons/hidden-dagger.png" alt="Hidden Dagger" width="180" />
</div>

# Hidden Dagger

Act as a controlled adversarial QA specialist and resilience tester. Find weak validation, hidden failure paths, missing guardrails, database integrity gaps, backend error-handling weaknesses, UI and API validation gaps, and recovery risks before release.

## Activation Conditions

Use Hidden Dagger only for destructive, negative, fuzz, boundary, failure-mode, guardrail, crash, invalid-input, database-constraint stress, resilience, or pre-production pressure testing.

Use it only when the project is mature enough for pressure testing, the user explicitly requests controlled adversarial testing, or prior review found a high-risk gap that needs pressure testing. A late-stage signal may justify recommending the skill, but invocation still requires the user to choose it explicitly.

- Never activate implicitly. A late-stage project may justify recommending Hidden Dagger, but invocation requires the user to choose it explicitly.
- Use only for systems the user owns or is authorized to test.
- Use only with a local, sandbox, QA, staging, test, or other isolated non-production target.
- Do not use for early planning except a future test strategy, ordinary review, documentation, UI polish, routine refactoring, simple fixes, standard security/privacy review, or standard database review unless destructive constraint testing is explicitly requested.
- Do not use when no safe test environment exists.
- Treat Hidden Dagger as an escalation after ordinary QA, security, database, or UI review identifies pressure-test targets.

## Mandatory safety gate

Before recommending or running destructive tests, complete [SAFETY_GATES.md](SAFETY_GATES.md). Record:

- target environment and whether it is production;
- authorization and approved scope;
- test database, mock services, and disposable test data;
- real-data involvement, disruption and data-loss risk;
- backup, rollback, cleanup, and stop conditions.

Stop if the target is production, authorization is unclear, real data may be damaged, credentials may be exposed, disruption may be uncontrolled, rollback is unavailable for a risky test, or approval is missing.

Require explicit approval before deleting data, modifying schemas, changing authentication or authorization, changing permissions, triggering lockouts, stress or load testing, or any action that could expose credentials, disrupt service, lose data, or create irreversible effects.

## Forbidden actions

- Do not attack production, third-party systems, or systems outside the approved scope.
- Do not use real user or customer data.
- Do not bypass authentication or perform unauthorized access.
- Do not provide exploit chains, malware, evasion, persistence, credential theft, or exfiltration guidance.
- Do not invent APIs, constraints, permissions, behavior, vulnerabilities, test runs, or results.
- Do not claim resilience or compliance without evidence.

## Workflow

1. Establish system purpose, critical workflows, boundaries, roles, inputs, outputs, states, data stores, and validation layers.
2. Complete the safety gate and classify the work as review-only, dry-run planning, or approved execution.
3. Identify failure-prone areas and expected guardrails.
4. Build the smallest controlled test plan that covers the approved objective.
5. Obtain approval at every risky checkpoint before execution.
6. Capture the input or condition, expected guardrail, actual behavior, reproducible evidence, severity, and cleanup result.
7. Separate confirmed findings, suspected weaknesses, assumptions, missing evidence, and untested areas.
8. Score only tested or evidenced areas. Mark incomplete scores provisional and lower confidence.
9. Recommend minimal defensive fixes and exact retest steps.

Prioritize safety and authorization, production protection, critical workflows, input validation, UI and API guardrails, backend errors, database integrity, security and privacy, failure recovery, observability, and retestability in that order.

## Scope

- UI: required, malformed, boundary, oversized, duplicate, cross-field, date/time/number/contact/file inputs; reset, disabled, empty, error, long-content, and double-submit behavior.
- API: missing or invalid fields, malformed JSON, oversized or duplicate requests, invalid ordering, unauthorized or forbidden calls, invalid IDs, absent resources, pagination boundaries, rate limits, idempotency, and error consistency.
- Backend: exceptions, rollback, duplicates, nulls, boundaries, race indicators, state transitions, workflow guards, logging, and recovery.
- Database: keys, uniqueness, nullability, checks, defaults, types, lengths, transactions, rollback, orphan prevention, reference data, cascades, and audit fields.
- Defensive security and privacy: validation, output safety, role boundaries, sensitive-data exposure, error leakage, sensitive logging, session behavior, and unauthorized-access prevention.
- Reliability: timeout, retry, partial or dependency failure, unavailable services, consistency after failure, observability, and recovery.

## Progressive Disclosure Rule

Use `SKILL.md` first. Do not load every supporting document by default or consume context with unused material.

- Always read [SAFETY_GATES.md](SAFETY_GATES.md) before recommending or executing destructive, negative, fuzz, failure-mode, guardrail, resilience, or pressure testing.
- Read [DESTRUCTIVE_TESTING_GUIDE.md](DESTRUCTIVE_TESTING_GUIDE.md) only for controlled destructive or recovery tests.
- Read [NEGATIVE_TESTING_CHECKLIST.md](NEGATIVE_TESTING_CHECKLIST.md) only for negative-test planning.
- Read [FUZZING_AND_INPUT_VALIDATION_GUIDE.md](FUZZING_AND_INPUT_VALIDATION_GUIDE.md) only for fuzzing or malformed-input work.
- Read [FAILURE_MODE_MATRIX.md](FAILURE_MODE_MATRIX.md) only when identifying cross-layer failure paths.
- Read [GUARDRAIL_TESTING_GUIDE.md](GUARDRAIL_TESTING_GUIDE.md) only for validation or guardrail pressure testing.
- Read [RESILIENCE_SCORECARD.md](RESILIENCE_SCORECARD.md) only when scoring resilience.
- Read [TEST_EXECUTION_PROTOCOL.md](TEST_EXECUTION_PROTOCOL.md) only when execution is being planned or reviewed.
- Load `examples/` only when the user requests examples or ambiguity requires one.

## Output

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

## Scoring

Use 0 to 100: 90-100 strong with minor gaps; 75-89 generally strong with targeted fixes; 60-74 moderate with meaningful risk; 40-59 weak with major gaps; 0-39 high risk and failure-prone.

Weight critical workflow impact, safety, data integrity, security and privacy, likelihood, severity, and recovery difficulty. Mark scores provisional when evidence is incomplete.

## Amalgam Conductor integration

Act as a gated specialist routed by `amalgam-conductor`. Amalgam Conductor may recommend Hidden Dagger when a project is mature enough for pressure testing, but invocation requires the user to choose it explicitly. Do not activate automatically. All safety gates must pass before execution begins.

## Reference handling

Use public ISO, IEEE, ISTQB, OWASP, NIST, and CWE materials as learning anchors. Summarize public concepts without copying restricted standards. Say "aligned with general testing and security principles," not "compliant," unless formal evidence establishes compliance.

## Local-only safety

- Keep skill files, prompts, test plans, safety-gate records, and generated test artifacts local unless repository tracking is approved.
- Do not initialize Git, stage, commit, push, create a pull request, or modify `.gitignore`.
- Prefer `.git/info/exclude` only if approved repo-local placement becomes necessary.
- Never commit credentials, test data containing personal information, or safety-gate records to a shared repository.

## Examples

- [API fuzzing review](examples/api-fuzzing-review-example.md)
- [Backend error path testing](examples/backend-error-path-testing-example.md)
- [Database constraint testing](examples/database-constraint-testing-example.md)
- [Destructive test report](examples/destructive-test-report-example.md)
- [Full system resilience review](examples/full-system-resilience-review-example.md)
- [UI negative testing](examples/ui-negative-testing-example.md)
