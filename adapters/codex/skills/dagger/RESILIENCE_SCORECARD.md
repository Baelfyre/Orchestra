# Resilience Scorecard

Score only evidenced areas. Use `N/A` when out of scope and `Provisional` when evidence is incomplete.

| Area | Score /100 | Evidence Required | Explanation |
|---|---:|---|---|
| Input Validation |  | Boundary and malformed-input results |  |
| UI Guardrails |  | UI behavior plus request/state evidence |  |
| API Guardrails |  | Responses, state checks, and server logs |  |
| Backend Error Handling |  | Failure traces, cleanup, and recovery |  |
| Database Integrity |  | Constraint and before/after state evidence |  |
| Security Hardening |  | Defensive control and denial evidence |  |
| Privacy Safety |  | Data-flow, access, logging, and redaction evidence |  |
| Reliability Under Failure |  | Timeout, retry, partial-failure, and recovery evidence |  |
| Observability and Logging |  | Correlated, redacted failure events |  |
| Recovery Readiness |  | Executed rollback or recovery evidence |  |
| Overall Resilience Score |  | Weighted evidence from applicable areas |  |

## Interpretation

- 90-100: Strong resilience with minor gaps
- 75-89: Generally strong with targeted fixes needed
- 60-74: Moderate resilience with meaningful risk
- 40-59: Weak resilience with major gaps
- 0-39: High-risk, failure-prone area

## Judgment

- Confidence: High / Medium / Low
- Score status: Final / Provisional
- Weighting rationale:
- Confirmed failures:
- Missing evidence:
- Untested areas:
- Highest-risk corrective action:

Weight critical workflow impact, safety, data integrity, security and privacy, likelihood, severity, and recovery difficulty. Never average missing areas into a deceptively high score.
