# Conductor Quick Route

## User request
Pressure-test invalid inputs and transaction rollback on our staging release candidate.

## Project signals
- Explicit pressure-test request, staging environment, release candidate, invalid-input and rollback scope

## Activation condition
- Explicit adversarial request and mature non-production target

## Safety gate requirement
- Confirm authorization, production exclusion, disposable data, backup or rollback, side effects, cleanup, and stop conditions before invocation or execution.

## Minimal skill stack
- `dagger`

## Recommended prerequisites
- Add `overseer`, `cipher`, `chronicler`, or `cloak` only when ordinary review evidence is missing in that domain.

## Execution sequence
1. Complete the safety gate and obtain approval.
2. Create the smallest bounded test plan.
3. Execute only approved tests, capture evidence, clean up, and define retests.

## Token-saving decision
Do not route every prerequisite when the supplied evidence already defines the pressure-test targets.

## Final copy-paste prompt
`Use $dagger to create a safety-gated invalid-input and transaction-rollback plan for this staging release candidate. Do not execute tests until I approve the scope and rollback plan.`
