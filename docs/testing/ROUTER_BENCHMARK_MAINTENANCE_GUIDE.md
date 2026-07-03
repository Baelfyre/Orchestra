# Router Benchmark Maintenance Guide

## Purpose
This document provides explicit instructions for maintaining the router benchmark definitions. It acts as a procedural guide to safely add, edit, and review routing tests while preserving continuous integration validation coverage.

## Scope
This guide covers only the definition, adjustment, and schema-compliance of the benchmark cases used by `scripts/router_benchmark_runner.py`.

## Source of Truth
The canonical machine-readable source of truth for benchmark evaluation is:
`tests/fixtures/router_benchmarks.json`

The human-readable explanation of these benchmarks is maintained in:
`docs/testing/ROUTER_VALIDATION_BENCHMARKS.md`

## When to Add a Benchmark Case
You should add a benchmark case if you are:
- Introducing a fundamentally new routing mode.
- Adding a new governance check that implies a new required routing behavior.
- Documenting an adversarial edge case that was previously undefined.

## When to Edit an Existing Case
You should edit an existing case if:
- A routing rule changes intentionally (e.g. relaxing or tightening required context).
- The underlying schema introduces new required fields.
- Note: Do NOT edit cases simply to cover up a regression.

## Required Fixture Fields
Every benchmark case must comply with the `ROUTER_BENCHMARK_FIXTURE_SCHEMA.md`.
Required fields for every case:
- `case_id`
- `request_type`
- `expected_mode`
- `expected_skill_route`
- `required_context`
- `excluded_context`
- `governance_status`
- `pass_criteria`

## Case ID Rules
- `case_id` must follow the format `BM-XX`, where `XX` is an incrementing numeric identifier.
- No duplicate `case_id`s are permitted in the fixture array.

## Execution Mode Selection
`expected_mode` must be one of:
- `FAST`
- `STANDARD`
- `GOVERNED`
- `AUDIT`
- `DESTRUCTIVE`

## Governance Status Selection
`governance_status` must be one of:
- `NOT_REQUIRED`
- `CONDITIONAL`
- `REQUIRED`
- `BLOCKED_PENDING_AUTHORIZATION`

## Context Selection Rules
`required_context` and `excluded_context` must be JSON arrays (lists of strings). They must never be scalar strings or null. If no context is required or excluded, use an empty array `[]`.

## Pass Criteria Rules
`pass_criteria` must be a clear, non-empty descriptive string explaining what runtime behavior constitutes a pass.

## Review Checklist
Before submitting a PR that edits the benchmark fixture:
- [ ] I verified the `schema_version` is exactly `"1.0"`.
- [ ] I preserved existing `case_id` values unless intentionally replacing a scenario.
- [ ] I did NOT weaken governance expectations for any existing case.
- [ ] I did NOT remove `DESTRUCTIVE` coverage.
- [ ] I did NOT reduce coverage across existing execution modes without explicit justification.
- [ ] I updated `docs/testing/ROUTER_VALIDATION_BENCHMARKS.md` to reflect any new or modified scenarios.

## Validation Commands
Run the following checks to prove your changes are schema-compliant and safe:

```bash
python scripts/router_benchmark_runner.py
python tests/behavior/test_router_benchmark_fixture_validation.py
python scripts/check_prompt_load_thresholds.py
python scripts/measure_prompt_load.py
python tests/behavior/evaluate_governance.py
python tests/behavior/run_tests.py
python scripts/validate_manifest.py
python scripts/governance_check.py --strict
git diff --check
```

## CI Reports to Review
Always verify the uploaded `governance-validation-report` artifact in your Pull Request to confirm:
1. `router_benchmark_report.txt` exits 0 cleanly.
2. `router_benchmark_negative_fixture_report.txt` exits 0 cleanly.

## Common Mistakes
- **Typos in Mode names**: e.g. using `DESTRUCT` instead of `DESTRUCTIVE`. The runner explicitly validates exact string matches.
- **Incorrect Type for Context**: Providing `"context_a"` instead of `["context_a"]` for `required_context`. The runner strictly requires lists.
- **Missing DESTRUCTIVE coverage**: The runner explicitly requires at least one destructive case to prove guardrails are active. Deleting it will fail the build.

## Non-Goals
This document does not specify how to write LLM behavior evaluation tests (those reside in `tests/behavior/`). It strictly concerns the maintenance of the JSON benchmark schema definitions.

## Expansion Plan
For information on planned future benchmarks, see the [ROUTER_BENCHMARK_COVERAGE_EXPANSION_PLAN.md](ROUTER_BENCHMARK_COVERAGE_EXPANSION_PLAN.md).

## Guide Result
ROUTER_BENCHMARK_MAINTENANCE_GUIDE_DEFINED

See [ROUTER_BENCHMARK_COVERAGE_COMPLETION_REVIEW.md](file:///c:/conductor/docs/testing/ROUTER_BENCHMARK_COVERAGE_COMPLETION_REVIEW.md) for the final Phase 7 outcome.
