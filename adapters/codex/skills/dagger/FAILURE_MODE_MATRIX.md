# Failure Mode Matrix

| Failure Area | Example Failure | Trigger | Expected Guardrail | Evidence to Capture | Severity | Recommended Fix Pattern |
|---|---|---|---|---|---|---|
| UI | Duplicate submit | Rapid approved double-click | Disable and deduplicate | UI recording, request count | Major | Idempotent submit and pending state |
| API | Malformed body | Invalid JSON fixture | Stable 4xx, no state change | Response, logs, state diff | Minor | Schema validation and safe errors |
| Backend | Unhandled exception | Approved dependency stub failure | Controlled error and cleanup | Trace, correlation ID | Major | Boundary handler and typed failure |
| Database | Orphan record | Parent rejection during transaction | Atomic rollback | Before/after rows, transaction log | Critical | Foreign key and transaction boundary |
| Authentication | Lockout weakness | Approved repeated failures | Bounded attempts and recovery | Audit events, test account state | Major | Rate limit and lockout policy |
| Authorization | Role crosses boundary | Approved lower-role request | Deny without data disclosure | Status, audit log, response | Critical | Server-side policy enforcement |
| File upload | Unsafe oversized file | Bounded test fixture | Reject before storage or processing | Size, response, storage check | Major | Type, size, and content validation |
| Form submission | Invalid cross-field state | Conflicting dates or totals | Explain and reject | UI/API errors, state check | Minor | Shared invariant validation |
| Transactions | Partial commit | Injected test failure mid-operation | Full rollback | Row diff, logs | Critical | Atomic unit of work |
| External services | Timeout cascade | Mock dependency timeout | Bounded timeout and retry | Timing, retry count, logs | Major | Timeout, circuit breaker, fallback |
| Logging | Secret leakage | Invalid approved credential fixture | Redacted structured event | Sanitized log sample | Critical | Central redaction and safe fields |
| Recovery | State remains degraded | Restart after simulated failure | Restore consistent service | Health checks, state diff | Major | Recovery procedure and idempotent replay |

Treat severity as provisional until impact and evidence are validated.
