# Authentication, Session, OAuth and OIDC Guide

## Start With the Identity Model

Before reviewing authentication, identify:
- who authenticates whom;
- human user vs service/workload;
- first-party vs third-party client;
- browser, native, SPA, backend or machine client;
- identity provider/authorization server;
- application session vs OAuth access token vs OIDC identity token.

Do not reuse advice across these models without checking that it applies.

## Password and Credential Authentication

Review:
- framework/platform-supported password hashing and credential storage;
- account recovery/reset as an authentication path;
- brute-force/automation controls appropriate to the system;
- MFA or step-up requirements from project policy;
- account disablement/revocation;
- error behavior that unnecessarily exposes account state.

Cipher defines requirements; Ponytail implements them.

## Session Cookies

When a browser cookie carries session authority, review:
- secure transport;
- `Secure`, `HttpOnly` and appropriate `SameSite` behavior;
- session fixation/rotation at meaningful privilege transitions;
- expiry and inactivity behavior according to project requirements;
- logout/server-side invalidation semantics where supported;
- CSRF exposure because cookies may be sent automatically by the browser.

Do not recommend CSRF controls merely because an API exists; determine whether the credential model creates ambient authority.

## Bearer Tokens

Bearer tokens grant authority to whoever possesses them.

Review:
- where tokens are stored and exposed;
- transport;
- intended audience/resource;
- issuer;
- expiry;
- scope/permissions;
- revocation or short-lived-token strategy according to architecture;
- log/error/telemetry exposure.

Do not treat an access token as an identity token unless the protocol and application explicitly define that use.

## OAuth 2.0 Security BCP

RFC 9700 / BCP 240 is the security anchor for OAuth 2.0 flows.

Review the exact client and flow. Important boundaries include:
- exact redirect URI handling;
- authorization-code interception defenses such as PKCE where applicable;
- authorization-response/session binding (`state` and protocol-specific mechanisms);
- avoiding obsolete/deprecated insecure flow patterns;
- refresh-token protection and replay mitigation appropriate to client type;
- preventing mix-up or authorization-server confusion where multiple issuers are involved;
- avoiding open redirectors and unsafe forwarding.

Do not copy legacy OAuth examples without checking them against current BCP guidance.

Reference:
- https://datatracker.ietf.org/doc/rfc9700/

## OpenID Connect

OIDC adds identity/authentication semantics on top of OAuth.

Review:
- issuer;
- audience/client ID;
- nonce where required by the flow;
- state/correlation;
- redirect URI;
- ID token signature and claims;
- separation of ID token purpose from API access-token purpose;
- user-info data exposure.

Reference:
- https://openid.net/specs/openid-connect-core-1_0.html

## JWT Validation

JWT is a format, not an authorization model.

When JWTs are used:
- constrain accepted algorithms according to the issuer/application contract;
- verify signature using the correct key source;
- validate issuer and audience;
- validate time-based claims that are required by the token profile;
- distinguish token types/contexts to avoid cross-protocol substitution;
- avoid trusting unverified header/claim data for security decisions.

Reference:
- https://datatracker.ietf.org/doc/rfc8725/

## Refresh Tokens

Review:
- whether the client can safely hold a refresh token;
- storage exposure;
- scope/audience;
- rotation or sender-constraining/replay controls when required by the deployment model;
- revocation/disablement;
- reuse detection if the selected design relies on rotation.

## Service-to-Service Identity

For machine/workload identities, review:
- workload identity source;
- credential issuance/rotation;
- audience and scope;
- service authorization separate from transport identity;
- secretless or managed identity mechanisms when the platform provides them;
- lateral movement risk from overly broad shared credentials.

## Finding Boundary

Cipher identifies the unsafe trust/control assumption. It does not design a new identity platform or implement the flow. Route architecture choices to Clockwork and implementation to Ponytail.