# Codex C2R1 Machine-JSON Reconciliation

## Status

```text
Program: Orchestra Shared Comparative Benchmark
Unit: Codex C2R1 Machine-JSON Prompt Representation
Recorded date: 2026-08-22
State: C2R1_EXECUTION_COMPLETE_RECONCILIATION_CANDIDATE
Primary accepted runs: 29/30
Primary invalid runs preserved: 1
Primary invalid reason: PROVIDER_OUTAGE
Supplemental recovery observations: 1
Supplemental replaces primary: false
Evidence maturity: CALIBRATION_ONLY
Promotion authority: NONE
```

This candidate reconciles the completed C2R1 Codex machine-JSON calibration. It keeps the primary execution record immutable and reports the separately authorized supplemental recovery only as sensitivity evidence.

## Frozen identity

- benchmark subject SHA: `d95f677dbf23ab79c4698c26645ea30cea9b3019`
- benchmark subject tree: `ceab55bd512ea6fde4e8e76877cbb7006d18500e`
- measurement core SHA: `e182e478988c77125127811375aa1b69278cca63`
- measurement core tree: `9e1d9c0dcf5e615c4b16dfd95bb72f63eaacc33e`
- task-set digest: `fd5109b2ec94709883bd75a9b7c6c89b6cd4f9bcc9840554bbd7cbb277a931a8`
- validator: `EXACT_JSON_CONFORMANCE_V1`
- adapter SHA: `0af078f6ad34d5cf406823bbd0e8258496923b60`
- provider/model: `openai-codex` / `gpt-5.6-sol`
- Codex CLI: `0.148.0`
- reasoning: `medium`
- prompt representation: `orchestra.prompt-representation.machine-json.v1`

## Primary execution record

```text
Planned slots: 30
Accepted runs: 29
Invalid runs: 1
Accepted cumulative total tokens: 336,488
Invalid slot: 5
Invalid arm: DEFAULT
Invalid reason: PROVIDER_OUTAGE
Retry performed: false
```

The original slot 5 attempt remains preserved. It was not retried or replaced inside the primary dataset.

### Primary arm totals — descriptive only

| Arm | Accepted runs | Total tokens | Mean total tokens |
|---|---:|---:|---:|
| DEFAULT | 9 | 98,636 | 10959.56 |
| CAVEMAN | 10 | 125,089 | 12508.90 |
| MURMURS | 10 | 112,763 | 11276.30 |

These means are unbalanced because DEFAULT has 9 accepted primary observations while CAVEMAN and MURMURS each have 10. They are not the preferred treatment comparison.

## Primary complete-case matched analysis

The incomplete R5/repetition-2 block is excluded in its entirety, leaving 9 matched blocks per arm.

| Arm | Blocks | Mean total tokens | vs DEFAULT |
|---|---:|---:|---:|
| DEFAULT | 9 | 10959.56 | baseline |
| CAVEMAN | 9 | 12567.56 | +14.67% |
| MURMURS | 9 | 10859.67 | -0.91% |

CAVEMAN is higher than DEFAULT in all 9 complete primary blocks, with a mean paired delta of `+1608.0` tokens.

MURMURS has a mean paired delta of `-99.9` tokens across the 9 complete primary blocks: 2 lower, 6 equal, and 1 higher.

## Supplemental recovery

A separately authorized supplemental replicate reproduced the missing DEFAULT R5/repetition-2 workload:

```text
Supplemental outcome: PASS
Supplemental total tokens: 15,026
Primary slot replaced: false
Counts as primary accepted run: false
Primary record remains: 29 accepted + 1 preserved invalid
```

## Balanced supplemental sensitivity analysis

Using the supplemental value only to complete the missing matched block produces 10 blocks per arm:

| Arm | Blocks | Mean total tokens | Median | vs DEFAULT |
|---|---:|---:|---:|---:|
| DEFAULT | 10 | 11366.2 | 10422.0 | baseline |
| CAVEMAN | 10 | 12508.9 | 12012.5 | +10.05% |
| MURMURS | 10 | 11276.3 | 10422.0 | -0.79% |

Paired sensitivity:

- CAVEMAN mean delta: `+1142.7` tokens; bootstrap 95% interval `[212.1, 1608.0]`; 1 lower, 0 equal, 9 higher than DEFAULT.
- MURMURS mean delta: `-89.9` tokens; bootstrap 95% interval `[-1351.2, 1291.1]`; 2 lower, 7 equal, 1 higher than DEFAULT.

The bootstrap is a deterministic 200,000-resample percentile bootstrap over the 10 paired total-token deltas, seed `20260822`.

## Task-level sensitivity

| Task | CAVEMAN vs DEFAULT | MURMURS vs DEFAULT |
|---|---:|---:|
| R5 capability manifest | -4.78% | -14.99% |
| O1/O2 compatibility | +15.49% | -5.05% |
| O3/O4 freshness | +15.43% | +0.00% |
| Assurance drift | +15.15% | +21.92% |
| O5/O6 routing | +15.48% | +0.00% |

The treatment effect is therefore workload-dependent. CAVEMAN is not uniformly more expensive on every workload, although its aggregate overhead direction persists. MURMURS ranges from savings to neutrality to material overhead.

## C1 natural-language versus C2R1 machine-JSON

Canonical C1 Codex aggregate:

| Arm | C1 natural-language mean | C2R1 balanced sensitivity mean | C2R1 vs C1 |
|---|---:|---:|---:|
| DEFAULT | 10,437.7 | 11366.2 | +8.90% |
| CAVEMAN | 12,377.8 | 12508.9 | +1.06% |
| MURMURS | 10,442.3 | 11276.3 | +7.99% |

Treatment effect relative to DEFAULT:

```text
C1 CAVEMAN: +18.59%
C2R1 CAVEMAN sensitivity: +10.05%
Change: -8.54 percentage points

C1 MURMURS: +0.04%
C2R1 MURMURS sensitivity: -0.79%
Change: -0.83 percentage points
```

No global machine-JSON token-saving benefit is established by these aggregate comparisons. CAVEMAN's overhead direction persists, but its magnitude changes materially. MURMURS remains near-neutral in aggregate and strongly task-dependent.

### Comparison limitation

The canonical C1 reconciliation files inspected here expose aggregate statistics and paired summaries, but not the full per-run Codex token series. Therefore the C1-to-C2R1 representation comparison above is descriptive at the arm-mean level. A formal run-level representation-effect test requires the original per-run C1 evidence series.

## Conclusions

1. C2R1 completed its primary frozen schedule with 29 accepted runs and one preserved `PROVIDER_OUTAGE` invalid observation.
2. The supplemental recovery succeeded but does not rewrite the primary dataset.
3. CAVEMAN overhead direction persists in both the complete-case primary analysis and the balanced supplemental sensitivity analysis.
4. MURMURS does not establish a global token-saving benefit; its effect varies materially by task.
5. Machine-JSON prompt representation does not establish a global token-saving benefit relative to the canonical C1 aggregate.
6. These are calibration findings only. No production promotion, A5 execution promotion, A6, B4, release publication, deployment, or automatic policy change is authorized.

## Provenance

Canonical C1 sources:

- `docs/benchmarking/CODEX_C1_CROSS_PROVIDER_RECONCILIATION.md`
- `machine/benchmarking/codex-c1-cross-provider-reconciliation.v1.json`

C2R1 source:

- exact operator-provided Stage 8B/8C/8D/8E execution outputs and their referenced local evidence records.

This candidate performs no repository mutation.
