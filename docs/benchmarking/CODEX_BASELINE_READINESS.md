# Codex Baseline Readiness

## Status

`READINESS_ONLY_NO_LIVE_CALLS`

This unit prepares the Codex CLI host adapter required for the controlled Antigravity-versus-Codex measurement baseline. It performs zero Codex model/provider calls and does not authorize the 30-run Codex baseline.

The live benchmark remains separately gated on an exact Codex CLI version, exact model, exact reasoning effort, authentication/counter identity, workspace binding, resource ceilings, and stop conditions.

## Identity model

The historical B3 plan used `control_identity.orchestra_revision` for the frozen comparison subject. That field must remain unchanged for the cross-host comparison, but it is not sufficient to identify the executable measurement harness.

| Identity | Exact value | Role |
| --- | --- | --- |
| Frozen benchmark subject | `d95f677dbf23ab79c4698c26645ea30cea9b3019` | Cross-host `control_identity.orchestra_revision` and benchmark subject |
| Frozen benchmark subject tree | `ceab55bd512ea6fde4e8e76877cbb7006d18500e` | Subject tree |
| Common measurement-core baseline | `e182e478988c77125127811375aa1b69278cca63` | First canonical revision containing the accepted Padayon-grounded task set, deterministic validator, and executor integration |
| Common measurement-core tree | `9e1d9c0dcf5e615c4b16dfd95bb72f63eaacc33e` | Measurement-core tree |
| Codex host adapter | `TO_BE_FROZEN_AFTER_CODEX_READINESS_CANONICALIZATION` | Host-specific execution provenance, separate from the frozen subject |

The frozen task-set digest remains:

```text
fd5109b2ec94709883bd75a9b7c6c89b6cd4f9bcc9840554bbd7cbb277a931a8
```

No frozen task, expected response, prompt digest, validation contract, communication arm, or accepted Antigravity evidence is modified by this readiness unit.

## Common measurement core parity

The following measurement-core files are byte-identical between the accepted `e182e478...` baseline and the pre-readiness canonical Orchestra main:

| File | Git blob SHA |
| --- | --- |
| `scripts/benchmarking/calibration_task_validator.py` | `0011e6034f482a8f32ab0ba5623fa36f63026af6` |
| `scripts/comparative_benchmark_runner.py` | `6de55d48fd2e37f8106ff64eecb522cde30b7a58` |
| `machine/benchmarking/b3-calibration-task-set.v1.json` | `b0f4fd6c2ad14d5a38db61851303e58d80577ccf` |
| `scripts/antigravity_benchmark_executor.py` | `4186683bee6732ee6af7d4c7a0aa331f9802a24d` |

The Codex adapter reuses the Antigravity executor's communication-treatment binding and `evaluate_task_outcome` function so DEFAULT, CAVEMAN, MURMURS, and `EXACT_JSON_CONFORMANCE_V1` semantics do not fork by host.

## Codex host surface

The adapter uses Codex CLI non-interactive execution with:

- `codex exec`;
- JSONL event output;
- ephemeral session state;
- read-only sandbox;
- user config ignored;
- project/user execpolicy `.rules` ignored;
- explicit model and reasoning effort;
- multi-agent tools disabled;
- web search disabled;
- shell tool disabled;
- approval policy set to `never`;
- no host-enforced `--output-schema`.

The final point is deliberate. The benchmark answer is evaluated by Orchestra's existing response-derived validator, not by a Codex-only structured-output enforcement mechanism.

Official Codex references used for this binding:

- `https://developers.openai.com/codex/cli/reference`
- `https://developers.openai.com/codex/non-interactive-mode`
- `https://developers.openai.com/codex/config-reference`

## JSONL measurement mapping

A valid run must contain:

1. at least one `thread.started` event;
2. no `turn.failed` or `error` event;
3. exactly one `turn.completed` event;
4. one completed non-empty `agent_message` used as the final response;
5. non-negative integer host counters for input, cached input, output, and reasoning output tokens;
6. no command, file-change, MCP, or web-search event under the no-tool calibration envelope.

Host counters map to the shared executor-result schema as:

```text
input_tokens        <- turn.completed.usage.input_tokens
cached_input_tokens <- turn.completed.usage.cached_input_tokens
output_tokens       <- turn.completed.usage.output_tokens
reasoning_tokens    <- turn.completed.usage.reasoning_output_tokens
fresh_billable_tokens = null
cost = UNAVAILABLE
```

Counter identity is assigned by Orchestra from the exact frozen host surface:

```text
codex-cli-{cli-version}:jsonl-usage:{model}:{reasoning-effort}
```

## Outcome boundary

Host execution success does not imply benchmark task PASS.

- valid host evidence + exact expected response -> `PASS`;
- valid host evidence + semantically wrong response -> `FAIL`;
- malformed/missing host evidence or control drift -> `INVALID_RUN`.

Model-authored `task_completed`, `validation_passed`, or `governance_valid` fields cannot bypass the deterministic validator.

## Live-run gate

Before any live Codex baseline call, freeze and record:

- exact installed Codex CLI version;
- exact Codex model;
- exact reasoning effort;
- exact counter identity;
- authentication surface;
- exact workspace binding;
- exact 30-run manifest generated from the frozen task set;
- per-call token ceiling;
- cumulative token ceiling;
- invalid-run and consecutive-invalid stop conditions.

No model, version, or reasoning setting is guessed by this readiness unit.

## Governance boundary

```text
CODEX_BASELINE_READINESS = IMPLEMENTATION_AND_VALIDATION_ONLY
LIVE_CODEX_CALLS = 0
LIVE_CODEX_BASELINE = NOT_AUTHORIZED_UNTIL_HOST_AND_RESOURCE_FREEZE
FROZEN_AGY_EVIDENCE = UNCHANGED
MURMURS_BENEFIT = NOT_ESTABLISHED
A5_EXECUTION_PROMOTION = NOT_AUTHORIZED
A6 = NOT_AUTHORIZED
B4 = BLOCKED
RELEASE_PUBLICATION = NOT_AUTHORIZED
DEPLOYMENT = NOT_AUTHORIZED
```
