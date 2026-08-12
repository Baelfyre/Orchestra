# Security Checklist

Use only the sections relevant to the inspected surface.

## Evidence and Scope
- [ ] Security objective and review boundary are explicit.
- [ ] Relevant code, configuration, data flow, dependency, endpoint, identity model, or policy evidence was inspected.
- [ ] Confirmed findings, assumptions, hardening notes, false positives, and missing evidence are separated.

## Authentication
- [ ] Identity source and authentication mechanism are explicit.
- [ ] Credential/password handling uses the framework/platform's supported secure mechanism.
- [ ] Recovery/reset behavior does not create a weaker authentication path.
- [ ] MFA and step-up boundaries are reviewed where required by project policy.
- [ ] Account-discovery and brute-force/automation exposure are considered without relying on UI hiding.

## Authorization
- [ ] Every protected operation enforces authorization server-side.
- [ ] Object/resource access is checked, not merely role membership.
- [ ] Function/action access is checked independently of UI visibility.
- [ ] Property/field-level read and write access is reviewed where sensitive fields exist.
- [ ] Tenant/account/organization boundaries are enforced at the authoritative boundary.
- [ ] Administrative and support privileges are explicit and least-privileged.
- [ ] Default behavior is deny/fail-closed when authority is missing or ambiguous.
- [ ] Jobs, callbacks, webhooks, queues and service-to-service paths preserve the intended authority context.

## Session and Token Handling
- [ ] Session/token generation, transport, storage, expiry and revocation are reviewed.
- [ ] Cookie attributes and CSRF implications match the session architecture.
- [ ] Logout/revocation semantics are clear for the actual token/session type.
- [ ] Token validation checks intended issuer, audience, signature/algorithm, time claims and token type where applicable.
- [ ] Refresh tokens or long-lived credentials have appropriate exposure and replay controls for the client model.

## OAuth/OIDC
- [ ] The exact OAuth/OIDC flow and client type are identified.
- [ ] Redirect URIs and authorization responses are constrained according to the protocol and deployment.
- [ ] PKCE/state/nonce or equivalent flow protections are applied where the selected flow requires them.
- [ ] Deprecated or insecure flow assumptions are not carried forward from obsolete examples.
- [ ] OAuth authorization and OIDC authentication/identity semantics are not conflated.

## Input and Output Safety
- [ ] Untrusted input is constrained by type, format, range, size and business invariant at the trust boundary.
- [ ] Output uses destination-context encoding or framework-safe APIs.
- [ ] Query/command/template construction uses framework-safe parameterization/binding where relevant.
- [ ] Untrusted serialized data is not treated as trusted executable/object state.
- [ ] File paths, filenames and archive extraction boundaries are constrained where applicable.

## Web and API Security
- [ ] Object-, function- and property-level authorization are reviewed.
- [ ] Resource-consumption controls match the expensive operation or shared resource at risk.
- [ ] Sensitive business flows include anti-automation/state-transition controls appropriate to the business invariant.
- [ ] SSRF/outbound-request destinations and redirect behavior are constrained where server-side fetching exists.
- [ ] Upload handling constrains type, size, storage, execution and serving behavior as applicable.
- [ ] CORS policy matches trusted browser origins and credential behavior.
- [ ] CSRF protections match cookie/ambient-authority use; bearer-token APIs are not assigned cookie-specific controls without evidence.
- [ ] API inventory, deprecated versions, debug/admin endpoints and environment exposure are reviewed.
- [ ] Third-party API data is treated as untrusted at the receiving boundary.

## Secrets and Cryptography
- [ ] Secrets are absent from source, logs, documentation, client bundles and public artifacts.
- [ ] Secret storage, scope, rotation/revocation ownership and environment separation are explicit.
- [ ] Standard framework/platform cryptography is preferred over custom constructions.
- [ ] Hashing, encryption, signing, password hashing and encoding are not treated as interchangeable.
- [ ] Key/nonce/IV reuse or algorithm misuse is reviewed only where evidence makes it relevant.

## Secure Configuration
- [ ] Debug/development behavior is disabled or isolated from production scope.
- [ ] Security-sensitive defaults, headers, transport, permissions and environment separation are reviewed.
- [ ] Reverse proxy/gateway trust assumptions do not let untrusted forwarding metadata become authority.
- [ ] Caches/CDNs/proxies do not expose personalized or sensitive responses across security boundaries.

## Dependency and Supply Chain
- [ ] Dependency findings identify direct/transitive and production/development exposure.
- [ ] Affected and fixed versions are confirmed from authoritative advisory/package evidence.
- [ ] Reachability/runtime use is considered when evidence exists.
- [ ] Build sources, lockfiles, CI permissions, artifacts and provenance/signing are reviewed where in scope.
- [ ] Scanner severity is not treated as project-specific exploitability by itself.

## Security Tool Findings
- [ ] SAST/CodeQL findings are checked for reachable source-to-sink/control-flow relevance.
- [ ] DAST findings identify environment, route, identity and configuration actually tested.
- [ ] Secret-scanner output is handled without printing sensitive values.
- [ ] False positives and non-applicable findings are explicitly closed with evidence rather than silently ignored.

## Logging and Auditability
- [ ] Security-relevant events record sufficient actor/action/target/result/correlation evidence when required.
- [ ] Logs exclude secrets and unnecessary sensitive/personal data.
- [ ] Audit events cannot be mistaken for authorization or permission.
- [ ] Integrity, access and retention ownership are identified.

## Privacy Exposure
- [ ] Sensitive/personal data collection and copies are minimized.
- [ ] Data access, sharing, exports, telemetry and support access are reviewed.
- [ ] Retention/deletion/backups are described technically without making legal sufficiency claims.
- [ ] Legal/privacy-obligation questions are routed to The Governor.

## Handoffs
- [ ] Implementation is routed to Ponytail.
- [ ] Architecture/control placement is routed to Clockwork.
- [ ] Persistence mechanics are routed to Chronicler.
- [ ] Frontend security UX is routed to Cloak.
- [ ] Validation strategy/readiness is routed to Overseer.
- [ ] Active negative/resilience testing is routed to Dagger only when authorized.