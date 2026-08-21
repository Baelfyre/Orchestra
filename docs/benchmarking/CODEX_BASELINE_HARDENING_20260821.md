# Codex Baseline Hardening — 2026-08-21

## Status

`PREBASELINE_HARDENING_IMPLEMENTED_PENDING_VALIDATION`

This bounded unit hardens the live Codex comparative-benchmark entrypoint after the controlled qualification diagnostic exposed a local workspace precondition that the canonical readiness adapter classified too broadly as `PROVIDER_OUTAGE`.

No formal 30-run Codex baseline is executed by this unit. Accepted Antigravity B3 evidence remains unchanged.

## Frozen comparison identity

- benchmark subject SHA: `d95f677dbf23ab79c4698c26645ea30cea9b3019`
- benchmark subject tree: `ceab55bd512ea6fde4e8e76877cbb7006d18500e`
- task-set digest: `fd5109b2ec94709883bd75a9b7c6c89b6cd4f9bcc9840554bbd7cbb277a931a8`
- validator: `EXACT_JSON_CONFORMANCE_V1`

## Codex host freeze

- Codex CLI: `0.148.0`
- model: `gpt-5.6-sol`
- reasoning effort: `medium`
- authentication surface: ChatGPT
- counter identity: `codex-cli-0.148.0:jsonl-usage:gpt-5.6-sol:medium`

## Qualification diagnostics

### Attempt 1 — invalid local precondition

The first controlled diagnostic reached `codex exec` with the frozen CLI/model/reasoning/workspace identity but returned exit code `1` with:

```text
Not inside a trusted directory and --skip-git-repo-check was not specified.
```

The canonical readiness adapter mapped any non-zero `codex exec` process exit to `PROVIDER_OUTAGE`. That classification was not supported by the observed evidence: the failure was a local Git-workspace precondition and no valid provider/model usage event was captured.

Disposition:

```text
OUTCOME=INVALID_RUN
ACCEPTED_MEASUREMENT=NO
ADAPTER_REASON=PROVIDER_OUTAGE
ACTUAL_OBSERVED_CAUSE=CODEX_GIT_REPOSITORY_PRECONDITION_FAILURE
PROVIDER_OUTAGE_ESTABLISHED=NO
TOKENS=UNAVAILABLE
```

### Attempt 2 — transport qualification passed

The same isolated workspace was initialized as a local Git repository without adding an `AGENTS.md`, Orchestra files, or workload mutations. The exact same request and frozen host settings were rerun once.

Observed result:

```text
OUTCOME=PASS
VALIDATION_PASSED=true
GOVERNANCE_VALID=true
TOKEN_SOURCE=HOST_REPORTED
COUNTER_ID=codex-cli-0.148.0:jsonl-usage:gpt-5.6-sol:medium
INPUT_TOKENS=10028
CACHED_INPUT_TOKENS=0
OUTPUT_TOKENS=95
REASONING_TOKENS=0
TOTAL_TOKENS=10123
PER_CALL_CEILING=45000
```

The diagnostic qualifies the Codex JSONL measurement transport. It is qualification evidence only and is not counted as one of the formal 30 baseline runs.

## Discovered adapter defect

`CODEX_ADAPTER_DEFECT_001`

Current readiness behavior can classify a non-zero local `codex exec` process exit as `PROVIDER_OUTAGE` without structured provider evidence. This could contaminate formal baseline evidence by attributing local CLI or starting-state failures to the provider.

Required behavior before formal execution:

1. require the live workspace to be a Git worktree before invoking Codex;
2. fail closed as `CORRUPTED_STARTING_STATE` when that precondition is absent;
3. classify an unstructured non-zero `codex exec` process exit as `MEASUREMENT_CAPTURE_FAILURE`, not automatically `PROVIDER_OUTAGE`;
4. preserve `PROVIDER_OUTAGE` for structured Codex `turn.failed` or `error` events;
5. perform no automatic retry.

## Implementation boundary

The canonical measurement core remains:

```text
scripts/codex_benchmark_executor.py
```

The formal live-baseline entrypoint is hardened through:

```text
scripts/codex_benchmark_executor_hardened.py
```

The wrapper delegates successful worktree-qualified execution to the canonical core, preserving prompt construction, communication-treatment binding, CLI/model/reasoning checks, JSONL parsing, token mapping, deterministic validation, and frozen subject identity. It adds only the live workspace preflight and the corrected non-zero-process classification boundary.

Regression coverage:

```text
tests/runtime/test_codex_benchmark_executor_hardening.py
```

The tests require that a non-Git workspace fail before canonical executor invocation, that a Git workspace delegates normally, that an unstructured non-zero process exit is not labeled as a provider outage, and that structured provider-error classification remains unchanged.

## Candidate formal resource freeze

```text
PER_CALL_TOKEN_CEILING=45000
CUMULATIVE_TOKEN_CEILING=1200000
PLANNED_RUNS=30
INVALID_RUN_STOP=IMMEDIATE
CONSECUTIVE_INVALID_LIMIT=1
AUTOMATIC_RETRY=NONE
```

These ceilings are not reduced based on the single successful diagnostic because doing so after observing performance would tune the resource envelope post hoc.

## Governance boundary

```text
LIVE_30_RUN_CODEX_BASELINE=NOT_STARTED
ACCEPTED_CODEX_BASELINE_RUNS=0
MERGE=NOT_AUTHORIZED
RELEASE_PUBLICATION=NOT_AUTHORIZED
A5_EXECUTION_PROMOTION=NOT_AUTHORIZED
A6=NOT_AUTHORIZED
B4=BLOCKED
```

Next gate: validate the hardened entrypoint and regression tests, then freeze the Codex-specific 30-run manifest. No baseline execution begins until that validation and a separate live-execution authorization are complete.
