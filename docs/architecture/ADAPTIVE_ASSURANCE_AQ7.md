# AQ-7 Runtime and Adapter Parity

AQ-7 exercises one bounded runtime path from an HTTP-shaped request through
authentication, tenant authorization, a domain invariant, an application
service, a persistence port, a provider-neutral persistence adapter, audit
serialization, and a stable response model.

The reference slice is intentionally framework-neutral. It exposes a direct
HttpRequest and HttpResponse handler rather than opening a socket or selecting
a production web framework. InMemoryTenantMemberRepository and
SQLiteTenantMemberRepository implement the same application port, so the
adapter contract can compare equivalent requests and responses without a
provider-specific authority model.

The exercised route is:

    PUT /tenants/{tenant_id}/members/{member_id}/role

The request body contains only role and optimistic-concurrency version. The
pipeline preserves these boundaries:

- authentication precedes authorization;
- authorization checks tenant and administrator scope before target lookup;
- unknown or cross-tenant targets cannot be enumerated by an unauthorized caller;
- the last administrator invariant is enforced in the domain;
- stale versions map to the same conflict response for both adapters;
- missing persistence or audit dependencies fail closed;
- duplicate or malformed JSON is rejected at the HTTP boundary;
- audit event fields and response models are deterministic and adapter-neutral.

The runtime test suite is the controlled AQ-7 challenge surface. It compares
in-memory and SQLite behavior, then exercises authentication denial, tenant
isolation, last-administrator protection, stale versions, invalid input, route
errors, missing dependencies, unexpected backend errors, and audit-field
serialization. It does not inject faults into production services, activate a
provider, open a network listener, weaken PRAI/AQ5, or authorize deployment.
