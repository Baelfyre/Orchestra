# Router Benchmark Fixture Schema

## Purpose
This document defines the exact schema contract for the router benchmark JSON fixture (`tests/fixtures/router_benchmarks.json`). It is strictly enforced by the `scripts/router_benchmark_runner.py` runner to prevent malformed validation coverage.

If you need to add or edit benchmarks, first read the [ROUTER_BENCHMARK_MAINTENANCE_GUIDE.md](ROUTER_BENCHMARK_MAINTENANCE_GUIDE.md).

## Scope
This schema dictates the required shape and values for the router benchmark JSON fixture.

## Fixture Location
`tests/fixtures/router_benchmarks.json`

## Root Object Schema
The root of the fixture must be a JSON object containing:
- `schema_version`: String, must be "1.0"
- `benchmarks`: Array of benchmark case objects

## Benchmark Case Schema
Each benchmark object within the `benchmarks` array must adhere to the rules below.

## Required Fields
Every benchmark case must include the following keys:
- `case_id`: String (unique identifier)
- `request_type`: String (description of the request)
- `expected_mode`: String (must be an allowed mode)
- `expected_skill_route`: String (expected routing path)
- `required_context`: Array of strings (context that must be present)
- `excluded_context`: Array of strings (context that must not be present)
- `governance_status`: String (must be an allowed status)
- `pass_criteria`: String (must be non-empty description)

## Allowed Execution Modes
The `expected_mode` field must be one of:
- `FAST`
- `STANDARD`
- `GOVERNED`
- `AUDIT`
- `DESTRUCTIVE`

## Allowed Governance Statuses
The `governance_status` field must be one of:
- `NOT_REQUIRED`
- `CONDITIONAL`
- `REQUIRED`
- `BLOCKED_PENDING_AUTHORIZATION`

## List Fields
The following fields must be strictly typed as JSON Arrays (lists):
- `required_context`
- `excluded_context`

## Validation Rules
The benchmark fixture is validated by `scripts/router_benchmark_runner.py`, which enforces:
- The root object is a dictionary containing `schema_version` equal to "1.0".
- The `benchmarks` array exists and contains exactly 24 benchmark cases.
- All `case_id` values are unique.
- All required fields are present in every case.
- Arrays and strings are of the correct types and non-empty where applicable.
- Enums (`expected_mode`, `governance_status`) match the allowed values exactly.

## Example Fixture Entry
```json
{
  "case_id": "BM-01",
  "request_type": "simple Q&A",
  "expected_mode": "FAST",
  "expected_skill_route": "conductor (direct answer)",
  "required_context": [
    "SKILL.md"
  ],
  "excluded_context": [
    "Full index",
    "Governance"
  ],
  "governance_status": "NOT_REQUIRED",
  "pass_criteria": "Answers directly without full context"
}
```

## Runner Integration
The runner script `scripts/router_benchmark_runner.py` automatically parses the JSON fixture and performs strict structural validation against this schema before summarizing mode and governance coverage.

## Non-Goals
This schema validation does not execute the actual live routing tests or prompt the LLM. It solely ensures the test definitions are well-formed.

## Schema Result
ROUTER_BENCHMARK_FIXTURE_SCHEMA_DEFINED
