# Router Benchmark Runner

## Purpose
The router benchmark runner automates the validation of benchmark case definitions for the Conductor's router-first execution model. It ensures that all benchmark scenarios are structurally sound, well-formed, and provide adequate coverage for the expected behaviors defined in the `ROUTER_VALIDATION_BENCHMARKS.md` specification.

## Scope
This runner script is scoped exclusively to parsing, validating, and summarizing the hardcoded definitions of benchmark cases.

## What It Validates
- Ensures every benchmark case has all required keys: `case_id`, `request_type`, `expected_mode`, `expected_skill_route`, `required_context`, `excluded_context`, `governance_status`, and `pass_criteria`.
- Validates the overall completeness of the defined scenarios.
- Verifies that destructive-operation coverage exists.

## What It Does Not Validate
- **Live Model Behavior**: This runner does NOT execute live LLM prompts.
- **Routing Engine Actuals**: It does not test if Conductor *actually* routes requests correctly; it only verifies that the benchmark test definitions cover the expected routes.

## How to Run
Execute the following from the repository root:
```bash
python scripts/router_benchmark_runner.py
```
*(Note: This runner is automatically executed as part of the CI validation workflow in `.github/workflows/governance-check.yml`.)*

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

## Runner Result
ROUTER_BENCHMARK_RUNNER_DEFINED
