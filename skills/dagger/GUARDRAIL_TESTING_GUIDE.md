# Guardrail Testing Guide

Guardrails prevent invalid, unsafe, unauthorized, inconsistent, or unrecoverable behavior.

## Expected layers

- UI: clear constraints, disabled pending actions, safe rendering, and recoverable errors.
- API: authentication, authorization, schemas, limits, idempotency, and consistent errors.
- Backend: business invariants, state machines, transactions, bounded retries, and safe exceptions.
- Database: keys, checks, uniqueness, nullability, types, lengths, and rollback.
- Security: least privilege, secure defaults, rate controls, redaction, and auditability.
- Privacy: data minimization, purpose limits, retention controls, access boundaries, and safe logs.

## Safe test method

1. State the invariant and enforcement layer.
2. Select the least destructive input that can disprove the guardrail.
3. Confirm target, identity, data, limits, approval, rollback, and stop conditions.
4. Test one boundary at a time and capture before/after state.
5. Verify failure is safe, observable, and recoverable.

## Reporting a missing guardrail

Record the expected invariant, observed behavior, affected layer, reproducible evidence, impact, severity, minimal fix location, defense-in-depth gap, cleanup status, and retest step. Mark it suspected when execution or evidence is incomplete.
