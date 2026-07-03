# Secure Application Foundations Guide

## Secure Application Layering Rule
- The UI is never trusted as the enforcement layer.
- Frontend validation is usability only, not security.
- APIs must enforce authentication, authorization, object ownership, validation, rate limits, and audit logging server-side.
- Backend services must reject direct API abuse even if the UI would normally prevent it.
- RBAC must be checked at every protected operation, not only at menu/page visibility.
- Object-level access must be verified server-side to prevent ID tampering and horizontal privilege abuse.
- Input validation must happen at the backend trust boundary.
- Sensitive operations require audit logs with actor, action, target, result, and timestamp.

## API Threat Considerations
When designing or reviewing APIs, always consider defenses against:
- Direct API abuse and scraping
- Request tampering and parameter pollution
- Replay attacks
- Malicious automation and bot traffic
- Insecure Direct Object References (IDOR) / ID manipulation
- Backend injection (SQL, NoSQL, Command, LDAP, etc.)

## API Hardening Boundaries
API hardening must include layered defenses at the network, gateway, and application boundaries:
- **Rate Limiting & Throttling**: Restrict requests per IP, user, or token using token bucket or sliding window algorithms.
- **Traffic Filtering**: Use Web Application Firewalls (WAF) or API Gateways to filter malicious signatures.
- **Resilience Controls**: Implement backpressure, load shedding, and circuit breakers to prevent cascading failures.
- **DDoS Mitigation**: Use network-level protection boundaries to absorb volumetric attacks before they hit the application layer.

## Security Control Specialist Boundaries
For overload, DDoS, and API abuse, follow these strict boundaries:
- **Cipher**: Defines rate limiting, abuse prevention, API protection, and DDoS mitigation requirements.
- **Dagger**: Designs controlled overload, resilience, and abuse-case scenarios.
- **Overseer**: Defines validation gates and pass/fail readiness checks.
- **Ponytail**: Implements the actual controls.
- **Clockwork**: Reviews whether the security control is placed in the correct layer.
- **Chronicler**: Handles persistence design for audit logs, access records, retention, and security data.
