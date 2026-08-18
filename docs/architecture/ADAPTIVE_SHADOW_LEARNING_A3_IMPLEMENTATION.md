# Adaptive Shadow Learning A3 Implementation

## Status

This document describes the A3.1 through A3.4 implementation that follows the canonical A3.0 contract freeze.

Canonical A3.0 baseline:

- commit: `07989ef6473657ab37530462ce7d2a9ef1c5f8e2`;
- tree: `5a5bddd42961b1d7119350e31fc18e3b4b575fa2`.

The implementation remains **shadow-only**. It does not alter routing, specialist selection, model or worker selection, strategy execution, authority, capabilities, governance, lifecycle gates, A1 profile materialization, A2 context attachment, provider integration, training, or recursive/test-time compute.

## Implementation map

| A3 unit | Implementation | Effect |
| --- | --- | --- |
| A3.1 | validated signal extraction and signal construction | creates machine-local shadow evidence only |
| A3.2 | bounded candidate learner | derives non-promoted shadow candidates only |
| A3.3 | deterministic shadow comparator | records comparison against the already-selected deterministic choice |
| A3.4 | adversarial/correction validation | proves fail-closed and non-authorizing boundaries |

Primary runtime surface:

`orchestra_runtime/adaptive/shadow.py`

Primary validation surface:

`tests/runtime/test_adaptive_shadow.py`

Canonical machine contract:

`machine/adaptive/a3-shadow-learning-contract.v1.json`

## A3.1 signal extraction

The A3 signal extractor accepts validated A1 observations and converts only bounded event families:

- explicit preference set -> `USER_SELECTION`;
- explicit preference corrected -> `USER_CORRECTION`;
- explicit preference removed -> `USER_REJECTION`;
- governed outcome recorded -> `TERMINAL_DISPOSITION`.

A1 inferred-pattern lifecycle events are deliberately not translated back into A3 signals. This prevents a feedback loop where A3 would learn from its own inferred output.

Generic phase success remains generic outcome evidence. It is not transformed into specialist-strategy success.

External governed evidence can build a signal only through the bounded source-kind vocabulary defined by the A3 contract. In particular:

- `SPECIALIST_STRATEGY_ACCEPTED` and `SPECIALIST_STRATEGY_REJECTED` require `STRATEGY_DECISION_EVIDENCE`;
- `MEASURED_LATENCY` and `MEASURED_COST` require `MEASURED_TELEMETRY` plus an explicit `TRUSTWORTHY_MEASURED` measurement object;
- raw conversation is not an accepted source kind;
- non-learnable authority/governance/security/gate subject roots continue to fail closed.

Signal identity is deterministic from exact scope, subject, observed value, source identity/digest, timestamp, and measurement metadata.

## Machine-local persistence

The shadow store derives its user-specific location from the A1 adaptive store layout and appends:

```text
~/.orchestra/adaptive/
  v1/<hashed-user>/
    observations.jsonl
    profile.json
    shadow/a3/
      signals.jsonl
      candidate-state.json
      comparisons.jsonl
```

`ORCHESTRA_ADAPTIVE_HOME` continues to override the adaptive root.

The existing repository-boundary check is reused, so an explicitly supplied repository root cannot become the adaptive storage root.

Shadow writes never mutate A1 `observations.jsonl` or `profile.json`.

## A3.2 candidate learning

Candidate learning groups evidence by exact:

- user/scope identity;
- subject key;
- candidate value.

It cannot combine evidence across users or scopes.

### Distinct-support rule

A durable candidate requires at least two distinct supporting source digests.

Repeated records of the same source evidence count once. One-off choices therefore remain evidence but do not become durable candidates.

The learner records supporting shadow-signal identities and digests in the candidate record.

### Candidate types

The implementation derives only the A3 contract types:

- `USER_PREFERENCE_TENDENCY`;
- `WORKFLOW_TENDENCY`;
- `SPECIALIST_STRATEGY_TENDENCY`.

Every candidate remains:

```text
shadow_only = true
promotion_state = NOT_PROMOTED
```

There is no confirmed shadow status and no automatic promotion threshold.

### Confidence

The learner uses the named deterministic method `BOUNDED_EVIDENCE_ACCUMULATION_V1`.

Confidence is bounded to `[0.0, 1.0]`, increases only with distinct supporting evidence, and may be reduced by explicit negative evidence. It is metadata for review and comparison only.

Confidence does not grant permission, promotion, routing authority, or execution authority.

### Explicit preference dominance

The learner can receive the current validated A1 materialized profile as read-only input.

For the same exact scope and subject:

- a conflicting confirmed explicit preference produces `BLOCKED_BY_EXPLICIT_PREFERENCE`;
- the candidate retains an explicit conflict reference;
- removal of the explicit preference does not automatically reactivate the blocked historical candidate;
- new supporting evidence after the blocked candidate's prior `last_seen` is required before it can be derived again as an active shadow candidate.

This preserves the pre-A3 precedence hardening and prevents stale inferred evidence from silently resurfacing.

### Negative evidence

A latest explicit `USER_REJECTION` or `SPECIALIST_STRATEGY_REJECTED` for the same exact candidate value marks the derived candidate `REJECTED`.

Earlier conflicting negative evidence remains visible through notes and reduces confidence rather than disappearing.

## A3.3 shadow comparison

The comparator receives a shadow candidate and an **already-selected deterministic choice**.

It records one of:

- `MATCH`;
- `MISMATCH`;
- `NO_COMPARABLE_DETERMINISTIC_CHOICE`;
- `CANDIDATE_BLOCKED`.

Every comparison hard-codes:

```text
execution_controlled_by = DETERMINISTIC_ORCHESTRA
shadow_influenced_execution = false
```

The comparator returns evidence only. It does not return or replace the execution choice used by Orchestra.

Optional outcome evidence may be attached later for analysis, but comparison evidence itself grants no promotion authority.

## A3.4 adversarial and correction validation

The focused runtime suite covers the required A3 contract attacks and edge cases:

1. one-off choice cannot become a durable candidate;
2. duplicated source evidence cannot inflate distinct support;
3. generic phase success cannot become specialist-strategy success;
4. unmeasured latency/cost is rejected;
5. raw conversation and non-learnable subject roots fail closed;
6. mixed-user learning fails closed;
7. separate project scopes do not leak;
8. explicit preferences block conflicting candidates;
9. explicit removal does not silently reactivate blocked history;
10. new post-removal evidence is required for re-derivation;
11. latest explicit negative evidence rejects a candidate;
12. shadow comparison cannot change deterministic execution;
13. shadow persistence does not mutate A1 observations or profile state;
14. malformed shadow state fails closed;
15. forged promotion or execution-control fields are rejected;
16. signal, candidate, and comparison runtime records validate against the A3.0 JSON Schemas.

## Explicit non-integration

A3 intentionally remains an opt-in library/storage surface rather than an automatic runtime hook.

The implementation does **not** modify:

- `RouterService`;
- default `RuntimeExecutor` routing behavior;
- `AdaptiveRuntimeExecutor` A2 context compilation;
- authority/capability evaluation;
- governance policy;
- required validation gates;
- specialist ownership;
- Tuner topology;
- model/worker selection;
- A1 inferred observation APIs;
- A1 profile materialization;
- A2 context packets.

This is deliberate. Shadow mode must first accumulate reviewable evidence without becoming execution-effective.

## Promotion boundary

A3.1 through A3.4 do not implement a promotion bridge.

Specifically, A3 does not:

- append a shadow candidate into the A1 inferred observation lifecycle;
- confirm an inferred pattern;
- materialize a shadow candidate into the A1 profile;
- attach shadow state to A2 context;
- automatically activate behavior after a confidence threshold.

Any later promotion mechanism must be separately designed and governed. It is not implied by A3 completion.

## A4 stop boundary

A3 completion does not authorize A4.

The following remain outside this implementation:

- specialist strategy execution selection;
- model selection;
- worker selection;
- route ranking or route mutation;
- learned coordination topology;
- adaptive context routing;
- policy promotion;
- provider training;
- recursive/test-time compute.

The A3 exit condition is therefore:

```text
SHADOW_EVIDENCE_IMPLEMENTED_AND_VALIDATED
DETERMINISTIC_EXECUTION_UNCHANGED
PROMOTION_BRIDGE_NONE
A4_NOT_AUTHORIZED
```
