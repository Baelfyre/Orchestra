# Security and Privacy Standards

Use these concepts as defensive review guidance. This skill does not certify compliance with ISO, OWASP, NIST, CIS, GDPR, or any other framework or law.

## Application Security Review
- Define scope, assets, trust boundaries, entry points, data flows, dependencies, and deployment context.
- Validate findings against reachable code and existing controls.
- Prioritize by impact, likelihood, exposure, and confidence.

## Privacy Risk Review
- Identify personal and sensitive data, purpose, actors, flows, storage, sharing, retention, and deletion behavior.
- Minimize data and access while preserving the stated objective.
- Treat legal basis and rights as documentation questions for qualified review, not legal conclusions.

## Secure SDLC and Threat Modeling
- Integrate security requirements, design review, implementation safeguards, testing, dependency controls, release gates, and response ownership.
- Model assets, boundaries, entry points, actors, abuse cases, mitigations, and residual risk at a defensive level.

## Authentication
- Review identity proofing assumptions, credential storage, recovery, multifactor support, rate controls, error messages, and auditability.
- Prevent account discovery and unsafe recovery behavior where applicable.

## Authorization and RBAC
- Enforce access server-side at every protected operation and object boundary.
- Default deny, minimize privilege, separate roles from ownership checks, and test horizontal and vertical access decisions defensively.

## Session Handling
- Review token generation, storage, transport, rotation, expiry, revocation, logout, concurrent sessions, and cross-site protections where relevant.

## Input Validation and Output Encoding
- Validate untrusted input by type, format, range, size, and business rule at the trust boundary.
- Encode output for its destination context and prefer safe framework APIs.
- Do not rely on client-side checks for server-side protection.

## Secrets Management
- Keep credentials out of source, logs, artifacts, client bundles, and documentation.
- Use approved secret storage, scoped access, rotation, revocation, and incident procedures.

## Sensitive Data Handling
- Limit collection, access, copies, exports, logging, and retention.
- Protect data in transit and at rest according to risk and environment.
- Define deletion, backup, and recovery behavior.

## Dependency and Supply Chain Security
- Use trusted sources, lockfiles, reviewable updates, provenance evidence when available, scoped build permissions, and timely vulnerability triage.
- Validate scanner findings and avoid automatic trust in scores.

## Logging and Auditability
- Record security-relevant actions with actor, target, time, result, and correlation context when required.
- Exclude secrets and unnecessary personal data.
- Protect integrity, access, retention, and alerting paths.

## Data Minimization and Retention
- Collect and retain only data needed for a documented purpose.
- Define retention, deletion, backup expiry, archive access, and legal or policy exceptions through qualified governance.

## Public Reference Links

Use these clean URLs as learning anchors. Do not reproduce restricted standard text.

- https://owasp.org/www-project-application-security-verification-standard/
- https://owasp.org/www-project-web-security-testing-guide/
- https://owasp.org/www-project-top-ten/
- https://owasp.org/API-Security/editions/2023/en/0x11-t10/
- https://csrc.nist.gov/pubs/sp/800/218/final
- https://www.nist.gov/cyberframework
- https://www.nist.gov/privacy-framework
- https://www.iso.org/standard/27001
- https://www.iso.org/standard/27701
- https://www.cisecurity.org/controls
- https://scorecard.dev/
- https://slsa.dev/
- https://gdpr-info.eu/art-5-gdpr/

Describe reviews as aligned with general security and privacy principles unless formal audit evidence supports a stronger claim.
