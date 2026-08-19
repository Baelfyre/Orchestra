# Comparative Measurement B3 - Murmurs Isolated Comparative Experiment

## Status

```text
Program: Orchestra Shared Comparative Benchmark
Phase: B3 Murmurs Isolated Comparative Experiment
Current bounded unit: B3.1 Antigravity Measurement Executor Binding
State: B3_1_ANTIGRAVITY_EXECUTOR_BINDING_IMPLEMENTED
Canonical entry: 06ede6bde3aa7682194950ba9130ba52e4fb0ea5
Canonical entry tree: baf159c27e4149ff2453f20f92245b4d963b4f19
Authoritative benchmark machine state: B0/B1/B3.1 executor binding
Measurement maturity after unit implementation: MEASUREMENT_NOT_STARTED
Murmurs benefit: NOT ESTABLISHED
A5 execution-effective selection: NOT AUTHORIZED
A6: NOT AUTHORIZED
Paid provider calls: NOT AUTHORIZED BY THIS UNIT
```

B3.1 implements the bounded Antigravity measurement executor binding needed for the Orchestra comparative benchmark harness.

It does not execute the 30-run B3 calibration in this unit, does not measure live token savings or benefit, does not vendor Caveman, and does not alter production runtime routing.

## Evidence boundary

```text
EXECUTOR BINDING IMPLEMENTATION != MEASURED CALIBRATION
PLAN-ONLY VALIDATION != MEASURED CALIBRATION
SYNTHETIC FIXTURE != MURMURS BENEFIT EVIDENCE
CAVEMAN PUBLISHED RESULTS != ORCHESTRA RESULTS
MEASUREMENT_NOT_STARTED remains current after B3.1
```

The authoritative benchmark machine state incorporates the B3.1 executor binding record (`machine/benchmarking/antigravity-executor-binding.v1.json`) alongside the B0 contract and B1 harness. Measurement maturity remains `MEASUREMENT_NOT_STARTED` until genuine calibrated evidence is collected.

## B3.1 Host Smoke Baseline

The host smoke establishes the baseline environment:

```text
host: Antigravity CLI
cli_version: 1.1.14
model: gemini-3.7-flash-high
structured_transport: JSON
native usage fields observed:
  - input_tokens
  - output_tokens
  - thinking_tokens
  - cache_read_tokens
  - total_tokens
useG1Credits: false
smoke_result: SUCCESS
```

Smoke execution was non-evidentiary and is not added to B3 calibration evidence.

## Host-Native Token Mapping

The Antigravity executor maps native structured usage fields as follows:

```text
Antigravity input_tokens       -> Orchestra tokens.input_tokens
Antigravity output_tokens      -> Orchestra tokens.output_tokens
Antigravity cache_read_tokens  -> Orchestra tokens.cached_input_tokens
Antigravity thinking_tokens    -> Orchestra tokens.reasoning_tokens
Antigravity total_tokens       -> preserved in raw_evidence only
```

Rules:
- `total_tokens` is preserved in `raw_evidence` only and is NOT mapped to `fresh_billable_tokens`.
- `fresh_billable_tokens` remains `null` unless Antigravity exposes a native field representing billable consumption.
- Cost remains `source = UNAVAILABLE`, `amount = null`, `currency = null` unless provider-reported monetary cost is exposed.

## Deterministic Counter Identity

Antigravity does not expose a vendor-assigned counter identifier in the observed structured result.

Orchestra assigns the deterministic measurement-surface identity:

```text
antigravity-cli-1.1.14:json-usage:gemini-3.7-flash-high
```

Provenance rules:
- This identifier represents Orchestra-assigned provenance identifying the exact host-native measurement surface.
- It is NOT claimed to be an Antigravity/provider-issued identifier.
- Paired B3 token deltas are valid only while this counter identity remains identical across `DEFAULT`, `CAVEMAN`, and `MURMURS` arms.
- If the CLI version, model identity, usage-field semantics, provider/host, or structured-output mechanism changes, the counter identity must change and the affected paired batch must not be combined as one comparable counter population.

## Execution Controls and B3.1.1 Live Invocation Hardening

The B3 Antigravity executor pins:

```text
model: gemini-3.7-flash-high
output_format: json
personal_credit_fallback: disabled (useG1Credits: false in ~/.gemini/antigravity-cli/settings.json)
mode: non-interactive (print-mode interface)
```

### Production Live-Execution Command Format (B3.1.1)

The live invocation path uses the validated Antigravity print-mode command interface:

```json
[
  "agy",
  "--model",
  "gemini-3.7-flash-high",
  "-p",
  "<PROMPT>",
  "--output-format",
  "json"
]
```

Invocation invariants:
- Prompt is delivered strictly through `-p` / `--print` argument.
- Benchmark prompt is not supplied through subprocess stdin.
- `shell=False` is mandatory; stdout and stderr are captured.
- Unvalidated `--no-use-g1-credits` command argument is removed (credit policy is enforced in `settings.json`).
- Non-zero subprocess exit codes fail closed as `MEASUREMENT_CAPTURE_FAILURE` or `HARNESS_FAILURE`.

### Fail-Closed Host Preflight (B3.1.1)

Before any real model invocation, the executor verifies:
1. Resolved Antigravity CLI version (`agy --version`) is exactly `1.1.14`.
2. `settings.json` exists and parses successfully.
3. `useG1Credits` is explicitly `false`.
4. Benchmark model in request control identity remains exactly `gemini-3.7-flash-high`.
5. Expected measurement-surface counter identity remains `antigravity-cli-1.1.14:json-usage:gemini-3.7-flash-high`.

If any preflight condition fails, the executor returns `INVALID_RUN` with `MEASUREMENT_CAPTURE_FAILURE` without executing a model call.

### Explicit Provenance Semantics (B3.1.1)

The observed Antigravity outer JSON envelope does not necessarily contain host-returned model or version fields. Provenance is preserved explicitly in raw evidence:
- CLI version: `source = PREFLIGHT_COMMAND` (exact validated `agy --version`)
- Model: `source = PINNED_COMMAND_ARGUMENT` (`gemini-3.7-flash-high`)
- Usage counters: `source = HOST_REPORTED_JSON_USAGE`
- Counter ID: `provenance = ORCHESTRA_ASSIGNED_MEASUREMENT_SURFACE` (not provider-issued)

### Communication Response Bytes (B3.1.1)

User-visible response bytes are measured from the `response` field of the Antigravity structured envelope (or `content` field when present), ensuring accurate communication accounting.

Fail-closed invariants:
The executor fails closed as `INVALID_RUN` with `MEASUREMENT_CAPTURE_FAILURE` (or `CORRUPTED_STARTING_STATE` / `HARNESS_FAILURE`) when:
1. Outer JSON cannot be parsed;
2. Host status is not usable (or not `SUCCESS`);
3. Native usage object is missing;
4. `input_tokens` is missing or invalid;
5. `output_tokens` is missing or invalid;
6. Model identity changes or mismatches the pinned model;
7. Counter identity changes inside a paired batch;
8. Canonical starting-state identity is corrupted;
9. Preflight checks fail (version, settings, credit policy).

## Quality Boundary: Host Status != Task Outcome

Antigravity status `SUCCESS` does NOT imply benchmark task `PASS`.

The benchmark task outcome is determined independently from explicit independently established evidence:
- Task completion (`task_completed`);
- Required validation (`validation_passed`);
- Governance preservation (`governance_valid`).

Missing task-completion, validation, or governance fields default to `false` and cannot manufacture a benchmark `PASS`. When host execution succeeds but benchmark validation fails, the run is recorded as a valid execution with outcome `FAIL` (not `PASS`, and not `INVALID_RUN`).

## Causal variable

B3 changes only communication mode.

The topology identity is fixed across all arms:

```text
topology_class = FIXED_DETERMINISTIC
same topology_candidate_id
same topology_digest
```

The required communication arms are exactly:

```text
DEFAULT
CAVEMAN
MURMURS
```

The runner rejects missing, additional, duplicate, or topology-varying Murmurs-isolated arms.

## Caveman role

Caveman is the external comparative baseline frozen by B0:

```text
repository: JuliusBrussee/caveman
pinned revision: ae405e872270acc57484693612ae038b16c8f6cd
role: PRIMARY_MURMURS_EXTERNAL_COMPARATIVE_BASELINE
runtime dependency: false
Orchestra authority source: false
```

The Caveman arm must be executed on Orchestra's own controlled workload under the same provider/model and measurement identity as the other arms. Published Caveman percentages cannot be imported as Orchestra benefit evidence.

B3.1 does not vendor Caveman, copy its source, install it, execute it, or introduce it as an Orchestra runtime dependency.

## Calibration floor

B3 inherits the B0 calibration floor:

```text
minimum tasks = 5
repetitions per arm = 2
fixed topology = required
communication arms = DEFAULT / CAVEMAN / MURMURS
arm order = randomized reproducibly
claims allowed = false
```

Expected plan size:

```text
5 tasks x 2 repetitions x 3 communication arms = 30 planned runs
```

## Quality and preservation gates

Efficiency is subordinate to correctness and governance. A Murmurs benefit claim cannot be established if communication reduction causes meaningful regressions in:

- task completion;
- required validation;
- governance boundaries;
- remediation iterations;
- regressions introduced;
- semantic preservation;
- required-information retention;
- handoff integrity;
- required specialist participation.

The B0 lexicographic winner hierarchy remains authoritative:

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

## Governance Boundary

This unit authorizes no:
- Live 30-run B3 calibration execution;
- Paid model calls or metered compute spend;
- Caveman installation or vendoring;
- Token savings or Murmurs benefit claims;
- Changes to Murmurs production semantics;
- A5 execution-effective selection;
- A6 initiation;
- B4 interaction experiment execution;
- Release publication or deployment.

B4 remains BLOCKED until valid measured B2 and B3 evidence exists.
