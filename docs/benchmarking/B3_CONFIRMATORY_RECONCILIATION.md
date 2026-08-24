# B3 Confirmatory Reconciliation

## Status

```text
B3 confirmatory session: VALID COMPLETE
Accepted runs: 450 / 450
Live model calls: 450 / 450
Automatic retries: 0
Paired blocks: 150
Murmurs benefit: CONFIRMATORY_BENEFIT_NOT_ESTABLISHED
```

The frozen confirmatory session completed against canonical preparation `e568ee4d9f72d005e73e828fd5d8aa6fc6cc3020` / tree `3b3bf7fc342eda0a0afb8754737f80524953ff4d`. Independent reconciliation verified every run-index digest and every retained raw-evidence digest. All runs passed their exact validator, all safety flags were false, and the repository remained unchanged.

## Preregistered analysis

The primary endpoint was paired output-token relative reduction for Murmurs versus Default across 150 matched task/repetition blocks.

| Gate | Result | Pass |
| --- | ---: | :---: |
| Median reduction >= 10% | -1.03% | No |
| Bootstrap 95% lower bound > 0 | [-4.68%, 2.07%] | No |
| Two-sided exact sign test p < 0.05 | 0.8699229710286416 | No |
| All quality and safety checks | 450/450 | Yes |
| Median total-token reduction >= -5% | -0.01% | Yes |
| Median input-token reduction >= -5% | -0.01% | Yes |
| Median latency reduction >= -10% | 0.06% | Yes |

Murmurs was lower in 73 blocks, higher in 76, and tied in one. Because all benefit gates were conjunctive, the terminal B3 conclusion is `CONFIRMATORY_BENEFIT_NOT_ESTABLISHED`.

## Evidence

The operator-retained session is at `D:\Dev\Orchestra-Benchmark-Evidence\b3-confirmatory-20260824T041357Z`. `B3_CONFIRMATORY_SESSION.zip` has SHA-256 `ed0d8fb053de46b966d24e0bd9f47f05a71216ea541aa0801fa958d679a4ff31`; `confirmatory-analysis.json` has SHA-256 `1516701a8cf2c1cfa67743b4dfc6501f61be114e415cd93e200f669683831828`.

This result grants no Murmurs semantic-authority expansion, production attachment, A5 promotion, release, deployment, or policy activation.
