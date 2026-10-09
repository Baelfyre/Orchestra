# Orchestra Spec Kitty-Derived Upgrade
## Combined Phase 2E.1, Phase 2E.2, Phase 2E.3, Phase 2E.4, and Phase 2E.4.1 Handoff
### Approved Unit Plan Extension, Validation, Runtime Integration, Compatibility, and Final Unit-Record Evidence

```text
PHASE: Combined Candidate Phase 2E.1, Phase 2E.2, Phase 2E.3, Phase 2E.4, and Phase 2E.4.1
VERDICT: READY_FOR_PHASE_2E_COMPLETION_REVIEW
BASELINE:
  branch: feature/spec-kitty-derived-runtime
  worktree: C:\conductor\.tmp\spec-kitty-derived-runtime
  commit: 7a3cd1aef86e4edb5194cd68f52d5e26cc2c66fc
  parent: 317c9449b2c6d264d0e826f229808439f1549ceb
  origin/main: 317c9449b2c6d264d0e826f229808439f1549ceb

IMPLEMENTATION_BRANCH: feature/spec-kitty-derived-runtime
IMPLEMENTATION_WORKTREE: C:\conductor\.tmp\spec-kitty-derived-runtime
PREFLIGHT_RESULT: PASS (Sync state aligned with origin/main)
PHASE_2D_BASELINE_VALIDATION: PASS (359 passed, 94.18% coverage before Phase 2E edits)

GATE_A_STATUS: COMPLETE
APPROVED_UNIT_PLAN_LOCATION: orchestra_runtime/models.py
CANONICAL_OWNER: The Steward (Scope Authority & Schema Owner)
SECONDARY_CONSUMER: Conductor (Execution Routing & Validation Enforcement)
FIELD_COUNT: 15 fields total
UNIVERSAL_REQUIRED_COUNT: 11 fields
CONDITIONAL_REQUIRED_COUNT: 1 field
OPTIONAL_COUNT: 3 fields
FIELD_MATRIX:
  - schema_version: Universal Required, String, Fixed "1.0.0", Extension Metadata
  - unit_id: Universal Required, String, Unique unit ID within phase, ApprovedUnitPlan
  - unit_revision: Universal Required, String | Integer, Normalized to "rev-1" or non-negative integer, ApprovedUnitPlan
  - unit_name: Universal Required, String, Human-readable descriptive name, ApprovedUnitPlan
  - phase_id: Universal Required, String, Associated phase ID, ApprovedUnitPlan
  - execution_envelope_ref: Universal Required, String, Delegated execution envelope ID reference, Root Execution Authority
  - scope_ref: Universal Required, String, Canonical scope section reference, ApprovedUnitPlan
  - responsible_specialist: Universal Required, String, Specialist role ("ponytail", "clockwork", "cloak", etc.), ApprovedUnitPlan
  - objective: Universal Required, String, Unit objective statement, ApprovedUnitPlan
  - expected_outputs: Universal Required, Tuple[String], Non-empty output paths list, ApprovedUnitPlan
  - validation_requirements: Universal Required, Tuple[String], Non-empty validation commands list, ApprovedUnitPlan
  - allowed_paths: Conditionally Required, Tuple[String] | None, Repository-relative allowed paths (Required for FILE_MUTATION; omitted for non-file units), ApprovedUnitPlan
  - prohibited_paths: Optional, Tuple[String] | None, Forbidden path boundaries, ApprovedUnitPlan
  - dependency_unit_ids: Optional, Tuple[String] | None, Predecessor unit IDs required before starting, ApprovedUnitPlan
  - governance_decision_ref: Optional, String | None, Non-authorizing Governor/Steward review reference, Governance Review

UNIT_TYPE_CLASSIFICATION:
  - FILE_MUTATION (allowed_paths required in contextual validation)
  - NON_FILE (allowed_paths omitted/optional)
  - READ_ONLY (allowed_paths omitted/optional)
  - READ_ONLY_REPOSITORY_REVIEW (allowed_paths omitted/optional)
  - ARCHITECTURE_OR_DESIGN (allowed_paths omitted/optional)
  - GOVERNANCE_OR_COMPLIANCE_REVIEW (allowed_paths omitted/optional)
  - VALIDATION_OR_EVIDENCE_REVIEW (allowed_paths omitted/optional)
  - DOCUMENTATION (allowed_paths conditionally required for doc paths)
  - NON_FILE_RUNTIME_OPERATION (allowed_paths omitted/optional)

FILE_MUTATION_RULE: allowed_paths is required and must be non-empty for FILE_MUTATION work (evaluated via validate_approved_unit_plan_context)
NON_FILE_RULE: Omitted allowed_paths for non-file units NEVER grants broad file authority
PATH_VALIDATION_MODEL: Repository-relative forward-slash normalization, no absolute paths, no drive letters, no file URIs, no path traversal (..), no persistent .agents/ path mutation
REVISION_MODEL: unit_revision differentiates post-approval amendments under the same execution_envelope_ref and unit_id
GATE_A_FOCUSED_TESTS: PASS (tests/runtime/test_approved_unit_plan.py)
GATE_A_RUNTIME_COVERAGE: PASS (370 passed, 93.67% coverage; 94% on models.py)
GATE_A_RESULT: PASS

GATE_B_STATUS: COMPLETE
EXECUTION_ENVELOPE_BINDING: execution_envelope_ref binds governing execution authority (DelegatedExecutionEnvelope / OrchestraRuntimeEnvelope validated via validate_approved_unit_plan_context)
SCOPE_BINDING: scope_ref is universally required across all unit types; allowed_paths narrows file mutation boundaries within scope
ALLOWED_PATHS_BINDING: Narrows repository file mutation; does NOT create scope or grant authority
PROHIBITED_PATHS_BINDING: Explicitly forbids path boundaries; overlapping allowed paths are rejected
DEPENDENCY_EVIDENCE_MODEL: Predecessors in dependency_unit_ids require accepted canonical evidence (execution completion alone is insufficient)
DEPENDENCY_ACCEPTANCE_RULE: Failed, unaccepted, or timed-out predecessors do NOT satisfy dependency
DEPENDENCY_CYCLE_MODEL: Self-dependencies and circular dependencies are rejected
GOVERNANCE_REFERENCE_MODEL: governance_decision_ref is optional, separate, and non-authorizing (presence alone never grants execution authority or replaces envelope/dependency evidence)
NON_AUTHORITY_TESTS: Verified (test_contextual_validator_execution_envelope_and_dependency_binding)
GATE_B_FOCUSED_TESTS: PASS (tests/runtime/test_approved_unit_plan.py)
GATE_B_RUNTIME_COVERAGE: PASS (370 passed, 93.67% coverage)
GATE_B_RESULT: PASS

GATE_C_STATUS: COMPLETE
STEWARD_PLANNING_PATH: The Steward scope authority & planning boundary
STEWARD_INTEGRATION_STATUS: MODEL_AND_VALIDATOR_INTEGRATED (Automatic runtime engine dispatch deferred)
VALIDATION_RESULT_MODEL: Deterministic ValidationResult with reason codes
REASON_CODE_MODEL: MISSING_ALLOWED_PATHS, ENVELOPE_MISMATCH, PHASE_MISMATCH, SPECIALIST_MISMATCH, UNACCEPTED_DEPENDENCY
HUMAN_ESCALATION_BOUNDARY: ESCALATE_HUMAN triggered ONLY for missing intent, material scope change, policy conflict, or required new authority. Ordinary structural validation defects return REJECTED status.
UNIT_REVISION_INTEGRATION: Revision increments managed through Steward planning boundary upon re-approval
AUTOMATIC_INTEGRATION_STATUS: Model and validator ready; full engine dispatch deferred
GATE_C_FOCUSED_TESTS: PASS (tests/runtime/test_approved_unit_plan.py)
GATE_C_RUNTIME_COVERAGE: PASS (370 passed, 93.67% coverage)
GATE_C_RESULT: PASS

GATE_D_STATUS: COMPLETE
SERIALIZATION_API: serialize_approved_unit_plan(plan) -> bytes (Returns UTF-8 JSON bytes)
DESERIALIZATION_API: deserialize_approved_unit_plan(payload) -> ApprovedUnitPlan (Public dict input REJECTED with TypeError)
STRICT_JSON_MODEL: Sorted keys, UTF-8 JSON, schema version enforcement, duplicate key rejection, non-finite float rejection
LEGACY_PLAN_POLICY: Legacy unit plan documents without embedded JSON blocks remain readable under legacy rules
LEGACY_AUTHORITY_POLICY: Legacy plans never gain broad file authority without explicit scope/paths
MIXED_VERSION_POLICY: Serializer omits absent optional fields; deserializer validates present fields byte-for-byte
MIGRATION_MODEL: Seamless in-memory deserialization migration
RETROACTIVE_MUTATION_POLICY: Prohibited (historical legacy records remain unchanged)
FINAL_AUTHORITY_MATRIX:
  - ApprovedUnitPlan: Canonical plan model
  - Steward: Primary owner & scope authority
  - Conductor: Validation enforcer & routing consumer
  - Execution Envelope: Governing execution authority source
  - Scope Ref: Universal scope reference
  - Governance Ref: Non-authorizing reference

FOCUSED_TEST_COMMANDS: python -m pytest tests/runtime/test_approved_unit_plan.py -q
FOCUSED_TEST_RESULTS: PASS (11 passed in 0.22s)

FULL_RUNTIME_COVERAGE_COMMAND: python -m pytest tests/runtime --cov=orchestra_runtime --cov-report=term-missing --cov-fail-under=90
FULL_RUNTIME_COVERAGE_RESULT: PASS (370 passed in 5.16s; 93.67% coverage vs 90% threshold; 94% on models.py, 93% on serialization.py)

BEHAVIOR_COMMAND: $env:ORCHESTRA_APPROVED_BASE_SHA = "7a3cd1aef86e4edb5194cd68f52d5e26cc2c66fc"; python tests/behavior/run_tests.py
BEHAVIOR_RESULT: PASS (All static behavioral expectation checks passed; validation suite PASSED)

DIRECT_VALIDATION_COMMANDS:
  - python scripts/governance_check.py --strict (PASS - 0 Errors, 0 Warnings)
  - python scripts/validate_governance_protocol_consistency.py (PASS)
  - python scripts/validate_routing_contract.py (PASS)
  - python scripts/validate_structure.py (PASS)
  - python scripts/validate_manifest.py (PASS)
  - python scripts/validate_ide_packaging.py (PASS)
  - python scripts/validate_artificer_internal.py (PASS)
  - python scripts/validate_artificer_records.py (PASS)
  - python scripts/validate_artificer_governance_records.py (PASS)
  - python scripts/validate_artificer_pattern_catalog.py (PASS)
  - python scripts/validate_prompt_load_budget.py (PASS)
  - python scripts/check_stale_references.py (PASS)
  - git diff --check (PASS)

DIRECT_VALIDATION_RESULTS: PASS (All direct script validators exited 0 with 0 errors and 0 warnings)

CHANGED_PATHS:
  - orchestra_runtime/__init__.py
  - orchestra_runtime/models.py
  - orchestra_runtime/serialization.py
  - tests/runtime/test_approved_unit_plan.py
  - docs/artificer/external-sources/SPEC_KITTY_PHASE_2E1234_HANDOFF.md
  - docs/artificer/external-sources/SPEC_KITTY_PHASE_2E41_CORRECTION_HANDOFF.md

UNEXPECTED_PATHS: None
RUNTIME_CHANGES: Updated ApprovedUnitPlan to exact 15 fields in models.py; added validate_approved_unit_plan_context; updated serialization.py; exported symbols in __init__.py.
TEST_CHANGES: Updated tests/runtime/test_approved_unit_plan.py (11 tests; 370 tests total in runtime suite).
ADAPTER_CHANGES: None (0 adapter changes).
SCRIPT_CHANGES: None.
POLICY_CHANGES: None.
DEPENDENCY_CHANGES: None (0 external PyPI dependencies added).
DURABLE_STORAGE_CHANGES: None (0 database or durable store files added).
MANIFEST_CHANGES: None.
PACKAGE_CHANGES: None.
CI_CHANGES: None.

STAGED_PATHS: None
COMMIT_STATUS: NOT_COMMITTED
PUSH_STATUS: NOT_PUSHED
PULL_REQUEST_STATUS: NOT_CREATED

SOURCE_INDEPENDENCE_RESULT: Verified (Zero external code copied; expressed as original Orchestra-native implementation)
DRIFT_CHECK_RESULT: PASS (Zero design drift from docs/project/ORCHESTRA_UNIT_RECORD_EXTENSION.md)
OPEN_QUESTIONS: None
BLOCKERS: None

PHASE_2E_COMPLETION_STATUS: MODEL_AND_CONTEXTUAL_VALIDATOR_COMPLETE
PHASE_2F_READINESS: Ready for maintainer review and explicit Phase 2F authorization.

MAINTAINER_DECISIONS_REQUIRED:
  1. Review Combined Candidate Phase 2E handoff and implementation in worktree C:\conductor\.tmp\spec-kitty-derived-runtime.
  2. Decide whether to grant authorization for Candidate Phase 2F.

NEXT_AUTHORIZED_ACTION:
  Stop and await maintainer review and explicit Phase 2F authorization.
```
