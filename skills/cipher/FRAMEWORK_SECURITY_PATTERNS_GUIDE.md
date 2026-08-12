# Framework-Aware Security Patterns Guide

Use this guide only after repository evidence identifies the framework. Treat version-specific behavior as something to verify from that framework's official documentation.

## General Rule

Prefer the framework's maintained security mechanisms over custom parallel security code.

Review for:
- middleware/filter order;
- route/method authorization;
- session/cookie configuration;
- CSRF/CORS behavior;
- serializer/model binding;
- validation;
- ORM/query parameterization;
- template escaping;
- secret/config loading;
- production debug/error settings.

## Java / Spring Security

Review whether:
- the security filter chain applies to the intended routes;
- request-level and method-level authorization are consistent where both are used;
- CSRF configuration matches browser/session vs stateless-token architecture;
- password handling uses supported encoders rather than custom hashing;
- CORS and proxy/forwarded-header trust are configured deliberately;
- actuator/admin endpoints have explicit exposure controls.

Do not assume annotations are effective without confirming the relevant security configuration enables them.

## Python / Django

Review whether:
- authentication/permission decorators or class-based permissions cover the route;
- object ownership/tenant checks occur after object lookup at the authoritative boundary;
- CSRF protections match cookie-backed browser flows;
- ORM parameterization is not bypassed with unsafe raw-query construction;
- template autoescaping is not disabled or bypassed for untrusted content;
- `DEBUG` and secret/config behavior are appropriate for the environment.

## Python / FastAPI

Review whether:
- security dependencies execute on every protected path;
- authorization is not reduced to authentication-only dependencies;
- Pydantic/schema validation is complemented by business and authorization checks;
- CORS origin/credential policy is intentional;
- background tasks preserve tenant/authority context where they perform protected actions;
- proxy/header trust matches deployment topology.

## Node.js / Express

Review whether:
- authentication and authorization middleware are ordered before protected handlers;
- object/tenant checks occur in the handler/service that owns the operation;
- request size and parser settings fit resource-risk requirements;
- cookie/session configuration matches CSRF and transport assumptions;
- CORS is not used as access control;
- untrusted values do not reach shell/template/query/path sinks through unsafe construction;
- proxy trust is not broader than the actual reverse-proxy topology.

## Node.js / NestJS

Review whether:
- guards and metadata cover each protected controller/handler;
- global vs controller/method guards do not leave bypass routes;
- DTO validation is enabled where relied upon;
- authorization policies include object/tenant state when needed, not only role metadata;
- interceptors/filters do not expose sensitive errors or data.

## ASP.NET Core

Review whether:
- authentication and authorization middleware order is correct;
- policies/requirements cover protected endpoints;
- resource-based authorization is used where object state matters;
- antiforgery behavior matches browser/cookie endpoints;
- Data Protection/key handling fits the deployment;
- forwarded headers are trusted only from intended proxies;
- development exception/debug behavior is not exposed in production.

## Frontend Frameworks

React, Vue, Angular, Svelte and similar route guards or hidden components are UX controls, not server authorization.

Review:
- token exposure to script-accessible storage according to the chosen architecture;
- XSS-sensitive rendering/HTML escape bypass features;
- redirects/callbacks;
- server/API enforcement behind visible controls.

## ORM and Query Layers

ORM use reduces some injection risk but does not make every query safe.

Review:
- raw SQL/query escape hatches;
- dynamic sort/filter/column identifiers;
- tenant filters;
- authorization before/after object loading;
- mass assignment/model binding of protected fields.

## Version Discipline

When a finding depends on framework behavior:
- record the detected framework/version evidence;
- verify the current official framework documentation;
- avoid generic recommendations that belong to another major version.