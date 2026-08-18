# Shared Comparative Measurement B1

## Status

```text
Program: Orchestra Shared Comparative Benchmark
Phase: B1 Shared Benchmark Harness
State: IMPLEMENTED_NON_PRODUCTION_NO_PROVIDER_ADAPTERS
Canonical entry: 3037b6207c844b75a6246fc5c1074cf849e7df82
Canonical entry tree: f39c4fe5d299ba76dce9d3b577c0705807c4efe9
A5 execution-effective selection: NOT AUTHORIZED
A6: NOT AUTHORIZED
Paid provider calls from B1 implementation: NOT AUTHORIZED
```

B1 implements the common evidence-collection harness frozen by B0. It does not run production routing, attach to Conductor dispatch, attach to `RuntimeExecutor`, select a production topology, expand Murmurs semantics, begin A6, deploy, publish a release, or establish A5/Murmurs benefit.

## Purpose

The B1 harness exists to make the three benchmark families reproducible under one execution and evidence protocol:

1. B2 A5 isolated comparative experiment;
2. B3 Murmurs isolated comparative experiment;
3. B4 A5 x Murmurs interaction experiment after valid B2 and B3 evidence.

The platform is shared, but the first two causal experiments remain isolated.

## Runner

The non-production runner is:

```text
scripts/comparative_benchmark_runner.py
```

It accepts:

```text
--manifest <manifest.json>
--executor-command-json '["python","adapter.py"]'
--output-dir <directory>
--plan-only
```

The executor command is an explicit JSON array. The harness invokes it with `shell=False`. B1 does not provide a provider adapter and does not require provider credentials or network access in the core runner.

## Adapter protocol

For each planned run, the harness invokes the configured adapter as a subprocess and sends exactly one JSON request over standard input. The adapter returns exactly one JSON result over standard output.

Machine contracts:

```text
machine/schemas/comparative-benchmark-manifest.schema.json
machine/schemas/comparative-benchmark-executor-request.schema.json
machine/schemas/comparative-benchmark-executor-result.schema.json
machine/schemas/comparative-benchmark-run.schema.json
machine/schemas/comparative-benchmark-experiment.schema.json
```

The request contains:

- experiment identity and stage;
- task identity and task class;
- repetition and randomized execution order;
- current experimental arm;
- exact common-control identity;
- opaque adapter task payload;
- digest of the task payload;
- A5, Murmurs, or interaction evaluation settings as applicable.

For A5-capable experiments, `a5_evaluation.eligible_topology_candidate_ids` transports the complete frozen candidate set to the adapter. This prevents the adapter from treating the currently executing arm as the only candidate available to the A5 shadow scorer.

## Execution isolation

### Paired blocks

Every task is run across every configured arm for every configured repetition.

Conceptually:

```text
Task A / repetition 1
  arm order randomized
  execute every arm

Task A / repetition 2
  arm order randomized independently
  execute every arm

Task B / repetition 1
  ...
```

The randomization seed is supplied by the manifest. Arm order is deterministic for the same manifest and seed, which allows exact reproduction while avoiding fixed all-one-arm-first ordering.

### A5 isolated

B1 enforces the B0 separation rule:

```text
experiment_kind = A5_ISOLATED
communication_mode = DEFAULT for every arm
```

Every configured eligible topology arm executes independently. The A5 shadow observation is collected from the same frozen candidate set.

For non-invalid A5 runs:

- eligibility digest must match the manifest;
- ranked candidate IDs must equal the configured topology candidate set;
- top candidate must be a configured candidate;
- A5 observation must be identical across all execution arms in the same task/repetition block.

The final condition is important: the A5 prediction is a property of the task and frozen evidence, not a function of whichever experimental arm happens to be executing.

A5 never decides which arms the harness runs.

### Murmurs isolated

B1 enforces:

```text
experiment_kind = MURMURS_ISOLATED
topology_class = FIXED_DETERMINISTIC
one identical topology identity across arms
communication modes = DEFAULT, CAVEMAN, MURMURS
```

The three communication arms receive the same task, topology, model/provider identity, specialist identity, authority/governance identity, validation identity, retry policy, and resource-budget identity.

If token measurements are supplied, they must be provider/host reported and carry a counter identity. A token delta is scientifically comparable only when paired arms share the same trustworthy counter identity. B1 does not estimate missing model-token values.

### Combined interaction

B1 can transport a configured topology-by-communication interaction design only when the manifest contains both isolated evidence digests.

B1 does not interpret the interaction or promote either isolated result. B4 remains gated on valid B2 and B3 evidence.

## Manifest controls

The manifest records the common identity held constant across paired arms:

- Orchestra revision;
- benchmark repository revision;
- system-instruction digest;
- provider;
- model and optional model revision;
- reasoning setting when configurable;
- temperature when configurable;
- tool-access digest;
- specialist-set digest;
- required-specialist-set digest;
- authority digest;
- governance digest;
- validation-contract digest;
- environment digest;
- retry-policy digest;
- resource-budget digest.

Task-specific controls add:

- exact starting-state digest;
- exact task-prompt digest;
- opaque task payload.

The task payload is adapter input. It is identical across the paired arms for that task. The harness does not infer hidden task semantics from it.

## Evidence capture

Each executor result contains:

### Outcome

```text
PASS
FAIL
INVALID_RUN
```

A `PASS` or `FAIL` is a task outcome. `INVALID_RUN` is reserved for measurement/infrastructure conditions covered by the B0 contract.

### Quality

- requirements satisfied;
- requirements missed;
- remediation iterations;
- validation failures;
- regressions introduced.

### Token evidence

Allowed source states:

```text
HOST_REPORTED
UNAVAILABLE
```

`HOST_REPORTED` requires:

- counter identity;
- input-token count;
- output-token count.

Optional counters may include cached input, reasoning, and fresh billable tokens when the provider exposes them.

`UNAVAILABLE` requires the counter identity and all token counts to remain `null`. B1 does not substitute word, character, byte, or foreign-tokenizer estimates.

### Cost

Allowed source states:

```text
PROVIDER_REPORTED
UNAVAILABLE
```

B1 does not synthesize monetary cost when the provider did not report it.

### Latency

The adapter may report:

- wall-clock time;
- model execution time;
- tool execution time;
- coordination overhead.

### Coordination

- specialist messages;
- cross-specialist messages;
- handoffs;
- handoff failures;
- duplicate-work events;
- contradiction events;
- join wait;
- specialist re-entry.

### Communication preservation

- progress messages;
- model progress calls;
- user-visible bytes;
- context-transfer bytes;
- semantic-preservation failures;
- required-information omissions.

### Safety

Every accepted result must preserve all hard B0 guards:

```text
required_specialist_omission = false
authority_expansion = false
capability_expansion = false
governance_violation = false
provider_privacy_expansion = false
mandatory_gate_suppression = false
```

The harness rejects an executor result that attempts to report a crossed safety boundary as a valid measurement record.

## Invalid-run preservation

Executor failures are not silently removed.

Examples handled by the core harness include:

- executor launch failure;
- timeout;
- non-zero executor exit;
- non-JSON result;
- invalid result object;
- result that violates the adapter measurement contract.

The harness records an `INVALID_RUN`, retains partial stderr/stdout evidence where available, and records a digest over the unavailable-measurement evidence object.

For an invalid A5 run, `a5_shadow_observation` may be `null`. The harness does not invent a ranking merely to satisfy a schema.

## B0 schema corrections discovered during implementation

B1 implementation exposed two B0 schema edge cases. Both corrections preserve the B0 experimental intent and authority boundary.

### Interaction fixed-topology flag

The initial experiment schema made `murmurs_evaluation.fixed_topology = true` for every experiment containing a Murmurs evaluation block. That is correct for `MURMURS_ISOLATED`, but impossible for the topology-varying interaction experiment.

The corrected schema now requires:

```text
MURMURS_ISOLATED -> fixed_topology = true
A5_MURMURS_INTERACTION -> fixed_topology = false
```

### Invalid A5 observation

The initial run schema required an A5 shadow-observation object for every `A5_ISOLATED` record, including measurement-invalid runs where the executor may never have produced an A5 decision.

The corrected schema now requires the object for `PASS` or `FAIL` A5-capable runs and permits `null` for `INVALID_RUN`.

No benchmark outcome, performance threshold, runtime authority, or A5/Murmurs state was changed by these corrections.

## Output layout

A completed harness collection writes:

```text
<output>/plan.json
<output>/runs/*.json
<output>/run-index.json
<output>/experiment.json
<output>/partial-evidence/*.json    when applicable
```

### plan.json

Contains the randomized execution order and manifest digest.

### runs/*.json

One provenance-bound run record per task/repetition/arm.

### run-index.json

Indexes every recorded run and its SHA-256 digest. Invalid runs remain in the index.

### experiment.json

Records experiment-level identity, controls, arms, run evidence digests, regression guards, and maturity state.

B1 collection does not perform final statistical synthesis. Calibration can only produce `MEASUREMENT_CALIBRATED`; it cannot establish benefit.

## Validation fixtures

B1 tests use a deterministic local fixture executor. The fixture exists only to prove harness mechanics:

- schema validation;
- paired all-arm execution;
- deterministic randomization;
- A5 shadow separation;
- fixed-topology Murmurs separation;
- provider-counter transport;
- combined experiment transport;
- invalid-run retention.

Synthetic fixture measurements are explicitly not benefit evidence.

## Resource boundary

B1 core implementation authorizes no paid model calls and no external compute spend.

A live B2 or B3 measurement executor must expose trustworthy provider-native counters where token/cost claims are intended. If execution consumes paid resources, a bounded resource ceiling must be established before those live runs.

This prevents implementation validation from quietly becoming an unbounded benchmark-spend authorization.

## Promotion boundary

B1 does not alter the canonical A5 closeout:

```text
measurable benefit over fixed eligible sequences = NOT_ESTABLISHED
execution-effective promotion = DEFERRED_NOT_PROMOTED
```

B1 also does not alter the Murmurs claim boundary:

```text
token savings = NOT CLAIMED WITHOUT TRUSTWORTHY COMPARABLE LIVE HOST COUNTERS
```

The harness is evidence infrastructure only.

A future benchmark result cannot automatically:

- make A5 topology-effective;
- attach A5 to production dispatch or runtime execution;
- omit required specialists;
- expand authority or capabilities;
- expand provider/privacy scope;
- suppress validation gates;
- change Murmurs from presentation/communication behavior into semantic evidence loss;
- authorize A6;
- authorize release or deployment.

Those transitions require their own governed decision after valid comparative evidence exists.
