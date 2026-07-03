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
- Objects must encapsulate state and expose behavior. Keep cohesion high and coupling low.

## Advanced OOP / AOOP Foundations
- Favor composition over inheritance. Design to stable interfaces.

## SOLID Review Rules
- Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion.

## Layered Architecture Model
- Maintain strict separation: UI/Presentation -> Service/Application -> Domain -> Infrastructure/Persistence.

## Dependency Direction Rules
- Dependencies must point inward toward the Domain.

## Domain Layer Rules
- Domain objects own business rules where appropriate.
- Domain must not depend on JDBC, ORM, SQL, HTTP, framework annotations, or storage details unless the project intentionally uses an active record pattern and that pattern is explicitly approved.

## Application / Service Layer Rules
- Services coordinate workflows and transaction boundaries.

## Repository Layer Rules
- Repositories hide persistence details behind stable contracts.

## Infrastructure / Persistence Layer Rules
- Infrastructure implements persistence details, keeping DB code out of core layers.

## DTO, Entity, Domain Object, and View Model Boundaries
- Mapping logic must not leak into UI. Use DTOs to cross network boundaries.

## Service and Repository Contract Rules
- Contracts define what the system needs, implementations define how it gets done.

## Persistence Integration Rules
- Clockwork reviews persistence integration across layers but does not own schema design.

## Transaction Boundary Rules
- Transaction boundaries should wrap complete business workflows, not random individual helper calls.

## ORM / JDBC / API Persistence Boundary Rules
- Shield the domain from ORM specifics.

## Exception and Error Boundary Rules
- Persistence errors must not be swallowed silently.

## Refactor Safety Rules
- Evaluate structural refactoring risk before suggesting wide changes.

## Architecture Smell Checklist
- UI or controller must not query the database directly.
- UI or controller must not contain hidden business rules.

## Smallest Safe Fix Rule
- Target the exact boundary violation with the minimal required structural correction.

## Specialist Handoff Rules
- Delegate properly: Ponytail (Code), Chronicler (DB), Overseer (QA).

## Clockwork Review Checklist
- Check for UI coupling, domain pollution, and improper transaction scopes.
