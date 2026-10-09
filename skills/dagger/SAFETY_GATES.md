# Dagger Safety Gates

Complete this gate before recommending or executing destructive tests. Unknown answers block risky execution.

## Environment

- Target environment:
- Production: Yes / No / Unknown
- Isolated from production:
- Test database:
- Mock services:
- Disposable test data:
- Real user or customer data present:
- Environment owner confirmed:
- Production connectivity blocked or explicitly isolated:
- Shared dependency and cross-tenant blast radius:

## QA Baseline Alignment

- Overseer baseline reviewed: Yes / No / Not applicable
- Related requirement or acceptance criterion:
- Related smoke, regression, UAT, or defect evidence:
- Stress scope derived from QA evidence:
- Exploratory Dagger scope clearly marked: Yes / No

## Authorization and scope

- System owner or authorized tester:
- Evidence of authorization:
- Approved objective:
- In scope:
- Out of scope:
- Time and resource limits:
- Workload or fault ceiling:
- Ramp, duration, and steady-state window:
- Allowed concurrency and request rate:
- Explicit approval required before execution:

## Protection and recovery

- Data-loss risk:
- Service-disruption risk:
- Credential-exposure risk:
- Backup verified:
- Rollback procedure verified:
- Cleanup owner and procedure:
- Monitoring available:
- Load-generator health monitored separately:
- Abort control tested:
- Recovery objectives and verification window:
- Residual-state check:

## Approval checkpoint

Obtain explicit approval before deletion, corruption simulation, schema changes, authentication or authorization changes, permission changes, account lockouts, load or stress tests, or any irreversible or disruptive action. Approval must name the target, scope, risk, and rollback.

## Stop conditions

Stop immediately if production is targeted; authorization or scope is unclear; real data may be damaged; credentials may be exposed; access would be unauthorized; disruption exceeds limits; rollback fails; unexpected cross-system effects appear; or approval is missing.

Before execution, translate stop conditions into observable thresholds with an owner: error rate, latency percentile, saturation, queue depth, retry amplification, memory growth, disk floor, data-integrity signal, cross-tenant effect, health-check failure, generator overload, or elapsed time. Unknown telemetry or an untested abort path blocks execution.

## Forbidden actions

- Production or unapproved third-party testing
- Real customer data as test input
- Authentication bypass or unauthorized access
- Unapproved data deletion, corruption, overload, or permission change
- Offensive exploit chains, malware, persistence, credential theft, or exfiltration

## Gate decision

- Status: Approved / Planning only / Blocked
- Approved tests:
- Approval evidence:
- Required safeguards:
- Stop conditions acknowledged:
