# B3 Pilot Reconciliation

Status: `VALID_COMPLETE_PILOT_SIGNAL_ONLY`

The separately authorized B3 pilot completed all 180 frozen slots with 180 model calls, 3,533,572 accepted tokens, no retry, no invalid run, and no safety or repository-boundary violation. Independent reconciliation verified all 180 run digests, all raw-evidence digests, and all 60 three-arm paired blocks.

The pilot does not establish Murmurs benefit. Against `DEFAULT`, Murmurs had a median paired output-token reduction of 4.25% with a deterministic bootstrap 95% interval from -4.90% to 8.14%. Median total-token reduction was approximately 0.01%, and median latency reduction was -1.50%.

For the preregistered 10% output-token practical effect, the observed paired relative standard deviation of 0.246718 requires 48 paired blocks at two-sided alpha 0.05 and power 0.80 under the frozen normal approximation. Canonical B0 retains a 50-task planning floor, so the confirmatory design uses 50 tasks, three repetitions, and three arms: 450 runs and at most 450 model calls.

The external pilot archive SHA-256 is `c144155aa5ba50e415161651b1b1cc6942974ab13d609cf86ac965357e5534f5`. The machine reconciliation is `machine/benchmarking/b3-pilot-reconciliation.v1.json`.
