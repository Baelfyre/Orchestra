# Diagram Standards

Use the project's source artifacts and chosen abstraction level as the authority.

## General

- State objective, audience, scope, current or proposed status, and notation.
- Keep names consistent with code, schema, requirements, or approved terminology.
- Label nonstandard symbols and relationship semantics.
- Avoid mixed abstraction levels and decorative detail that obscures meaning.
- Split diagrams when independent concerns cannot remain readable together.

## UML Class Diagrams

- Show only classes and interfaces relevant to the objective.
- Use association, dependency, generalization, realization, aggregation, and composition deliberately.
- Show multiplicity only when evidence supports it.
- Review responsibility, coupling, cohesion, encapsulation, and substitutability.

## Use Case Diagrams

- Place system behavior inside a named boundary and external roles outside it.
- Name use cases as user goals, not screens or implementation methods.
- Use `include`, `extend`, and actor generalization only when confirmed.

## Sequence Diagrams

- Show the initiating actor, relevant lifelines, ordered messages, and meaningful returns.
- Distinguish synchronous, asynchronous, alternative, loop, failure, and timeout behavior.
- Keep messages at one abstraction level and align ownership with code or architecture.

## Activity Diagrams

- Use clear start and end nodes, actions, guarded decisions, merges, forks, and joins.
- Distinguish parallel work from alternative paths.
- Use swimlanes only when responsibility matters.

## State Diagrams

- Model states, triggering events, guards, transitions, and terminal states for one lifecycle.
- Do not substitute workflow steps for true object or system states.
- Show recovery transitions when they affect correctness.

## Component Diagrams

- Show components, provided or required interfaces, and dependencies.
- Keep responsibilities and ownership explicit.
- Do not mix class-level detail into a component view.

## Deployment Diagrams

- Show runtime nodes, environments, artifacts, networks, protocols, and external services when known.
- Mark replication, regions, trust zones, and scaling only from evidence.
- Separate build-time and runtime relationships.

## ERDs

- State conceptual, logical, or physical level.
- Show entities, keys, relationships, cardinality, and optionality consistently.
- Resolve many-to-many relationships when an associative entity is confirmed.
- Do not infer constraints or columns absent from schema evidence.

## System Architecture Diagrams

- State context, container, component, or deployment level.
- Show actors, boundary, components, stores, external systems, direction, and known protocols.
- Distinguish current state from proposals and label trust or ownership boundaries.

## Workflow and User Flow Diagrams

- Begin with a trigger and end with a defined outcome.
- Label decisions, alternate paths, failures, and recovery.
- Anchor user flows to a user goal and entry point.
- Keep backend internals out unless they explain visible behavior.
