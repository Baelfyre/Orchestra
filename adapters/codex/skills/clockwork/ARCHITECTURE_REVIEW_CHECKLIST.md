# Architecture Review Checklist

## Evidence First
- [ ] Relevant files, callers, state owners, and runtime boundaries were inspected before making architecture claims.
- [ ] Repository conventions and explicit project constraints were identified before recommending a pattern.
- [ ] Assumptions are separated from verified architecture facts.

## Foundational OOP Review
- [ ] Encapsulation is preserved; internal state and implementation details are not exposed unnecessarily.
- [ ] Abstraction is clear; callers depend on stable behavior or contracts, not concrete implementation details.
- [ ] Polymorphism is used where appropriate to reduce type-checking, duplicated branching, and caller-specific logic.
- [ ] Inheritance is valid, substitutable, and not used where composition would be safer.
- [ ] Cohesion is high enough that responsibilities have clear reasons to change.
- [ ] Coupling is intentional and does not leak infrastructure details into domain logic.

## Layer Boundaries
- [ ] UI or controller does not query the database directly unless an explicitly approved architecture requires it.
- [ ] UI or controller does not contain hidden business rules.
- [ ] Services coordinate workflows without becoming unrelated logic dumping grounds.
- [ ] Repositories hide persistence details behind appropriate contracts.
- [ ] Domain logic does not depend on transport, framework, ORM, queue, or cache implementation details without an explicit architecture decision.

## State and Concurrency Ownership
- [ ] Every mutable state surface has an identifiable owner.
- [ ] Shared mutable state has explicit concurrency and conflict semantics.
- [ ] Ordering requirements are stated at the narrowest necessary scope.
- [ ] Duplicate execution behavior is defined for concurrent, retried, queued, or scheduled work.
- [ ] Cancellation, timeout, retry, and backpressure ownership are identified where concurrency makes them relevant.
- [ ] A distributed lock is not recommended when the invariant can be enforced more simply at the authoritative state owner.

## Service and Distributed Boundaries
- [ ] Each service/process boundary has a demonstrated ownership, deployment, scaling, data, or failure-isolation reason.
- [ ] Chatty cyclic service dependencies are absent or explicitly justified.
- [ ] Network calls are treated as partial-failure boundaries.
- [ ] Compatibility expectations are explicit for cross-process contracts.
- [ ] A modular/in-process boundary was considered before adding distributed infrastructure.

## API Evolution
- [ ] Existing API/versioning conventions were inspected before proposing a strategy.
- [ ] Additive compatible evolution is preferred when feasible.
- [ ] Breaking changes identify affected consumers and migration boundaries.
- [ ] Defaults, enum expansion, pagination, ordering, and error contracts are reviewed where applicable.

## Caching
- [ ] The authoritative source of truth is named.
- [ ] Cache ownership and invalidation ownership are explicit.
- [ ] Freshness and stale-read tolerance are defined.
- [ ] Cache failure behavior is defined.
- [ ] Tenant/security-sensitive cache concerns are handed to Cipher where applicable.

## Multi-Tenancy
- [ ] Tenant context entry and propagation boundaries are identified.
- [ ] Jobs, events, caches, and service calls retain the correct tenant context where required.
- [ ] Clockwork does not invent authorization or persistence isolation mechanics.
- [ ] Cipher and Chronicler handoffs are explicit where tenant security or persistence enforcement is involved.

## Event-Driven Architecture
- [ ] Message intent is clear: event reports a fact; command requests an action.
- [ ] Producer ownership is clear.
- [ ] Duplicate, delayed, reordered, retried, or replayed delivery behavior is considered when relevant.
- [ ] Idempotency responsibility is identified for retryable or duplicate-prone effects.
- [ ] Event contracts do not expose internal persistence models unnecessarily.
- [ ] Eventual-consistency boundaries identify authoritative and derived state.

## Jobs and Workflows
- [ ] Background job producer/trigger, payload, worker, and state-transition ownership are explicit.
- [ ] Retry and failed-work ownership are explicit.
- [ ] Long-running workflows define durable state, step boundaries, terminal states, compensation, cancellation, and human-gated transitions where applicable.
- [ ] A scheduler is not being used as an implicit workflow engine without clear state ownership.
- [ ] Protected human gates remain authority boundaries and are not converted into implicit automation permission.

## Outbox and Inbox
- [ ] Outbox is considered only when local state mutation and durable publication can diverge.
- [ ] Outbox dispatcher ownership and duplicate-publication expectations are explicit.
- [ ] Inbox/deduplication is considered only when durable consumer processing identity is required.
- [ ] Schema and database transaction mechanics are routed to Chronicler.

## Refactor Safety
- [ ] Current callers and compatibility surfaces are identified.
- [ ] State ownership changes are explicit.
- [ ] Migration sequencing and rollback constraints are considered.
- [ ] The smallest safe structural correction is preferred over a broad rewrite.

## Scope Enforcement
- [ ] Implementation is routed to Ponytail.
- [ ] Security policy, auth/RBAC, privacy, secrets, and threat modeling are routed to Cipher.
- [ ] Schema, SQL, migrations, indexes, database isolation mechanics, and persistence design are routed to Chronicler.
- [ ] UI/UX and accessibility requirements are routed to Cloak.
- [ ] QA strategy, test scope, validation gates, and release readiness are routed to Overseer.
- [ ] Documentation is routed to Scribe.
- [ ] Ambiguous or multi-specialist sequencing is routed to Conductor.

## Structured Knowledge
- [ ] `patterns/architecture-patterns.json` is used only for deterministic lookup where useful.
- [ ] JSON pattern metadata does not override repository evidence, user requirements, or Markdown guidance.
- [ ] No pattern match is treated as automatic permission to introduce infrastructure, dependencies, or protected actions.
