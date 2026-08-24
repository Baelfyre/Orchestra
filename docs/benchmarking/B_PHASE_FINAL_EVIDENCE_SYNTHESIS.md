# B Phase Final Evidence Synthesis

## Terminal conclusions

| Evidence question | Conclusion |
| --- | --- |
| A5 topology benefit | `CONFIRMATORY_BENEFIT_NOT_ESTABLISHED` |
| Murmurs benefit | `CONFIRMATORY_BENEFIT_NOT_ESTABLISHED` |
| A5 x Murmurs interaction | `NOT_RUN_NOT_ELIGIBLE` |

B2 and B3 each produced valid, internally consistent confirmatory evidence, but neither established its preregistered benefit claim. The canonical B2 reconciliation explicitly marks the B4 isolated-benefit prerequisite as unsatisfied. B4 therefore consumed zero calls and was not run; a combined experiment cannot convert insufficient isolated evidence into a benefit claim.

## Resource history

The B phase consumed 911 model calls: 246 in B2, including the preserved 42-call stopped B2.5 session, and 665 in B3, including two invalid diagnostic calls. B4 consumed zero. Zero-call preflights and failures before model invocation are not counted.

## Promotion decision

Measurement evidence is not promotion authority. No A5 execution-effective promotion, Murmurs semantic-authority expansion, production runtime attachment, release, deployment, policy activation, installed-integration refresh, or destructive cleanup is authorized or performed. The B phase terminates with A5 `DEFERRED_NOT_PROMOTED` and Murmurs carrying no benefit claim.

Reproduction identities and exact numerical results are in `machine/benchmarking/b2-5-confirmatory-reconciliation.v1.json`, `machine/benchmarking/b3-confirmatory-reconciliation.v1.json`, `machine/benchmarking/b4-controlled-interaction-disposition.v1.json`, and `machine/benchmarking/b5-final-evidence-synthesis.v1.json`.
