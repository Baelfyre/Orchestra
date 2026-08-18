# Adaptive Tuner A5

## Status

```text
Phase: A5.0
State: CONTRACT_FREEZE_NO_RUNTIME_TOPOLOGY_SELECTION
Issue: #340
Canonical entry head: fb0ace102d3ab0e662937bb4d824a40b103c1976
Canonical entry tree: c3f8b2efa4e1e75b64d5fc1ae10c92402a5b47f8
A4 execution-effective promotion: DEFERRED_NOT_PROMOTED
```

A5 begins only after the explicit A4 exit decision to retain the canonical A4 selector in shadow-only, non-authorizing mode. A5.0 defines the machine contracts needed to evaluate permitted coordination topologies later. It introduces no learned topology runtime behavior.

## Existing authority reused

A5 does not create a second coordination system. The existing cross-specialist coordination runtime and protocol remain authoritative for collaboration state, participants, ownership, contradictions, invalidation, readiness, and re-entry.

The role boundaries remain unchanged:

- Conductor owns routing and dispatch.
- The Tuner assembles and evaluates coordination state but does not route.
- Arbiter owns transition decisions.
- Overseer owns validation strategy and evidence quality.
- Domain specialists retain their existing domain decisions and ownership.
- Required specialists cannot be omitted by adaptive ranking.

The canonical existing surfaces are:

- `orchestra_runtime/coordination.py`
- `docs/routing/CROSS_SPECIALIST_COORDINATION_PROTOCOL.md`
- `orchestra_runtime/services.py`

## A5.0 purpose

A5.0 freezes three record types:

1. an immutable topology eligibility envelope;
2. an exact-option topology evidence packet;
3. a shadow topology decision.

The contract allows later A5 work to compare already-permitted coordination patterns such as sequential ordering, permitted parallel grouping, bounded decomposition, join/review points, required re-entry ordering, and permitted prior-output disclosure.

A5.0 does not rank or execute those patterns.

## Eligibility before ranking

Adaptive topology ranking may receive only candidates that have already passed deterministic coordination and runtime constraints.

Before a candidate can be considered eligible, the caller must establish that:

- the collaboration session is valid;
- all required specialists are present;
- domain ownership is complete and unchanged;
- The Tuner has not gained routing, approval, or transition authority;
- governance requirements are satisfied;
- open contradictions and stale contracts are resolved for the evaluated revision;
- provider/privacy restrictions remain satisfied;
- lifecycle state permits evaluation;
- deterministic resource and parallelism ceilings remain satisfied;
- context disclosure remains inside the existing ceiling.

The adaptive layer cannot add an unpermitted specialist, restore a blocked participant, omit a required specialist, change ownership, create authority, bypass a contradiction, suppress required re-entry, increase parallelism beyond deterministic ceilings, or expand context disclosure.

## Topology candidate boundary

A topology candidate is a complete already-permitted coordination arrangement bound to one collaboration session and one exact coordination-contract revision.

A candidate may describe:

- ordered sequential stages;
- an already-permitted parallel group;
- bounded decomposition among already-permitted specialists;
- explicit join or review points;
- required specialist re-entry ordering;
- references to prior outputs that are already permitted for disclosure.

The candidate is not a new authority envelope. It cannot grant capabilities, create a participant, change required specialist status, or alter a domain decision.

## Evidence qualification

A5 evidence must bind the exact topology candidate, collaboration session, and coordination-contract revision.

Allowed evidence classes at A5.0 are:

- governed coordination outcomes;
- validation evidence;
- remediation evidence;
- trustworthy measured telemetry.

Generic phase success is not topology-performance evidence. Raw conversation is not authority. Duplicate source digests count once. Latency, cost, token, iteration, remediation, validation-failure, or parallelism measurements may be used only when directly measured and provenance-bound.

A3 `WORKFLOW_TENDENCY` is not automatically topology evidence. The current A3 record does not guarantee exact topology identity binding, so A5.0 records no direct A3 topology-evidence support. A later unit may qualify such evidence only if the exact candidate identity and scope can be proven without inventing a bridge.

## Precedence

The frozen precedence order is:

```text
Deterministic authority/capability/governance/privacy/ownership/resource ceilings
  > required specialist and required re-entry completeness
  > explicit current user constraint
  > explicit scoped user preference
  > qualified exact-topology evidence
  > deterministic coordination order
```

Confidence or score is never authority.

## Shadow decision

Any later A5 shadow decision must preserve:

```text
execution_controlled_by = DETERMINISTIC_ORCHESTRA
dispatch_controlled_by = CONDUCTOR
transition_controlled_by = ARBITER
topology_effective = false
shadow_influenced_execution = false
promotion_state = NOT_PROMOTED
```

Missing evidence, invalid evidence, an unavailable adaptive layer, or no eligible topologies must fall back to the existing deterministic coordination behavior or fail closed when no deterministic candidate exists.

## A4 boundary at A5 entry

A4 remains canonical but intentionally non-promoted for execution control. A5 does not reinterpret A4 shadow selection as permission to change dispatch, worker execution, specialist ownership, provider eligibility, or route selection.

The A4 post-execution attachment may be used as historical architecture evidence only. It is not an A5 authority source.

## Required adversarial validation for A5 implementation

Any A5.1 or later implementation must prove at minimum that:

- required specialists cannot be omitted;
- unpermitted specialists cannot be added;
- domain ownership cannot be reassigned;
- The Tuner cannot become a router or transition authority;
- open contradictions, missing ownership, and stale contracts cannot be bypassed;
- authority, capability, governance, privacy, disclosure, and resource ceilings cannot expand;
- required specialist re-entry cannot be suppressed;
- duplicate evidence does not inflate support;
- generic phase success does not become topology success;
- unmeasured metrics are not invented;
- cross-scope evidence fails closed;
- shadow topology cannot alter execution or dispatch;
- malformed or stale coordination identity fails closed;
- deterministic fallback preserves current coordination behavior.

## Future boundary

A5.0 authorizes only this contract freeze.

Not implemented by A5.0:

- A5.1 shadow topology ranker;
- topology-effective coordination selection;
- automatic policy promotion;
- additional parallel execution capability;
- learned specialist omission or ownership changes;
- A6 adaptive context routing;
- A7 Conductor route ranking or offline policy promotion;
- A8 recursive or test-time compute;
- release, deployment, or publication.

Each later transition requires a fresh canonical reread and separately bounded authorization.
