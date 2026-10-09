# Test Execution Protocol

## 1. Pre-test confirmation

- Confirm ownership or authorization, objective, target version, non-production isolation, scope, exclusions, and test mode.
- Complete `SAFETY_GATES.md`. Block risky execution on any unknown safety requirement.
- Link the scenario to an Overseer baseline or mark it exploratory. State the single failure hypothesis, workload model, expected safe behavior, and evidence needed to disprove it.

## 2. Environment and data

- Verify test database, mock dependencies, disposable synthetic data, resource ceilings, monitoring, backup, rollback, and cleanup.
- Record a reproducible baseline and redact secrets.
- Confirm the generator, fault injector, telemetry collector, and target clocks are usable and separately observable. Prove the generator can stop without depending on the impaired target.

## 3. Approval checkpoint

- Present exact tests, side effects, limits, stop conditions, rollback, and cleanup.
- Obtain explicit approval before destructive, disruptive, schema, auth, permission, lockout, load, or data-changing execution.
- Bind approval to target revision, environment identity, exact ceiling, duration, blast radius, allowed tools, rollback owner, and expiry. Approval for one scenario does not authorize the next escalation.

## 4. Execution

- Run the smallest approved case first.
- Change one condition at a time.
- Observe limits and stop immediately when a stop condition occurs.
- Do not broaden scope based on an unexpected result without new approval.
- Warm up only when the workload model requires it, keep measurement windows distinct, and watch target and generator saturation. Change one independent variable at a time unless interaction is the approved hypothesis.

## 5. Evidence and failure documentation

Capture test ID, time, target, input, expected guardrail, actual behavior, sanitized logs, before/after state, severity, reproducibility, and cleanup result. Separate confirmed failures from suspected weaknesses.

For pressure or fault scenarios also capture workload/fault configuration, tool versions, configuration hash, rate and concurrency, latency percentiles, throughput, errors, saturation, queue/pool signals, retries, stop reason, recovery timeline, and measurement caveats. Never report an average alone as capacity or resilience proof.

## 6. Cleanup and verification

- Roll back transactions or restore the baseline.
- Remove fixtures, files, temporary identities, permissions, traffic, and mocks.
- Verify health, state consistency, and absence of residual test data.
- Continue observation through the recovery window. Verify queues drain, pools normalize, retries stop amplifying, temporary limits and fault rules are removed, and no delayed or duplicate work remains.

## 7. Retest

After a fix, rerun the minimal reproducer, verify the intended guardrail, check adjacent regressions, capture new evidence, and update the score and confidence.
