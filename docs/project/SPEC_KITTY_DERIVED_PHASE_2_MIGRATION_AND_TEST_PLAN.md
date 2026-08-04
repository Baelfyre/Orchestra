# Spec Kitty-Derived Orchestra Phase 2 Migration and Test Plan

## Status
```text
MIGRATION AND TEST PLAN EXECUTED
RUNTIME VALIDATED
MERGED
NOT RELEASED
POLICY NOT INTEGRATED
PR #208
MERGE COMMIT: 1e2992b94abe67a76c1e6ec0b98f8b712ae256e4
REVIEWED HEAD: 1a57c489445a9a333e929cae8f857312bb126a62
VERDICT: PHASE_2_MIGRATION_AND_TEST_PLAN_EXECUTED_AND_MERGED
```

## Overview
This document specifies the migration strategy, test plan, canonical validation contract matrix, and policy activation gates for integrating the four accepted Spec Kitty-derived designs into Orchestra during Phase 2B through Phase 2F.

## Legacy Record Inventory
- **Legacy Runtime Results**: Unversioned execution output dictionaries produced by `orchestra_runtime/`.
- **Legacy Transition Records**: Existing Arbiter transition decision JSON records.
- **Legacy Approved Unit Plans**: Standard 4-field `ApprovedUnitPlan` instances.
- **Legacy Phase Evidence & Handoffs**: Historical Phase 0–1F handoffs and evidence packets.

## Migration Principles
1. **Zero Retroactive Reconstruction**: Historical handoffs, decision logs, and transition records remain untouched and valid under their legacy schemas.
2. **Additive Non-Breaking Extensions**: All new fields (`OrchestraRuntimeEnvelope`, `OrchestraCorrelationID`, `OrchestraPhaseRetrospective`, unit plan extension fields) are additive and optional for legacy readers.
3. **Fail-Closed for Machine Action**: Unknown major schema versions (`2.x`) fail closed to prevent improper automated transitions.
4. **Policy Activation Gate**: Canonical policy (`DELEGATED_EXECUTION_POLICY.md` Section 4) is amended ONLY in Phase 2E.4 after runtime models and validators are fully tested.

## Canonical Validation Contract Matrix

| Category | Canonical Source | Exact Command / Script | Executed | Result | Required for Phase 2B Baseline | Notes |
|---|---|---|---|---|---|---|
| Preflight Sync | `scripts/preflight_sync_check.py` | `python scripts/preflight_sync_check.py origin/main` | Yes | PASS (Exit 0) | Yes | Branch aligned with origin/main |
| Strict Governance | `scripts/governance_check.py` | `python scripts/governance_check.py --strict` | Yes | PASS (0 Errors, 0 Warnings) | Yes | 9 deterministic check groups pass |
| Governance Protocol | `scripts/validate_governance_protocol_consistency.py` | `python scripts/validate_governance_protocol_consistency.py` | Yes | PASS (Exit 0) | Yes | Governance protocols consistent |
| Routing Contract | `scripts/validate_routing_contract.py` | `python scripts/validate_routing_contract.py` | Yes | PASS (Exit 0) | Yes | Routing contracts deterministic |
| Runtime Tests | `tests/runtime/` | `python -m pytest tests/runtime` | Yes | PASS (276 passed) | Yes | 276 runtime tests pass in 6.07s |
| Runtime Coverage | `pyproject.toml` / Policy | `python -m pytest tests/runtime --cov=orchestra_runtime --cov-report=term-missing --cov-fail-under=90` | Yes | PASS (93.84% coverage) | Yes | Exceeds 90% coverage threshold |
| Behavior Suite | `tests/behavior/run_tests.py` | `python tests/behavior/run_tests.py` | Yes | PASS (27/27 checks) | Yes | Requires `$env:ORCHESTRA_APPROVED_BASE_SHA` |
| Structure | `scripts/validate_structure.py` | `python scripts/validate_structure.py` | Yes | PASS (Exit 0) | Yes | 14 skills, 18 commands, 10 adapters |
| Manifest | `scripts/validate_manifest.py` | `python scripts/validate_manifest.py` | Yes | PASS (Exit 0) | Yes | Skills match frontmatter source |
| IDE Packaging | `scripts/validate_ide_packaging.py` | `python scripts/validate_ide_packaging.py` | Yes | PASS (Exit 0) | Yes | IDE packaging scaffolds validated |
| Artificer Internal | `scripts/validate_artificer_internal.py` | `python scripts/validate_artificer_internal.py` | Yes | PASS (Exit 0) | Yes | Internal contracts valid |
| Artificer Records | `scripts/validate_artificer_records.py` | `python scripts/validate_artificer_records.py` | Yes | PASS (Exit 0) | Yes | Record instances valid |
| Artificer Governance | `scripts/validate_artificer_governance_records.py` | `python scripts/validate_artificer_governance_records.py` | Yes | PASS (22 pass, 1 skip) | Yes | 1 pre-existing temp dir case skip |
| Pattern Catalog | `scripts/validate_artificer_pattern_catalog.py` | `python scripts/validate_artificer_pattern_catalog.py` | Yes | PASS (Exit 0) | Yes | Catalog synchronized with records |
| Prompt Load Budget | `scripts/validate_prompt_load_budget.py` | `python scripts/validate_prompt_load_budget.py` | Yes | PASS (Exit 0) | Yes | Prompt sizes within budget |
| Formatting Check | `git diff` | `git diff --check` | Yes | PASS (Clean) | Yes | Zero trailing whitespace / format errors |
| Scope Audit | `git status` | `git status --porcelain=v1 --untracked-files=all` | Yes | PASS (Clean) | Yes | Authorized planning paths only |

## Reconciled Skipped Test Log
- **Test Node Identifier**: `tests/behavior/test_artificer_governance_records.py::GovernanceRecordsTests::test_registry_case_insensitive_collision_end_to_end_when_supported`
- **Source File & Line**: `tests/behavior/test_artificer_governance_records.py:500`
- **Skip Reason**: `filesystem is case-insensitive in the temporary directory`
- **Classification**: `PERMITTED_PREEXISTING_SKIP` / `ADVISORY_ENVIRONMENT_SKIP` (OS capability check on Windows NTFS).
- **Impact on Baseline Verdict**: None (Pre-existing authorized test skip).

## Test Categories & Merged Execution Results

### 1. Runtime & Integration Tests (`tests/runtime/`)
- `test_runtime_envelope.py`: Validated 40 tests covering variant discrimination, serialization/deserialization, strict JSON bytes parser, and non-string/missing field negative cases.
- `test_correlation.py`: Validated 35 tests covering zero-dependency RFC 9562 UUIDv7 generator, 48-bit millisecond timestamp encoding, version/variant bits, root generation, and child propagation.
- `test_retrospective.py`: Validated 32 tests covering `OrchestraPhaseRetrospective` model, deterministic builder, provenance metric derivation, and strict JSON transport.
- `test_approved_unit_plan.py`: Validated 48 tests covering 15-field extension, path checks, structural validation, and `validate_approved_unit_plan_context` contextual validator.
- `test_spec_kitty_contract_integration.py`: Validated 20 cross-contract integration scenarios across envelope, correlation, retrospective, and unit plan interactions.
- `test_adapter_contracts.py`: Validated Codex and Antigravity adapter mixin integration.

### 2. Full Suite Validation Outcomes
- Runtime tests: 390 passed, 93.72% coverage (`pytest tests/runtime --cov=orchestra_runtime`).
- Behavior suite: passed with exit code 0 (`python tests/behavior/run_tests.py`).
- Direct validators: 13 direct validators passed (`governance_check.py --strict`, `validate_structure.py`, `validate_manifest.py`, `validate_ide_packaging.py`, `check_stale_references.py`, etc.).
- GitHub Actions CI: 9 of 9 status checks passed in PR #208 (Windows, Ubuntu, macOS, CodeQL, governance, runtime-tests, validate).

## Policy Activation Gate
Canonical execution policy (`docs/governance/DELEGATED_EXECUTION_POLICY.md`) Section 4 was deliberately NOT amended during Phase 2 implementation. Policy integration remains deferred until future maintainer authorization.

## Evidence Requirements
- Handoff reports `SPEC_KITTY_PHASE_2B1_HANDOFF.md` through `SPEC_KITTY_PHASE_2F2_FINAL_CLOSURE_HANDOFF.md` were recorded during Phase 2 progression and merged under `docs/artificer/external-sources/`.

## Open Questions (Deferred to Respective Phase Decision Gates)
- None for Phase 2A/2A.1 planning.
