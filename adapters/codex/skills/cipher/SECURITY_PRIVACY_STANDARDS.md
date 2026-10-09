# Security and Privacy Standards

Use these sources as defensive review anchors. Cipher does not certify compliance with OWASP, NIST, ISO, CIS, GDPR, or any other standard, framework, contract, policy, or law.

## Source Hierarchy

1. Repository evidence and explicit project requirements.
2. Applicable protocol or platform specification.
3. Current primary security standard or taxonomy.
4. Secondary guidance only when primary material is insufficient.

A generic checklist never overrides repository evidence or a protocol's normative requirements.

## OWASP ASVS

The current stable OWASP Application Security Verification Standard is ASVS 5.0.0 at the time of this SK3 update.

Use ASVS to:
- frame technical verification objectives;
- identify missing control classes;
- communicate a specific verification requirement when the mapping is supported.

When citing a requirement identifier, include its ASVS version, for example `v5.0.0-x.y.z`, because identifiers can move between versions.

Do not state that an application is "ASVS compliant" unless the required verification scope and evidence actually support that conclusion.

Reference:
- https://owasp.org/www-project-application-security-verification-standard/

## OWASP API Security Top 10

Use the 2023 API Security Top 10 as an awareness taxonomy for API-specific review, including:
- object-level authorization;
- authentication;
- object-property authorization;
- resource consumption;
- function-level authorization;
- sensitive business flows;
- SSRF;
- security misconfiguration;
- inventory/version exposure;
- unsafe consumption of third-party APIs.

A Top 10 category is not proof of a vulnerability and is not a complete API security specification.

Reference:
- https://owasp.org/API-Security/editions/2023/en/0x11-t10/

## MITRE CWE

Use CWE to name a demonstrated or strongly supported weakness at the most appropriate level.

Prefer a specific root-cause mapping over a generic umbrella category when evidence supports it. Do not choose a CWE solely because its title resembles a symptom.

The current CWE Top 25 can inform review attention, but ranking is not project-specific severity.

References:
- https://cwe.mitre.org/
- https://cwe.mitre.org/top25/

## OAuth 2.0 Security

Use RFC 9700 / BCP 240 as the current OAuth 2.0 security best-current-practice anchor.

Review the actual client type and flow before applying protocol guidance. Pay particular attention to redirect-based flows, authorization-code handling, PKCE where applicable, refresh-token protections, sender-constrained or replay-resistant mechanisms when required by the deployment model, and deprecated/insecure flow patterns identified by the BCP.

Reference:
- https://datatracker.ietf.org/doc/rfc9700/

## JWT

When JSON Web Tokens are actually used, RFC 8725 is the JWT security BCP anchor.

Review intended token type, accepted algorithms, issuer, audience, signature verification, key selection, expiry/time claims and cross-protocol confusion risks according to the application's token model.

Reference:
- https://datatracker.ietf.org/doc/rfc8725/

## OpenID Connect

When OIDC is used, distinguish authentication/identity claims from OAuth authorization. Review nonce/state/redirect/issuer/audience and token-use boundaries according to the actual flow and implementation.

Reference:
- https://openid.net/specs/openid-connect-core-1_0.html

## NIST Secure Software Development

Use NIST SSDF as process guidance for secure software-development practices, not as proof that an individual control is implemented.

Reference:
- https://csrc.nist.gov/pubs/sp/800/218/final

## Privacy Risk Review

Cipher may review technical privacy exposure:
- collection and data minimization;
- access and visibility;
- transport/storage exposure;
- logging and telemetry;
- retention/deletion implementation;
- sharing and third-party data flow;
- backups, exports and support access.

Legal basis, statutory rights, jurisdictional obligations, contract interpretation and compliance sufficiency belong to The Governor through Conductor.

## Mapping Rules

- Map only when the evidence supports the mapping.
- Record the mapping as contextual evidence, not authority.
- Keep version-specific identifiers versioned.
- Separate weakness taxonomy from severity.
- Separate technical security review from legal/compliance conclusions.
- Prefer primary-source links over copied restricted standard text.