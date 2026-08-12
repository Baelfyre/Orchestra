# Web and API Security Controls Guide

## Authorization Comes First

Many API failures are authorization failures, not input-validation failures.

Review access at:
- object/resource level;
- function/action level;
- object-property/field level;
- tenant/account/organization boundary;
- state-transition/eligibility boundary.

A valid identifier does not imply permission to access the identified object.

## Sensitive Business Flows

Identify workflows whose abuse creates business harm even when individual requests are syntactically valid:
- scarce reservations or appointments;
- waitlists/queues;
- invitations/referrals;
- account recovery;
- promotions/coupons;
- enrollment/registration;
- limited inventory;
- payout/refund/approval workflows;
- expensive report/export/search operations.

Review:
- server-owned eligibility;
- ordering and uniqueness;
- per-actor and per-resource quotas;
- replay/duplicate behavior;
- automation controls;
- auditability.

Rate limiting supports the invariant but is not the invariant.

## Resource Consumption

Apply limits at the resource that can be exhausted:
- request body;
- upload;
- pagination/page size;
- query complexity;
- search/report generation;
- concurrency;
- background jobs;
- outbound calls;
- authentication/recovery attempts.

Clockwork owns distributed capacity architecture; Cipher owns the defensive abuse objective.

## SSRF and Outbound Requests

If a server fetches a destination influenced by untrusted input:
- define permitted destination classes;
- constrain scheme/host/port/path as required;
- account for redirects;
- account for DNS and network trust;
- isolate access to internal/metadata/management services through infrastructure controls where relevant;
- cap time/bytes/connections;
- treat response content as untrusted.

Do not provide bypass payloads or internal-address targeting instructions.

## CORS

CORS controls browser cross-origin reading/sharing. It is not authentication or authorization.

Review:
- exact trusted origins;
- credentialed-request behavior;
- wildcard use;
- preflight/method/header policy;
- whether sensitive responses are exposed cross-origin.

Non-browser clients are not constrained by CORS.

## CSRF

CSRF is relevant when a browser automatically attaches authority, commonly session cookies.

Review:
- request method/state change;
- cookie/session model;
- SameSite behavior;
- anti-CSRF token or origin validation mechanisms as supported by the framework;
- unsafe state-changing GET requests.

Do not add cookie-specific CSRF controls to a non-cookie bearer-token design without evidence that ambient browser authority exists.

## Uploads

Review:
- maximum size/count;
- allowed business content;
- storage and execution boundary;
- filename/path handling;
- content sniffing/serving behavior;
- access control;
- archive extraction;
- downstream parsers.

Do not rely on file extension alone.

## Third-Party APIs

Treat provider data as untrusted input.

Review:
- provider endpoint identity;
- credential scope;
- response schema validation;
- redirects;
- timeout/retry;
- propagation into templates, commands, queries or access-control decisions;
- provider compromise/failure assumptions.

## API Inventory and Versioning

Security review should identify:
- deprecated API versions still exposed;
- debug/admin/test endpoints;
- undocumented alternate routes;
- stale schemas or clients;
- environment endpoints;
- inconsistent authorization between versions.

Clockwork owns compatibility/version architecture; Cipher reviews security exposure.

## Error Handling

Errors should:
- fail closed for security decisions;
- avoid secrets and unnecessary implementation details;
- retain safe correlation context;
- distinguish client errors from server failures without exposing sensitive internals.

## References

- OWASP API Security Top 10 2023:
  https://owasp.org/API-Security/editions/2023/en/0x11-t10/
- OWASP ASVS:
  https://owasp.org/www-project-application-security-verification-standard/