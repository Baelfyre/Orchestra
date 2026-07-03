# CI Artifact Index

## Purpose
This document provides a central index of every CI artifact produced by the governance validation workflow (`governance-check.yml`). These artifacts ensure high visibility into prompt load sizes, benchmark health, and governance validation metrics without cluttering pull request conversations.

## Scope
This index covers the artifacts bundled into the `governance-validation-report` artifact, which is generated and uploaded upon completion of the governance check workflow.

## Governance Validation Artifact Bundle
The governance CI workflow generates multiple text reports that are zipped into a single downloadable artifact named `governance-validation-report`. This bundle is retained for 14 days and contains the reports detailed below.

## Artifact List
The following files are included in the bundle:
- `artifacts/router_benchmark_report.txt`
- `artifacts/router_benchmark_negative_fixture_report.txt`
- `artifacts/prompt_load_metrics.txt`
- `artifacts/prompt_load_threshold_report.txt`
- `artifacts/governance_report.txt`
- `artifacts/dagger_guardrail_report.txt`
- `artifacts/evaluate_governance_report.txt`
- `artifacts/run_tests_report.txt`

## Router Benchmark Reports
**Files**: `artifacts/router_benchmark_report.txt`, `artifacts/router_benchmark_negative_fixture_report.txt`
The primary report validates the benchmark case definitions against the expected schema, ensuring consistency across all routing test vectors. The negative fixture report proves that malformed inputs cause the runner to fail appropriately. See [ROUTER_BENCHMARK_RUNNER.md](ROUTER_BENCHMARK_RUNNER.md) for execution details.

## Prompt Load Metrics Report
**File**: `artifacts/prompt_load_metrics.txt`
This report captures raw prompt load measurements (line count, word count, character count, and token estimations) across all context groups. See [PROMPT_LOAD_METRICS.md](../performance/PROMPT_LOAD_METRICS.md) for token estimation logic.

## Prompt Load Threshold Report
**File**: `artifacts/prompt_load_threshold_report.txt`
This report compares the raw token approximations against established soft thresholds to detect context bloat. It currently operates in report-only (dry-run) mode and does not cause hard CI failures. See [PROMPT_LOAD_THRESHOLD_CHECKER.md](../performance/PROMPT_LOAD_THRESHOLD_CHECKER.md) and [PROMPT_LOAD_THRESHOLD_POLICY.md](../performance/PROMPT_LOAD_THRESHOLD_POLICY.md) for limits.

## Governance Reports
The remaining artifacts capture standard repository behavior and governance rule conformance:
- `artifacts/governance_report.txt`: Output of strict Stage 1 structural checks.
- `artifacts/dagger_guardrail_report.txt`: Output of Dagger simulation tests.
- `artifacts/evaluate_governance_report.txt`: Output of LLM behavioral expectation regex checks.
- `artifacts/run_tests_report.txt`: Output of general regression suites.

## How to Access Artifacts
1. Navigate to the **Actions** tab of the repository on GitHub.
2. Select a recent run of the **Governance Check** workflow.
3. Scroll to the **Artifacts** section at the bottom of the summary page.
4. Download the `governance-validation-report` zip file.

## How to Interpret Artifacts
- **Threshold reports** should be checked for `[WATCH]`, `[REVIEW]`, or `[EXCEEDED]` statuses, which indicate context bloat.
- **Benchmark reports** should indicate cleanly parsed schemas.
- **Governance reports** must pass strict Stage 1 checks; failure in these will also cause the CI run to fail.

## Maintainer Review Guidance
When reviewing pull requests:
1. If the PR modifies documentation loaded by the Conductor, inspect the `prompt_load_threshold_report.txt` for growth warnings.
2. If the PR adds test scenarios, confirm `router_benchmark_report.txt` parsed them successfully.
3. Use the artifacts to identify regressions early without needing to pull down and run the validation scripts locally.

## Non-Goals
This index does not document application build artifacts (e.g., compiled binaries, docker images) or deployment metadata. It is scoped entirely to the static validation outputs of the router-first architecture.

## Index Result
CI_ARTIFACT_INDEX_DEFINED

## Related Documents
- [Prompt Load Metrics](../performance/PROMPT_LOAD_METRICS.md)
- [Prompt Load Threshold Checker](../performance/PROMPT_LOAD_THRESHOLD_CHECKER.md)
- [Router Benchmark Runner](ROUTER_BENCHMARK_RUNNER.md)
