# B2.2 Real Calibration Freeze and Zero-Call Preflight

## Status

```text
Program: Orchestra Shared Comparative Benchmark
Phase: B2 A5 Isolated Comparative Experiment
Unit: B2.2 Real Calibration Freeze and Zero-Call Preflight
State: PREPARED_ZERO_LIVE_CALLS_REQUIRES_CANONICALIZATION_AND_HOST_PREFLIGHT
Source baseline: 3ecbe83d2c4e8ea237c529963ea0184a898ca06c
Source baseline tree: cc58620351ec14de609687547612a2a8e054af5b
Live B2 model calls in this unit: 0
A5 execution-effective promotion: NOT AUTHORIZED
A6/A7/A8: NOT AUTHORIZED
B4: BLOCKED
```

B2.2 freezes the executable calibration identity after canonical B2.1 established that the benchmark can enact real sequential topology differences. This unit still performs **zero model calls**. It binds the exact topology envelope, task identities, Codex host identity, workspace, resource ceilings, run count, retry policy, and stop conditions that a later explicitly authorized live B2 calibration must use.

```text
FREEZE != LIVE AUTHORIZATION
ZERO-CALL HOST PREFLIGHT != MODEL EXECUTION
BENCHMARK TOPOLOGY EXECUTION != A5 PRODUCTION PROMOTION
```

## Experimental variable

The only experimental variable is specialist coordination order.

### Arm A — deterministic benchmark baseline

```text
Clockwork -> Overseer -> fixed finalizer
candidate_id: b2.seq.clockwork-overseer.v1
candidate_digest: c28e14b11c586cd21397892239ce881f46e230993353013918212dbef7291183
```

### Arm B — reversed eligible sequence

```text
Overseer -> Clockwork -> fixed finalizer
candidate_id: b2.seq.overseer-clockwork.v1
candidate_digest: 067a8867aaa3a7bc82b4915da40ec60222413e261460863b1e8de90b836773f3
```

Both candidates preserve exactly the same required specialist set, use sequential stages only, use `DEFAULT` communication, and finish through the identical fixed finalizer outside the topology variable. The shared benchmark harness selects every arm; the A5 shadow ranker does not control execution.

The canonical benchmark eligibility envelope is:

```text
machine/benchmarking/b2-real-calibration-eligibility-envelope.v1.json
SHA-256 canonical envelope digest:
26af9b40870a13a138f52b23e45189a052875a81c8d4004366f2b93e9361bb55
```

## Workload freeze

B2 reuses the exact Padayon-grounded five-task task set already frozen for B3/C1/C2R1:

```text
machine/benchmarking/b3-calibration-task-set.v1.json
aggregate task-set digest:
fd5109b2ec94709883bd75a9b7c6c89b6cd4f9bcc9840554bbd7cbb277a931a8
validator:
EXACT_JSON_CONFORMANCE_V1
```

The five tasks remain:

1. `b3-cal-padayon-r5-capability-manifest` — `SINGLE_DOMAIN`
2. `b3-cal-padayon-o1-o2-compatibility` — `DEPENDENCY_HEAVY`
3. `b3-cal-padayon-o3-o4-freshness` — `VALIDATION_HEAVY`
4. `b3-cal-padayon-assurance-drift` — `DEBUGGING`
5. `b3-cal-padayon-o5-o6-routing` — `HIGH_COORDINATION`

Their starting-state, prompt, payload, and validation-contract digests are frozen in `machine/benchmarking/b2-real-calibration-freeze.v1.json`. B2 does not rewrite the task semantics. This preserves comparability with the completed communication experiments while introducing only the coordination-order treatment.

## Calibration schedule

```text
5 tasks
x 2 repetitions
x 2 topology arms
= 20 benchmark runs

3 bounded Codex calls per run
= maximum 60 underlying model calls
```

The randomization seed is `20260822`. Arm order is randomized reproducibly within each task/repetition block by the existing B1 harness. Automatic retry is off and each slot has one attempt only.

## Exact Codex binding

The frozen host surface reuses the independently qualified C1/C2R1 Codex identity:

```text
provider: openai-codex
CLI: 0.148.0
model: gpt-5.6-sol
reasoning: medium
transport: jsonl-usage
counter: codex-cli-0.148.0:jsonl-usage:gpt-5.6-sol:medium
binding: NODE_EXACT_NPM_ENTRYPOINT
```

Frozen executable identities:

```text
Node:
C:\Program Files\nodejs\node.exe
sha256 e921fe5307e29bf6fd00000dd594356affd3a7b044e52720c7f10decbdc305b9

Codex JS:
C:\Users\ACER\.codex-cli-0.148.0\node_modules\@openai\codex\bin\codex.js
sha256 134063e133f0b4244fa3b251acf973d4fe4b4aeeacbdc135211bf480f59f1477

Codex package.json:
C:\Users\ACER\.codex-cli-0.148.0\node_modules\@openai\codex\package.json
sha256 071f84ec4e6ff199b3dce2c2560a77c2248443b0d8b17e64f6e3f08427d32fc2
```

The frozen workspace is the already isolated empty Git workspace used by C2R1:

```text
D:\Dev\Repositories\+Orchestra-C2-Workspace
```

It must remain Git-backed, empty outside Git metadata, free of `AGENTS.md`, read-only for model execution, and unable to mutate the Orchestra repository.

## Resource freeze

The live calibration, if separately authorized later, is bounded by:

```text
per-run total-token ceiling:          75,000
cumulative accepted-token ceiling: 1,200,000
maximum benchmark runs:                  20
maximum underlying model calls:          60
model calls per run:                       3
per-call timeout:                         600 seconds
automatic retry:                          OFF
stop on first invalid run:                ON
```

Resource-budget digest:

```text
32ea2bda042dd05467fbbd02f95b2504a32c5a2c4c0080c5b7b53ec225f50c78
```

The 75,000 ceiling is a run-level aggregate over the two specialist calls plus fixed finalizer. The cumulative ceiling remains the previously governed 1.2M-token experimental ceiling and can stop the experiment before all 20 runs if reached.

## Zero-call preflight

The repository preflight is:

```text
python scripts/b2_real_calibration_preflight.py
```

This validates the static freeze, canonical envelope, candidate digests, five task identities, schedule/resource arithmetic, and no-live-authority boundary.

After B2.2 becomes canonical, the exact local host preflight is:

```text
python scripts/b2_real_calibration_preflight.py --verify-host --output <evidence-path>
```

`--verify-host` may execute only the pinned Codex `--version` command. It verifies the Node/Codex/package hashes and the isolated Git workspace. It never invokes `codex exec`; successful status is `PASS_ZERO_LIVE_CALLS` with `live_model_calls=0`.

## Fail-closed stop policy

Live B2 execution must stop without automatic retry on the first:

- freeze or eligibility-envelope drift;
- task-set or task-identity drift;
- CLI/executable/model/reasoning/counter drift;
- non-empty, non-Git, or `AGENTS.md`-contaminated workspace;
- disallowed tool event;
- repository mutation event;
- invalid run or validator failure;
- 75,000 per-run token-ceiling breach;
- 1,200,000 cumulative accepted-token ceiling breach;
- 60-call maximum breach;
- unadjudicated identity or authority drift.

Invalid evidence is preserved and is not silently retried or converted into task failure.

## Exit condition

B2.2 is complete when:

1. the freeze record and eligibility envelope are canonical and validated;
2. repository static preflight passes with zero model calls;
3. all normal exact-head repository gates pass;
4. after canonicalization, the exact local host preflight reports `PASS_ZERO_LIVE_CALLS`;
5. live execution remains disabled until a separate explicit human authorization.

Only then may a separately authorized B2 calibration execute the 20 frozen slots. B2.2 itself establishes no A5 benefit and grants no production authority.
