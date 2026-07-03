# Negative Testing Checklist

Use only items relevant to the approved workflow.

## Inputs

- [ ] Empty, whitespace-only, and missing required values
- [ ] Null values at each accepted boundary
- [ ] Wrong primitive, object, collection, and encoding types
- [ ] Minimum, maximum, just-below, and just-above boundary values
- [ ] Zero, negative, overflow, precision, and rounding cases
- [ ] Oversized text, files, arrays, requests, and pagination values within safe limits
- [ ] Special, Unicode, control, delimiter, quoting, and line-break characters
- [ ] Malformed structured input and invalid formats

## Actions and states

- [ ] Duplicate click, submission, request, import, or seed action
- [ ] Out-of-order workflow steps
- [ ] Invalid state transitions and stale-state actions
- [ ] Missing, nonexistent, expired, or already-processed resources
- [ ] Unauthorized and forbidden actions using approved test identities
- [ ] Client-side validation bypass awareness with server-side enforcement checked

## Failure conditions

- [ ] Timeout and cancellation
- [ ] Dependency unavailable, slow, or partially failing
- [ ] Transaction interruption and rollback
- [ ] Retry exhaustion and duplicate retry effects
- [ ] Offline or reconnect behavior
- [ ] Logging, user-facing errors, and sensitive-data redaction

For every selected case, record expected guardrail, safe limit, evidence source, cleanup, and stop condition.
