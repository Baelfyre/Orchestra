# Secure Application Foundations Guide

## Core Trust Rule

The frontend is not an enforcement boundary.

Client-side validation, hidden buttons, disabled controls, route guards and UI role checks can improve UX but cannot replace server-side authentication, authorization, business-state and input enforcement.

## Server-Side Authorization Layers

Review authorization at the narrowest authoritative layer that owns the operation.

Distinguish:
- route/function permission;
- object/resource permission;
- property/field read/write permission;
- tenant/account/organization boundary;
- ownership/delegation;
- state-transition eligibility.

Do not centralize all decisions into a single coarse role if the domain requires additional object or state context.

## Security State Ownership

Identify the authoritative owner for:
- identity/session state;
- permissions/roles;
- ownership/delegation;
- tenant context;
- security-sensitive workflow state;
- revocation/disablement;
- rate/quota counters when they enforce policy.

Caches and projections must not silently become security authority unless the design explicitly makes them authoritative and handles staleness.

## Browser Boundary

Review:
- cookie vs bearer-token authority model;
- CSRF only where ambient browser credentials make it relevant;
- CORS as a browser sharing policy, not an authentication mechanism;
- content security/encoding boundaries for rendered untrusted data;
- secure cookie attributes where cookies carry session authority;
- redirect and callback destinations.

## API Boundary

Every protected API operation should enforce its own server-side security invariants even when the normal client prevents invalid actions.

Review:
- authentication;
- object/function/property authorization;
- input and payload size constraints;
- business-flow state;
- error disclosure;
- pagination/resource limits;
- version/inventory exposure;
- abuse/automation controls.

## Sensitive Business Flows

High-value or scarce-resource workflows need server-owned rules such as:
- eligibility;
- ordering/queue position;
- quota;
- uniqueness;
- reservation/claim ownership;
- approval;
- cooldown;
- terminal-state protection.

Automation defenses support these rules. They do not replace them.

## Outbound Requests and SSRF Boundary

When the server fetches user-influenced URLs or connects to destinations derived from untrusted data:
- constrain allowed schemes/destinations according to the business need;
- resolve redirects and DNS/network trust deliberately;
- protect cloud/internal metadata and management endpoints through platform/network controls where relevant;
- apply time/size/resource limits;
- treat third-party responses as untrusted input.

Clockwork owns network/service architecture; Ponytail implements accepted controls.

## Upload and Content Boundary

Review:
- allowed content types and actual content handling;
- filename/path handling;
- size/count/resource limits;
- storage location and execution permissions;
- malware/content-scanning requirements only when project risk requires them;
- serving/download headers and access control;
- archive extraction boundaries where applicable.

## Background Jobs and Webhooks

Security context must survive non-browser execution.

Review:
- authenticated/verified origin where required;
- tenant/account context;
- idempotency/replay implications;
- authorization of the requested state transition;
- secret/signature handling;
- retry behavior and duplicate effects;
- audit correlation.

## Rate Limiting and Resource Protection

Choose controls based on the threatened resource:
- per identity/account/tenant;
- per operation;
- per expensive resource;
- per source/network when meaningful;
- global capacity protection.

Cipher defines the security objective. Clockwork places distributed controls. Dagger may test overload only when authorized. Overseer owns validation strategy.

## Third-Party API Consumption

External API responses are untrusted.

Review:
- endpoint trust;
- authentication/authorization to the provider;
- transport and certificate assumptions;
- response validation;
- redirect behavior;
- data sensitivity;
- failure/retry behavior;
- unsafe propagation of provider fields into commands, templates, queries or authorization decisions.

## Logging and Audit

Security logs should support the actual objective without becoming a data leak.

Record appropriate actor, action, target, result, time and correlation context. Do not log secrets or unnecessary sensitive values. Audit evidence never grants permission by itself.

## Specialist Boundaries

- Cipher: defensive security requirement.
- Clockwork: architecture/control placement.
- Ponytail: implementation.
- Chronicler: persistence/index/transaction mechanics.
- Cloak: frontend security UX.
- Overseer: validation/readiness.
- Dagger: controlled negative/resilience execution when authorized.