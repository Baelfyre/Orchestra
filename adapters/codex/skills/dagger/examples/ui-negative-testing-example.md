# Fictional UI Negative Testing Example

## Safety gate

- Environment: isolated staging UI with mock API
- Production: No
- Authorization: fictional product owner approval
- Data: disposable synthetic account
- Mode: executed within approved form only

## Evidence reviewed

- Browser recording `UI-NEG-04`
- Mock API log showing one request
- Before/after synthetic profile snapshot

## Test and result

- Condition: double-click Save with an invalid end date
- Expected guardrail: one request at most; invalid dates rejected
- Actual result: one request; mock API returned 422; no profile change
- Status: Passed for this fixture only

## Assumptions

- Mock behavior matches the documented API contract.

## Missing evidence

- Mobile viewport and real staging API were not tested.

## Defensive recommendation

- Retest the same case against the isolated staging API before release.
