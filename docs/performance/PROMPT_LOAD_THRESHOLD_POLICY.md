# Prompt Load Threshold Policy

## Purpose
This policy defines the bounds for acceptable prompt payload sizes during the Conductor's routing phase. It establishes soft thresholds to ensure the router-first architecture remains highly performant and cost-efficient.

## Scope
This policy applies to context files loaded during the initial routing phase, specifically targeting the files measured by `scripts/measure_prompt_load.py`.

## Measurement Source
All thresholds are based on the output of `scripts/measure_prompt_load.py`, which provides a lightweight character count and an approximate token count.

## Threshold Philosophy
- The Conductor's default prompt load must remain as small as possible to ensure fast and cheap routing.
- Historical advisory reporting remains available through `scripts/check_prompt_load_thresholds.py`.
- Blocking budget enforcement now lives in `scripts/validate_prompt_load_budget.py`.

## Original Baseline
These historical values are retained for comparison and are not current replacement baselines:
- Group A (Core Router-First Minimal Context): ~7087 estimated tokens
- Group B (Broader Routing Context): ~5027 estimated tokens
- Group C (Governance Context): ~2636 estimated tokens
- Group D (Baseline Performance Docs): ~2330 estimated tokens
- Grand Total: ~17080 estimated tokens

## Approved Baseline Packages

Approved bootstrap baselines live in `docs/performance/PROMPT_LOAD_BASELINE.json`.
They were measured after Issue #171 cleanup and are now strict-governance inputs, not advisory guesses.

Packages include:

- Conductor
- default routing
- ambiguous routing
- governance core
- Steward governance
- Governor governance
- release governance

## Blocking Thresholds

### Conductor and default routing

- `REVISION_REQUIRED`: more than 5% above approved baseline
- `BLOCKED`: more than 10% above approved baseline

### Governance execution packages

- `REVISION_REQUIRED`: more than 10% above approved baseline
- `BLOCKED`: more than 15% above approved baseline

### Optional or reference-only packages

- `REVISION_REQUIRED`: more than 15% above approved baseline
- `BLOCKED`: more than 25% above approved baseline

Threshold equality is non-failing. Only values strictly above a threshold change status.

## Validator Outcomes

`scripts/validate_prompt_load_budget.py` returns:

- `PASS`
- `REVISION_REQUIRED`
- `BLOCKED`
- `CONFIGURATION_ERROR`

Exit codes:

- `0` for `PASS`
- `1` for `REVISION_REQUIRED` or `BLOCKED`
- `2` for `CONFIGURATION_ERROR`

Both `REVISION_REQUIRED` and `BLOCKED` fail strict governance.

## Baseline Change Protection

Feature work must not raise its own baseline merely to silence drift.
Baseline entries must document:

- previous baseline
- new baseline
- growth percentage
- reason
- alternatives considered
- Maintainer approval
- decision-log reference

Undocumented or malformed baseline changes are configuration failures.

Approval states are explicit:

- `BOOTSTRAP_PENDING` is valid only when `previous_baseline_tokens` is `null`.
- `APPROVED` is required for any later baseline increase.
- Empty or arbitrary approval text is invalid.
- Recorded growth percentage must equal the calculated change from previous to new baseline.

## Recommended Actions When Thresholds Are Exceeded
If a soft threshold is exceeded, maintainers should:
1. **Split Documents**: Move non-critical context into secondary files loaded only upon specific intent triggers.
2. **Shorten Phrasing**: Refine the documentation to be more concise without losing governance meaning.
3. **Move to Selective Retrieval**: Ensure the file is not loaded by default but instead selectively fetched via `ask_question` or `grep_search`.

## Threshold Checker
Use `scripts/check_prompt_load_thresholds.py` for advisory historical reporting.
Use `scripts/validate_prompt_load_budget.py` for blocking governance enforcement.

## CI Artifact Usage
The `measure_prompt_load.py` script runs automatically in the `governance-check.yml` CI workflow. Its output is published as `prompt_load_metrics.txt` in the `governance-validation-report` artifact. This ensures continuous observability-only tracking of prompt load metrics. For details on all governance artifacts, see the [CI Artifact Index](../testing/CI_ARTIFACT_INDEX.md).

## Non-Goals
This policy does not govern user prompt sizes, session history limits, or downstream specialist output tokens. It governs the static context injected into routing and governance execution packages.

## Policy Result
PROMPT_LOAD_THRESHOLD_POLICY_DEFINED

## Related Documents
- [Prompt Load Metrics](PROMPT_LOAD_METRICS.md)
- [Prompt Load Threshold Checker](PROMPT_LOAD_THRESHOLD_CHECKER.md)
- [CI Artifact Index](../testing/CI_ARTIFACT_INDEX.md)
