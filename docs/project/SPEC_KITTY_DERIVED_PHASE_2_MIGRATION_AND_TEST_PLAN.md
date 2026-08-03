# Spec Kitty-Derived Orchestra Phase 2 Migration and Test Plan

## Status
```text
PLANNING ONLY
NO MIGRATION EXECUTED
NO TESTS MODIFIED
POLICY NOT INTEGRATED
NOT RELEASED
VERDICT: READY_FOR_PHASE_1_AND_2A_DOCUMENTATION_COMMIT_REVIEW
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

## Test Categories & Plan for Phase 2 Implementation

### 1. Unit Tests (`tests/unit/`)
- `test_runtime_envelope.py`: Validate serialization, parsing, variant discrimination, reason-code transcription, and negative schema inputs for `OrchestraRuntimeEnvelope`.
- `test_correlation_id.py`: Validate RFC 9562 UUIDv7 layout, 48-bit timestamp checks, version/variant bits, and generator option behavior.
- `test_phase_retrospective.py`: Validate 16-field retrospective rendering, neutral outcome summary generation, and sanitized retention boundaries.
- `test_unit_plan_extension.py`: Validate 15-field extension schema, `scope_ref` validation, `allowed_paths` enforcement on `FILE_MUTATION` units, and predecessor evidence checks.

### 2. Behavior Tests (`tests/behavior/`)
- `test_adapter_envelope.py`: Verify Codex and Gemini adapter output formatting when wrapped in runtime envelopes.
- `test_correlation_propagation.py`: Verify correlation ID preservation across parent-child delegated execution chains, retries, and transition records.
- `test_retrospective_retention.py`: Verify `MIXED_RETENTION_MODEL` (sanitized public repo summaries vs detailed local artifact logs).
- `test_routing_unit_consumption.py`: Verify Conductor routing consumption of extended unit plans and Arbiter transition checks.

### 3. Governance & Security Tests (`scripts/` & `tests/`)
- `scripts/governance_check.py`: Verify deterministic Stage 1 governance gates pass across all new model modules.
- `scripts/validate_governance_protocol_consistency.py`: Verify governance protocols remain internally consistent.
- `scripts/validate_routing_contract.py`: Verify routing contracts remain deterministic.
- Secret & Prompt Leakage Audit: Verify zero API keys, secrets, or raw prompt text are serialized into envelopes, retrospectives, or unit records.

### 4. Cross-Version Python & Compatibility Tests
- Validate legacy record parsing across Python 3.11, 3.12, 3.13, and 3.14.
- Verify fallback behavior when running under runtimes lacking native `uuid.uuid7()`.

## Policy Activation Gate
Canonical execution policy (`docs/governance/DELEGATED_EXECUTION_POLICY.md`) Section 4 will be updated ONLY during Phase 2E.4 after:
1. Extended unit plan models and validators pass 100% of unit and behavior tests.
2. Migration and backward-compatibility tests confirm zero breakage of legacy plan parsing.
3. Explicit maintainer authorization is granted for policy integration.

## Evidence Requirements
- Every implementation phase (2B through 2G) must produce a formal handoff report recording exact preflight results, changed path sets, test execution counts, pass/fail results, and baseline preservation hashes.

## Open Questions (Deferred to Respective Phase Decision Gates)
- None for Phase 2A/2A.1 planning.
