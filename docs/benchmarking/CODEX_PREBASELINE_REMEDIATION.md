# Codex Prebaseline Remediation

## Status

`IMPLEMENTED_ON_BRANCH_VALIDATION_PENDING`

This bounded unit records and remediates the Codex CLI measurement-adapter defect discovered during live transport qualification on 2026-08-21. It does not start or authorize the formal 30-run Codex comparative baseline.

Machine-readable authority for this unit is `machine/benchmarking/codex-prebaseline-remediation.v1.json`.

## Frozen comparison identities

The cross-host benchmark subject and task set remain unchanged:

- benchmark subject SHA: `d95f677dbf23ab79c4698c26645ea30cea9b3019`;
- benchmark subject tree: `ceab55bd512ea6fde4e8e76877cbb7006d18500e`;
- common measurement-core SHA: `e182e478988c77125127811375aa1b69278cca63`;
- task-set digest: `fd5109b2ec94709883bd75a9b7c6c89b6cd4f9bcc9840554bbd7cbb277a931a8`;
- validator: `EXACT_JSON_CONFORMANCE_V1`.

The frozen Codex host surface is:

```text
CLI = 0.148.0
MODEL = gpt-5.6-sol
REASONING = medium
AUTHENTICATION = ChatGPT
COUNTER = codex-cli-0.148.0:jsonl-usage:gpt-5.6-sol:medium
```

## Diagnostic Attempt 1

Attempt 1 was invalid before a valid model measurement was established.

```text
ADAPTER_STATUS = INVALID_RUN
ADAPTER_INVALID_REASON = PROVIDER_OUTAGE
PROCESS_RETURN_CODE = 1
STDERR = Not inside a trusted directory and --skip-git-repo-check was not specified.
ACCEPTED_MEASUREMENT = NO
HOST_TOKEN_EVIDENCE = UNAVAILABLE
```

The observed failure was a local Codex/Git workspace precondition failure. A provider outage was not established. The adapter had accepted any existing directory as a workspace and mapped every non-zero `codex exec` exit to `PROVIDER_OUTAGE`, so the first diagnostic exposed a classification gap rather than a provider incident.

## Diagnostic Attempt 2

The isolated workspace was initialized as an empty Git repository with no `AGENTS.md`, and the exact same frozen request/model/reasoning settings were retried once under the explicit diagnostic gate.

Attempt 2 passed:

```text
STATUS = PASS
INVALID_REASON = null
TOKEN_SOURCE = HOST_REPORTED
INPUT_TOKENS = 10028
CACHED_INPUT_TOKENS = 0
OUTPUT_TOKENS = 95
REASONING_TOKENS = 0
TOTAL_TOKENS = 10123
COUNTER = codex-cli-0.148.0:jsonl-usage:gpt-5.6-sol:medium
SEMANTIC_VALIDATION = PASS
GOVERNANCE_VALID = true
TOOL_LEAKAGE = false
```

This qualifies the Codex JSONL measurement transport. It is diagnostic evidence only and does not count toward the formal 30-run baseline.

## Remediation

The Codex executor is hardened in two places.

### Live workspace preflight

Before a real `codex exec` process is launched, the executor now verifies the configured workspace with:

```text
git -C <workspace> rev-parse --is-inside-work-tree
```

An existing directory that is not inside a Git worktree fails closed as `CORRUPTED_STARTING_STATE` before model invocation. Synthetic `raw_jsonl` readiness tests remain exempt because they do not launch a real Codex process.

### Non-zero process classification

A non-zero `codex exec` exit is no longer automatically attributed to the provider.

- known Git/trusted-directory rejection -> `CORRUPTED_STARTING_STATE`;
- known invocation/configuration rejection -> `MEASUREMENT_CAPTURE_FAILURE`;
- structured Codex `turn.failed` or `error` evidence -> `PROVIDER_OUTAGE`;
- otherwise-unstructured non-zero process exit -> `INFRASTRUCTURE_OUTAGE`.

This keeps provider attribution evidence-based and fail-closed.

## Regression coverage

`tests/runtime/test_codex_benchmark_workspace_preflight_regression.py` covers:

- live non-Git workspace rejection before the Codex process;
- the exact trusted-directory error observed during Diagnostic Attempt 1;
- conservative classification of unstructured process exits;
- configuration-rejection classification;
- preservation of structured provider-error classification.

Existing deterministic Codex executor tests remain authoritative for JSONL validation, exact task validation, no-tool enforcement, host identity drift, counter identity, and result-schema compatibility.

## Antigravity evidence reconciliation

The accepted B3 Antigravity evidence was checked before Codex execution:

```text
RUN_INDEX_RECORDED = 30
RUN_FILES_CHECKED = 30
RUN_DIGEST_MISMATCHES = 0
VALID_RUNS = 30
PASS_RUNS = 30
INVALID_RUNS = 0
CUMULATIVE_TOTAL_TOKENS = 877582
```

The canonical JSON digests for the manifest, experiment, and run index match the frozen B3 records. The local `calibration_summary.json` canonical digest differs from its recorded frozen digest, but the underlying 30 indexed run records independently reproduce the canonical aggregate metrics. This is recorded as derived-summary artifact drift and does not alter the frozen task-set or accepted run evidence used for Codex comparison. No Antigravity rerun is required by this remediation unit.

## Resource and execution boundary

The prospective Codex baseline budget remains:

```text
PER_CALL_TOTAL_TOKEN_CEILING = 45000
CUMULATIVE_TOTAL_TOKEN_CEILING = 1200000
FORMAL_PLANNED_RUNS = 30
FORMAL_COMPLETED_RUNS = 0
AUTOMATIC_RETRY = false
```

The formal run must stop on any invalid run, host/model/reasoning identity drift, disallowed tool event, or token-ceiling breach.

## Governance boundary

This remediation authorizes no merge, release publication, A5 execution promotion, A6 initiation, B4 execution, or formal Codex 30-run baseline by itself. Validation and human review remain required before canonicalization.
