# Comparative Measurement B3 - Murmurs Isolated Comparative Experiment

## Status

```text
Program: Orchestra Shared Comparative Benchmark
Phase: B3 Murmurs Isolated Comparative Experiment
Current bounded unit: B3.1.2 Communication Arm Operationalization
State: B3_1_2_COMMUNICATION_ARM_OPERATIONALIZATION_IMPLEMENTED
Canonical entry: dfeb94ee8dccd1e812b7e2c2a5ae8ae1c40b5874
Canonical entry tree: ba672942a93dcf945a51dac104d990b672ee897b
Authoritative benchmark machine state: B0/B1/B3.1.2 executor binding
Measurement maturity after unit implementation: MEASUREMENT_NOT_STARTED
Murmurs benefit: NOT ESTABLISHED
A5 execution-effective selection: NOT AUTHORIZED
A6: NOT AUTHORIZED
Paid provider calls: NOT AUTHORIZED BY THIS UNIT
Diagnostic execution: DIAGNOSTIC_READINESS_ONLY (NOT EXECUTED)
Calibration execution: NOT EXECUTED
```

B3.1.2 implements the communication arm operationalization needed for the Orchestra comparative benchmark harness, making `DEFAULT`, `CAVEMAN`, and `MURMURS` genuinely distinct and machine-verifiable before diagnostic or calibration execution.

It does not execute Antigravity model turns, does not execute the 3-run diagnostic, does not execute the 30-run calibration, does not measure live token savings or benefit, does not vendor Caveman, and does not alter production runtime routing.

## Evidence boundary

```text
ARM OPERATIONALIZATION IMPLEMENTATION != MEASURED CALIBRATION
PLAN-ONLY VALIDATION != MEASURED CALIBRATION
SYNTHETIC FIXTURE != MURMURS BENEFIT EVIDENCE
CAVEMAN PUBLISHED RESULTS != ORCHESTRA RESULTS
MEASUREMENT_NOT_STARTED remains current after B3.1.2
```

The authoritative benchmark machine state incorporates the B3.1.2 executor binding record (`machine/benchmarking/antigravity-executor-binding.v1.json`) alongside the B0 contract and B1 harness. Measurement maturity remains `MEASUREMENT_NOT_STARTED` until genuine calibrated evidence is collected.

## B3.1.2 Communication Treatments

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
Canonical json counter:        antigravity-cli-1.1.14:json-usage:gemini-3.7-flash-high
Canonical stream-json counter: antigravity-cli-1.1.14:stream-json-usage:gemini-3.7-flash-high
```

Paired comparability invariants:
- All arms within a paired block must use the exact same transport and counter identity.
- Cross-run validation fails closed if `counter_id` drifts across arms.
- Native usage counters (`input_tokens`, `output_tokens`, `cache_read_tokens`, `thinking_tokens`) map deterministically into Orchestra token schema regardless of transport format.
- `total_tokens` remains in `raw_evidence` only.
- Cost remains `UNAVAILABLE`.

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
