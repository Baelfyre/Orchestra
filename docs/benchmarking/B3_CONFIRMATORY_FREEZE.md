# B3 Confirmatory Freeze

Status: `PREPARED_NOT_SELF_AUTHORIZED`

This package freezes 50 held-out synthetic tasks, five per B0 task-class stratum, before confirmatory outcomes. Calibration and pilot task IDs are excluded. Each task is repeated three times under `DEFAULT`, `CAVEMAN`, and `MURMURS` with a fixed deterministic topology, producing exactly 450 randomized one-attempt slots.

The primary endpoint is median paired output-token relative reduction for Murmurs versus Default. Benefit requires at least 10% reduction, a paired-bootstrap 95% lower bound above zero, a two-sided exact sign-test result below 0.05, complete task/quality/safety conformance, and every frozen regression guard. Total-token and input-token median regressions may not exceed 5%; latency median regression may not exceed 10%.

The host remains the pilot stratum: Antigravity CLI 1.1.19, `gemini-3.7-flash-high`, high reasoning, and `stream-json-usage`. Historical 1.1.15 calibration counters remain separate.

- planned runs and maximum model calls: 450
- per-run token ceiling: 45,000
- cumulative token ceiling: 20,250,000
- automatic retry: disabled
- stop on first invalid run, failure, validator error, repository mutation, or resource violation

The canonical freeze sets `live_execution_authorized=false`. Live execution requires a child authorization bound to the signed canonical preparation SHA, tree, freeze, manifest, plan, task-set, and preregistration digests.
