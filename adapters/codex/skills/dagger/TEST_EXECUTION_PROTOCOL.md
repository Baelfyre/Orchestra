# Test Execution Protocol

## 1. Pre-test confirmation

- Confirm ownership or authorization, objective, target version, non-production isolation, scope, exclusions, and test mode.
- Complete `SAFETY_GATES.md`. Block risky execution on any unknown safety requirement.

## 2. Environment and data

- Verify test database, mock dependencies, disposable synthetic data, resource ceilings, monitoring, backup, rollback, and cleanup.
- Record a reproducible baseline and redact secrets.

## 3. Approval checkpoint

- Present exact tests, side effects, limits, stop conditions, rollback, and cleanup.
- Obtain explicit approval before destructive, disruptive, schema, auth, permission, lockout, load, or data-changing execution.

## 4. Execution

- Run the smallest approved case first.
- Change one condition at a time.
- Observe limits and stop immediately when a stop condition occurs.
- Do not broaden scope based on an unexpected result without new approval.

## 5. Evidence and failure documentation

Capture test ID, time, target, input, expected guardrail, actual behavior, sanitized logs, before/after state, severity, reproducibility, and cleanup result. Separate confirmed failures from suspected weaknesses.

## 6. Cleanup and verification

- Roll back transactions or restore the baseline.
- Remove fixtures, files, temporary identities, permissions, traffic, and mocks.
- Verify health, state consistency, and absence of residual test data.

## 7. Retest

After a fix, rerun the minimal reproducer, verify the intended guardrail, check adjacent regressions, capture new evidence, and update the score and confidence.
