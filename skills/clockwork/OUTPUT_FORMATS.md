# Clockwork Output Formats

Generate output using exactly one format below. Default to `Compact` unless `Full` or `ArchitectureComplexityDecision` is requested.

## Compact

Use for quick audits, narrow architecture decisions, or mid-workflow boundary checks.

```markdown
# Clockwork Quick Check

**Status:** [Ready / Not ready / Needs clarification]
**Scope:** [Files inspected / Boundaries involved]

## Boundary Map
**Allowed:**
- [Observed or accepted dependency / ownership direction]

**Blocked:**
- [Observed or proposed boundary that violates the architecture contract]

## Findings
1. [Evidence-based architecture finding]

## Smallest Safe Fix
[Architecture correction or "Audit only"]

## Handoff
- [Owning specialist and decision or implementation needed]

**Stop/Go:** [Safe for downstream implementation / Audit only / Blocked / Needs user approval]
```

## Full

Use for comprehensive architecture reviews, distributed-boundary reviews, deep OOP/SOLID analysis, or material refactor planning. This is an architecture review, not a Ponytail implementation plan and not an Overseer QA plan.

```markdown
# Clockwork Architecture Review

## 1. Readiness status
[Ready / Not ready / Ready with minor notes / Needs clarification]

## 2. Scope observed
- **Files inspected:** [List]
- **Boundaries involved:** [UI, Application, Domain, Repository, Infrastructure, Service, API, Event, Cache, Job, Workflow]
- **Runtime topology observed:** [In-process / Multi-process / Distributed / Unknown]
- **State owners observed:** [List]
- **Assumptions:** [Only unverified assumptions]

## 3. Architecture findings
[For each finding:]
- **Finding:** [Description]
- **Evidence:** [File/module/service/API/event/state evidence]
- **Boundary involved:** [Boundary]
- **Principle affected:** [Ownership, cohesion, coupling, dependency direction, compatibility, concurrency, idempotency, etc.]
- **Risk level:** [low / medium / high / blocker]
- **Why it matters:** [Architecture impact]
- **Smallest safe fix:** [Architecture correction]
- **Likely implementation surface:** [Files/modules/services likely affected]
- **Required handoff:** [Ponytail/Cipher/Chronicler/Cloak/Overseer/Conductor/None]

## 4. Boundary map
- **Presentation/UI ownership:** [Observed]
- **Application/service ownership:** [Observed]
- **Domain ownership:** [Observed]
- **Persistence/infrastructure boundary:** [Observed]
- **State/concurrency ownership:** [Observed]
- **External/API/event/job/workflow boundaries:** [Observed]

## 5. Pattern decision
- **Pattern considered:** [Pattern or None]
- **Decision:** [Use / Reject / Defer]
- **Repository evidence:** [Why]
- **Complexity introduced:** [New failure/operational boundaries]

## 6. Refactor recommendation
[No refactor needed / Small patch recommended / Incremental refactor recommended / Broad refactor requires separate approval / Refactor unsafe now]

## 7. Downstream validation properties
- [Architecture property downstream implementation or QA should preserve or prove]
- [Compatibility, idempotency, ordering, failure isolation, cache invalidation, tenant propagation, etc.]

Clockwork does not own the QA strategy. Route test scope, gate selection, and release readiness to Overseer.

## 8. Specialist handoffs
- **Ponytail:** [Implementation boundary or None]
- **Cipher:** [Security decision or None]
- **Chronicler:** [Persistence decision or None]
- **Cloak:** [UI/UX decision or None]
- **Overseer:** [Validation ownership or None]
- **Conductor:** [Sequencing/routing need or None]

## 9. Stop/go decision
[Safe for downstream implementation / Audit only / Needs user approval before broad changes / Blocked]
```

## ArchitectureComplexityDecision

Use when evaluating proposed architectural or infrastructure complexity (new databases, caches, queues, microservices, workers, replicas, multi-region, or orchestrators) against upstream `ProductIntentContract` and `CapacityEnvelope` inputs.

```text
CONTRACT: ArchitectureComplexityDecision
SCHEMA: orchestra.architecture-complexity-decision.v1
OWNER: clockwork
REVISION: [revision]
REQUESTED_CHANGE: [exact architectural change proposed]
CURRENT_ARCHITECTURE: [baseline architecture]
REQUIREMENT_DRIVER: [concrete accepted requirement]
CAPACITY_ENVELOPE_REF: [revision or URI, if applicable]
COMPLEXITY_ADDED: [database, cache, queue, event_bus, service, worker, replica, container, orchestrator, search_cluster, multi_region, cloud_provider, other]
JUSTIFICATION_CATEGORIES: [CURRENT_FUNCTIONAL_REQUIREMENT | MEASURED_PERFORMANCE_BOTTLENECK | SECURITY_REQUIREMENT | RELIABILITY_REQUIREMENT | ISOLATION_REQUIREMENT | COMPLIANCE_REQUIREMENT | CAPACITY_THRESHOLD | OPERATIONAL_REQUIREMENT | APPROVED_ARCHITECTURE_DECISION]
SCALE_POSTURE_BEFORE: [SCALE_READY | SCALE_PROVISIONED]
SCALE_POSTURE_AFTER: [SCALE_READY | SCALE_PROVISIONED]
SIMPLER_ALTERNATIVES: [list of simpler alternatives considered]
DECISION: [ACCEPT | ACCEPT_WITH_CONSTRAINTS | DEFER | REJECT]
CONSTRAINTS: [list of constraints or "none"]
EVIDENCE_REFS: [benchmarks, tickets, requirements, or contracts]
```
