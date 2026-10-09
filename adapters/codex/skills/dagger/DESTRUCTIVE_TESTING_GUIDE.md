# Controlled Destructive Testing Guide

Controlled destructive testing deliberately triggers bounded failures to verify guardrails, rollback, cleanup, and recovery. It is not permission to damage systems.

## Use when

- A near-release system has a safe non-production target.
- Ordinary reviews identify a high-risk failure path.
- The user explicitly requests pressure, recovery, crash, or destructive testing.

Do not use for production, real data, unauthorized systems, ordinary first-pass review, or environments without recovery controls.

## Safe setup

1. Complete the safety gate.
2. Clone or seed disposable data with no private records.
3. Verify backups, rollback, isolation, monitoring, limits, and cleanup ownership.
4. Define one failure hypothesis and the expected guardrail per test.
5. Start with review-only or simulation; escalate only when lower-risk evidence is insufficient.

## Failure-oriented tests

- Interrupt a transaction and verify atomic rollback.
- Simulate a dependency timeout and verify bounded retries and useful errors.
- Submit duplicate operations and verify idempotency or duplicate rejection.
- Exhaust a documented non-production limit within an approved ceiling.
- Simulate partial completion and verify consistency and recovery.

## Recovery and cleanup

Record recovery time, residual state, audit events, orphaned data, retry behavior, and manual intervention. Restore the baseline, remove disposable data, revoke temporary permissions, stop test traffic, and verify the environment after every test.

## Evidence

Capture target and version, timestamp, approval, inputs, expected behavior, actual behavior, logs with secrets redacted, before/after state, cleanup proof, severity, fix, and retest command. A missing artifact means the result is unconfirmed.
