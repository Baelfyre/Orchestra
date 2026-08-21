# Changelog

## Post-v1.6.0 Comparative Benchmark Codex Prebaseline Workspace and Exit Classification Remediation - Candidate

- Requires a live Codex benchmark workspace to pass `git -C <workspace> rev-parse --is-inside-work-tree` before `codex exec`; a non-Git live workspace fails closed as `CORRUPTED_STARTING_STATE` before the Codex process is invoked, while synthetic `raw_jsonl` tests remain exempt because they launch no live process.
- Reclassifies non-zero Codex process exits from observed evidence instead of treating every failure as a provider outage: structured `turn.failed` / `error` evidence maps to `PROVIDER_OUTAGE`, known trusted-directory or Git-workspace rejection maps to `CORRUPTED_STARTING_STATE`, recognized invocation/configuration rejection maps to `MEASUREMENT_CAPTURE_FAILURE`, and otherwise-unstructured non-zero exits map to `INFRASTRUCTURE_OUTAGE`.
- Adds focused deterministic regression coverage proving live non-Git rejection occurs before process invocation, the Diagnostic Attempt 1 trusted-directory failure is classified as local starting-state corruption, structured provider errors retain `PROVIDER_OUTAGE`, and configuration or unstructured process failures remain separately classified.
- Records the bounded 2026-08-21 Codex prebaseline remediation and diagnostic evidence while preserving the frozen benchmark subject `d95f677dbf23ab79c4698c26645ea30cea9b3019`, task-set digest `fd5109b2ec94709883bd75a9b7c6c89b6cd4f9bcc9840554bbd7cbb277a931a8`, accepted Antigravity evidence, and the prospective 45,000 per-call / 1,200,000 cumulative token ceilings without tuning them from Diagnostic Attempt 2.
- Keeps the formal Codex comparative baseline at 0/30 and authorizes no formal baseline execution, A5 execution promotion, A6, B4, release publication, deployment, or destructive operation.

## Post-v1.6.0 Comparative Benchmark Codex Baseline Readiness - Candidate

- Adds a zero-live-call Codex CLI executor binding in `scripts/codex_benchmark_executor.py` for the controlled cross-host baseline while preserving the exact frozen `d95f677dbf23ab79c4698c26645ea30cea9b3019` benchmark-subject identity and the `e182e478988c77125127811375aa1b69278cca63` common measurement-core baseline as separate provenance fields.
- Reuses canonical `DEFAULT` / `CAVEMAN` / `MURMURS` treatment binding and `EXACT_JSON_CONFORMANCE_V1` response-derived outcome validation from the unchanged Antigravity measurement core rather than introducing host-specific task-success semantics.
- Maps Codex JSONL `turn.completed` host usage counters into the shared executor-result schema and fails closed on CLI/model/reasoning drift, malformed or missing usage, host errors, missing final response, or any tool activity under the synthetic no-tool baseline.
- Adds deterministic zero-live-call regression coverage and machine/human readiness records without modifying the frozen task-set digest `fd5109b2ec94709883bd75a9b7c6c89b6cd4f9bcc9840554bbd7cbb277a931a8`, accepted Antigravity evidence, or existing B3 measurements.
- Keeps exact Codex CLI version, model, reasoning effort, authentication/counter identity, workspace, resource ceilings, and stop conditions unfrozen pending a separate human live-execution gate.
- Authorizes no live Codex/provider calls, A5 execution promotion, A6, B4, release publication, deployment, installed-integration refresh, or destructive operation.

## Post-v1.6.0 Registry Adaptive Consumption O1-O6 Realignment - Candidate

- Implements deterministic Registry capability negotiation with explicit required/optional contracts, fail-closed incompatible required capabilities, and a bounded legacy compatibility profile for the immutable trusted Registry v0.2.0 surface without inventing unpublished R5 metadata.
- Adds multi-jurisdiction/provider/domain Registry selection while preserving exact source-to-obligation provenance and binding the adaptive path back into the existing `ComplianceQueryReceipt` and downstream compliance set-equality protocol.
- Adds query-scoped freshness so unrelated stale sources do not poison unrelated queries while stale, overdue, or untracked required sources fail the affected query closed.
- Adds deterministic R6 release-delta verification and scoped impact analysis with tamper, authority-expansion, unsupported-capability, and human-review dispositions preserved as evidence rather than execution authority.
- Adds governed Registry-domain to existing-specialist resolution with Conductor retained as the exclusive router; unknown domains escalate to human routing and cannot create or select unbounded agents.
- Adds an exact Registry R5 candidate fixture plus focused O1-O6, edge, and joint-contract regression coverage, and documents the adaptive architecture in `docs/architecture/REGISTRY_ADAPTIVE_CONSUMPTION_O1_O6.md`.
- Preserves the frozen B3 benchmark evidence, Registry PR #23/#24 unmerged state, trusted Registry release boundary, A5 non-promotion, A6 unauthorized state, B4 block, and all deployment/release/policy/destructive-operation gates.

## Post-v1.6.0 Comparative Benchmark B3 Calibration Execution Closeout & Evidence Freeze - Candidate

- Executes and validates full 30-run B3 calibration across 10 paired blocks (5 Padayon-grounded tasks x 2 repetitions x 3 communication arms) under Antigravity CLI 1.1.15 and `gemini-3.7-flash-high` stream-json transport.
- Achieves 100.0% semantic pass rate (30/30) derived strictly through `EXACT_JSON_CONFORMANCE_V1` deterministic response validation with zero invalid runs and zero safety violations (0 required specialist omissions, 0 authority expansions, 0 capability expansions, 0 governance violations).
- Measures empirical per-arm token consumption:
  - `DEFAULT`: mean 29,049.1 total tokens / 27,751.3 input / 1,297.8 output / 1,120.0 reasoning
  - `CAVEMAN`: mean 29,864.6 total tokens (+2.81% vs DEFAULT) / 28,597.9 input (+3.05% vs DEFAULT) / 1,266.7 output (-2.40% vs DEFAULT) / 1,092.4 reasoning (-2.46% vs DEFAULT)
  - `MURMURS`: mean 28,844.5 total tokens (-0.70% vs DEFAULT) / 27,752.8 input (+0.01% vs DEFAULT) / 1,091.7 output (-15.88% vs DEFAULT) / 913.9 reasoning (-18.40% vs DEFAULT)
- Bounds resource consumption well within frozen ceilings: cumulative total tokens 877,582 <= 1,200,000 ceiling, peak per-call tokens 31,268 <= 45,000 ceiling, and zero invalid runs.
- Cryptographically anchors and freezes calibration evidence in `machine/benchmarking/antigravity-executor-binding.v1.json`, `docs/benchmarking/COMPARATIVE_MEASUREMENT_B3.md`, and `README.json`.
- Enforces measurement boundaries: Murmurs benefit remains unestablished from calibration sample alone (inconclusive), token savings are evidence-derived only, confirmatory benchmark is required before establishing production claims, A5 execution promotion remains unauthorized, A6 remains unauthorized, and B4 remains blocked.

## Post-v1.6.0 Comparative Benchmark B3.2.1 Padayon-Grounded Calibration Task-Set & Deterministic Outcome Validation - Candidate

- Recalibrates B3 calibration task-set to be grounded in Padayon's approved work sequence (R5 capability manifest, R6/O1/O2 compatibility, O3/O4 freshness, Issue #115 assurance drift, O5/O6 routing) across 5 synthetic, self-contained task definitions.
- Implements a pure deterministic host-independent response validator in `scripts/benchmarking/calibration_task_validator.py` under contract `EXACT_JSON_CONFORMANCE_V1`, deriving task completion, validation, and governance outcomes directly from model responses against validation contracts without trusting self-reported pass flags or pre-seeding success booleans.
- Integrates `calibration_task_validator` into `scripts/antigravity_benchmark_executor.py` (`evaluate_task_outcome`, `parse_stream_json_output`, `parse_antigravity_output`), deriving outcome, quality, and safety fields from evaluated response content.
- Creates machine task-set record `machine/benchmarking/b3-calibration-task-set.v1.json` recording task-set version (`orchestra.b3-calibration-task-set.v1`), aggregate digest (`fd5109b2ec94709883bd75a9b7c6c89b6cd4f9bcc9840554bbd7cbb277a931a8`), Padayon source provenance (`03d1ffd4d1dea512230da5628741ae919d70e7ef`), and frozen benchmark subject (`d95f677dbf23ab79c4698c26645ea30cea9b3019`).
- Updates calibration plan-only fixture `tests/fixtures/benchmarking/b3-murmurs-isolated-calibration-plan-only.json` scheduling 30 runs in 10 paired blocks across `DEFAULT`, `CAVEMAN`, and `MURMURS` arms with `execution_allowed=false`.
- Adds comprehensive task-set documentation in `docs/benchmarking/B3_CALIBRATION_TASK_SET.md` and updates calibration floor details in `docs/benchmarking/COMPARATIVE_MEASUREMENT_B3.md`.
- Expands deterministic test suite in `tests/runtime/test_comparative_benchmark_b3_plan.py` proving all required invariants with zero live model/provider calls.
- Preserves all governance boundaries: zero live provider calls in this unit, live calibration remains unauthorized without separate human authorization and frozen resource budget, Murmurs benefit remains unestablished, token savings remain unclaimed, A5 execution promotion remains deferred, A6 remains unauthorized, and B4 remains blocked.

## Post-v1.6.0 Comparative Benchmark B3.2 Diagnostic Attempt 4 Evidence Closeout & Calibration Plan-Only Readiness - Candidate

- Records B3.2 Diagnostic Attempt 4 as a valid, completed 3-arm instrumentation diagnostic (`VALID_COMPLETE` / `diagnostic_execution=PASS` / `accepted_measurements=3` / `invalid_runs=0` / `live_host_turns=3` / `cumulative_total_tokens=92630` / `weekly_remaining_fraction_drop=0.0006388425827026367 <= 0.05`).
- Verifies and anchors Attempt 4 empirical evidence from external disk directory with exact file SHA-256 digests across report, manifest, plan, resource-budget, run-index, executor-results, requests, runs, preflight, and quota files without committing raw external test traces.
- Confirms headless workspace binding via `--add-dir` successfully bounds host print-mode context to minimal task workspace, establishing minimal workspace resource ceiling within the 45,000 token per-call budget (DEFAULT=29908, MURMURS=29668, CAVEMAN=33054).
- Preserves paired comparability invariants: identical counter identity (`antigravity-cli-1.1.15:stream-json-usage:gemini-3.7-flash-high`), identical fixed deterministic topology digest, invariant task prompt digest, disabled credit fallback (`effective_use_g1_credits=false`), and independent task outcome evaluation (`FAIL / FAIL / FAIL`).
- Reconciles B3 machine discovery and binding contracts (`antigravity-executor-binding.v1.json`, `README.json`) so diagnostic execution is marked completed (`diagnostic_executed=true`, `b3_valid_diagnostic=COMPLETED`, `b3_diagnostic_execution=VALID_COMPLETE`).
- Updates the frozen B3 Murmurs-isolated calibration plan-only fixture (`tests/fixtures/benchmarking/b3-murmurs-isolated-calibration-plan-only.json`) and test suite (`tests/runtime/test_comparative_benchmark_b3_plan.py`) to the canonical entry baseline `d95f677dbf23ab79c4698c26645ea30cea9b3019`.
- Proves deterministically that the plan-only calibration schedules exactly 30 runs (5 tasks x 2 repetitions x 3 arms in 10 paired blocks) with zero live model turns using an impossible executor sentinel.
- Preserves all core governance boundaries: `MEASUREMENT_NOT_STARTED` remains active, live calibration remains unauthorized without separate human authorization and frozen resource budget, Murmurs benefit remains unestablished, token savings remain unclaimed, A5 execution promotion remains deferred, A6 remains unauthorized, and B4 remains blocked.

## Post-v1.6.0 Comparative Benchmark B3.1.6 Explicit Antigravity Headless Workspace Binding - Candidate

- Implements deterministic explicit Antigravity headless workspace binding in `scripts/antigravity_benchmark_executor.py` via `resolve_workspace` and the verified native AGY CLI 1.1.15 `--add-dir <path>` argument interface.
- Prevents headless print-mode file tool calls from defaulting to the CLI scratch workspace (`~/.gemini/antigravity-cli/scratch`) by binding workspace-scoped operations directly to an explicit target directory without deriving workspace implicitly from process working directory or the Orchestra repository root.
- Enforces fail-closed validation (`INVALID_RUN` / `MEASUREMENT_CAPTURE_FAILURE`) when a configured workspace directory is missing, non-existent, or points to a file before model invocation or host preflight.
- Records full workspace-binding provenance in `raw_evidence.workspace_binding` (`bound`, `workspace_path`, `workspace_flag`, `workspace_mechanism`, `provenance.source`, `provenance.resolved_path`, `provenance.is_directory`).
- Preserves all B3.1.5 stream-json envelope normalization, B3.1.4 sparse settings semantics, B3.1.3 exact host qualification, communication treatments (`DEFAULT`, `CAVEMAN`, `MURMURS`), and governance boundaries.
- Records B3.2 Diagnostic Attempt 3 compatibility disposition (`INVALID_RUN` / `HEADLESS_WORKSPACE_BINDING_FAILURE` / `observed_total_tokens=61230` / `accepted_measurements=0` / `minimal_workspace_resource_ceiling=NOT_ESTABLISHED`) as diagnostic compatibility evidence without altering prior attempt records.
- Adds comprehensive deterministic runtime unit tests in `tests/runtime/test_comparative_benchmark_antigravity_executor.py` with zero live model turns.
- Updates machine binding record `machine/benchmarking/antigravity-executor-binding.v1.json`, machine discovery in `README.json`, and human documentation `docs/benchmarking/COMPARATIVE_MEASUREMENT_B3.md`.

## Post-v1.6.0 Comparative Benchmark B3.1.5 Antigravity Stream-JSON Result Envelope Normalization - Candidate

- Normalizes stream-json terminal result envelopes in `scripts/antigravity_benchmark_executor.py` via `normalize_stream_terminal_event` to correctly recognize wrapped Antigravity CLI 1.1.15 terminal events (`{"event": "result", "result": {"status": "SUCCESS", "usage": {...}, ...}}`).
- Resolves measurement fields (`status`, `usage`, `response`, `conversation_id`, `duration_seconds`, `num_turns`, `cli_version`, `model`, `latency`, `coordination`) from the nested canonical result payload.
- Enforces fail-closed validation (`INVALID_RUN` / `MEASUREMENT_CAPTURE_FAILURE`) against missing terminal events, non-object result payloads, missing/non-SUCCESS status, missing/malformed usage objects, and conflicting critical fields (`status`, `usage`, `cli_version`, `model`) between outer wrapper and nested payload.
- Recognizes `event` field discriminators (e.g., `event = "step_update"`, `event = "init"`, `event = "tool_start"`) in progress event processing, while strictly excluding the terminal result from intermediate progress counts.
- Preserves full original wrapper in `raw_evidence.terminal_event_envelope` (and `raw_evidence.outer_envelope`) and normalized payload in `raw_evidence.terminal_result_payload`.
- Maintains full backwards compatibility with flat legacy terminal fixtures (`{"type": "result", "status": "SUCCESS", ...}`).
- Records B3.2 Diagnostic Attempt 2 compatibility disposition (`INVALID_RUN` / `AGY_STREAM_RESULT_ENVELOPE_SCHEMA_MISMATCH` / `RESOURCE_CEILING_EXCEEDED`) as diagnostic compatibility evidence without committing external run directories or interpreting counters as comparative performance evidence.
- Adds comprehensive deterministic regression tests in `tests/runtime/test_comparative_benchmark_antigravity_executor.py` with zero live model turns.
- Updates machine discovery in `README.json`, machine binding record `machine/benchmarking/antigravity-executor-binding.v1.json`, and documentation in `docs/benchmarking/COMPARATIVE_MEASUREMENT_B3.md`.

## Post-v1.6.0 Comparative Benchmark B3.1.4 Antigravity Sparse Settings Semantic Preflight - Candidate

- Refactors Antigravity host preflight in `scripts/antigravity_benchmark_executor.py` to interpret `useG1Credits` according to documented Antigravity sparse-settings semantics where system default is `false`.
- Introduces `resolve_use_g1_credits` deterministic helper mapping absent keys to effective `false` with `SYSTEM_DEFAULT_SPARSE_PERSISTENCE` provenance and explicit `false` to `EXPLICIT_SETTING` provenance.
- Enforces fail-closed validation (`INVALID_RUN` / `MEASUREMENT_CAPTURE_FAILURE`) when `useG1Credits` is explicitly `true` or set to non-boolean/malformed values (`null`, `0`, `1`, `"false"`, `"true"`, `{}`, `[]`) without silent coercion.
- Preserves the core benchmark invariant that `effective_use_g1_credits` must be `false`, keeping personal credit fallback strictly disabled during comparative measurement.
- Preserves raw and effective provenance in `credit_fallback_policy` machine evidence across execution results.
- Preserves all prior preflights: exact CLI version matching (1.1.15), model pinning (`gemini-3.7-flash-high`), stream-json and json counter identities, communication treatment bindings (`DEFAULT`, `CAVEMAN`, `MURMURS`), and independent task outcome evaluation.
- Adds comprehensive deterministic runtime test coverage in `tests/runtime/test_comparative_benchmark_antigravity_executor.py` with zero live model turns.
- Updates machine discovery in `README.json`, machine binding record `machine/benchmarking/antigravity-executor-binding.v1.json`, and documentation `docs/benchmarking/COMPARATIVE_MEASUREMENT_B3.md`.

## Post-v1.6.0 Comparative Benchmark B3.1.3 Exact Host Version Pin Externalization - Candidate

- Externalizes the exact expected Antigravity host CLI version via `--expected-cli-version` CLI argument in `scripts/antigravity_benchmark_executor.py`, removing operational hard-coding while preserving exact fail-closed version matching.
- Rejects loose, range, wildcard, and operator version strings (e.g., empty, latest, `>=1.1.15`, `^1.1.15`) in `validate_version_format`.
- Qualifies Antigravity CLI 1.1.15 host surface via zero-turn structured preflight probes (`/model`, `/effort`, `/usage`, `num_turns=0`, `usage_counters=0`, `model=gemini-3.7-flash-high`).
- Derives measurement surface counter identity dynamically from validated exact version: `antigravity-cli-1.1.15:json-usage:gemini-3.7-flash-high` and `antigravity-cli-1.1.15:stream-json-usage:gemini-3.7-flash-high`.
- Separates provenance in `raw_evidence`: `expected_cli_version` (`EXECUTOR_ARGUMENT` / `DEFAULT_QUALIFIED_HOST`) and `observed_cli_version` (`PREFLIGHT_COMMAND` / `HOST_REPORTED_*`).
- Preserves all B3.1.2 communication treatments (`DEFAULT`, `CAVEMAN`, `MURMURS`), stream-json transport, fail-closed settings preflight (`useG1Credits: false`), and independent task outcome evaluation.
- Expands deterministic test suite in `tests/runtime/test_comparative_benchmark_antigravity_executor.py` with zero live model turns.
- Updates machine discovery in `README.json`, machine binding record `machine/benchmarking/antigravity-executor-binding.v1.json`, and documentation `docs/benchmarking/COMPARATIVE_MEASUREMENT_B3.md`.

## Post-v1.6.0 Comparative Benchmark B3.1.2 Communication Arm Operationalization - Candidate

- Operationalizes `DEFAULT`, `CAVEMAN`, and `MURMURS` communication treatments in `scripts/antigravity_benchmark_executor.py` into distinct, machine-verifiable benchmark treatments.
- Binds `DEFAULT` as the uncompressed baseline with `PresentationMode.NORMAL` and identity verification.
- Binds `CAVEMAN` against the pinned external repository `JuliusBrussee/caveman` at revision `ae405e872270acc57484693612ae038b16c8f6cd` and `skills/caveman/SKILL.md` (Git blob SHA-1 `bd22d86b32e4a99e09ff7482a35509faac7a6f65`), failing closed on revision/blob mismatch and prohibiting context compression proxies without vendoring or adopting runtime dependencies.
- Binds `MURMURS` to canonical `orchestra_runtime.presentation` contracts (`PresentationMode.MURMURS`, `murmurs-policy.v1.json`, `murmurs-vocabulary.v1.json`), reducing routine lifecycle events via `decide_presentation` while keeping the underlying task prompt invariant.
- Adds stream-json NDJSON event parsing with token counter mapping, event sequence retention, and counter identity invariance.
- Expands runtime unit test suite in `tests/runtime/test_comparative_benchmark_antigravity_executor.py` with 20 new tests covering all required B3.1.2 invariants with zero live model turns.
- Updates machine discovery parity in `README.json`, machine binding record `machine/benchmarking/antigravity-executor-binding.v1.json`, and documentation `docs/benchmarking/COMPARATIVE_MEASUREMENT_B3.md`.

## Post-v1.6.0 Comparative Benchmark B3.1.1 Antigravity Live Invocation Hardening - Candidate

- Hardens the live Antigravity CLI invocation path in `scripts/antigravity_benchmark_executor.py` to use validated print-mode syntax: `["agy", "--model", "gemini-3.7-flash-high", "-p", prompt, "--output-format", "json"]`.
- Removes prompt passing via subprocess stdin and removes unvalidated `--no-use-g1-credits` command-line argument.
- Implements fail-closed host preflight verifying exact CLI version (1.1.14), `settings.json` parsing, explicit `useG1Credits: false`, model pinning, and deterministic counter identity (`antigravity-cli-1.1.14:json-usage:gemini-3.7-flash-high`) before model execution.
- Establishes explicit provenance semantics across CLI version (`PREFLIGHT_COMMAND`), model (`PINNED_COMMAND_ARGUMENT`), usage counters (`HOST_REPORTED_JSON_USAGE`), and counter ID (`ORCHESTRA_ASSIGNED_MEASUREMENT_SURFACE`).
- Enforces quality boundaries ensuring host `SUCCESS` alone does not produce benchmark `PASS` by requiring explicit task completion, validation, and governance evidence.
- Accurately measures response bytes from the Antigravity `response` payload field.
- Adds comprehensive deterministic runtime test coverage in `tests/runtime/test_comparative_benchmark_antigravity_executor.py` without live model or provider execution.
