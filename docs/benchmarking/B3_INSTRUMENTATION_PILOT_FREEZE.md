# B3 Instrumentation Pilot Freeze

Status: `PREPARED_NOT_SELF_AUTHORIZED`

This package freezes the B0 pilot target for the isolated Murmurs experiment: 20 held-out synthetic tasks, three repetitions, and the `DEFAULT`, `CAVEMAN`, and `MURMURS` communication arms under one fixed deterministic topology. The resulting plan contains exactly 180 one-call slots. It produces pilot signals only and cannot establish Murmurs benefit.

## Task and plan boundary

The task set contains two scenarios for each of the ten B0 task-class strata. It excludes every B3 calibration task ID and freezes each prompt, starting state, exact response validator, ordering seed, and task payload before live outcomes. The canonical manifest and deterministic plan are:

- `machine/benchmarking/b3-pilot-task-set.v1.json`
- `machine/benchmarking/b3-pilot-manifest.v1.json`
- `machine/benchmarking/b3-pilot-plan.v1.json`
- `machine/benchmarking/b3-pilot-freeze.v1.json`

## Host replacement boundary

The historical calibration remains bound to Antigravity CLI 1.1.15. That executable is no longer installed. The pilot therefore uses a separately frozen replacement stratum: Antigravity CLI 1.1.19, `gemini-3.7-flash-high`, high reasoning, and `stream-json-usage`. Calibration and pilot token counters may not be pooled. Pilot variance alone will determine the later confirmatory design.

The host preflight invokes only `agy --version` and `agy models`. It performs zero model calls and fails closed on executable, version, model, settings, workspace, Caveman policy, source, manifest, plan, or resource drift.

## Resource and stop boundary

- planned runs: 180
- maximum model calls: 180
- attempts per slot: 1
- automatic retry: disabled
- per-run total-token ceiling: 45,000
- cumulative token ceiling: 8,100,000
- stop on first invalid run, failed task, validator failure, repository mutation, or ceiling violation

The canonical freeze has `live_execution_authorized=false`. A child authorization bound to the signed canonical preparation SHA, tree, and frozen digests is required before execution.
