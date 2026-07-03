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
- Explicit approval required before execution:

## Protection and recovery

- Data-loss risk:
- Service-disruption risk:
- Credential-exposure risk:
- Backup verified:
- Rollback procedure verified:
- Cleanup owner and procedure:
- Monitoring available:

## Approval checkpoint

Obtain explicit approval before deletion, corruption simulation, schema changes, authentication or authorization changes, permission changes, account lockouts, load or stress tests, or any irreversible or disruptive action. Approval must name the target, scope, risk, and rollback.

## Stop conditions

Stop immediately if production is targeted; authorization or scope is unclear; real data may be damaged; credentials may be exposed; access would be unauthorized; disruption exceeds limits; rollback fails; unexpected cross-system effects appear; or approval is missing.

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
