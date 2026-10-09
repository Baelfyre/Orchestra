# Modern Application Architecture Guide

## Purpose

Provide Clockwork with architecture foundations for modern application boundaries without turning Clockwork into an implementation, database, security, deployment, or QA specialist.

## Architecture Selection Rule

Choose the simplest architecture that satisfies the accepted requirements and observed constraints.

Do not recommend microservices, queues, caches, workflow engines, distributed locks, service meshes, or separate runtimes only because they are common patterns. Every added boundary creates operational and failure complexity.

## Architecture Complexity and Scale Posture Governance

For evaluating proposed additions of material architecture or infrastructure complexity, simpler alternatives, and scale posture (SCALE_READY vs SCALE_PROVISIONED), load [ARCHITECTURE_COMPLEXITY_AND_SCALE_POSTURE_GUIDE.md](ARCHITECTURE_COMPLEXITY_AND_SCALE_POSTURE_GUIDE.md).

Primary Invariant:
`FUTURE_SCALABILITY_ALONE_IS_NOT_SUFFICIENT_JUSTIFICATION`

Use repository evidence to answer:

1. What owns the behavior?
2. What owns the state?
3. What consistency is required?
4. What is the failure boundary?
5. What must scale independently?
6. What compatibility contract exists?
7. What latency and availability assumptions are acceptable?
8. Which decisions belong to another specialist?

## Modular Monolith vs Distributed Services

A modular monolith is appropriate when:
- one deployment unit is acceptable;
- domain/module boundaries can be enforced in-process;
- independent scaling or fault isolation is not required;
- transactional workflows benefit from local coordination;
- operational simplicity has higher value than deployment independence.

A service boundary may be justified when there is evidence for one or more of these needs:
- independent deployment cadence;
- independent scaling profile;
- explicit team or ownership boundary;
- fault containment;
- technology/runtime isolation required by a real constraint;
- independent availability objective;
- data ownership that must be isolated behind a stable service contract.

A service split is not justified solely by file size, class count, theoretical purity, or the existence of a domain noun.

## Service Boundary Review

For each proposed service, identify:
- owned capability;
- owned state or authoritative data contract;
- public and internal interfaces;
- synchronous and asynchronous dependencies;
- failure behavior when dependencies are unavailable;
- compatibility expectations;
- observability boundary;
- downstream specialist decisions still required.

Avoid cyclic service dependencies. If two services require frequent coordinated changes and synchronous round trips for one business operation, review whether the boundary is premature or misplaced.

## Dependency Direction

Prefer dependencies toward stable policy contracts rather than volatile infrastructure details.

At process boundaries, treat network interfaces as fallible external contracts even when both processes are maintained in one repository.

Do not let a domain model depend directly on transport clients, queue SDKs, cache SDKs, ORM details, or vendor-specific service discovery unless the architecture explicitly accepts that coupling.

## API Boundary and Versioning

Versioning exists to manage compatibility. It does not replace careful contract evolution.

Review:
- request and response compatibility;
- field addition/removal semantics;
- default behavior;
- enum expansion behavior;
- pagination and ordering contracts;
- error contract stability;
- deprecation path;
- consumer migration needs.

Prefer additive compatible evolution when feasible. Introduce a new version only when incompatible behavior is necessary and the project has a real versioning boundary.

Do not invent URL, header, media-type, or schema versioning conventions when the repository already has one.

## State Ownership

Every mutable state surface should have one primary owner.

Examples include:
- domain aggregate state;
- session state;
- workflow state;
- queue ownership;
- scheduled-job ownership;
- cache entries;
- in-memory coordination state;
- derived projections.

Shared writable state across unrelated components increases coupling and race risk. Prefer an explicit owner with stable access contracts.

## Concurrency Ownership

For concurrent work, identify:
- the unit of concurrency;
- the state being protected or coordinated;
- whether operations may run in parallel;
- ordering requirements;
- duplicate execution behavior;
- conflict resolution semantics;
- cancellation and timeout ownership;
- retry safety;
- resource limits and backpressure boundary.

Clockwork defines ownership and architecture expectations. Chronicler owns database isolation and locking mechanics. Ponytail owns implementation. Overseer owns the validation strategy.

Do not recommend a distributed lock before proving that the protected invariant spans processes and cannot be enforced more simply at the authoritative state boundary.

## Caching Architecture

A cache review must name:
- the authoritative source of truth;
- cache owner;
- key scope;
- freshness expectations;
- invalidation owner;
- stale-read tolerance;
- failure behavior when the cache is unavailable;
- tenant and security sensitivity where applicable.

Cache-aside, write-through, write-behind, and refresh-ahead are different consistency choices. Do not select one without matching the accepted freshness and failure requirements.

A cache must not silently become a second source of truth.

Cipher owns sensitive-data and authorization concerns. Chronicler owns persistence implications. Ponytail owns implementation.

## Multi-Tenant Architecture

Clockwork reviews structural tenant boundaries, including:
- where tenant context enters the system;
- how tenant context propagates across service, job, event, and cache boundaries;
- which components are tenant-aware;
- where cross-tenant aggregation is intentionally allowed;
- which components must remain tenant-neutral;
- how background work retains the correct tenant context.

Clockwork does not define authorization policy or database enforcement mechanics.

Handoffs:
- Cipher: tenant trust, authorization, privacy, and isolation requirements;
- Chronicler: row/schema/database isolation, constraints, indexes, and persistence mechanics;
- Ponytail: implementation;
- Overseer: validation strategy.

## Background Jobs and Schedulers

A background-job architecture should define:
- producer/trigger owner;
- job payload contract;
- worker owner;
- retry and duplicate-execution expectations;
- timeout/cancellation behavior;
- idempotency expectation;
- scheduling semantics;
- visibility of failed or abandoned work.

Do not use a scheduler as a hidden workflow engine. If work spans multiple durable steps with compensation, pause/resume, or human approval, review whether an explicit workflow model is required.

## Long-Running Workflows

For multi-step workflows, identify:
- durable workflow state owner;
- step boundaries;
- success and failure transitions;
- retryable vs terminal failures;
- compensation requirements;
- external side effects;
- idempotency boundaries;
- timeout and cancellation semantics;
- human-gated transitions.

Clockwork defines the workflow architecture. It does not bypass governance or convert protected human gates into automated transitions.

## Failure Boundary Review

Distributed boundaries require explicit treatment of:
- partial failure;
- timeout;
- retry;
- duplicate delivery or execution;
- out-of-order messages;
- stale reads;
- unavailable dependencies;
- degraded operation;
- recovery ownership.

Do not claim exactly-once execution from ordinary messaging or retries. Prefer designing handlers and state transitions so repeated delivery is safe where possible.

## Observability Boundary

Architecture review should identify where correlation or trace context must cross process, job, or event boundaries when the project already has observability requirements.

Clockwork does not select monitoring vendors or invent logging policy. It identifies the architectural points where observability continuity is necessary.

## Refactor Safety

Before splitting modules, services, queues, caches, or workflows:
- identify current callers and dependencies;
- identify compatibility surfaces;
- identify state ownership changes;
- identify migration sequencing;
- identify temporary dual-write or dual-read risk if applicable;
- identify rollback constraints;
- prefer a strangler or incremental boundary move when a big-bang rewrite is not necessary.

## Specialist Handoffs

- Implementation -> Ponytail
- Security policy and threat modeling -> Cipher
- Persistence and database mechanics -> Chronicler
- QA strategy and release readiness -> Overseer
- UI/UX -> Cloak
- Documentation -> Scribe
- Multi-specialist sequencing -> Conductor
