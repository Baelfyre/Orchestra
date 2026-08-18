# Adaptive Selection A4

## Status

A4.0 is a contract-freeze unit for bounded specialist-strategy, model, and worker selection under issue #340.

Entry baseline:

- canonical `main`: `a520beabe6761161baf3179c1f6de5f055adbfc2`;
- canonical tree: `b81703473e2350c9c41fecd7b459de6097d24fee`;
- A3.1-A3.4: canonical shadow behavioral learning;
- A4.0 runtime effect: **none**.

A4.0 defines the contracts that a later A4 shadow ranker must obey. It does not implement an execution-effective selector, change routing, alter specialist ownership, add providers, expand model/worker eligibility, change authority/capabilities/governance, or introduce A5-A8 behavior.

Machine contracts:

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

## Selection types

A4.0 defines one common bounded contract for:

1. `SPECIALIST_STRATEGY`
2. `MODEL`
3. `WORKER`

These selection types do not have equal evidence maturity.

### Specialist strategy

A3 currently produces `SPECIALIST_STRATEGY_TENDENCY` shadow candidates from bounded strategy-decision evidence. Those candidates may become qualified input to a later A4 shadow ranker when exact scope, option identity, source integrity, and eligibility all match.

A3 `USER_PREFERENCE_TENDENCY` and `WORKFLOW_TENDENCY` are not automatically strategy-performance evidence.

### Model and worker

A3 does not currently produce direct model- or worker-performance tendency candidates.

A4.0 therefore prohibits treating A3 strategy evidence, generic task success, raw conversation, or inferred telemetry as model/worker performance evidence.

Until direct governed evidence is available and validated for the exact eligible model or worker, the required disposition is deterministic fallback.

This contract does not add a provider, provider API, provider transmission path, model registry entry, worker capability, or training path.

## Eligibility envelope

The eligibility envelope is produced by the deterministic control plane before adaptive ranking.

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

An empty eligible set is a fail-closed state, not an invitation for adaptive discovery.

## Evidence qualification

Permitted evidence source kinds are deliberately bounded:

- A3 shadow candidate;
- A3 shadow comparison;
- governed selection outcome;
- validation evidence;
- remediation evidence;
- trustworthy measured telemetry.

Evidence must bind to the exact selection type and option identity.

Raw conversation is not authoritative selection evidence.

Generic phase success does not prove that a strategy, model, or worker caused the success.

Latency, cost, or token measurements may be used only when they are actually and trustworthily measured. Missing measurements remain missing.

Duplicate source digests count once. Cross-user, cross-project, cross-specialist, or otherwise mis-scoped evidence fails closed.

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

Adaptive scores are evidence metadata. They are not authority.

## Ranking contract

A later A4 ranker must use a named, versioned deterministic scorer.

For the same validated eligibility envelope, validated evidence packet, scorer version, and explicit constraints, the ranked order must be reproducible.

Stable tie-breaking is mandatory.

A4.0 does not freeze an arbitrary numeric weighting formula. A concrete scorer is an implementation decision for a later separately reviewed A4 unit and must be versioned, tested, and bound to this contract.

Insufficient evidence, invalid evidence, stale/malformed eligibility, or adaptive unavailability produces deterministic fallback.

## Shadow decision

The A4.0 decision record is non-authorizing.

It records:

- immutable eligibility digest;
- evidence digest;
- scorer version;
- ranked candidate identities where ranking was valid;
- shadow recommendation;
- actual deterministic execution choice;
- fallback or rejection disposition.

Every A4.0 decision requires:

```text
execution_controlled_by = DETERMINISTIC_ORCHESTRA
selection_effective = false
shadow_influenced_execution = false
promotion_state = NOT_PROMOTED
```

A shadow recommendation cannot alter execution.

## Required adversarial validation for later A4 implementation

A later A4 implementation must prove at minimum that:

1. the ranker cannot add an ineligible option;
2. provider/privacy-filtered options cannot be restored;
3. authority or capability cannot be expanded;
4. required specialist ownership cannot change;
5. explicit current constraints dominate adaptive scores;
6. cross-scope evidence fails closed;
7. duplicate evidence cannot inflate support;
8. generic phase success cannot become strategy/model/worker success;
9. unmeasured latency, cost, or tokens are not invented;
10. model/worker selection without direct qualified evidence falls back deterministically;
11. shadow recommendations never change execution;
12. malformed or stale eligibility/evidence fails closed;
13. no A5, A6, A7, or A8 behavior is introduced.

## Promotion boundary

A4.0 defines no promotion bridge.

Execution-effective adaptive selection requires a later explicit promotion decision after a shadow implementation, regression suite, adversarial review, deterministic fallback evidence, and separately governed canonical transition.

A4 completion must not silently authorize A5 Tuner topology learning, A6 adaptive context routing, A7 route ranking/policy promotion, or A8 recursive/test-time compute.
