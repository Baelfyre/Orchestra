# Orchestra Spec Kitty-Derived Upgrade
## Phase 2E.4.1 Correction Handoff Report
### Canonical Unit-Type Classification, Real Steward Integration, Authority Binding, and Evidence-Complete Validation

```text
PHASE: Candidate Phase 2E.4.1 Correction
VERDICT: READY_FOR_PHASE_2E_COMPLETION_REVIEW
BASELINE:
  branch: feature/spec-kitty-derived-runtime
  worktree: C:\conductor\.tmp\spec-kitty-derived-runtime
  commit: 7a3cd1aef86e4edb5194cd68f52d5e26cc2c66fc
  parent: 317c9449b2c6d264d0e826f229808439f1549ceb
  origin/main: 317c9449b2c6d264d0e826f229808439f1549ceb

IMPLEMENTATION_BRANCH: feature/spec-kitty-derived-runtime
IMPLEMENTATION_WORKTREE: C:\conductor\.tmp\spec-kitty-derived-runtime
FINAL_WORKING_TREE_STATUS: DIRTY (Uncommitted authorized Phase 2B/2C/2D/2E changes)

CORRECTION_1_GIT_AND_FILE_INTEGRITY:
  git_status: DIRTY
  models_numstat: 385 additions, 1 deletion relative to HEAD 7a3cd1aef86e4edb5194cd68f52d5e26cc2c66fc
  serialization_numstat: 67 additions relative to HEAD
  init_numstat: 51 additions relative to HEAD
  existing_symbols_preserved: YES (Skill, Command, ContextPackage, RouteDecision, GovernanceRule, ValidationResult, ExecutionResult, AuditEventType, RunIdentity, RuntimeAuditEvent, EnvelopeMessageType, OrchestraRuntimeEnvelope)
  unexpected_removals: NONE
  result: PASS

CORRECTION_2_SCHEMA_AUDIT:
  actual_field_matrix:
    - unit_id: Universal Required, String
    - unit_revision: Universal Required, String | Integer
    - unit_name: Universal Required, String
    - phase_id: Universal Required, String
    - execution_envelope_ref: Universal Required, String
    - scope_ref: Universal Required, String
    - responsible_specialist: Universal Required, String
    - objective: Universal Required, String
    - expected_outputs: Universal Required, Tuple[String]
    - validation_requirements: Universal Required, Tuple[String]
    - schema_version: Universal Required, String (Default "1.0.0")
    - allowed_paths: Conditionally Required, Tuple[String] | None
    - prohibited_paths: Optional, Tuple[String] | None
    - dependency_unit_ids: Optional, Tuple[String] | None
    - governance_decision_ref: Optional, String | None
  field_count: 15 fields total (11 universal required, 1 conditionally required, 3 optional)
  extra_field_status: ABSENT (unit_type field removed from dataclass to match exact 15-field schema)

CORRECTION_3_UNIT_TYPE_CLASSIFICATION:
  unit_type_source: Design B (Trusted Validation Context)
  unit_type_context_status: CONTEXTUAL_VALIDATOR_IMPLEMENTED
  implementation: validate_approved_unit_plan_context(plan, operation_context="FILE_MUTATION") enforces allowed_paths requirement under file mutation operation context; context-free dataclass __post_init__ does pure structural validation.

CORRECTION_4_VALIDATION_LAYERS:
  structural_validator: ApprovedUnitPlan.__post_init__ (validates 15 fields, path syntax, no traversal, no .agents/ mutation)
  contextual_validator: validate_approved_unit_plan_context (validates operation_context allowed_paths requirement)
  authority_validator: validate_approved_unit_plan_context (validates execution_envelope_ref binding)
  dependency_validator: validate_approved_unit_plan_context (validates predecessor_evidence acceptance)

CORRECTION_5_ENVELOPE_BINDING:
  execution_envelope_model: DelegatedExecutionEnvelope / OrchestraRuntimeEnvelope
  execution_envelope_lookup: Provided via envelope argument to validate_approved_unit_plan_context
  execution_envelope_binding_status: CONTEXTUAL_VALIDATOR_IMPLEMENTED
  scope_binding_status: COMPLETE (scope_ref universally required across all unit types)

CORRECTION_6_DEPENDENCY_ACCEPTANCE:
  dependency_evidence_record: ExecutionEvidencePacket / CoordinationEvidenceRecord
  dependency_evidence_writer: Arbiter / CoordinationController
  dependency_acceptance_status: CONTEXTUAL_VALIDATOR_IMPLEMENTED (predecessors checked for COMPLETED/ACCEPTED evidence status)

CORRECTION_7_STEWARD_INTEGRATION:
  steward_class_or_service: The Steward (Scope Authority & Planning Boundary)
  steward_planning_method: ApprovedUnitPlan construction and validate_approved_unit_plan_context
  steward_integration_status: DEFERRED (MODEL_AND_VALIDATOR_ONLY; full automatic engine dispatch deferred)

CORRECTION_8_VALIDATION_RESULT:
  validation_result_type: ValidationResult(allowed: bool, status: str, reasons: tuple[str, ...], evaluated_rules: tuple[str, ...])
  reason_code_type: Stable deterministic reason strings ("MISSING_ALLOWED_PATHS", "ENVELOPE_MISMATCH", "PHASE_MISMATCH", "SPECIALIST_MISMATCH", "UNACCEPTED_DEPENDENCY")

CORRECTION_9_ESCALATION:
  escalation_classifier: validate_approved_unit_plan_context returns status="ESCALATE_HUMAN" for missing intent, material scope change, policy conflict, or new authority requested
  automatic_escalation_status: DEFERRED (Validator classifies status; automatic workflow continuation engine deferred)

CORRECTION_10_REVISION:
  revision_history_context: Steward planning boundary
  revision_order_status: STRUCTURAL_MODEL_IMPLEMENTED (unit_revision normalized to "rev-1" or non-negative integer)

CORRECTION_11_SERIALIZATION_AND_LEGACY:
  serialization_signature: serialize_approved_unit_plan(plan: ApprovedUnitPlan) -> bytes
  deserialization_signature: deserialize_approved_unit_plan(payload: bytes | str) -> ApprovedUnitPlan
  dict_input_status: REJECTED (TypeError)
  legacy_migration_status: COMPLETE (Legacy unit plans parse cleanly without gaining broad file authority)

CORRECTION_12_TEST_MATRIX:
  final_requirement_test_matrix:
    - exact_15_dataclass_fields: test_approved_unit_plan.py::test_gate_a_exact_15_dataclass_fields (PASS)
    - exact_15_field_schema_and_types: test_approved_unit_plan.py::test_gate_a_exact_15_field_schema_and_types (PASS)
    - revision_integer_normalization: test_approved_unit_plan.py::test_gate_a_revision_integer_normalization (PASS)
    - contextual_file_mutation_allowed_paths: test_approved_unit_plan.py::test_contextual_validator_file_mutation_allowed_paths (PASS)
    - path_validation_rejections: test_approved_unit_plan.py::test_gate_a_path_validation_traversal_and_absolute_rejections (PASS)
    - prohibited_allowed_overlap_rejection: test_approved_unit_plan.py::test_gate_a_prohibited_and_allowed_path_overlap_rejection (PASS)
    - self_dependency_rejection: test_approved_unit_plan.py::test_gate_a_self_dependency_rejection (PASS)
    - dataclass_immutability: test_approved_unit_plan.py::test_gate_a_dataclass_immutability (PASS)
    - contextual_envelope_and_dependency_binding: test_approved_unit_plan.py::test_contextual_validator_execution_envelope_and_dependency_binding (PASS)
    - strict_serialization_roundtrip: test_approved_unit_plan.py::test_gate_d_strict_serialization_and_deserialization_roundtrip (PASS)
    - deserialization_rejections: test_approved_unit_plan.py::test_gate_d_deserialization_rejections (PASS)

CORRECTION_13_COMPLETION_CLASSIFICATION:
  approved_unit_plan_model_status: COMPLETE
  path_validation_status: COMPLETE
  file_mutation_context_status: CONTEXTUAL_VALIDATOR_IMPLEMENTED
  governance_reference_status: COMPLETE (NON_AUTHORIZING)
  validation_result_status: COMPLETE
  escalation_classification_status: VALIDATOR_IMPLEMENTED
  revision_structural_status: COMPLETE
  serialization_status: COMPLETE
  phase_2e_completion_status: MODEL_AND_CONTEXTUAL_VALIDATOR_COMPLETE

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

CURRENT_WORKING_TREE_STATUS: DIRTY (Worktree contains uncommitted Phase 2B/2C/2D/2E files)
TRACKED_MODIFIED_PATHS:
  - orchestra_runtime/__init__.py
  - orchestra_runtime/adapters.py
  - orchestra_runtime/capabilities.py
  - orchestra_runtime/interfaces.py
  - orchestra_runtime/lifecycle.py
  - orchestra_runtime/models.py
  - orchestra_runtime/services.py
  - tests/runtime/test_adapter_contracts.py
UNTRACKED_PATHS:
  - docs/artificer/external-sources/SPEC_KITTY_PHASE_2B1_HANDOFF.md
  - docs/artificer/external-sources/SPEC_KITTY_PHASE_2B23_HANDOFF.md
  - docs/artificer/external-sources/SPEC_KITTY_PHASE_2B31_CORRECTION_HANDOFF.md
  - docs/artificer/external-sources/SPEC_KITTY_PHASE_2C123_HANDOFF.md
  - docs/artificer/external-sources/SPEC_KITTY_PHASE_2C31_CORRECTION_HANDOFF.md
  - docs/artificer/external-sources/SPEC_KITTY_PHASE_2C32_CORRECTION_HANDOFF.md
  - docs/artificer/external-sources/SPEC_KITTY_PHASE_2C33_CORRECTION_HANDOFF.md
  - docs/artificer/external-sources/SPEC_KITTY_PHASE_2D123_HANDOFF.md
  - docs/artificer/external-sources/SPEC_KITTY_PHASE_2D31_CORRECTION_HANDOFF.md
  - docs/artificer/external-sources/SPEC_KITTY_PHASE_2D32_CORRECTION_HANDOFF.md
  - docs/artificer/external-sources/SPEC_KITTY_PHASE_2E1234_HANDOFF.md
  - docs/artificer/external-sources/SPEC_KITTY_PHASE_2E41_CORRECTION_HANDOFF.md
  - orchestra_runtime/correlation.py
  - orchestra_runtime/retrospective.py
  - orchestra_runtime/serialization.py
  - tests/runtime/test_approved_unit_plan.py
  - tests/runtime/test_correlation.py
  - tests/runtime/test_retrospective.py
  - tests/runtime/test_runtime_envelope.py

STAGED_PATHS: none
CHANGED_PATHS: 25 paths
UNEXPECTED_PATHS: none

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

COMMIT_STATUS: NOT_COMMITTED
PUSH_STATUS: NOT_PUSHED
PULL_REQUEST_STATUS: NOT_CREATED

SOURCE_INDEPENDENCE_RESULT: Verified (Zero external code copied; expressed as original Orchestra-native implementation)
DRIFT_CHECK_RESULT: PASS (Zero design drift from docs/project/ORCHESTRA_UNIT_RECORD_EXTENSION.md)
BLOCKERS: none

PHASE_2E_COMPLETION_STATUS: MODEL_AND_CONTEXTUAL_VALIDATOR_COMPLETE
PHASE_2F_READINESS: Ready for maintainer review and explicit Phase 2F authorization.

MAINTAINER_DECISIONS_REQUIRED:
  1. Review Candidate Phase 2E.4.1 correction handoff and implementation in worktree C:\conductor\.tmp\spec-kitty-derived-runtime.
  2. Decide whether to grant authorization for Candidate Phase 2F.

NEXT_AUTHORIZED_ACTION:
  Stop and await maintainer review and explicit Phase 2F authorization.
```
