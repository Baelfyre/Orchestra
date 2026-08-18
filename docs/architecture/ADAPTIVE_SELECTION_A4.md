# Adaptive Selection A4

## Status

A4.0 is the canonical contract freeze for bounded specialist-strategy, model, and worker selection under issue #340.

A4.1 implements the first bounded shadow ranker and evidence-qualification surface under those frozen contracts.

A4.0 canonical closeout:

- canonical `main`: `d6c342049b4a92fe07f2f6875cfe421ad05c1bb6`;
- canonical tree: `c8ca50d5e0a25991aca4d3fdabd8dbbae16fda29`;
- A3.1-A3.4: canonical shadow behavioral learning;
- A4.0 runtime effect: **none**.

A4.1 source baseline:

- canonical `main`: `d6c342049b4a92fe07f2f6875cfe421ad05c1bb6`;
- canonical tree: `c8ca50d5e0a25991aca4d3fdabd8dbbae16fda29`;
- runtime surface: `orchestra_runtime/adaptive/selection.py`;
- validation surface: `tests/runtime/test_adaptive_selection.py`;
- machine implementation record: `machine/adaptive/a4-shadow-ranker-implementation.v1.json`;
- scorer: `orchestra.adaptive-selection-scorer.v1`;
- A4.1 execution effect: **none**.

A4.1 does not modify deterministic routing, required specialist ownership, authority, capability, governance, provider/model/worker eligibility, runtime lifecycle authority, Tuner routing authority, Conductor routing authority, or A5-A8 behavior.

Machine contracts remain:

- `machine/adaptive/a4-bounded-selection-contract.v1.json`
- `machine/schemas/adaptive-selection-eligibility-envelope.schema.json`
- `machine/schemas/adaptive-selection-evidence.schema.json`
- `machine/schemas/adaptive-selection-decision.schema.json`

## Core ordering rule

Adaptive ranking begins only after deterministic Orchestra has already established the eligible set.

```text
deterministic route and ownership
  -> authority
  -> capability
  -> governance
  -> provider/privacy restrictions
  -> lifecycle/resource ceilings
  -> immutable eligible-option envelope
  -> bounded evidence qualification
  -> shadow adaptive ranking
  -> comparison with deterministic execution choice
```

The adaptive layer may rank an eligible option. It may not create, restore, broaden, or mutate eligibility.

An explicit current user constraint may narrow an otherwise eligible set. It cannot make a prohibited option eligible.

## A4.1 implementation boundary

A4.1 is deliberately a pure bounded selection surface rather than a second router.

The caller supplies an already-filtered `SelectionEligibilityEnvelope`. Construction requires evidence that all frozen deterministic filters were applied:

- ownership;
- trusted route binding;
- authority;
- runtime capability;
- governance;
- provider/privacy;
- lifecycle;
- resource ceilings.

The module rejects a candidate whose declared specialist owner differs from the already-routed specialist. It never discovers a specialist, model, worker, provider, capability, or authority grant.

The ranker returns a `SelectionDecision` that is structurally non-authorizing:

```text
execution_controlled_by = DETERMINISTIC_ORCHESTRA
selection_effective = false
shadow_influenced_execution = false
promotion_state = NOT_PROMOTED
```

No A4.1 API mutates `RouterService`, `RuntimeExecutor`, `RuntimeComposition`, authority scopes, capability manifests, governance rules, provider restrictions, or specialist ownership.

## Selection types

A4 uses one common bounded contract for:

1. `SPECIALIST_STRATEGY`
2. `MODEL`
3. `WORKER`

These selection types do not have equal evidence maturity.

### Specialist strategy

A3 currently produces `SPECIALIST_STRATEGY_TENDENCY` shadow candidates from bounded strategy-decision evidence.

A4.1 may qualify an A3 strategy candidate only when:

- selection type is `SPECIALIST_STRATEGY`;
- the option is already in the immutable eligible set;
- the A3 candidate type is exactly `SPECIALIST_STRATEGY_TENDENCY`;
- candidate status remains `CANDIDATE`;
- `shadow_only` remains true;
- `promotion_state` remains `NOT_PROMOTED`;
- user/project/specialist/task scope matches the eligibility envelope;
- candidate value binds the exact eligible option.

A3 comparisons are separately bound to the candidate identity and digest. A comparison may provide positive evidence on `MATCH` or neutral comparison evidence on `MISMATCH`; a mismatch is not automatically treated as proof that the shadow option was bad.

A3 `USER_PREFERENCE_TENDENCY` and `WORKFLOW_TENDENCY` are explicitly unsupported as specialist-strategy performance evidence.

### Model and worker

A3 does not currently produce direct model- or worker-performance tendency candidates.

A4.1 therefore rejects qualified A3 evidence for `MODEL` or `WORKER` ranking. It does not repurpose strategy evidence.

Without direct qualified evidence that already binds the exact eligible model or worker, A4.1 returns deterministic fallback.

The frozen schemas permit direct governed selection outcome, validation, remediation, and trustworthy measured telemetry evidence. A4.1 can rank such pre-qualified exact-option evidence, but it does not create the upstream provider integration, worker registry, telemetry collector, or evidence authority needed to produce that evidence.

This unit adds no provider, provider API, model registry entry, worker capability, external transmission path, or training path.

## Eligibility envelope

The eligibility envelope is produced from deterministic control-plane results before adaptive ranking.

It records:

- selection type;
- user/project/task identity where applicable;
- existing deterministic route and routed specialist;
- evidence that ownership, route binding, authority, capability, governance, provider/privacy, lifecycle, and resource ceilings were applied;
- the finite eligible candidates.

Every candidate in the envelope is already eligible.

The adaptive layer must not:

- add a candidate;
- restore a filtered candidate;
- change a capability or owner;
- bypass a provider/privacy restriction;
- substitute a different routed specialist;
- infer eligibility from historical success.

An empty eligible set returns `NO_ELIGIBLE_CANDIDATES`. It is not an invitation for adaptive discovery.

## Evidence qualification

Permitted evidence source kinds remain:

- A3 shadow candidate;
- A3 shadow comparison;
- governed selection outcome;
- validation evidence;
- remediation evidence;
- trustworthy measured telemetry.

Evidence must bind to the exact selection type and option identity.

Raw conversation is not authoritative selection evidence.

Generic phase success does not prove that a strategy, model, or worker caused the success. The A4.1 selector accepts only the frozen evidence-source vocabulary and requires qualified evidence to carry an explicit direction.

Latency, cost, or token measurements are accepted only through a `SelectionMeasurement` whose status is exactly `TRUSTWORTHY_MEASURED`. Missing measurements remain missing.

Duplicate source digests count once. One source digest may not support multiple options in one decision.

A3 evidence is additionally subject to exact scope qualification. Direct governed evidence remains an upstream trust input and must already be exact-option bound before entering the A4.1 packet.

## Precedence

A4 preserves the established adaptive hierarchy:

```text
deterministic governance / authority / capability /
privacy / ownership ceilings
  > explicit current user constraint
  > explicit scoped user preference
  > qualified adaptive evidence
  > deterministic default order
```

An explicit current constraint retains deterministic ordering.

An explicit scoped preference may become the shadow recommendation only when that option is already eligible. It cannot restore a filtered option.

Adaptive scores are evidence metadata. They are not authority.

## A4.1 scorer

The A4.1 named scorer is:

```text
orchestra.adaptive-selection-scorer.v1
```

Its bounded behavior is:

1. validate exact envelope/evidence binding and monotonic timestamps;
2. reject qualified evidence that references an ineligible option;
3. reject one source digest bound to multiple options;
4. reject unsupported A3 evidence for the selection type;
5. deduplicate by source digest;
6. require at least two distinct positive evidence digests before adaptive preference;
7. rank using positive-minus-negative evidence, then positive support, then neutral evidence;
8. preserve the deterministic eligible order as the stable tie-break.

If no option reaches the support floor, the result is deterministic fallback.

The scorer does not convert its score into execution authority.

## Fail-closed dispositions

The frozen decision dispositions are used as follows:

- `SHADOW_RANKED`: a bounded non-authorizing shadow order exists;
- `DETERMINISTIC_FALLBACK`: qualified support is insufficient or an eligible scoped preference cannot be applied;
- `NO_ELIGIBLE_CANDIDATES`: deterministic filtering produced an empty set;
- `INVALID_ELIGIBILITY`: the claimed deterministic execution choice is not in the envelope;
- `INVALID_EVIDENCE`: packet binding, timestamp ordering, option binding, or evidence identity is invalid;
- `EXPLICIT_CONSTRAINT`: current user constraint retains deterministic precedence;
- `UNSUPPORTED_EVIDENCE_FOR_SELECTION_TYPE`: evidence class cannot support the requested selection type.

Malformed object construction fails before ranking through typed Python validation errors. Semantically stale or mismatched bound records fail closed through a decision disposition.

## Adversarial validation

`tests/runtime/test_adaptive_selection.py` verifies the frozen A4 requirements, including:

1. envelope, evidence, and decision serialization against the A4.0 JSON Schemas;
2. all deterministic eligibility filters are mandatory;
3. routed specialist ownership cannot change;
4. candidate kind must match selection type;
5. deterministic execution choice must remain inside the envelope;
6. explicit current constraints dominate adaptive scores;
7. scoped preferences cannot restore filtered options;
8. A3 strategy evidence requires exact scope and exact option binding;
9. A3 non-strategy tendency evidence cannot become strategy-performance evidence;
10. A3 evidence cannot become model/worker evidence;
11. model/worker selection without direct qualified evidence falls back;
12. duplicate evidence cannot inflate support;
13. one evidence digest cannot support multiple options;
14. evidence cannot add an ineligible option;
15. unmeasured telemetry is rejected;
16. mismatched or stale evidence fails closed;
17. the same inputs produce the same rank and stable tie order;
18. shadow decisions remain structurally non-authorizing.

## Promotion boundary

A4.1 implements the shadow ranker. It does not create an execution-effective promotion bridge.

Execution-effective adaptive selection remains a later A4 decision that requires:

- exact-head validation of the shadow implementation;
- adversarial regression evidence;
- deterministic fallback evidence;
- review of any execution attachment point;
- proof that deterministic eligibility remains external and immutable;
- explicit versioned promotion state;
- canonical traceability.

Successful task execution never rewrites the active adaptive policy.

A4 completion must not silently authorize A5 Tuner topology learning, A6 adaptive context routing, A7 route ranking/policy promotion, or A8 recursive/test-time compute. Those remain separate phases under the adaptive program and repository governance.
