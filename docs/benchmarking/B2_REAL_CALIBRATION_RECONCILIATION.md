# B2 Real Calibration Evidence Reconciliation

## Status

```text
Program: Orchestra Shared Comparative Benchmark
Phase: B2 A5 Isolated Comparative Experiment
Unit: B2 Real Calibration Evidence Reconciliation
Recorded date: 2026-08-23
State: B2_REAL_CALIBRATION_COMPLETE_VALID_RECONCILIATION_CANDIDATE
Evidence maturity: CALIBRATION_ONLY
Benefit claim: NOT ESTABLISHED
A5 execution-effective promotion: NOT AUTHORIZED
B4: BLOCKED
```

This reconciliation records the completed B2 real topology calibration without converting calibration evidence into production authority or a confirmatory benefit claim.

The live execution completed the exact frozen 20-slot schedule under the separately authorized B2.2 envelope:

```text
planned runs:                    20
recorded runs:                   20
PASS:                            20
INVALID_RUN:                      0
observed Codex model calls:      60 / 60
automatic retry:                OFF
accepted cumulative tokens: 632,037 / 1,200,000
stop reason:                    null
```

## Frozen identity

The run evidence is bound to:

```text
canonical Orchestra SHA:
f8ad563f2a6444345671a7b8548c9d27d04d10e0

canonical tree:
dc7165547f0b9b782666c1e2995d808af6dd8d6b

freeze digest:
be5e2926642d7f52c31e8d8dcdce13962b7a9ac2f708483ad31ab2f4f6adf2f8

manifest digest:
b4d9c279da5681d5c3c3f76dbb04592d575121bc66772861926dacdeeedea8d7

plan digest:
2378893ae121d398628a2fe15ffd50a281a4e769219cd42d012318520531578a

eligibility envelope:
26af9b40870a13a138f52b23e45189a052875a81c8d4004366f2b93e9361bb55

task set:
f7af904895107a7f00abb6ab125d7a33a7bcb5c729b0665acfe9049bf2050ee8

provider: openai-codex
Codex CLI: 0.148.0
model: gpt-5.6-sol
reasoning: medium
validator: EXACT_JSON_CONFORMANCE_V1
communication: DEFAULT
```

## Evidence archive

The operator-provided raw evidence archive is retained outside the repository and anchored here by digest:

```text
ORCHESTRA_B2_REAL_CALIBRATION_20260823T041337-0600.zip
SHA-256:
9de700264d005cdb7afe1f0daca1dbed44d050bab3d0715d6f7f359848eddc7c

files: 67
session-level records: 7
requests: 20
executor results: 20
run records: 20
partial-evidence records: 0
```

The repository does not embed the raw run archive. The reconciliation record is a derived audit summary whose provenance is the exact external archive digest above.

## Integrity audit

Independent reconciliation checks passed:

- the frozen plan contains 20 request IDs and each maps to exactly one request, executor result, and run record;
- all 20 run digests recompute to the values in `run-index.json`;
- `experiment.json` carries those same 20 run-evidence digests in execution order;
- all 20 final responses satisfy `EXACT_JSON_CONFORMANCE_V1`;
- every recorded safety field is `false`;
- every run contains exactly three calls: two specialists in the configured arm order followed by the fixed finalizer;
- no partial executor-error evidence is present;
- every task produced one identical final response across its four executions.

## Arm-level descriptive results

Both topologies reached the exact validator ceiling:

| Metric | Clockwork -> Overseer | Overseer -> Clockwork |
|---|---:|---:|
| Runs | 10 | 10 |
| Exact passes | 10/10 | 10/10 |
| Total tokens | 313,073 | 318,964 |
| Mean total tokens/run | 31,307.3 | 31,896.4 |
| Median total tokens/run | 30,858.5 | 30,999.5 |
| Total wall time | 337.566 s | 344.902 s |
| Median wall time/run | 33.702 s | 33.616 s |
| Output tokens | 3,267 | 3,609 |
| Context-transfer bytes | 11,254 | 16,840 |

The aggregate token difference is `+1.8817%` for Overseer -> Clockwork. The aggregate wall-clock difference is `+2.1732%`. These are descriptive calibration statistics only.

## Paired analysis

Across the 10 matched task/repetition blocks, using `Overseer -> Clockwork minus Clockwork -> Overseer`:

```text
total tokens
mean delta:    +589.1
median delta:  +135.5
higher/equal/lower: 8 / 0 / 2

wall clock
mean delta:    +733.6 ms
median delta: +1,993.0 ms
higher/equal/lower: 6 / 0 / 4

context transfer
mean delta:    +558.6 bytes
median delta:  +543.5 bytes
higher/equal/lower: 10 / 0 / 0
aggregate delta: +49.6357%
```

The most consistent directional signal is context propagation: Overseer-first transferred more advisory context in all ten matched blocks. This is a calibration signal, not a benefit claim.

## Quality result

Both arms passed every task:

```text
Clockwork -> Overseer: 10/10
Overseer -> Clockwork: 10/10
```

For each task, the final answer was byte-identical across all four executions. B2 therefore observes no topology quality difference under the frozen exact-JSON validator.

```text
CALIBRATION PASS RATE TIE != TOPOLOGY BENEFIT
DESCRIPTIVE EFFICIENCY DIFFERENCE != CONFIRMATORY BENEFIT
SHADOW TOP-1 != PROMOTION AUTHORITY
```

## Token-counter stability anomaly

One repeated first-specialist prompt had the exact same prompt digest:

```text
787328ab443402a884bb71a383adfbeae79c38e3d30fb3b9860d24503d7ecec4
```

Identity:

```text
task: b2-cal-cache-freshness
arm: Overseer -> Clockwork
specialist: Overseer
call position: 1
```

Observed host counters differed:

| Repetition | Input tokens | Cached input tokens |
|---|---:|---:|
| 1 | 10,108 | 0 |
| 2 | 14,761 | 5,888 |

The input-token delta is `4,653` despite identical prompt digest.

This does not invalidate either run under the frozen B2.2 contract. It does prevent the raw `+1.8817%` aggregate token difference from being cleanly attributed to topology without further counter-stability review.

## Evidence-design limitation

The executor preserved specialist response digests, usage, timing, prompt digests, role, and specialist identity, but not the actual specialist advisory text.

Therefore the archive proves that the calls occurred and preserves their response identities, but an independent auditor cannot reconstruct the actual handoff text or recompute `context_transfer_bytes` directly from raw advisory content.

Before pilot or confirmatory use, the evidence surface should preserve bounded synthetic specialist advisory text or equivalent recomputable byte evidence.

## A5 shadow observation

All 20 runs carried the same shadow result:

```text
1. b2.seq.clockwork-overseer.v1
2. b2.seq.overseer-clockwork.v1

top candidate: b2.seq.clockwork-overseer.v1
disposition: DETERMINISTIC_FALLBACK
topology_effective: false
shadow_influenced_execution: false
```

The empirical quality result is a tie, and the efficiency evidence is descriptive with a counter-stability anomaly. The shadow ranking therefore does not establish predictive benefit.

## Reconciliation conclusion

```text
B2_REAL_CALIBRATION = COMPLETE_VALID

QUALITY_RESULT =
NO_OBSERVED_TOPOLOGY_DIFFERENCE

EFFICIENCY_RESULT =
DESCRIPTIVE_ONLY_NOT_BENEFIT_ESTABLISHED

CONTEXT_TRANSFER_RESULT =
CONSISTENT_DIRECTIONAL_SIGNAL
OVERSEER_CLOCKWORK_HIGHER_10_OF_10

TOKEN_MEASUREMENT_STABILITY =
REQUIRES_REVIEW_BEFORE_CONFIRMATORY_USE

A5_EXECUTION_PROMOTION =
NOT_AUTHORIZED

B4 =
BLOCKED
```

The appropriate next step is to validate and canonicalize this reconciliation record. Any later pilot or confirmatory design is a separate bounded unit and must address counter stability and recomputable specialist-handoff evidence first.

## Authority boundary

This reconciliation grants no:

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
