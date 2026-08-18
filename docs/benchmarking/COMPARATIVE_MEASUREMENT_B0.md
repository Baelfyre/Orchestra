# Shared Comparative Measurement Program B0

## Status

```text
Program: Orchestra Shared Comparative Benchmark
Phase: B0 Comparative Measurement Contract Freeze
State: CONTRACT_FREEZE_NO_BENCHMARK_EXECUTION
Issue: #340
Canonical entry: 579bf4be46a0dcb1fd46b83a8e0ca1a6df17ff4b
Canonical entry tree: 7dd2f25fc4f8ac72a8cc83b431e2f1694acb887d
A5 entry disposition: A5_CLOSED_AT_SHADOW_MATURITY_EXECUTION_PROMOTION_DEFERRED_BENEFIT_NOT_ESTABLISHED
A6 authorized: false
```

The approved measurement architecture is:

> One shared benchmark platform, two isolated primary experiments, then one controlled combined experiment.

B0 freezes the measurement contract only. It does not execute workloads, implement the benchmark runner, change production runtime behavior, promote A5, expand Murmurs semantics, begin A6, deploy, or publish a release.

## Why the experiments are separated

A5 and Murmurs change different causal variables:

- A5 evaluates coordination topology.
- Murmurs changes communication/presentation representation.

Changing both in the same primary experiment would make attribution ambiguous. A measured improvement could come from topology, communication compression, or an interaction between them. Therefore the first two experiments are isolated and the interaction experiment runs only after both isolated experiments have valid evidence.

```text
Shared benchmark platform
  -> B2 A5 isolated experiment
       communication fixed
       topology varies
  -> B3 Murmurs isolated experiment
       topology fixed
       communication varies
  -> B4 controlled interaction experiment
       topology x communication
       only after valid B2 and B3 evidence
```

## Program phases

### B0 - Comparative Measurement Contract Freeze

Freeze the common evidence schema, provenance requirements, controlled variables, invalid-run policy, outcome hierarchy, analysis policy, regression guards, and promotion boundaries.

### B1 - Shared Benchmark Harness

Implement one non-production harness capable of:

- reproducing the same starting state for paired runs;
- executing explicitly configured topology and communication arms;
- randomizing arm order within a task;
- collecting provider-native counters when available;
- running identical validation and governance checks;
- emitting machine-readable provenance-bound evidence;
- keeping A5 prediction separate from benchmark execution control.

### B2 - A5 Isolated Comparative Experiment

Hold communication mode fixed at `DEFAULT`. Execute every already-eligible topology candidate in the frozen A5 eligibility envelope. Run the A5 shadow scorer against the same frozen eligible set, but do not let the scorer choose which benchmark arm executes.

Compare:

- A5 ranked order;
- empirical best eligible topology;
- Top-1 match;
- Top-k match;
- regret;
- governed task success;
- remediation burden;
- resource use;
- latency;
- coordination overhead;
- task-class conditional performance.

A5 remains structurally shadow-only:

```text
topology_effective = false
shadow_influenced_execution = false
runtime_topology_control = false
```

### B3 - Murmurs Isolated Comparative Experiment

Hold topology fixed to the deterministic control. Compare:

```text
DEFAULT
CAVEMAN
MURMURS
```

Use the same task, provider, model, reasoning settings, tools, starting state, validation contract, and resource policy. Token deltas are valid only when the compared arms use the same provider-native counter identity.

Caveman is an external comparative baseline, not an Orchestra dependency or authority source. Published Caveman percentages are not imported as Orchestra evidence. Orchestra must run its own controlled comparison.

### B4 - Controlled A5 x Murmurs Interaction Experiment

Run only after B2 and B3 provide valid isolated evidence. Use a controlled factorial design over already-permitted topology candidates and communication modes.

The interaction conclusion is recorded separately as:

```text
POSITIVE
NEUTRAL
NEGATIVE
INCONCLUSIVE
```

The combined result cannot retroactively convert an invalid or insufficient isolated experiment into a valid benefit claim.

### B5 - Evidence Synthesis and Promotion Decision

Produce three separate conclusions where applicable:

1. A5 topology benefit conclusion;
2. Murmurs benefit conclusion;
3. A5 x Murmurs interaction conclusion.

Measurement evidence is not promotion authority. Any A5 execution-effective selection or broader Murmurs semantic-compression authority requires a separately governed transition.

## Experimental unit

One experimental run is:

```text
ONE TASK
+ ONE EXACT STARTING STATE
+ ONE FIXED MODEL/WORKER CONFIGURATION
+ ONE FIXED SPECIALIST SET
+ ONE EXPERIMENTAL ARM
= ONE RUN
```

The design is paired. Each task is repeated across every eligible arm for that experiment.

## Controlled variables

The following are held constant across paired arms unless the field is the explicit experimental variable:

- model and model revision;
- provider;
- reasoning setting when configurable;
- temperature when configurable;
- tool access;
- repository revision;
- starting worktree or fixture;
- task prompt;
- system instructions except the experimental mechanic;
- specialist set;
- required specialist set;
- authority envelope;
- governance state;
- context ceiling;
- resource/token/tool-call/time budgets when configurable;
- retry policy;
- validation contract;
- dependency and environment identity.

A topology or communication arm must not gain capabilities unavailable to another paired arm.

## Primary outcome

The primary outcome is `VALIDATED_GOVERNED_TASK_SUCCESS`.

A run passes only when all three are true:

1. the task completed;
2. required validation passed;
3. governance boundaries were preserved.

Run states are:

```text
PASS
FAIL
INVALID_RUN
```

`INVALID_RUN` is not silently treated as task failure. It is reserved for failures such as provider outage, infrastructure outage, benchmark harness failure, corrupted starting state, unresolvable external dependency failure, or measurement-capture failure. The reason and available partial evidence must be retained.

## Winner hierarchy

The empirically preferred arm is determined lexicographically rather than by an arbitrary weighted score:

```text
1. Governance valid
2. Task success
3. Validation success
4. Fewer remediation iterations
5. Lower resource consumption
6. Lower latency
7. Lower communication overhead
8. Deterministic baseline tie-break
```

Correctness and governance therefore dominate efficiency. A faster or cheaper incorrect result does not win.

## Required measurements

Where applicable and measurable, each run records:

### Quality and remediation

- task outcome;
- validation result;
- governance result;
- requirements satisfied and missed;
- remediation iterations;
- validation failures;
- regressions introduced.

### Token and cost

Provider-native counters are preferred and are the measurement authority when available:

- input tokens;
- output tokens;
- cached input tokens when exposed;
- reasoning tokens when exposed;
- fresh/billable tokens when exposed;
- provider-reported monetary cost when exposed.

Orchestra does not substitute character, byte, word, or foreign-tokenizer estimates for unavailable provider counters.

### Latency

- wall-clock time;
- model execution time when observable;
- tool execution time when observable;
- coordination overhead when observable.

### Coordination

- specialist messages;
- cross-specialist messages;
- handoffs;
- handoff failures;
- duplicate-work events;
- contradiction events;
- join wait time;
- specialist re-entry events.

### Communication preservation

- progress messages;
- model progress calls;
- user-visible bytes;
- context-transfer bytes;
- semantic-preservation failures;
- required-information omissions.

## A5-specific evaluation

The A5 experiment does not create a fifth execution topology. The harness executes the already-eligible topology candidates independently. A5 ranks the same frozen set in shadow mode.

Example:

```text
Frozen eligible set: A, B, C, D

Harness executes A
Harness executes B
Harness executes C
Harness executes D

A5 shadow ranking: C, A, D, B
Empirical best: C
Top-1 match: true
```

### Regret

Selection accuracy alone is insufficient. Record regret so a near-tie is distinguished from a materially poor selection.

Conceptually:

```text
regret = performance(best observed eligible topology)
         - performance(A5 top-ranked topology)
```

The exact normalized computation must be frozen before confirmatory testing and must preserve the winner hierarchy rather than collapsing governance and quality into a convenience score.

## Murmurs-specific evaluation

The Murmurs experiment asks whether communication reduction survives end-to-end accounting and preserves outcome quality.

A valid benefit signal requires equivalent governed task quality plus one or more measurable improvements such as:

- lower total fresh token consumption;
- lower output consumption;
- lower provider-reported cost;
- lower latency;
- lower communication overhead.

A lower visible-message or output-token count is not sufficient if it increases input overhead, retries, remediation, semantic loss, or task failure.

## Repetition stages

### Calibration

Planning target:

```text
minimum 5 tasks
2 repetitions per arm
```

Purpose: validate harness behavior, measurement capture, arm isolation, and approximate variance. Calibration produces no benefit claim.

### Pilot

Planning target:

```text
20 tasks
3 repetitions per arm
```

Purpose: estimate variance, identify task-class effects, evaluate metric stability, and determine confirmatory design. Pilot results are signals only.

### Confirmatory

The final sample size is selected from pilot variance and power analysis. A planning range of 50 to 100 tasks with approximately 3 repetitions per arm is retained when feasible, but it is not an arbitrary fixed requirement.

Before confirmatory outcomes are observed:

- the task manifest is frozen;
- benefit thresholds are preregistered;
- exclusions are frozen except objective invalid-run rules;
- analysis rules are frozen;
- A5 must not be tuned against the confirmatory set.

## Practical-benefit policy

Statistical detectability is not sufficient for promotion.

The B0 planning signals are deliberately non-authoritative:

```text
task success: +5 percentage points
remediation: >=15% relative reduction
fresh tokens: >=10% relative reduction
latency: >=10% relative reduction
```

These are pilot planning signals only. They are not current promotion thresholds and cannot be cited as established Orchestra performance. Confirmatory thresholds must be preregistered after pilot variance is known and may not be changed after confirmatory outcomes are observed.

## Analysis policy

The evidence synthesis must:

- use paired comparisons;
- report absolute and relative differences;
- report uncertainty for success rates;
- prefer median and IQR for skewed continuous measures;
- prefer paired bootstrap confidence intervals for continuous deltas where appropriate;
- report task-class stratification;
- report p90, p95, and worst-case behavior for important regression metrics;
- retain failed and invalid runs rather than presenting only successful examples.

A statistically significant efficiency gain cannot override a governance, validation, or material quality regression.

## Regression guards

Benefit cannot be established by crossing any of these boundaries:

- required specialist omission;
- authority expansion;
- capability expansion;
- governance violation;
- provider/privacy expansion;
- mandatory validation-gate suppression;
- significant governed-task-success degradation;
- unacceptable tail-failure regression;
- unresolved information-preservation regression.

## Task stratification

The benchmark manifest should cover multiple task structures because topology and communication effects may be conditional:

- single-domain;
- multi-domain;
- architecture-heavy;
- debugging;
- security-sensitive;
- validation-heavy;
- documentation plus implementation;
- dependency-heavy;
- parallel-friendly;
- high-coordination.

No claim that one topology is globally optimal should be made from a workload that represents only one task class.

## External comparative references

External systems provide methodology and workload references, not Orchestra performance claims.

### MAFBench

Pinned repository revision for B0 review:

```text
CoDS-GCS/MAFBench
86893aa65f0ecf404779749ec046e78afdb1bd35
arXiv:2602.03128
```

Use as the primary reference for controlled architectural isolation, standardized execution/logging, and coordination/topology evaluation.

### AgentsNet

Pinned repository revision for B0 review:

```text
floriangroetschla/AgentsNet
269f576e966f441e54ba72a653769663a4f4322c
arXiv:2507.08616
```

Use as the primary topology-sensitive coordination workload reference.

### Caveman

Pinned repository revision for B0 review:

```text
JuliusBrussee/caveman
ae405e872270acc57484693612ae038b16c8f6cd
```

Use as the external Murmurs comparative baseline. Caveman is not bundled and its published savings percentages are not Orchestra evidence.

### SWE-bench Verified

Use as one secondary real-software-engineering workload source rather than the sole confirmatory benchmark. Its real-world issue tasks are useful for workload realism, but benchmark age and contamination risk must be recorded in the evidence limitations.

### GPTSwarm

Use as a secondary adaptive-topology research reference. Its graph-optimization approach may inform analysis, but an external learned graph policy is not imported as Orchestra authority.

## Machine records

B0 introduces:

- `machine/benchmarking/comparative-measurement-contract.v1.json`;
- `machine/schemas/comparative-benchmark-run.schema.json`;
- `machine/schemas/comparative-benchmark-experiment.schema.json`.

The schemas define evidence interchange. They do not themselves authorize execution.

## Evidence states

The benchmark program uses explicit maturity states:

```text
MEASUREMENT_NOT_STARTED
MEASUREMENT_CALIBRATED
PILOT_EVIDENCE_INSUFFICIENT
PILOT_BENEFIT_SIGNAL
CONFIRMATORY_BENEFIT_ESTABLISHED
CONFIRMATORY_BENEFIT_NOT_ESTABLISHED
CONFIRMATORY_REGRESSION_DETECTED
```

A5 and Murmurs conclusions remain separate even when the combined experiment is later run.

## Promotion boundary

B0 does not reopen the prior A5 closeout decision. Until new governed comparative evidence exists, the canonical A5 result remains:

```text
measurable benefit over fixed eligible sequences = NOT_ESTABLISHED
execution-effective topology promotion = DEFERRED_NOT_PROMOTED
```

The benchmark program creates a governed route to collect the missing evidence. It does not pre-decide the outcome.

Likewise, Murmurs continues to make no token-savings claim without trustworthy comparable live-host counters.

A future benefit result cannot automatically:

- make A5 topology-effective;
- attach A5 to Conductor dispatch or `RuntimeExecutor`;
- change required specialist ownership;
- widen Murmurs into semantic evidence compression;
- change authority, capability, governance, provider/privacy, or validation ceilings;
- authorize A6 or later adaptive phases;
- authorize release or deployment.

Those transitions require their own governed decision after the evidence is reviewed.
