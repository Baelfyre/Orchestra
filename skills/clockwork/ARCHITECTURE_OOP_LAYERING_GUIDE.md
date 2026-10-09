# Architecture, OOP, and Layering Guide

## Purpose
Enhance Clockwork with sufficient foundational knowledge for OOP, AOOP, layered architecture, persistence integration, repository/service boundaries, transaction placement, and database handoff boundaries.

## Clockwork Scope
Clockwork is an architecture and boundary specialist. Do not rewrite Clockwork into a coding specialist. Clockwork defines boundaries; it does not implement application code.

## Boundary with Chronicler
- Clockwork reviews persistence integration across architecture layers.
- Chronicler owns schema, normalization, SQL, migrations, indexes, seed data, and database report logic.

## Boundary with Ponytail
- Clockwork defines the boundary and hands off to Ponytail.
- Ponytail owns actual implementation after Clockwork defines the boundary.

## Boundary with Overseer
- Overseer owns validation plans, test strategy, regression, and release readiness.

## OOP Foundations
- Objects must encapsulate state and expose behavior.
- Objects should have high cohesion and low coupling.
- OOP review must explicitly check encapsulation, abstraction, polymorphism, and inheritance before relying on broader SOLID review.

## Foundational OOP Pillar Checks

### Encapsulation
- Verify that object state is protected from unnecessary external access.
- Verify that callers interact through methods, interfaces, or clear boundaries instead of directly modifying internal data.
- Flag public fields, exposed mutable collections, leaked persistence objects, or UI code that mutates domain state directly.
- Treat repositories, services, and domain objects as separate access boundaries.

### Abstraction
- Verify that callers depend on essential behavior rather than implementation details.
- Verify that public contracts hide complexity that the caller does not need to know.
- Prefer stable interfaces, domain methods, service contracts, DTOs, or boundary objects where they reduce coupling.
- Flag code that forces callers to know storage details, framework details, SQL details, or internal workflow steps.

### Polymorphism
- Verify that shared interfaces, base types, or contracts allow different implementations to behave correctly through the same call site.
- Prefer polymorphic behavior when it removes duplicated branching, long type checks, or caller-specific conditionals.
- Verify that each implementation owns its own behavior instead of forcing the caller to decide every variation.
- Keep polymorphism simple and justified; do not introduce abstractions that the project does not need.

### Inheritance
- Verify that inheritance represents a valid is-a relationship.
- Verify that subclasses preserve the expectations of the parent type and can safely substitute for the parent.
- Prefer composition when reuse does not require a true parent-child model.
- Flag inheritance used only to share utilities, bypass access boundaries, or force unrelated classes into one hierarchy.

## Advanced OOP / AOOP Foundations
- Favor composition over inheritance when the relationship is has-a, uses-a, or varies by behavior.
- Design to stable interfaces when it improves substitutability, testability, or boundary clarity.
- Keep inheritance shallow unless the domain model clearly requires a hierarchy.
- Avoid speculative abstraction. Create interfaces, base types, or abstract classes only when they clarify variation or protect a real boundary.

## SOLID Review Rules
- Single Responsibility: Each class, method, or module should have one clear reason to change.
- Open/Closed: New behavior should be addable without unsafe edits to stable, tested code where practical.
- Liskov Substitution: Subtypes must preserve the contract and expectations of their parent type.
- Interface Segregation: Callers should not depend on methods they do not use.
- Dependency Inversion: High-level policy should depend on stable contracts, not low-level implementation details.

## Layered Architecture Model
- Maintain strict separation: UI/Presentation -> Service/Application -> Domain -> Infrastructure/Persistence.

## Dependency Direction Rules
- Dependencies must point inward toward the Domain.
- Domain should not depend on UI, persistence, framework, transport, or infrastructure concerns.

## Domain Layer Rules
- Domain objects own business rules where appropriate.
- Domain must not depend on JDBC, ORM, SQL, HTTP, framework annotations, or storage details unless the project intentionally uses an active record pattern and that pattern is explicitly approved.

## Application / Service Layer Rules
- Services coordinate workflows and transaction boundaries.
- Services should call repositories through stable contracts where practical.
- Services should not become dumping grounds for unrelated business rules.

## Repository Layer Rules
- Repositories hide persistence details behind stable contracts.
- Repositories should not contain UI logic.
- Repositories should not expose storage-specific details unless the boundary explicitly allows it.

## Infrastructure / Persistence Layer Rules
- Infrastructure implements persistence details, keeping DB code out of core layers.

## DTO, Entity, Domain Object, and View Model Boundaries
- Mapping logic must not leak into UI.
- Use DTOs to cross network or external boundaries where appropriate.
- Do not treat database entities, UI view models, and domain objects as automatically interchangeable.

## Service and Repository Contract Rules
- Contracts define what the system needs, implementations define how it gets done.
- Contracts should be stable, focused, and aligned to caller needs.

## Persistence Integration Rules
- Clockwork reviews persistence integration across layers but does not own schema design.

## Transaction Boundary Rules
- Transaction boundaries should wrap complete business workflows, not random individual helper calls.

## ORM / JDBC / API Persistence Boundary Rules
- Shield the domain from ORM specifics.

## Exception and Error Boundary Rules
- Persistence errors must not be swallowed silently.
- Exceptions should cross boundaries in a form appropriate to the receiving layer.

## Refactor Safety Rules
- Evaluate structural refactoring risk before suggesting wide changes.

## Architecture Smell Checklist
- UI or controller must not query the database directly.
- UI or controller must not contain hidden business rules.
- Domain objects must not expose unnecessary mutable state.
- Long type checks should be reviewed for possible polymorphic replacement.
- Inheritance should be reviewed when a class hierarchy appears forced or fragile.

## Smallest Safe Fix Rule
- Target the exact boundary violation with the minimal required structural correction.

## Specialist Handoff Rules
- Delegate properly: Ponytail (Code), Chronicler (DB), Overseer (QA).

## Clockwork Review Checklist
- Check for UI coupling, domain pollution, improper transaction scopes, and foundational OOP pillar violations.
