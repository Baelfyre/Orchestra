# B2.4 Instrumentation Pilot Freeze

## Status

```text
Phase: B2.4 instrumentation pilot
State: COMPLETE_VALID_REPLACEMENT_RECONCILIATION
Tasks: 2
Repetitions per task: 2
Topology arms: 2
Planned runs: 8
Codex calls per run: 3
Maximum underlying model calls: 24
Attempted slots: 8
Accepted runs: 8
Reconciled live model calls consumed: 24
Live execution authorized: false
```

B2.4 remains an instrumentation pilot only. The first attempt stopped on an executor command-contract defect before any model invocation; a separately authorized replacement session then completed all eight runs with valid instrumentation. See [B2_INSTRUMENTATION_PILOT_RECONCILIATION.md](B2_INSTRUMENTATION_PILOT_RECONCILIATION.md).

The pilot establishes no topology benefit and is not A5 promotion evidence. Its descriptive counter and context-transfer observations are eligible only for the separately frozen B2.5 design.

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

The next unit is the B2.5 held-out task-set freeze and zero-call preflight. B2.5 must bind a new held-out task set, deterministic plan, exact host and workspace identities, and its own finite resource ceiling before any further model call.
