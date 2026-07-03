# Router Benchmark Runner

## Purpose
The router benchmark runner automates the validation of benchmark case definitions for the Conductor's router-first execution model. It ensures that all benchmark scenarios are structurally sound, well-formed, and provide adequate coverage for the expected behaviors defined in the `ROUTER_VALIDATION_BENCHMARKS.md` specification.

## Scope
This runner script is scoped exclusively to parsing, validating, and summarizing the machine-readable benchmark definitions stored in `tests/fixtures/router_benchmarks.json`.

## Source of Truth
- **Machine-Readable Fixture**: Benchmark definitions live in `tests/fixtures/router_benchmarks.json`. The runner loads and validates this fixture.
- **Fixture Schema**: The exact schema contract is defined in [ROUTER_BENCHMARK_FIXTURE_SCHEMA.md](ROUTER_BENCHMARK_FIXTURE_SCHEMA.md).
- **Maintenance Guide**: Refer to [ROUTER_BENCHMARK_MAINTENANCE_GUIDE.md](ROUTER_BENCHMARK_MAINTENANCE_GUIDE.md) before making edits to the fixture.
- **Human-Readable Guide**: `docs/testing/ROUTER_VALIDATION_BENCHMARKS.md` remains the primary human-readable benchmark guide.

## Validation Scope

## What It Validates
- Ensures every benchmark case has all required keys: `case_id`, `request_type`, `expected_mode`, `expected_skill_route`, `required_context`, `excluded_context`, `governance_status`, and `pass_criteria`.
- Validates the overall completeness of the defined scenarios.
- Ensures the fixture contains exactly 24 benchmark cases.
- Verifies that destructive-operation coverage exists.

## What It Does Not Validate
- **Live Model Behavior**: This runner does NOT execute live LLM prompts.
- **Routing Engine Actuals**: It does not test if Conductor *actually* routes requests correctly; it only verifies that the benchmark test definitions cover the expected routes.

## How to Run
Execute the following from the repository root:
```bash
python scripts/router_benchmark_runner.py
```
*(Note: This runner is automatically executed as part of the CI validation workflow in `.github/workflows/governance-check.yml`. For details on the generated `router_benchmark_report.txt` artifact, see the [CI Artifact Index](CI_ARTIFACT_INDEX.md).)*

## Expected Output
A structured text report detailing:
- Total number of benchmark definitions evaluated.
- Any missing fields or structural anomalies found.
- Coverage summaries by Mode, Governance Status, and Destructive Operations.
- A final pass/fail status.

## Coverage Summary
The runner automatically extracts and counts:
- Mode occurrences (e.g., FAST, STANDARD, GOVERNED, AUDIT, DESTRUCTIVE).
- Governance conditions (e.g., NOT_REQUIRED, CONDITIONAL, REQUIRED, BLOCKED_PENDING_AUTHORIZATION).
- The total number of benchmark cases that handle destructive or unauthorized conditions.

## Failure Conditions
The runner will exit with code `1` (fail) if:
- Any benchmark definition is missing a required field.
- The total destructive-operation coverage count is `0`.

## Non-Goals
- It is not a goal to run an LLM evaluation loop in this script. Live behavioral bounds are evaluated separately by `tests/behavior/evaluate_governance.py`.
- It is not a goal to modify or write any files.

## Negative Validation Testing
The runner script itself is validated against malformed data inputs by `tests/behavior/test_router_benchmark_fixture_validation.py`. This script automatically constructs temporary malformed JSON fixtures and verifies that the runner fails appropriately for each defined constraint. This negative validation test runs continuously in CI to ensure the strictness of the benchmark runner is never degraded.

## Runner Result
ROUTER_BENCHMARK_RUNNER_DEFINED

## Related Documents
- [Phase 8A Audit](../routing/ROUTER_FIRST_INTEGRATION_HARDENING_AUDIT.md)
- [CI Artifact Index](CI_ARTIFACT_INDEX.md)
