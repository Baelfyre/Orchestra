# Comparative Measurement B3 - Murmurs Isolated Comparative Experiment

## Status

```text
Program: Orchestra Shared Comparative Benchmark
Phase: B3 Murmurs Isolated Comparative Experiment
Current bounded unit: B3.2 Diagnostic Attempt 4 Evidence Closeout + Calibration Plan-Only Readiness
State: B3_2_DIAGNOSTIC_ATTEMPT_4_VALID_COMPLETE_CALIBRATION_PLAN_READY
Canonical entry: d95f677dbf23ab79c4698c26645ea30cea9b3019
Canonical entry tree: ceab55bd512ea6fde4e8e76877cbb7006d18500e
Authoritative benchmark machine state: B0/B1/B3.2 Attempt 4 diagnostic closeout + B3 calibration plan-only
Validated local Antigravity host: Antigravity CLI 1.1.15
Measurement maturity after unit implementation: MEASUREMENT_NOT_STARTED
Murmurs benefit: NOT ESTABLISHED
A5 execution-effective selection: NOT AUTHORIZED
A6: NOT AUTHORIZED
Paid provider calls: NOT AUTHORIZED BY THIS UNIT
Diagnostic execution: VALID_COMPLETE (3/3 calls accepted, minimal workspace ceiling established)
Calibration execution: PLAN_ONLY_READY (NOT EXECUTED LIVE)
```

B3.2 Diagnostic Attempt 4 records a valid, completed 3-arm instrumentation diagnostic closeout for the Orchestra comparative benchmark harness under Antigravity CLI 1.1.15 and `gemini-3.7-flash-high` stream-json transport. It confirms that native `--add-dir <path>` headless workspace binding successfully isolates host operations to the configured minimal task directory, bounding per-call host consumption well within the 45,000 token limit (DEFAULT=29908, MURMURS=29668, CAVEMAN=33054; cumulative=92630 <= 120000; weekly remaining fraction drop=0.0006388425827026367 <= 0.05). All 3 planned arm calls completed with identical counter identity (`antigravity-cli-1.1.15:stream-json-usage:gemini-3.7-flash-high`) and zero invalid runs.

In addition, B3 calibration readiness is established by refreshing the frozen plan-only calibration fixture (`tests/fixtures/benchmarking/b3-murmurs-isolated-calibration-plan-only.json`) and test suite (`tests/runtime/test_comparative_benchmark_b3_plan.py`) against canonical entry baseline `d95f677dbf23ab79c4698c26645ea30cea9b3019`, deterministically verifying 30 scheduled runs (5 tasks x 2 repetitions x 3 arms in 10 paired blocks) with zero live model turns.

It does not execute live calibration calls, does not measure live token savings or comparative benefit, does not vendor Caveman, and does not alter production runtime routing.

## Evidence boundary

```text
ARM OPERATIONALIZATION IMPLEMENTATION != MEASURED CALIBRATION
PLAN-ONLY VALIDATION != MEASURED CALIBRATION
SYNTHETIC FIXTURE != MURMURS BENEFIT EVIDENCE
CAVEMAN PUBLISHED RESULTS != ORCHESTRA RESULTS
MEASUREMENT_NOT_STARTED remains current after B3.1.6
```

The authoritative benchmark machine state incorporates the B3.1.6 executor binding record (`machine/benchmarking/antigravity-executor-binding.v1.json`) alongside the B0 contract and B1 harness. Measurement maturity remains `MEASUREMENT_NOT_STARTED` until genuine calibrated evidence is collected.

## B3.1.2 / B3.1.3 Communication Treatments

The three communication arms are deterministically bound by the executor:

### 1. DEFAULT Treatment
- **Presentation Mode**: `NORMAL`
- **Substance**: Task prompt unchanged; no compression policy applied.
- **Treatment Identity**: Deterministic digest over `{"communication_mode": "DEFAULT", "presentation_mode": "NORMAL", "treatment_effective": true, "provenance": {"source": "ORCHESTRA_CANONICAL_PRESENTATION", "mode": "DEFAULT", "presentation_mode": "NORMAL"}}`.
- **Output Accounting**: Full text length of intermediate progress and final response bytes.

### 2. CAVEMAN Treatment
- **External Pinned Baseline**: `JuliusBrussee/caveman` at revision `ae405e872270acc57484693612ae038b16c8f6cd`.
- **Target Policy**: `skills/caveman/SKILL.md` (Git blob SHA-1 `bd22d86b32e4a99e09ff7482a35509faac7a6f65`).
- **Fail-Closed Verification**: Revision mismatch, blob mismatch, missing policy, or empty content fails closed as `UNRESOLVABLE_EXTERNAL_DEPENDENCY_FAILURE`.
- **Exclusion**: `caveman-compress` and context proxies are strictly prohibited.
- **Effective Prompt**: `[COMMUNICATION POLICY]\n<CAVEMAN_POLICY>\n\n[TASK]\n<TASK_PROMPT>`.
- **Treatment Identity**: Deterministic digest including repository, revision, skill path, blob hash, and policy digest.

### 3. MURMURS Treatment
- **Canonical Presentation**: `orchestra_runtime.presentation` engine with `PresentationMode.MURMURS`.
- **Contracts**: `machine/presentation/murmurs-policy.v1.json` and `machine/presentation/murmurs-vocabulary.v1.json`.
- **Prompt Invariant**: Underlying task prompt substance remains completely unpolluted.
- **Presentation Dispositions**: Routine lifecycle events reduce to `SILENT` (0 bytes) or non-semantic `MURMUR` (short filler bytes); forced explain events remain `EXPLAIN` (full payload bytes).
- **Treatment Identity**: Deterministic digest over presentation mode, policy digest, and vocabulary digest.

## Task Prompt Invariant

Under B3 comparative measurement:
- `task_prompt_digest` remains identical across `DEFAULT`, `CAVEMAN`, and `MURMURS` arms for the same benchmark task.
- `effective_prompt_or_policy_digest` is tracked separately:
  - For `DEFAULT`: identical to `task_prompt_digest`.
  - For `CAVEMAN`: digest of the policy-prepended effective prompt.
  - For `MURMURS`: identical to `task_prompt_digest` (presentation logic runs outside the prompt).

## Host Transport and Counter Identity

The executor supports host-native structured JSON and NDJSON event streaming (`stream-json`):

```text
Canonical json counter:        antigravity-cli-1.1.15:json-usage:gemini-3.7-flash-high
Canonical stream-json counter: antigravity-cli-1.1.15:stream-json-usage:gemini-3.7-flash-high
```

Paired comparability invariants:
- All arms within a paired block must use the exact same transport and counter identity.
- Cross-run validation fails closed if `counter_id` drifts across arms.
- Native usage counters (`input_tokens`, `output_tokens`, `cache_read_tokens`, `thinking_tokens`) map deterministically into Orchestra token schema regardless of transport format.
- `total_tokens` remains in `raw_evidence` only.
- Cost remains `UNAVAILABLE`.

## Sparse Settings Semantics & Credit Policy Resolution

Antigravity CLI settings persistence follows sparse persistence semantics:
1. `useG1Credits` has system default `false`.
2. Values equal to system defaults may be omitted from `settings.json`.
3. An omitted `useG1Credits` key and `"useG1Credits": false` both represent the exact same effective host policy: `effective_use_g1_credits = false` (credit fallback disabled).
4. The benchmark invariant is strictly: `effective_use_g1_credits` must be `false`.

Preflight state resolution table:
- **Key absent (`settings = {}`)**: resolves to `effective_use_g1_credits = false`, passes preflight with `effective_source: SYSTEM_DEFAULT_SPARSE_PERSISTENCE`.
- **Key explicitly false (`settings = {"useG1Credits": false}`)**: resolves to `effective_use_g1_credits = false`, passes preflight with `effective_source: EXPLICIT_SETTING`.
- **Key explicitly true (`settings = {"useG1Credits": true}`)**: fails closed as `INVALID_RUN` (`MEASUREMENT_CAPTURE_FAILURE`) because personal credit fallback is enabled.
- **Key present with non-boolean value (`null`, `0`, `1`, `"false"`, `"true"`, `{}`, `[]`)**: fails closed as `INVALID_RUN` (`MEASUREMENT_CAPTURE_FAILURE`) without silent coercion.

Raw and effective provenance is recorded in `raw_evidence.credit_fallback_policy` to distinguish the physical file representation from the resolved host policy.

## B3.1.5 Stream-JSON Result Envelope Normalization

B3.1.5 introduces deterministic stream-json terminal envelope normalization in `scripts/antigravity_benchmark_executor.py` via `normalize_stream_terminal_event`. It aligns canonical parser behavior with empirical Antigravity CLI 1.1.15 host evidence where the terminal stream event has structure `{"event": "result", "result": {"status": "SUCCESS", "usage": {...}, "response": "..."}}`.

Key normalization and invariant rules:
- **Wrapped 1.1.15 Event**: Detects `event == "result"` and canonical payload in `event["result"]`.
- **Legacy Flat Compatibility**: Preserves flat terminal structures `{"type": "result", "status": "SUCCESS", "usage": {...}}` and flat envelopes.
- **Dual Envelope Retention**: Preserves both the full original host wrapper in `raw_evidence.terminal_event_envelope` (and `raw_evidence.outer_envelope`) and the normalized payload in `raw_evidence.terminal_result_payload`.
- **Intermediate Event Discrimination**: Discriminates progress events using `event` in addition to `event_kind`/`kind`/`type` (e.g. `event = "step_update"`, `event = "tool_start"`), while strictly excluding the terminal result from intermediate progress counts.
- **Fail-Closed Conflict Handling**: Fails closed if outer wrapper and nested result contain conflicting measurement-critical fields (`status`, `usage`, `cli_version`, `model`).
- **Fail-Closed Malformation**: Fails closed if terminal result is missing, result payload is not an object, status is missing/non-SUCCESS, usage is missing/malformed, or multiple conflicting terminal results exist in the stream.

## B3.1.6 Explicit Antigravity Headless Workspace Binding

B3.1.6 introduces deterministic explicit workspace binding for Antigravity headless print-mode execution in `scripts/antigravity_benchmark_executor.py` via `resolve_workspace` and the verified `--add-dir <path>` native AGY CLI 1.1.15 argument interface.

Key workspace binding and invariant rules:
- **Explicit Binding Mechanism**: Passes `--add-dir <resolved_workspace_path>` as discrete argument tokens without shell concatenation (`shell=False`).
- **No Implicit CWD Derivation**: Does not derive the AGY workspace implicitly from process working directory or the Orchestra repository root.
- **Deterministic Validation**: Resolves and validates the workspace path before model invocation. Fails closed (`INVALID_RUN` / `MEASUREMENT_CAPTURE_FAILURE`) before real turns if the workspace is missing, non-existent, or not a directory.
- **Independent Workspace Selection**: Allows external diagnostic minimal workspaces to be bound independently from Orchestra runtime contract resolution.
- **Provenance Retention**: Records complete workspace binding provenance in `raw_evidence.workspace_binding` (`bound`, `workspace_path`, `workspace_flag`, `workspace_mechanism`, `provenance.source`, `provenance.resolved_path`, `provenance.is_directory`).
- **Scratch Fallback Prohibition**: Fails closed rather than silently falling back to `~/.gemini/antigravity-cli/scratch`.

## B3.2 Diagnostic Attempt 2 Compatibility Disposition

Empirical diagnostic evidence from B3.2 Attempt 2 recorded the following compatibility finding (external evidence directory remains uncommitted):

```text
B3_2_DIAGNOSTIC_ATTEMPT_2 = INVALID_RUN

cause:
AGY_STREAM_RESULT_ENVELOPE_SCHEMA_MISMATCH

additional finding:
RESOURCE_CEILING_EXCEEDED

observed host counters:
input_tokens = 142896
output_tokens = 4692
thinking_tokens = 2804
cache_read_tokens = 786302
total_tokens = 147588

configured diagnostic ceiling:
45000 total_tokens per call

live_host_turns_consumed:
1

accepted_benchmark_measurements:
0

benefit evidence:
NONE
```

## B3.2 Diagnostic Attempt 3 Compatibility Disposition

Empirical diagnostic evidence from B3.2 Attempt 3 recorded the following compatibility finding (external evidence directory remains uncommitted):

```text
B3_2_DIAGNOSTIC_ATTEMPT_3 = INVALID_RUN

cause:
HEADLESS_WORKSPACE_BINDING_FAILURE

observed host counters:
input_tokens = 59833
output_tokens = 1397
thinking_tokens = 1183
cache_read_tokens = 48900
total_tokens = 61230

configured diagnostic ceiling:
45000 total_tokens per call

live_host_turns_consumed:
1

accepted_benchmark_measurements:
0

minimal_workspace_resource_ceiling:
NOT_ESTABLISHED

benefit evidence:
NONE
```

The values above represent diagnostic compatibility evidence only. They are not comparative Murmurs/Caveman performance evidence.

## B3.2 Diagnostic Attempt 4 Empirical Evidence & Closeout Disposition

Empirical diagnostic evidence from B3.2 Attempt 4 in local directory `_orchestra-benchmark-evidence/b3-2-three-arm-diagnostic-20260820-013812` recorded the following verified instrumentation disposition:

```text
B3_2_DIAGNOSTIC_ATTEMPT_4 = VALID_COMPLETE
diagnostic_execution = PASS
task_outcomes = FAIL / FAIL / FAIL
accepted_measurements = 3
invalid_runs = 0
live_host_turns = 3
minimal_workspace_resource_ceiling = ESTABLISHED_WITHIN_LIMIT
headless_workspace_binding = WORKING (--add-dir <minimal-workspace>)
stream_json_measurement_capture = WORKING
same_counter_identity = WORKING
counter_id = antigravity-cli-1.1.15:stream-json-usage:gemini-3.7-flash-high
transport = stream-json-usage
planned_calls = 3
completed_calls = 3
planned_arm_order = DEFAULT, MURMURS, CAVEMAN
credit_fallback = false
initial_gemini_weekly_remaining_fraction = 0.6658271551132202
final_gemini_weekly_remaining_fraction = 0.6651883125305176
weekly_remaining_fraction_drop = 0.0006388425827026367 (<= 0.05 ceiling)
cumulative_host_total_tokens = 92630 (<= 120000 budget ceiling)
```

### Observed Host Counters by Arm (Diagnostic Compatibility Evidence Only)

- **DEFAULT Arm**:
  - `outcome_status`: `FAIL`
  - `total_tokens`: `29908` (<= 45000 per-call ceiling)
  - `input_tokens`: `29119`
  - `output_tokens`: `789`
  - `reasoning_tokens`: `662`
  - `cached_input_tokens`: `24462`
  - `progress_messages`: `8`
  - `model_progress_calls`: `7`
  - `user_visible_bytes`: `130`

- **MURMURS Arm**:
  - `outcome_status`: `FAIL`
  - `total_tokens`: `29668` (<= 45000 per-call ceiling)
  - `input_tokens`: `29014`
  - `output_tokens`: `654`
  - `reasoning_tokens`: `527`
  - `cached_input_tokens`: `24462`
  - `progress_messages`: `7`
  - `model_progress_calls`: `6`
  - `user_visible_bytes`: `167`

- **CAVEMAN Arm**:
  - `outcome_status`: `FAIL`
  - `total_tokens`: `33054` (<= 45000 per-call ceiling)
  - `input_tokens`: `32374`
  - `output_tokens`: `680`
  - `reasoning_tokens`: `554`
  - `cached_input_tokens`: `24468`
  - `progress_messages`: `7`
  - `model_progress_calls`: `6`
  - `user_visible_bytes`: `130`

### Authoritative Local Raw Evidence SHA-256 Provenance

The external diagnostic evidence directory (`_orchestra-benchmark-evidence/b3-2-three-arm-diagnostic-20260820-013812`) is anchored by cryptographic SHA-256 hashes without committing raw host run artifacts:

| Evidence File | SHA-256 Digest | Size (bytes) |
|---|---|---|
| `diagnostic-report.json` | `3ae52d2e1efb484805383d10a1289f84a22eab217a79c86cf7b564c9dd41f8c8` | 3450 |
| `manifest.json` | `5c630f0520e01bd6f8ff03adb06ac0d64ef99255d6003551d6b2bbbbd76c094e` | 3783 |
| `plan.json` | `46da32eca3710884b5321642a1c14720e1240590bd2356e2397376054dd04f85` | 2153 |
| `resource-budget.json` | `d26def995823d1e78ba921635206a201ebd44f9f2e1930a0f624e80adae33887` | 293 |
| `run-index.json` | `2ab6087f72343ba41d02f6bd93221ef0b71d3d33463c5376a7696db5a4f13561` | 1072 |
| `experiment.json` | `433871169eac0f6d69e7179f743e3421c229bb9f54f82ebdd8347b84c8d4bed7` | 3905 |
| `final-usage.json` | `dd89d18b35b4cb54bc10d5e82950af27f85e06a2f2400201b6f24fa267e0abba` | 2776 |
| `host-preflight.json` | `2af7827535276da8a87f9e74dd3f37df4a4a54623876bfe0403e5678f6a92576` | 4506 |
| `caveman-preflight.json` | `0d6c8943b4136203844fabff21e5fd5c23e6188f870b8f13e38fde8a86332df2` | 296 |
| `minimal-workspace/diagnostic_input.json` | `87a2fc40e0c330716698110c1cd50e310d5d2eda217fe9b45c7d0fbab5303c52` | 171 |
| `executor-results/01-74187e41b2b2047f443f5da7.json` | `eea8297f4e0c6ff57437dd6603fc663b93e3c1e8bde599de3abd4a8e552526f7` | 12555 |
| `executor-results/02-838c60d4f8dee4fdd2ef91fc.json` | `f53243fc61bd21f43423a92e9af1a1d398a4e78205f409e48f2914ba05ea440e` | 12436 |
| `executor-results/03-5d2cb3c43e0b8c42a6292369.json` | `0a13b797a0bebedf669de0cd94cbcb3ac5bb2252a61693715be783615b0c7278` | 12540 |
| `runs/00001-74187e41b2b2047f443f5da7.json` | `0a9a6795e448e4637fe8348afeff17a3703e00c71c89e6a04de09c66e353e647` | 4216 |
| `runs/00002-838c60d4f8dee4fdd2ef91fc.json` | `774c0641124e7875d642b28273ffb28b97557373012769ec2d90f05ef6660faf` | 4216 |
| `runs/00003-5d2cb3c43e0b8c42a6292369.json` | `a7a95737c3a8b171d9f9ace985d3a1b19a7fb98aa2f697c3ecabca050fe3afa6` | 4216 |
| `requests/01-74187e41b2b2047f443f5da7.json` | `140e9e416892d5e757512ddec14d88a797b57231b724ceb18090bfc6e98e0ea4` | 3247 |
| `requests/02-838c60d4f8dee4fdd2ef91fc.json` | `2887425a9dcae946c7504457b201a6be1dba3b624391525b781d684665a1a9c0` | 3247 |
| `requests/03-5d2cb3c43e0b8c42a6292369.json` | `7d82c0e1706da1427671d3b6c0d863662e234a5ae9814da78eebfb5f6d66bf58` | 3247 |
| `quota/after-01-DEFAULT.json` | `3caf02f8afc4ddf6525ec204a9d51f4e81b02521930b13c9f88220fac3bdaaf8` | 3036 |
| `quota/after-02-MURMURS.json` | `df0a1c0aae0894f50428de968521a4852adbb2639e7629be4403e724780dfbea` | 3032 |
| `quota/after-03-CAVEMAN.json` | `a9fb617938d71822628ad9a3386459ba7dc34872f6bfbfb048efec3ce6fc6ad9` | 3031 |

### Non-Inference Rule

The values above represent instrumentation diagnostic evidence only. They cannot be used to infer comparative Murmurs or Caveman token savings percentages or efficiency claims.


## Quality Boundary: Host Status != Task Outcome

Antigravity status `SUCCESS` does NOT imply benchmark task `PASS`.

The benchmark task outcome is determined independently from explicit independently established evidence:
- Task completion (`task_completed`);
- Required validation (`validation_passed`);
- Governance preservation (`governance_valid`).

Missing task-completion, validation, or governance fields default to `false` and cannot manufacture a benchmark `PASS`.

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

B3.1.2 does not vendor Caveman, copy its source, install it, execute it, or introduce it as an Orchestra runtime dependency.

## Calibration floor & Plan-Only Readiness

B3 inherits the B0 calibration floor and establishes zero-turn plan-only readiness under the Padayon-grounded task set:

```text
task-set version = orchestra.b3-calibration-task-set.v1
task-set status = PADAYON_GROUNDED_V1_FROZEN
task-set aggregate digest = fd5109b2ec94709883bd75a9b7c6c89b6cd4f9bcc9840554bbd7cbb277a931a8
validator type = EXACT_JSON_CONFORMANCE_V1
minimum tasks = 5
repetitions per arm = 2
fixed topology = required
communication arms = DEFAULT / CAVEMAN / MURMURS
arm order = randomized reproducibly
claims allowed = false
canonical entry baseline = d95f677dbf23ab79c4698c26645ea30cea9b3019
calibration plan-only fixture = tests/fixtures/benchmarking/b3-murmurs-isolated-calibration-plan-only.json
calibration test suite = tests/runtime/test_comparative_benchmark_b3_plan.py
planned runs = 30 (5 tasks x 2 repetitions x 3 communication arms)
paired task/repetition blocks = 10
live model turns during dry run = 0
executor sentinel = impossible executor verified
```

Expected plan size:

```text
5 tasks x 2 repetitions x 3 communication arms = 30 planned runs
```

Deterministic dry-run validation proves that running the plan-only calibration against an impossible executor sentinel creates no `runs/`, `run-index.json`, `experiment.json`, or `partial-evidence/` artifacts and executes zero live provider/model turns.

The five calibration tasks are grounded in Padayon's approved work sequence (R5 capability manifest, R6/O1/O2 compatibility, O3/O4 freshness, Issue #115 assurance drift, and O5/O6 routing), each carrying a deterministic validation contract (`EXACT_JSON_CONFORMANCE_V1`) to derive task completion, validation, and governance outcomes directly from model responses rather than relying on pre-seeded booleans or self-reported status.

Live calibration execution remains **NOT AUTHORIZED** until a separate human-gated decision freezes the live calibration workload, per-call and cumulative resource budgets, and stop conditions.

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
- Antigravity/model/provider calls during this bounded closeout unit;
- 30-run live calibration execution;
- Pilot or confirmatory benchmark execution;
- Paid model calls or metered compute spend;
- Caveman installation, vendoring, or runtime dependency;
- Token savings or Murmurs benefit claims;
- Changes to Murmurs production semantics;
- A5 execution-effective selection;
- A6 initiation;
- B4 interaction experiment execution;
- Release publication or deployment.

B4 remains BLOCKED until valid measured B2 and B3 evidence exists.
