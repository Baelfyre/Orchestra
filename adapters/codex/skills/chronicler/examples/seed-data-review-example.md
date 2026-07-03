# Chronicler Quick DB Review

## Database Objective
- Maintain canonical employment-status reference data.

## Confirmed Issues
1. `Regular` appears twice with different identifiers.
2. One seed script uses `Probationary`; another uses `Probation`.
3. Inserts are not repeatable and fail on a second run.

## Highest-Risk Gap
- Conflicting canonical values can make repository lookups nondeterministic.

## Recommended Next Action
- Select the approved canonical list, compare live references, and plan a reversible repair before editing seeds or data.
