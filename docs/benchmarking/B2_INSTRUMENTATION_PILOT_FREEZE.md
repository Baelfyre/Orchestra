# B2.4 Instrumentation Pilot Freeze

## Status

```text
Phase: B2.4 instrumentation pilot preparation
State: PREPARED_NOT_AUTHORIZED
Tasks: 2
Repetitions per task: 2
Topology arms: 2
Planned runs: 8
Codex calls per run: 3
Maximum underlying model calls: 24
Live model calls consumed during preparation: 0
Live execution authorized: false
```

B2.4 prepares an instrumentation pilot only. It establishes no topology benefit and is not A5 promotion evidence. The prepared driver must not run until a separate exact human live-execution authorization is issued.

## Frozen task selection

The first task is `b2-cal-cache-freshness`, required because calibration exposed the counter-stability anomaly there.

The second task is `b2-cal-cross-layer-release`. The locked rule excludes the mandatory task from the canonical B2 topology calibration task set, selects tasks with `task_class = HIGH_COORDINATION`, and chooses the lexicographically smallest `task_id`. No prior outcome or benefit result participated in selection.

## Deterministic paired plan

The manifest and plan freeze two repetitions of both sequential topology arms for both tasks. The existing seeded paired-block scheduler determines exact order:

1. cache freshness, repetition 1: Overseer -> Clockwork; Clockwork -> Overseer
2. cache freshness, repetition 2: Overseer -> Clockwork; Clockwork -> Overseer
3. cross-layer release, repetition 1: Clockwork -> Overseer; Overseer -> Clockwork
4. cross-layer release, repetition 2: Clockwork -> Overseer; Overseer -> Clockwork

The machine records are:

- `machine/benchmarking/b2-instrumentation-pilot-freeze.v1.json`
- `machine/benchmarking/b2-instrumentation-pilot-manifest.v1.json`
- `machine/benchmarking/b2-instrumentation-pilot-plan.v1.json`

## Host and execution boundaries

The pilot reuses the canonical pinned Codex 0.148.0 Node entrypoint, `gpt-5.6-sol`, medium reasoning, JSONL usage transport, and isolated Git-backed workspace. The workspace remains read-only, approval policy is `never`, and web search, agents, and model shell tools are disabled.

`scripts/b2_instrumentation_pilot_preflight.py` verifies the frozen task, manifest, plan, executable, host, and workspace identities. Host verification may invoke only Codex `--version`; it reports `codex_exec_invoked=false` and `live_model_calls=0`.

## Prepared driver

`scripts/b2_instrumentation_pilot_driver.py` requires a separate exact authorization record before invoking the existing B2.3.1 executor. It permits one attempt per slot, reserves at most three calls per slot, stops after the first invalid run or validator failure, enforces the 24-call and token ceilings, and rejects repository mutation or evidence recomputation drift.

The session retains authorization, plan, requests, raw executor results, normalized run records, run index, experiment record, and terminal summary outside the repository and model workspace.

## Evidence boundary

Every valid run must retain exact specialist advisory text, UTF-8 bytes and raw-byte SHA-256, ordered advisory references, independently recomputed context-transfer bytes, exact `turn.completed.usage` objects, usage digests, and counter identities. Cached input greater than input is invalid. A specialist advisory above 16,384 UTF-8 bytes invalidates the run without truncation.

Cross-run reconciliation supports `STABLE_EXACT`, `CACHE_STATE_VARIANT`, `INPUT_COUNTER_VARIANT`, and `UNSTABLE_ATTRIBUTION`.

## Next gate

The exact authorization must use schema `orchestra.b2-instrumentation-pilot-live-authorization.v1`, set `live_execution_authorized=true`, and bind the canonical preparation SHA and tree plus the exact freeze, manifest, and plan digests, eight planned runs, and maximum 24 underlying model calls.

Until that authorization is issued, B2.4 remains `PREPARED_NOT_AUTHORIZED`; B2.5, A5 execution promotion, A6-A8, B4, release, deployment, and policy activation remain unauthorized or blocked.
