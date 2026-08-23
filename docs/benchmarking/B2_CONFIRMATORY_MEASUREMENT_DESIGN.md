# B2 Confirmatory Measurement Design Freeze

## Status

```text
Program: Orchestra Shared Comparative Benchmark
Phase: B2 A5 Isolated Comparative Experiment
Unit: B2.3 Confirmatory Measurement Design Freeze
Recorded date: 2026-08-23
State: B2_3_CONFIRMATORY_MEASUREMENT_DESIGN_FROZEN_NO_LIVE_CALLS
Evidence maturity: DESIGN_ONLY
Live model calls authorized by this unit: 0
B2 rerun: NOT AUTHORIZED
A5 execution-effective promotion: NOT AUTHORIZED
B4: BLOCKED
```

This unit freezes the evidence-repair and confirmatory-measurement design required after the valid B2 real calibration reconciliation. It does not execute Codex, change A5 runtime behavior, promote any topology, or establish benefit.

The canonical B2 calibration reconciliation identified two measurement weaknesses that must be corrected before confirmatory use:

1. specialist advisory text was not retained, so `context_transfer_bytes` could not be independently recomputed from raw handoff content;
2. identical first-specialist prompt evidence produced different host-reported input-token counters across repetitions, so raw token differences could not be cleanly attributed to topology.

The confirmatory design also addresses the calibration quality ceiling by pre-registering a primary coordination-efficiency endpoint with a strict quality guardrail rather than treating the 10/10 versus 10/10 calibration tie as evidence of topology quality benefit.

## Design principle

```text
CALIBRATION SIGNAL != CONFIRMATORY BENEFIT
RECOMPUTABLE EVIDENCE != HOST COUNTER TRUST BY ASSUMPTION
TOKEN COUNTER IDENTITY != TOKEN ATTRIBUTION STABILITY
SHADOW TOP-1 != EXECUTION AUTHORITY
CONFIRMATORY SUCCESS != A5 PROMOTION AUTHORITY
```

The next live measurement must be preceded by implementation and zero-call fixture validation of the evidence contract below.

## B2.3.1 Specialist handoff evidence contract

For each B2 specialist call, the executor must retain bounded synthetic advisory evidence sufficient for an independent auditor to reproduce the communication metric.

Required specialist call evidence:

- `response_text`: exact synthetic advisory text returned by the specialist;
- `response_encoding`: fixed to `UTF-8`;
- `response_utf8_bytes`: exact byte length of `response_text.encode("utf-8")`;
- `response_utf8_sha256`: SHA-256 of the raw UTF-8 response bytes;
- existing canonical `response_digest`: retained for backward compatibility;
- `prior_advisory_inputs`: ordered references to every prior advisory inserted into that specialist prompt, including specialist identity, source call index, UTF-8 byte length, and raw UTF-8 SHA-256;
- exact `prompt_digest` and stage identity as already recorded.

For the fixed finalizer call, evidence must retain `advisory_inputs` referencing every specialist advisory supplied to the finalizer.

The run evidence must also contain a recomputation ledger:

```text
downstream_specialist_handoff_bytes
+ finalizer_advisory_bytes
= recomputed_context_transfer_bytes
```

For the current two-stage sequential topology:

- the first specialist advisory is transferred once to the second specialist;
- both specialist advisories are transferred once to the fixed finalizer;
- `communication.context_transfer_bytes` must equal `recomputed_context_transfer_bytes` exactly;
- any mismatch is `INVALID_RUN / MEASUREMENT_CAPTURE_FAILURE`.

Raw advisory retention is permitted only for the synthetic benchmark task surface. External repository content, private user content, credentials, secrets, network-derived content, and tool-derived content remain prohibited by the existing read-only/no-tools/no-web benchmark boundary.

A per-specialist retained advisory ceiling of 16,384 UTF-8 bytes is frozen for the instrumentation implementation. Exceeding the ceiling fails the run closed rather than truncating evidence.

## B2.3.2 Codex counter provenance contract

The executor must preserve the exact measurement-critical Codex `turn.completed` usage evidence instead of retaining only normalized aggregate counters.

Each call must retain:

- exact `turn.completed` usage object;
- canonical digest of the retained usage object;
- host `counter_id`;
- prompt digest;
- role and specialist identity;
- CLI version;
- model;
- reasoning effort;
- transport identity;
- workspace identity;
- `input_tokens`;
- `cached_input_tokens`;
- `output_tokens`;
- `reasoning_output_tokens`;
- derived `non_cached_input_tokens = input_tokens - cached_input_tokens`, only when the host fields are internally valid.

If `cached_input_tokens > input_tokens`, the measurement is invalid rather than coerced.

The implementation must derive a deterministic `counter_stability_key` from measurement identity fields that are expected to be identical for a repeated first-stage call:

```text
prompt_digest
counter_id
role
specialist
CLI version
model
reasoning effort
transport
workspace identity
```

Repeated calls with the same `counter_stability_key` are classified as:

- `STABLE_EXACT` when host-reported `input_tokens` and `cached_input_tokens` are exact across repetitions;
- `CACHE_STATE_VARIANT` when cached-input counters differ;
- `INPUT_COUNTER_VARIANT` when input-token counters differ;
- `UNSTABLE_ATTRIBUTION` when either input or cache identity prevents clean topology attribution.

The classifications are measurement evidence. They do not cause a task-quality failure. They control only whether host token efficiency is claim-eligible.

## Token attribution gate

Host token counts may support a topology-efficiency claim only when all repeated first-stage control groups required by the frozen measurement plan are `STABLE_EXACT`.

Otherwise:

```text
TOKEN_ATTRIBUTION_GATE = FAIL
TOKEN_EFFICIENCY = DESCRIPTIVE_ONLY
```

A failed token-attribution gate does not invalidate independently recomputable context-transfer evidence.

## B2.3.3 Zero-call implementation validation

Before any live pilot, the executor changes must pass fixture-only validation with zero model calls.

Required zero-call cases include:

1. exact UTF-8 byte and SHA-256 recomputation from retained advisory text;
2. exact downstream-handoff and finalizer-advisory byte accounting;
3. rejection of a mismatched reported/recomputed `context_transfer_bytes` value;
4. rejection of advisory evidence exceeding 16,384 UTF-8 bytes;
5. preservation and digest verification of the exact usage object;
6. `STABLE_EXACT` classification for identical synthetic counter fixtures;
7. `CACHE_STATE_VARIANT` classification when cached-input counters differ;
8. `INPUT_COUNTER_VARIANT` classification when input counters differ;
9. rejection when `cached_input_tokens > input_tokens`;
10. proof that fixture validation never invokes `codex exec`.

Passing these tests authorizes no live calls. It only makes a separately governed instrumentation pilot eligible for human authorization.

## B2.4 Instrumentation pilot design

The first live phase after implementation is an instrumentation pilot, not a benefit test.

Frozen pilot structure:

```text
stage: PILOT
purpose: instrumentation and attribution validation only
tasks: 2
repetitions: 2
arms: 2
runs: 8
Codex calls per run: 3
maximum underlying model calls: 24
automatic retry: OFF
benefit claim: PROHIBITED
```

Pilot task identities must include:

- `b2-cal-cache-freshness`, because the calibration counter anomaly occurred on this task;
- one additional already-frozen B2 calibration task selected deterministically before pilot authorization.

The pilot may reuse calibration tasks because it is diagnostic instrumentation evidence only. Pilot results must not be pooled into the later confirmatory benefit analysis.

Pilot success requires:

- complete retained advisory text and digest evidence for every specialist call;
- exact recomputation of every communication byte metric;
- exact retained usage provenance for every Codex call;
- complete counter-stability classification for every repeated first-stage control group;
- zero safety/governance violations;
- no automatic retry;
- exact frozen host and workspace identity.

Counter instability may be observed during the pilot without invalidating the handoff evidence implementation. If instability remains, token efficiency stays non-claimable in confirmatory analysis.

The pilot requires a new exact-host zero-call preflight and a separate explicit human live-execution authorization. This design unit does not provide that authorization.

## B2.5 Confirmatory measurement design

Confirmatory measurement is a separate later unit and must use a held-out topology-sensitive task set that was not used in B2 calibration or the instrumentation pilot.

Pre-registered confirmatory structure:

```text
held-out tasks: 10
repetitions per task: 2
arms: 2
matched task/repetition blocks: 20
runs: 40
Codex calls per run: 3
maximum underlying model calls: 120
automatic retry: OFF
communication mode: DEFAULT
```

The confirmatory task set, exact host identity, workspace, resource ceilings, randomized paired plan, and task-set digest must be separately frozen and canonicalized before any confirmatory model call.

### Primary hypothesis

The directional calibration signal is pre-registered as:

```text
Clockwork -> Overseer uses less specialist context transfer
than Overseer -> Clockwork
without degrading deterministic task quality.
```

This is a hypothesis to test, not an established result.

### Primary endpoint

Primary endpoint: independently recomputed `context_transfer_bytes` from retained raw synthetic specialist advisories.

For each matched block:

```text
delta = Overseer->Clockwork bytes - Clockwork->Overseer bytes
```

A positive delta favors Clockwork -> Overseer.

A confirmatory coordination-efficiency benefit may become an evidence candidate only if all of the following are true:

1. every accepted run passes its frozen deterministic task validator;
2. no accepted run contains a safety or governance violation;
3. Clockwork -> Overseer has lower recomputed context-transfer bytes in at least 15 of 20 matched blocks;
4. the two-sided exact sign test against a 50/50 directional null is below `p < 0.05`;
5. the median paired relative reduction in context-transfer bytes is at least 10%;
6. all context-transfer values independently recompute from retained advisory evidence.

The `15 of 20` directional threshold is frozen because it is sufficient for a two-sided exact sign-test result below 0.05 at 20 matched blocks. The 10% median relative-reduction threshold is the minimum practical coordination-efficiency effect required by this design, independent of statistical significance.

### Quality guardrail

This confirmatory design does not claim topology quality superiority from an exact-validator ceiling.

Instead:

```text
QUALITY ROLE = NON-DEGRADATION GUARDRAIL
```

Any deterministic quality failure in the topology proposed as more efficient blocks a topology-efficiency benefit conclusion from this confirmatory unit.

### Secondary endpoints

Secondary descriptive endpoints:

- wall-clock latency;
- model-execution latency;
- output tokens;
- host input and cached-input tokens;
- A5 shadow ordering observations.

Host token efficiency becomes claim-eligible only when `TOKEN_ATTRIBUTION_GATE = PASS`. If the gate fails, token results remain descriptive regardless of effect size.

## Confirmatory disposition matrix

| Condition | Disposition |
|---|---|
| Primary context-transfer criteria pass + quality guardrail pass | `B2_CONFIRMATORY_COORDINATION_BENEFIT_EVIDENCE_CANDIDATE` |
| Context-transfer effect fails threshold/sign test | `B2_CONFIRMATORY_BENEFIT_NOT_ESTABLISHED` |
| Handoff evidence is not recomputable | `INVALID_MEASUREMENT_EVIDENCE` |
| Token attribution gate fails | `TOKEN_EFFICIENCY_DESCRIPTIVE_ONLY` |
| Quality guardrail fails | `B2_CONFIRMATORY_BENEFIT_NOT_ESTABLISHED` |
| Safety/governance violation | fail closed under existing benchmark rules |

Even a successful confirmatory result remains evidence only.

```text
B2_CONFIRMATORY_COORDINATION_BENEFIT_EVIDENCE_CANDIDATE
!= A5_EXECUTION_EFFECTIVE_PROMOTION
```

A5 runtime promotion would require a separately authorized architecture/governance decision and its own validation chain.

## Required implementation sequence

```text
B2.3 DESIGN FREEZE
    -> B2.3.1 EXECUTOR EVIDENCE IMPLEMENTATION
    -> B2.3.2 ZERO-CALL FIXTURE VALIDATION
    -> B2.4 SEPARATELY AUTHORIZED INSTRUMENTATION PILOT
    -> PILOT EVIDENCE RECONCILIATION
    -> B2.5 HELD-OUT TASK-SET + CONFIRMATORY FREEZE
    -> SEPARATE HUMAN LIVE AUTHORIZATION
    -> CONFIRMATORY EXECUTION
    -> CONFIRMATORY EVIDENCE RECONCILIATION
    -> SEPARATE A5 ADJUDICATION, IF WARRANTED
```

No phase may infer authority from the preceding phase.

## Authority boundary

This design grants no:

- B2 live model calls or reruns;
- A5 execution-effective promotion;
- production runtime attachment;
- parallel production capability;
- A6, A7, or A8 authority;
- B4 authority;
- release publication;
- deployment;
- policy activation;
- installed-integration refresh;
- destructive cleanup;
- branch deletion;
- force push or history rewrite.
