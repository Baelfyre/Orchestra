# Conductor Quick Route

## User request
Review our release-candidate test plan and decide whether it is ready for regression testing.

## Project signals
- Test plan, acceptance criteria, prior defect list, and release-candidate status

## Minimal skill stack
- `overseer`

## Execution sequence
1. Review requirements testability and test-case evidence.
2. Identify regression gaps and release blockers.
3. Return priority fixes and retest steps.

## Token-saving decision
Do not add Dagger because destructive or adversarial testing was not requested.

## Final copy-paste prompt
`Use $overseer to audit this release-candidate test plan, acceptance criteria, defect evidence, regression coverage, and release readiness. Do not invent test results.`
