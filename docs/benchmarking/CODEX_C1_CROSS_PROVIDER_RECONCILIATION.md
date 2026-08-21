# Codex C1 Cross-Provider Reconciliation

## Status

```text
Program: Orchestra Shared Comparative Benchmark
Unit: Codex C1 Cross-Provider Natural-Language Baseline Reconciliation
Recorded date: 2026-08-22
State: C1_COMPLETE_RECONCILED_CALIBRATION_ONLY
Codex formal accepted runs: 30/30
Codex accepted task/validation/governance pass rate: 100%
Codex invalid attempts preserved: 1
Invalid-attempt reason: PROVIDER_OUTAGE
Murmurs benefit: NOT ESTABLISHED
Promotion authority: NONE
```

This report records the completed Codex C1 natural-language baseline and reconciles it with the previously frozen Antigravity B3 calibration. It is a research-results record, not a production-promotion decision.

## Frozen comparison identity

The cross-provider comparison preserves the same Orchestra benchmark subject and task set:

- benchmark subject SHA: `d95f677dbf23ab79c4698c26645ea30cea9b3019`;
- benchmark subject tree: `ceab55bd512ea6fde4e8e76877cbb7006d18500e`;
- common measurement-core SHA: `e182e478988c77125127811375aa1b69278cca63`;
- common measurement-core tree: `9e1d9c0dcf5e615c4b16dfd95bb72f63eaacc33e`;
- task-set aggregate digest: `fd5109b2ec94709883bd75a9b7c6c89b6cd4f9bcc9840554bbd7cbb277a931a8`;
- validator: `EXACT_JSON_CONFORMANCE_V1`;
- tasks: 5;
- communication arms: `DEFAULT`, `CAVEMAN`, `MURMURS`;
- repetitions per arm: 2;
- accepted runs per provider calibration: 30.

## Provider surfaces

### Antigravity calibration

```text
CLI: Antigravity CLI 1.1.15
Model: gemini-3.7-flash-high
Transport: stream-json-usage
Counter: antigravity-cli-1.1.15:stream-json-usage:gemini-3.7-flash-high
Accepted runs: 30/30
Invalid runs: 0
Accepted cumulative total tokens: 877,582
```

### Codex C1

```text
CLI: Codex CLI 0.148.0
Model: gpt-5.6-sol
Reasoning: medium
Transport: jsonl-usage
Counter: codex-cli-0.148.0:jsonl-usage:gpt-5.6-sol:medium
Accepted runs: 30/30
Accepted cumulative total tokens: 332,578
Invalid live attempts preserved: 1
```

## Primary result

The cross-provider result is not a simple provider-token comparison. The decision-relevant comparison is the within-provider treatment effect relative to each provider's own `DEFAULT` arm.

| Provider | DEFAULT mean total | CAVEMAN mean total | CAVEMAN vs DEFAULT | MURMURS mean total | MURMURS vs DEFAULT |
|---|---:|---:|---:|---:|---:|
| Antigravity | 29,049.1 | 29,864.6 | +2.81% | 28,844.5 | -0.70% |
| Codex | 10,437.7 | 12,377.8 | +18.59% | 10,442.3 | +0.04% |

The evidence supports two different observations:

1. **CAVEMAN overhead direction replicates.** CAVEMAN consumes more total tokens than `DEFAULT` on both provider/model stacks.
2. **MURMURS token-saving direction does not replicate.** Antigravity shows a small total-token reduction while Codex is effectively neutral.

Therefore the current evidence does not establish a provider-general MURMURS token-efficiency benefit.

## Input, output, and reasoning behavior

| Metric | Antigravity CAVEMAN vs DEFAULT | Codex CAVEMAN vs DEFAULT | Antigravity MURMURS vs DEFAULT | Codex MURMURS vs DEFAULT |
|---|---:|---:|---:|---:|
| Mean input tokens | +3.05% | +18.80% | +0.01% | 0.00% |
| Mean output tokens | -2.40% | +1.55% | -15.88% | +3.55% |
| Mean reasoning tokens | -2.46% | +22.22% | -18.40% | +17.28% |

MURMURS input-token behavior does replicate in the sense that it leaves input-token volume effectively unchanged relative to `DEFAULT` on both tested stacks. This is consistent with the benchmark operationalization where MURMURS presentation logic does not prepend a large policy payload to the task prompt.

CAVEMAN's Codex treatment has a substantially larger context-transfer footprint than `DEFAULT` and MURMURS and correspondingly larger mean input-token usage.

Relative reasoning-token percentages on Codex should be interpreted cautiously because the absolute reasoning-token counts are small.

## Codex paired-block analysis

Across the 10 matched task-by-repetition blocks:

### CAVEMAN versus DEFAULT

- mean total-token delta: `+1,940.1` tokens;
- paired-bootstrap 95% interval: `[+1,501.9, +2,747.9]` tokens;
- lower than DEFAULT: `0/10` blocks;
- equal to DEFAULT: `0/10` blocks;
- higher than DEFAULT: `10/10` blocks.

This is a stable direction within the Codex calibration.

### MURMURS versus DEFAULT

- mean total-token delta: `+4.6` tokens;
- paired-bootstrap 95% interval: `[-40.5, +47.5]` tokens;
- lower than DEFAULT: `1/10` blocks;
- equal to DEFAULT: `5/10` blocks;
- higher than DEFAULT: `4/10` blocks.

This is consistent with an effectively neutral total-token effect in the Codex calibration rather than a stable saving.

## Task-class observations for Codex MURMURS

Mean MURMURS total-token delta versus DEFAULT by task class:

| Task class | Mean delta |
|---|---:|
| DEBUGGING | +7.0 |
| DEPENDENCY_HEAVY | +90.5 |
| HIGH_COORDINATION | 0.0 |
| SINGLE_DOMAIN | -74.5 |
| VALIDATION_HEAVY | 0.0 |

The direction is not stable across the five calibration task classes.

## Provider-outage adjudication

The formal C1 sequence stopped after 25 accepted runs when slot 26 produced a structured Codex provider error:

```text
request_id: 1d3cdc802809e37c8f4661c9
slot: 26
classification: INVALID_RUN / PROVIDER_OUTAGE
structured event: error
message: Reconnecting... 2/5 (request timed out)
```

Observed stderr also recorded Codex/ChatGPT transport failures, including a timeout refreshing models and HTTP failures against the ChatGPT MCP backend.

The invalid attempt was preserved rather than silently discarded. After human adjudication, exactly one replacement attempt for the same frozen slot was authorized. The replacement passed with `15,894` accepted total tokens, after which slots 27-30 also passed.

Final C1 checkpoint:

```text
formal_completed_runs: 30
formal_planned_runs: 30
last_status: PASS
cumulative_total_tokens: 332578
recovery_session: true
```

The accepted-measurement total of `332,578` does not include an inferred token value for the failed provider attempt because no accepted provider-token measurement was established for that failed attempt.

A robustness check excluding accepted replacement slot 26 still leaves CAVEMAN materially above the full DEFAULT mean, so the observed CAVEMAN overhead direction is not dependent on that recovered high observation.

## Cross-provider absolute-token caveat

Accepted host-reported total tokens differ substantially:

```text
Antigravity accepted total: 877,582
Codex accepted total:       332,578
Difference:                -545,004
Relative to Antigravity:    -62.10%
```

This is a descriptive difference in provider-native counters. It must not be converted into the claim that Codex is intrinsically `62.10%` more efficient.

The benchmark contract treats provider-native counters as authoritative within their provider surface and requires same-provider counter identity for token-delta comparisons. Different providers/models may use different tokenization, caching, reasoning accounting, and usage-reporting semantics.

The stronger cross-provider replication test is therefore whether the **relative treatment effect against each provider's own DEFAULT arm** reproduces.

## What C1 establishes

C1 establishes the following calibration observations:

1. The Codex adapter and benchmark harness completed the full frozen 30-run task set with 100% accepted task, validation, and governance success.
2. CAVEMAN increases input and total token consumption relative to DEFAULT on both tested provider/model stacks.
3. MURMURS leaves input tokens effectively unchanged relative to DEFAULT on both tested stacks.
4. MURMURS total-token savings observed on Antigravity do not reproduce on Codex; Codex is effectively neutral.
5. A genuine Codex provider-outage event occurred during C1 and was preserved and adjudicated without silently deleting evidence.

## What C1 does not establish

C1 does not establish:

1. a provider-general MURMURS efficiency benefit;
2. a production or runtime-promotion justification;
3. a direct cross-provider efficiency ranking from absolute token totals;
4. a reliable latency benefit;
5. a causal explanation for why MURMURS behaves differently across the two provider/model stacks;
6. exact task-by-task cross-provider bootstrap statistics, because the Antigravity raw 30-run calibration files remain external to the repository and the canonical repository retains aggregate results plus cryptographic digests.

## Follow-up investigation

The non-replication result creates a new research question rather than a defect conclusion:

> Why does MURMURS reduce output and total token usage on the Antigravity/Gemini calibration while producing an effectively neutral total-token effect on Codex/GPT under the same frozen task set and communication-arm design?

Potential investigation dimensions must be treated as hypotheses until tested. They include provider-specific instruction handling, response planning behavior, tokenizer/accounting differences, hidden system/context overhead, reasoning behavior, and the point in each host stack where presentation constraints take effect.

No causal explanation is accepted by this C1 record.

## Next planned experiment

After this C1 result is frozen and documented, the next separately governed extension is C2: a machine-readable canonical JSON prompt-representation comparison using the same frozen task semantics, validator, communication modes, and controlled read-only execution.

C2 is intended to test whether deterministic machine-readable task representation changes efficiency, consistency, or treatment behavior relative to the natural-language C1 baseline. C2 results must remain distinct from C1 and must not retroactively alter the frozen natural-language evidence.

## Evidence provenance

The local reconciliation package generated from the accepted Codex evidence is anchored by:

```text
orchestra_c1_reconciliation_bundle.zip
SHA-256: b2d6fe46410f437be662645176b46c5ce71d2d2438568676aad154211f6ffe91
```

The uploaded Codex C1 evidence package was independently reconciled against the frozen plan and canonical benchmark identities before this report was prepared.

Canonical repository references:

- `docs/benchmarking/COMPARATIVE_MEASUREMENT_B3.md`;
- `machine/benchmarking/comparative-measurement-contract.v1.json`;
- `machine/benchmarking/b3-calibration-task-set.v1.json`;
- `machine/benchmarking/codex-executor-binding.v1.json`;
- `machine/benchmarking/codex-prebaseline-remediation.v1.json`.

## Research boundary

This remains calibration evidence. The frozen benchmark contract states that calibration validates instrumentation and estimates variance, while production-benefit claims require later pilot/confirmatory evidence. C1 grants no A5 promotion, A6 authority, B4 execution, release publication, deployment, or automatic policy change.
