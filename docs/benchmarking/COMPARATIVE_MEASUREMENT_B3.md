# Comparative Measurement B3 - Murmurs Isolated Comparative Experiment

## Status

```text
Program: Orchestra Shared Comparative Benchmark
Phase: B3 Murmurs Isolated Comparative Experiment
Current bounded unit: B3.1.6 Explicit Antigravity Headless Workspace Binding
State: B3_1_6_HEADLESS_WORKSPACE_BINDING_IMPLEMENTED_SOURCE_ONLY
Canonical entry: 13350b1be10e115fb95abc5f2cecc66dd95427bc
Canonical entry tree: cee417e44db96ec8425929fbeb3299d4b74b7cc9
Authoritative benchmark machine state: B0/B1/B3.1.6 executor binding
Validated local Antigravity host: Antigravity CLI 1.1.15
Measurement maturity after unit implementation: MEASUREMENT_NOT_STARTED
Murmurs benefit: NOT ESTABLISHED
A5 execution-effective selection: NOT AUTHORIZED
A6: NOT AUTHORIZED
Paid provider calls: NOT AUTHORIZED BY THIS UNIT
Diagnostic execution: DIAGNOSTIC_READINESS_ONLY (NOT COMPLETED)
Calibration execution: NOT EXECUTED
```

B3.1.6 introduces deterministic explicit Antigravity headless workspace binding in `scripts/antigravity_benchmark_executor.py` via `resolve_workspace` and the verified `--add-dir <path>` native AGY CLI 1.1.15 argument interface, binding relative workspace-scoped file tool invocations to explicit external directory targets rather than defaulting to `~/.gemini/antigravity-cli/scratch`. It enforces fail-closed validation on missing, non-existent, or non-directory workspace paths before live host execution while preserving B3.1.5 stream-json envelope normalization, B3.1.4 sparse settings, and B3.1.3 exact host qualification invariants.

It does not execute Antigravity model turns, does not execute the 3-run diagnostic (Attempt 4 is not authorized), does not execute the 30-run calibration, does not measure live token savings or benefit, does not vendor Caveman, and does not alter production runtime routing.

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
- Antigravity model turns during implementation;
- 3-run diagnostic execution;
- 30-run calibration execution;
- Paid model calls or metered compute spend;
- Caveman installation, vendoring, or runtime dependency;
- Token savings or Murmurs benefit claims;
- Changes to Murmurs production semantics;
- A5 execution-effective selection;
- A6 initiation;
- B4 interaction experiment execution;
- Release publication or deployment.

B4 remains BLOCKED until valid measured B2 and B3 evidence exists.
