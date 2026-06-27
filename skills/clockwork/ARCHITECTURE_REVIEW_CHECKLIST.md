# Architecture Review Checklist

## Layer Boundaries
- [ ] UI or controller must not query the database directly.
- [ ] UI or controller must not contain hidden business rules.
- [ ] Services coordinate workflows and transaction boundaries.
- [ ] Repositories hide persistence details behind stable contracts.

## Domain Isolation
- [ ] Domain objects own business rules where appropriate.
- [ ] Domain must not depend on JDBC, ORM, SQL, HTTP, framework annotations, or storage details unless the project intentionally uses an approved active record pattern.

## Persistence Integration
- [ ] Persistence errors must not be swallowed silently.
- [ ] Transaction boundaries should wrap complete business workflows, not random individual helper calls.
- [ ] Mapping logic must not leak into UI.

## Scope Enforcement
- [ ] Schema, SQL, migrations, and database design are routed to Chronicler.
- [ ] Validation, test strategy, and release readiness are routed to Overseer.
- [ ] Code implementation is routed to Ponytail.
