# Router Benchmark Coverage Expansion Plan

## Purpose
This document outlines the strategic plan for expanding the validation coverage of the Conductor's router-first execution model. It identifies existing coverage gaps, establishes principles for adding new cases, and prioritizes future benchmark additions without altering the current operational fixture.

## Scope
This plan applies to the definition and structured expansion of the machine-readable benchmark cases stored in `tests/fixtures/router_benchmarks.json` and evaluated by `scripts/router_benchmark_runner.py`. It is a planning document and does not actively modify the runtime test suite.

## Current Coverage Baseline
As of the initial router-first validation release, the coverage baseline is exactly **12 benchmark cases**:
- **Execution Modes**: Full coverage established (`FAST`, `STANDARD`, `GOVERNED`, `AUDIT`, `DESTRUCTIVE`).
- **Governance Statuses**: Full coverage established (`NOT_REQUIRED`, `CONDITIONAL`, `REQUIRED`, `BLOCKED_PENDING_AUTHORIZATION`).
- **Destructive Operations**: Coverage exists to prove active blocks.

## Coverage Gaps
While foundational modes and statuses are covered, the following complex scenarios lack explicit benchmark definitions:
- Multi-skill routing chains and handoffs.
- Ambiguous requests requiring clarification before routing.
- Context-driven escalation from `STANDARD` to `GOVERNED`.
- True audit-only tasks that must not edit any files.
- Persistent blocks on multi-stage destructive operations.
- Frontend modifications requiring pre-requisite work by `Clockwork`, `Cipher`, or `Chronicler` before delegating to `Ponytail`.
- Documentation-only tasks that should aggressively minimize prompt load.
- Explicitly database-sensitive and security-sensitive boundary checks.
- Continuous Integration (CI/CD) and release-readiness operational checks.
- Specific measurement boundaries for prompt-load and context-selection efficiency.

## Expansion Principles
1. **No Regression**: New cases must not reduce existing coverage or weaken governance expectations.
2. **Distinct Value**: Every new case must test a unique routing path, mode transition, or governance boundary not covered by existing cases.
3. **Deterministic Verification**: Pass criteria must be objectively verifiable through static structural assertions or predictable LLM behavior.
4. **Minimal Overlap**: Cases should isolate specific routing behaviors rather than testing everything at once.

## Candidate Benchmark Categories
Future expansion will target the following categories to close the identified gaps:

### Priority 1 Cases (BM-13 through BM-16)
- **Multi-Skill Handoff**: Explicitly routing to an initial specialist with a designated follow-up (e.g., `weaver` -> `scribe`).
- **Ambiguity Resolution**: Forcing the router to ask a clarifying question rather than guessing a path.
- **Contextual Escalation**: Starting as a standard task but escalating due to implicit database or security context.
- **Audit Compliance**: Enforcing read-only behavior for comprehensive review tasks.

### Priority 2 Cases (BM-17 through BM-20)
- **Frontend Guardrails**: Requiring architecture (`Clockwork`), security (`Cipher`), or data (`Chronicler`) review before executing frontend changes (`Ponytail`).
- **Documentation Efficiency**: Stripping all code files from context for pure documentation updates.
- **Database Sensitivity**: Aggressive `GOVERNANCE_LAYER.md` loading for schema changes.
- **Security Scrutiny**: Unconditional escalation for authentication/authorization changes.

### Priority 3 Cases (BM-21 through BM-24)
- **CI/CD Impact**: Mode escalation for modifying workflow files.
- **Release Readiness**: Triggering formal audit generation for release preparations.
- **Prompt Load Extremes**: Cases designed specifically to measure the limits of minimal vs. full context loading.
- **Complex Destructive Paths**: Ensuring `dagger` blocks persist across multi-step adversarial requests.

## Governance-Sensitive Expansion Areas
Future benchmarks must rigorously test the boundaries of:
- `CONDITIONAL` vs `REQUIRED` governance states.
- The precise conditions that force the inclusion of `GOVERNANCE_LAYER.md`.
- Read-only preservation during `AUDIT` mode.

## Context Retrieval Expansion Areas
We will add cases to verify:
- Aggressive stripping of frontend files during backend tasks.
- Aggressive stripping of backend files during frontend tasks.
- Exclusion of implementation files during pure architectural planning.

## Skill Routing Expansion Areas
We need targeted cases to prove the router selects:
- `cloak` over `ponytail` for purely visual changes.
- `chronicler` over `ponytail` for persistence layer modifications.
- `weaver` for diagram generation without code modification.

## Destructive Operation Expansion Areas
Additional cases must verify that the `BLOCKED_PENDING_AUTHORIZATION` state is impenetrable, even when wrapped in seemingly benign multi-step workflows.

## Acceptance Criteria for New Cases
Before any new benchmark case is added to the active fixture, it must meet the following criteria:
1. The case maps explicitly to exactly one execution mode (`FAST`, `STANDARD`, `GOVERNED`, `AUDIT`, `DESTRUCTIVE`).
2. The case defines a clear governance status.
3. The case explicitly defines `required_context` and `excluded_context`.
4. The case has concrete, verifiable `pass_criteria`.
5. The case does not duplicate the routing path of an existing benchmark.
6. The inclusion of the new case does not remove or dilute existing destructive coverage.
7. All validation scripts pass cleanly after the addition.

## Validation Requirements
Adding cases defined in this plan requires running the full validation suite:
```bash
python scripts/router_benchmark_runner.py
python tests/behavior/test_router_benchmark_fixture_validation.py
python scripts/check_prompt_load_thresholds.py
python scripts/measure_prompt_load.py
python tests/behavior/evaluate_governance.py
python tests/behavior/run_tests.py
python scripts/validate_manifest.py
python scripts/governance_check.py --strict
```

## Non-Goals
This plan does not actively modify the JSON fixture. It serves as a roadmap for subsequent milestones to execute the expansion safely.

## Plan Result
ROUTER_BENCHMARK_COVERAGE_EXPANSION_PLAN_DEFINED
