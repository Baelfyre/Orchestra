# Fictional Backend Error-Path Example

## Safety gate

- Environment: local service with mock payment dependency
- Production: No
- Authorization: fictional service owner approval
- Mode: approved dependency-failure simulation

## Evidence reviewed

- Correlated application log `ERR-PATH-12`
- Mock timeout trace
- Before/after order state

## Test and result

- Condition: dependency timeout during order confirmation
- Expected guardrail: bounded timeout, no duplicate order, recoverable pending state
- Actual result: request returned a safe 503, but order remained in an undocumented intermediate state
- Severity: Major confirmed failure

## Assumptions

- Mock timeout is representative of the dependency contract.

## Missing evidence

- Automated recovery after process restart was not tested.

## Defensive recommendation

- Define a terminal or retryable state, add transactional cleanup, then retest timeout and restart recovery.
