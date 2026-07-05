# Architecture Review Checklist

## Foundational OOP Review
- [ ] Encapsulation is preserved; internal state and implementation details are not exposed unnecessarily.
- [ ] Abstraction is clear; callers depend on stable behavior or contracts, not concrete implementation details.
- [ ] Polymorphism is used where appropriate to reduce type-checking, duplicated branching, and caller-specific logic.
- [ ] Inheritance is valid, substitutable, and not used where composition would be safer.

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

## SOLID Alignment
- [ ] Single Responsibility is preserved; each class, method, or module has one clear reason to change.
- [ ] Open/Closed is considered where new behavior should be added without unsafe edits to stable code.
- [ ] Liskov Substitution is preserved for any subtype or inherited model.
- [ ] Interface Segregation is preserved; callers do not depend on methods they do not use.
- [ ] Dependency Inversion is applied where high-level policy should depend on stable contracts.

## Scope Enforcement
- [ ] Schema, SQL, migrations, and database design are routed to Chronicler.
- [ ] Validation, test strategy, and release readiness are routed to Overseer.
- [ ] Code implementation is routed to Ponytail.
