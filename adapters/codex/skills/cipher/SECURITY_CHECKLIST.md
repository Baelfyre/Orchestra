# Security Checklist

## Authentication
- [ ] Identity, credential, recovery, rate-control, multifactor, and account-discovery behavior are reviewed.

## Authorization
- [ ] Every protected operation and object enforces server-side access decisions.
- [ ] Horizontal and vertical access boundaries are verified defensively.

## RBAC
- [ ] Roles, permissions, ownership rules, defaults, and administrative boundaries are explicit.

## Session Handling
- [ ] Tokens or cookies have secure generation, storage, transport, expiry, rotation, revocation, and logout behavior.

## Input Validation
- [ ] Untrusted input is constrained by type, format, range, size, and business rule at trust boundaries.

## Output Encoding
- [ ] Output uses destination-context encoding or safe framework APIs.

## Error Handling
- [ ] Errors avoid sensitive details, fail safely, preserve useful correlation, and support recovery.

## Secrets
- [ ] Credentials and keys are absent from source, logs, artifacts, documentation, and client bundles.
- [ ] Storage, scope, rotation, revocation, and incident response are documented.

## Dependency Security
- [ ] Dependencies use trusted sources, lockfiles, supported versions, and validated vulnerability findings.

## Logging
- [ ] Security-relevant events are useful, protected, and free of secrets or unnecessary personal data.

## Audit Trails
- [ ] Required actor, action, target, time, result, and correlation evidence is retained with integrity controls.

## Secure Configuration
- [ ] Production defaults, debug settings, headers, transport, permissions, and environment separation are reviewed.

## API Security
- [ ] Authentication, authorization, object access, validation, rate limits, errors, pagination, and versioning are reviewed where relevant.
- [ ] UI is not treated as a security boundary; attackers can bypass the UI and call APIs directly.
- [ ] Frontend validation is not treated as enforcement; backend must enforce auth, authz, RBAC, object ownership, and validation.
- [ ] API hardening boundaries are defined (rate limiting, throttling, token bucket, sliding window, traffic filtering, WAF/API gateway, backpressure, load shedding, circuit breaker, DDoS mitigation).
- [ ] Defenses are in place against direct API abuse, request tampering, replay, automation, ID manipulation, and backend injection.

## Supply Chain Risk
- [ ] Build sources, provenance, CI permissions, artifacts, release signing, and update workflow are assessed when evidence exists.

## Secure SDLC Evidence
- [ ] Security requirements, design review, testing, findings, remediation, release gates, and ownership have current evidence.
