# Event-Driven and Workflow Architecture Guide

## Purpose

Provide Clockwork with architecture guidance for events, queues, asynchronous processing, outbox/inbox placement, retries, idempotency, and durable workflows while preserving specialist boundaries.

## Event vs Command

Use an event to report that something happened. Use a command to request that an owner perform an action.

Review whether the message contract expresses:
- fact vs request;
- producer ownership;
- consumer expectations;
- correlation identity;
- compatibility expectations;
- ordering assumptions;
- duplicate-delivery behavior.

Do not disguise synchronous request/response coupling as event-driven architecture merely by putting a broker between components.

## Event Ownership

An event should be published by the component that owns the state transition or authoritative fact.

Consumers should not need private producer implementation details to understand the contract.

Avoid events that expose internal persistence models wholesale. Prefer stable domain or integration contracts where a boundary is required.

## Delivery Semantics

Treat common messaging as potentially duplicated, delayed, reordered, or retried unless the actual platform contract proves stronger guarantees.

Architecture review should define which of these matter to the business invariant:
- at-most-once effects;
- at-least-once delivery tolerance;
- ordering by key or aggregate;
- duplicate suppression or idempotent handling;
- replay behavior;
- poison-message handling.

Do not claim exactly-once business effects merely because a transport advertises exactly-once features. End-to-end side effects still require architecture review.

## Idempotency

Idempotency means repeated processing produces an acceptable final effect for the same logical operation.

Identify:
- the logical operation identity;
- the state owner that can detect or tolerate repetition;
- the side effects that must not repeat;
- the retention window for deduplication when one is needed.

Clockwork defines where the idempotency boundary belongs. Chronicler owns persistence mechanics. Ponytail implements the accepted design. Overseer owns validation strategy.

## Transactional Outbox

Consider an outbox when one local business transaction must update authoritative state and reliably publish a message without a distributed transaction.

Clockwork reviews:
- which transaction owns the state change;
- where the outbox record belongs architecturally;
- which dispatcher owns publication;
- duplicate-publication expectations;
- consumer idempotency requirements;
- failure recovery boundary.

Chronicler owns the outbox schema, indexes, transaction details, and query mechanics.

Do not add an outbox when no durable message publication problem exists.

## Inbox or Consumer Deduplication

Consider an inbox/deduplication boundary when consumers must safely tolerate repeated delivery and the state owner needs durable processing identity.

Clockwork defines the boundary and responsibility. Chronicler owns persistence implementation. Ponytail implements.

## Retry Architecture

Retries are safe only when the operation can tolerate repetition or has a compensating guard.

Define:
- retry owner;
- retryable failure classes at an architectural level;
- maximum attempt or terminal-failure boundary when requirements specify one;
- backoff ownership;
- duplicate side-effect risk;
- visibility of exhausted work.

Do not stack retries independently at multiple layers without understanding multiplication of attempts and latency.

## Dead-Letter or Failed-Work Boundary

When the messaging platform or workflow requires failed-work retention, identify:
- who owns triage;
- whether replay is safe;
- whether the original contract version remains available;
- whether manual intervention is required;
- whether replay can violate current invariants.

Clockwork does not invent operational runbooks or production actions. It defines the architecture boundary that must exist.

## Ordering

Require ordering only where the domain invariant needs it.

If ordering matters, identify its scope:
- global;
- tenant;
- account;
- aggregate;
- entity;
- partition/key.

Global ordering is expensive and often unnecessary. Prefer the narrowest ordering scope that preserves the invariant.

## Eventual Consistency

When state is asynchronously propagated, identify:
- authoritative source;
- derived projection or replica;
- expected lag tolerance;
- user-visible stale-state behavior where applicable;
- reconciliation owner;
- conflict behavior.

A projection, cache, search index, or read model must not silently become the write authority unless the architecture explicitly assigns it that role.

## Background Jobs

For queued or scheduled jobs, define:
- producer or schedule owner;
- payload contract;
- worker owner;
- state transition owner;
- duplicate execution behavior;
- cancellation and timeout behavior;
- retry ownership;
- failed-job visibility.

Avoid passing large mutable internal objects as job payloads when a stable identifier or boundary DTO is sufficient.

## Workflow Patterns

Use a durable workflow model when work spans multiple steps that must survive process restarts, wait on external systems, require compensation, or pause for human decisions.

### Orchestration

A coordinator owns workflow state and tells participants what step to execute next.

Use when explicit sequencing, state visibility, compensation, or human-gated transitions are central.

Risk: the coordinator can become an overly coupled central service if it absorbs participant business logic.

### Choreography

Participants react to events without a central step coordinator.

Use when reactions are naturally independent and the global workflow does not require one owner to control every transition.

Risk: implicit flow, difficult tracing, cyclic reactions, and unclear ownership.

Choose based on ownership and failure requirements, not fashion.

## Saga and Compensation

A saga coordinates multiple local transactions when one atomic transaction cannot span the required boundaries.

Define:
- each local transaction owner;
- compensation semantics;
- irreversible side effects;
- failure transitions;
- retry behavior;
- operator or human-gated recovery points.

Compensation is not automatic rollback. It is a separate business action and may itself fail.

## Human Gates

A workflow may represent a protected approval or publication gate, but it must not convert the gate into implicit authority.

The existence of a workflow step, passing validation, mergeability, or successful prior execution does not create permission for a protected action.

## Message Contract Evolution

Review event and command evolution for:
- additive fields;
- required vs optional semantics;
- enum expansion;
- producer/consumer deployment order;
- old consumer tolerance;
- replay compatibility;
- schema/version ownership.

Clockwork defines compatibility architecture. Ponytail implements. Overseer owns contract-test strategy.

## Specialist Handoffs

- Broker/client implementation -> Ponytail
- Auth, message trust, privacy, secrets, and abuse controls -> Cipher
- Outbox/inbox schema, database transaction mechanics, locks, and persistence -> Chronicler
- Validation strategy, failure injection, regression, and release readiness -> Overseer
- Multi-specialist sequencing -> Conductor
