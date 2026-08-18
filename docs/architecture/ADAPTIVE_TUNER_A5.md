# Adaptive Tuner A5

## Status

```text
Phase: A5 closeout
State: A5_CLOSED_AT_SHADOW_MATURITY_EXECUTION_PROMOTION_DEFERRED_BENEFIT_NOT_ESTABLISHED
Issue: #340
A5.0 canonical content tree: 5a8a2b66a44eb233643a37aa9365222d50a732df
A5.1 source baseline: 8a365eea7dd52022c427b83d7f3b484aba7152ff
A5.1 source baseline tree: 5a8a2b66a44eb233643a37aa9365222d50a732df
A5.1 canonical head: 8acb03802834e9e56b078496a3e5e0f1aa498ebf
A5.1 canonical tree: e493b260ba2def53fb46298109637f8635f99970
A5 execution-effective promotion: DEFERRED_NOT_PROMOTED
A6 authorization from A5 closeout: NONE
```

A5 begins only after the explicit A4 exit decision to retain the canonical A4 selector in shadow-only, non-authorizing mode. A5.0 defines the machine contracts needed to evaluate permitted coordination topologies. A5.1 implements and canonically integrates the bounded shadow scorer and exact topology evidence-qualification surface under those frozen contracts.

A5 closes at shadow maturity. The required topology parity and adversarial validation is satisfied, but measurable benefit over fixed eligible sequences is not established because no governed exact-topology comparative measurement set was available to the A5 closeout under the frozen evidence contract. Synthetic or generic phase success is not accepted as a substitute. Execution-effective topology selection therefore remains deferred and not promoted.

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

A5 adds no attachment to any of those execution or dispatch surfaces.

## A5.0 contract purpose

A5.0 froze three record types:

1. an immutable topology eligibility envelope;
2. an exact-option topology evidence packet;
3. a shadow topology decision.

The contract allows A5 work to compare already-permitted coordination patterns such as sequential ordering, permitted parallel grouping, bounded decomposition, join/review points, required re-entry ordering, and permitted prior-output disclosure.

A5.0 itself does not rank or execute those patterns.

## A5.1 implementation surface

A5.1 adds:

- runtime scorer and evidence qualification: `orchestra_runtime/adaptive/topology.py`;
- primary validation: `tests/runtime/test_adaptive_topology.py`;
- adversarial and fail-closed validation: `tests/runtime/test_adaptive_topology_edges.py`;
- machine implementation record: `machine/adaptive/a5-shadow-topology-ranker-implementation.v1.json`;
- scorer identity: `orchestra.adaptive-topology-scorer.v1`.

The A5.1 module is a pure bounded shadow surface. The caller supplies an eligibility envelope that has already been established by the deterministic coordination control plane. A5.1 neither discovers participants nor constructs new routing, authority, capability, provider, privacy, governance, lifecycle, or resource permissions.

The output remains structurally non-authorizing:

```text
execution_controlled_by = DETERMINISTIC_ORCHESTRA
dispatch_controlled_by = CONDUCTOR
transition_controlled_by = ARBITER
topology_effective = false
shadow_influenced_execution = false
promotion_state = NOT_PROMOTED
```

There is no A5 `RuntimeExecutor` attachment and no Conductor dispatch attachment.

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

A5.1 requires every frozen invariant field to be present and exactly true before the envelope is accepted.

The adaptive layer cannot add an unpermitted specialist, restore a blocked participant, omit a required specialist, change ownership, create authority, bypass a contradiction, suppress required re-entry, increase parallelism beyond deterministic ceilings, or expand context disclosure. A5.1 only reorders candidate identifiers that are already present in the immutable envelope.

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

A5.1 additionally verifies that every candidate carries the exact envelope coordination-contract revision and exact required-specialist set, and that every required specialist appears in the candidate topology. The ranker never adds a candidate that was absent from the envelope.

## Evidence qualification

A5 evidence must bind the exact topology candidate, collaboration session, and coordination-contract revision.

Allowed evidence classes remain:

- governed coordination outcomes;
- validation evidence;
- remediation evidence;
- trustworthy measured telemetry.

A5.1 exposes explicit qualification for those evidence classes only. Generic phase success is not topology-performance evidence. Raw conversation is not authority. Duplicate source digests count once. A single source digest cannot support multiple topology candidates in one decision.

Latency, cost, tokens, iterations, remediations, validation failures, or parallelism measurements may be used only when they are directly measured and provenance-bound. Telemetry evidence without a validated measurement record is rejected rather than inferred.

A3 `WORKFLOW_TENDENCY` is not topology evidence in A5.1. The A3 record does not guarantee exact topology identity binding, and A5.1 adds no invented bridge from generic workflow tendency to topology performance.

Evidence marked qualified is rechecked by the ranker. A candidate, session, or coordination-contract revision mismatch causes deterministic fallback even if an upstream caller incorrectly labeled the item as qualified.

## Precedence

The frozen precedence order remains:

```text
Deterministic authority/capability/governance/privacy/ownership/resource ceilings
  > required specialist and required re-entry completeness
  > explicit current user constraint
  > explicit scoped user preference
  > qualified exact-topology evidence
  > deterministic coordination order
```

Confidence or score is never authority.

An explicit current constraint prevents adaptive evidence from reordering the deterministic topology set. An explicit scoped preference may be a shadow preference only when that candidate is already eligible. It cannot restore or create a candidate.

## A5.1 deterministic shadow scoring

The named scorer is:

```text
orchestra.adaptive-topology-scorer.v1
```

The scorer:

- requires at least two distinct positive source digests before evidence can create an adaptive shadow preference;
- counts duplicate source digests once;
- scores each eligible candidate by net positive versus negative qualified evidence, then positive support, then neutral evidence;
- uses the existing deterministic eligible order as the stable tie break;
- returns deterministic fallback when qualified evidence does not meet the support floor;
- returns deterministic fallback for stale, mismatched, malformed, or cross-bound evidence;
- records `ADAPTIVE_UNAVAILABLE` when the adaptive layer is explicitly unavailable;
- fails closed with `NO_ELIGIBLE_TOPOLOGIES` when the immutable eligible set is empty.

A shadow recommendation is descriptive evidence only. It cannot change the actual deterministic topology.

## Parallel topology boundary

A candidate may contain a `PARALLEL` stage only when the deterministic caller has already established that the topology is eligible under the existing resource and parallelism ceilings.

A5.1 does not create a new parallel execution mechanism. Even when a parallel candidate ranks first in shadow mode:

```text
topology_effective = false
shadow_influenced_execution = false
dispatch_controlled_by = CONDUCTOR
```

## Shadow decision

Every A5.1 decision preserves:

```text
execution_controlled_by = DETERMINISTIC_ORCHESTRA
dispatch_controlled_by = CONDUCTOR
transition_controlled_by = ARBITER
topology_effective = false
shadow_influenced_execution = false
promotion_state = NOT_PROMOTED
```

Missing evidence, invalid evidence, an unavailable adaptive layer, or insufficient distinct support falls back to the existing deterministic coordination order. No eligible topology fails closed rather than creating one.

## A4 boundary at A5 entry

A4 remains canonical but intentionally non-promoted for execution control. A5 does not reinterpret A4 shadow selection as permission to change dispatch, worker execution, specialist ownership, provider eligibility, or route selection.

The A4 post-execution attachment may be used as historical architecture evidence only. It is not an A5 authority source.

## A5.1 adversarial validation

A5.1 tests prove at minimum that:

- every frozen deterministic coordination invariant must be present and true;
- required specialists cannot be omitted from a candidate topology;
- all candidates preserve the exact required-specialist set and coordination-contract revision;
- an ineligible candidate cannot be created or restored by evidence;
- the actual deterministic topology must bind the immutable eligible set;
- an explicit current constraint dominates adaptive evidence;
- a scoped preference cannot restore an ineligible topology;
- evidence qualification requires exact candidate, session, and revision binding;
- duplicate evidence does not inflate support;
- one source digest cannot support multiple topology candidates;
- manually mislabeled cross-session or stale-revision evidence fails closed;
- A3 `WORKFLOW_TENDENCY` cannot be used as direct topology evidence;
- generic phase success cannot be used as topology evidence;
- unmeasured telemetry cannot be invented;
- stale evidence and predated evaluation fall back deterministically;
- an unavailable adaptive layer preserves deterministic order;
- an empty eligible set fails closed;
- a shadow recommendation containing permitted parallel grouping does not activate parallel execution;
- identical inputs produce identical rank and decision identity;
- every decision remains structurally non-authorizing.

## A5 canonical validation

A5.1 was source-validated, signed through the isolated materialization lane, and independently validated on the signed protected-main candidate before canonical integration.

Canonical identity:

```text
canonical head = 8acb03802834e9e56b078496a3e5e0f1aa498ebf
canonical tree = e493b260ba2def53fb46298109637f8635f99970
canonical parent = 8a365eea7dd52022c427b83d7f3b484aba7152ff
canonical signature = GitHub verified / valid
```

Protected-main exact-head validation on signed candidate `4d035ed80fab3400a5d2365c5f4f803675652c0c`:

- Governance Check `32153174122`: PASS
- validate `32153173966`: PASS
- Required Analysis Compatibility `32153174005`: PASS
- Cross-platform Validation `32153174063`: PASS
- cosmic-ray-confidence `32153174102`: PASS
- Cosmic Ray artifact digest: `sha256:e97af168f4669241393e676edbb8e364afa009b647c2da6a2ec3239db89c0f6f`

## A5 exit decision

The A5 exit gate has two distinct parts and they are recorded separately rather than conflated.

```text
topology parity and adversarial validation = SATISFIED
measurable benefit over fixed eligible sequences = NOT_ESTABLISHED
execution-effective topology promotion = DEFERRED_NOT_PROMOTED
A5 phase disposition = CLOSED_AT_SHADOW_MATURITY
```

The measurable-benefit result is intentionally not upgraded from synthetic tests, generic task success, A3 workflow tendency, or unmeasured estimates. Under the frozen A5 evidence policy, a benefit claim requires trustworthy evidence bound to the exact topology candidate, collaboration session, coordination-contract revision, and any claimed measurement. No governed comparative measurement set satisfying that boundary was available to this closeout.

Because measurable benefit is not established, A5 does not create an execution-control bridge. There is no learned topology scheduler, no RuntimeExecutor attachment, no Conductor dispatch attachment, and no new parallel execution capability.

Closing A5 at shadow maturity is a negative promotion decision, not a positive performance claim. It preserves the validated shadow research surface while refusing to make topology-effective selection authoritative without the required evidence.

## Future boundary

A5 is closed at shadow maturity with execution-effective promotion deferred and not promoted.

Not authorized or introduced by this closeout:

- topology-effective coordination selection;
- automatic policy promotion;
- additional parallel execution capability;
- learned specialist omission or ownership changes;
- attachment to Conductor dispatch;
- attachment to `RuntimeExecutor`;
- A6 adaptive context routing;
- A7 Conductor route ranking or offline policy promotion;
- A8 recursive or test-time compute;
- release, deployment, or publication.

A later phase cannot treat this closeout as evidence that adaptive topology is measurably better than fixed eligible sequences. Any future reconsideration of topology-effective promotion requires new governed comparative evidence under the A5 exact-topology evidence contract and a separately authorized transition.
