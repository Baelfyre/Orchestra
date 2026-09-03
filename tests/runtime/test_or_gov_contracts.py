"""Tests for OR-GOV-1 Shared Machine Contracts and Schemas.

Proves:
- All 7 schemas conform to Draft 2020-12
- CapacityEnvelope supports exact, range, observed, estimated, UNKNOWN, TO_BE_MEASURED, and NOT_APPLICABLE
- Unknown values are not treated as validation errors
- ProductIntentContract decouples problem evidence from requested_solution
- ArchitectureComplexityDecision validates complexity categories, scale postures, and rejects future scalability alone
- MigrationRiskContract is engine-agnostic and supports unknown production parameters
- ArchitectureGovernanceIntake validates all intake classifier enums
- ArchitectureValidationContract distinguishes PROVEN, NOT_PROVEN, NOT_REQUIRED, and FAILED
- ProjectArchitectureGovernanceProfile supports all tenancy models and does not enforce global numeric thresholds
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from jsonschema import Draft202012Validator
import pytest

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS_DIR = ROOT / "machine" / "schemas"

SCHEMA_FILES: dict[str, str] = {
    "CapacityEnvelope": "capacity-envelope.v1.schema.json",
    "ProductIntentContract": "product-intent-contract.v1.schema.json",
    "ArchitectureComplexityDecision": "architecture-complexity-decision.v1.schema.json",
    "MigrationRiskContract": "migration-risk-contract.v1.schema.json",
    "ArchitectureGovernanceIntake": "architecture-governance-intake.v1.schema.json",
    "ArchitectureValidationContract": "architecture-validation-contract.v1.schema.json",
    "ProjectArchitectureGovernanceProfile": "project-architecture-governance-profile.v1.schema.json",
}


def load_schema(contract_name: str) -> dict[str, Any]:
    filename = SCHEMA_FILES.get(contract_name)
    if not filename:
        raise ValueError(f"Unknown contract: {contract_name!r}")
    schema_path = SCHEMAS_DIR / filename
    return json.loads(schema_path.read_text(encoding="utf-8"))


def get_validator(contract_name: str) -> Draft202012Validator:
    schema = load_schema(contract_name)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def validate_contract_schema(contract_name: str, instance: dict[str, Any]) -> list[str]:
    validator = get_validator(contract_name)
    return [err.message for err in validator.iter_errors(instance)]


def validate_architecture_complexity_decision(instance: dict[str, Any]) -> list[str]:
    """Validate ArchitectureComplexityDecision with schema and semantic invariants.

    Invariant: FUTURE_SCALABILITY_ALONE_IS_NOT_SUFFICIENT_JUSTIFICATION.
    Future scalability language without recognized justification and evidence is rejected.
    """
    errors = validate_contract_schema("ArchitectureComplexityDecision", instance)
    if errors:
        return errors

    justifications = instance.get("justification_categories", [])
    if not justifications:
        errors.append("MISSING_JUSTIFICATION_CATEGORIES: At least one recognized justification category is required.")

    req_driver = str(instance.get("requirement_driver", "")).lower()
    decision = instance.get("decision")
    if decision in ("ACCEPT", "ACCEPT_WITH_CONSTRAINTS"):
        speculative_terms = (
            "might need it later",
            "future scalability alone",
            "future scalability",
            "just in case",
            "in case we need it",
        )
        if any(term in req_driver for term in speculative_terms):
            evidence_based_categories = {
                "MEASURED_PERFORMANCE_BOTTLENECK",
                "CAPACITY_THRESHOLD",
                "SECURITY_REQUIREMENT",
                "RELIABILITY_REQUIREMENT",
                "ISOLATION_REQUIREMENT",
                "COMPLIANCE_REQUIREMENT",
            }
            has_evidence_category = any(j in evidence_based_categories for j in justifications)
            has_evidence_ref = bool(instance.get("evidence_refs"))
            if not (has_evidence_category and has_evidence_ref):
                errors.append(
                    "FUTURE_SCALABILITY_ALONE_INSUFFICIENT: Material complexity cannot be accepted "
                    "on future growth speculation alone without an empirical bottleneck or capacity threshold justification and evidence."
                )

    return errors


@pytest.mark.parametrize(
    "contract_name",
    [
        "CapacityEnvelope",
        "ProductIntentContract",
        "ArchitectureComplexityDecision",
        "MigrationRiskContract",
        "ArchitectureGovernanceIntake",
        "ArchitectureValidationContract",
        "ProjectArchitectureGovernanceProfile",
    ],
)
def test_schema_is_valid_draft_2020_12(contract_name: str) -> None:
    schema = load_schema(contract_name)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    Draft202012Validator.check_schema(schema)


# -----------------------------------------------------------------------------
# 1. CapacityEnvelope Tests
# -----------------------------------------------------------------------------


def test_capacity_envelope_exact_and_range_values() -> None:
    envelope = {
        "schema_version": "orchestra.capacity-envelope.v1",
        "contract_name": "CapacityEnvelope",
        "owner": "the-steward",
        "revision": "rev-001",
        "product_stage": "STANDARD_DEVELOPMENT",
        "target_horizon": "6-12 months",
        "workload_metrics": {
            "tenants": {
                "value_status": "EXACT",
                "exact_value": 20,
                "confidence": "HIGH",
                "basis": "OBSERVED_METRIC",
            },
            "concurrent_users": {
                "value_status": "RANGE",
                "range_value": {"min": 50, "max": 150},
                "confidence": "MEDIUM",
                "basis": "USER_PROVIDED_ESTIMATE",
            },
            "messages_per_day": {
                "value_status": "OBSERVED",
                "exact_value": 5000,
                "confidence": "HIGH",
                "basis": "OBSERVED_METRIC",
            },
            "requests_per_second": {
                "value_status": "ESTIMATED",
                "exact_value": 25.5,
                "confidence": "MEDIUM",
                "basis": "HISTORICAL_DATA",
            },
        },
        "known_values": ["tenants", "messages_per_day"],
        "assumed_values": ["concurrent_users", "requests_per_second"],
        "unknown_values": [],
        "not_applicable_values": [],
        "evidence_refs": ["metrics:production-telemetry:20260901"],
    }
    assert validate_contract_schema("CapacityEnvelope", envelope) == []


def test_capacity_envelope_unknown_and_unmeasured_values_are_valid() -> None:
    """Critical invariant: UNKNOWN, TO_BE_MEASURED, and NOT_APPLICABLE are valid states, not failures."""
    envelope = {
        "schema_version": "orchestra.capacity-envelope.v1",
        "contract_name": "CapacityEnvelope",
        "owner": "the-steward",
        "revision": "rev-002",
        "product_stage": "IDEATION_OR_PROTOTYPE",
        "workload_metrics": {
            "tenants": {
                "value_status": "UNKNOWN",
                "confidence": "UNKNOWN",
                "basis": "UNKNOWN",
            },
            "peak_requests_per_second": {
                "value_status": "TO_BE_MEASURED",
                "confidence": "LOW",
                "basis": "ASSUMPTION",
            },
            "storage_growth": {
                "value_status": "NOT_APPLICABLE",
            },
        },
        "unknown_values": ["tenants"],
        "not_applicable_values": ["storage_growth"],
    }
    assert validate_contract_schema("CapacityEnvelope", envelope) == []


def test_capacity_envelope_invalid_status_rejected() -> None:
    envelope = {
        "schema_version": "orchestra.capacity-envelope.v1",
        "contract_name": "CapacityEnvelope",
        "owner": "the-steward",
        "revision": "rev-003",
        "workload_metrics": {
            "tenants": {
                "value_status": "GUESS_FABRICATED",
            }
        },
    }
    errors = validate_contract_schema("CapacityEnvelope", envelope)
    assert errors, "Expected schema validation error for invalid value_status enum"


def test_capacity_envelope_malformed_range_rejected() -> None:
    envelope = {
        "schema_version": "orchestra.capacity-envelope.v1",
        "contract_name": "CapacityEnvelope",
        "owner": "the-steward",
        "revision": "rev-004",
        "workload_metrics": {
            "tenants": {
                "value_status": "RANGE",
                "range_value": {"min": 50},  # missing 'max'
            }
        },
    }
    errors = validate_contract_schema("CapacityEnvelope", envelope)
    assert errors, "Expected schema validation error for range missing max"


# -----------------------------------------------------------------------------
# 2. ProductIntentContract Tests
# -----------------------------------------------------------------------------


def test_product_intent_decoupled_from_requested_solution() -> None:
    """Problem may exist and be documented separately from requested_solution."""
    record_without_solution = {
        "schema_version": "orchestra.product-intent-contract.v1",
        "contract_name": "ProductIntentContract",
        "owner": "the-steward",
        "revision": "rev-pi-1",
        "problem_statement": "Users cannot search past messages efficiently under high volume.",
        "problem_evidence": ["ticket:BUG-4091", "feedback:quarterly-survey-2026"],
        "affected_users": ["Support Agents", "Team Admins"],
        "decision": "REQUIRE_ALTERNATIVES",
        "decision_rationale": "Customer requested full-text Elasticsearch cluster; need simpler Postgres FTS alternative analysis first.",
        "acceptance_criteria": ["Search response under 500ms for 95th percentile query"],
    }
    assert validate_contract_schema("ProductIntentContract", record_without_solution) == []

    record_with_solution = dict(record_without_solution)
    record_with_solution["requested_solution"] = "Deploy a managed Elasticsearch cluster with custom sync pipeline"
    record_with_solution["decision"] = "ACCEPT_WITH_CONSTRAINTS"
    assert validate_contract_schema("ProductIntentContract", record_with_solution) == []


@pytest.mark.parametrize(
    "decision",
    [
        "ACCEPT_REQUESTED_SOLUTION",
        "ACCEPT_WITH_CONSTRAINTS",
        "REQUIRE_ALTERNATIVES",
        "DEFER",
        "REJECT",
        "INSUFFICIENT_CONTEXT",
        "NOT_APPLICABLE",
    ],
)
def test_product_intent_decision_enums(decision: str) -> None:
    record = {
        "schema_version": "orchestra.product-intent-contract.v1",
        "contract_name": "ProductIntentContract",
        "owner": "the-steward",
        "revision": "rev-pi-enum",
        "problem_statement": "Order notification delays during peak sale events.",
        "problem_evidence": ["logs:timeout-spikes"],
        "affected_users": ["End Users"],
        "decision": decision,
        "decision_rationale": f"Disposition evaluated as {decision}.",
    }
    assert validate_contract_schema("ProductIntentContract", record) == []


def test_product_intent_invalid_decision_rejected() -> None:
    record = {
        "schema_version": "orchestra.product-intent-contract.v1",
        "contract_name": "ProductIntentContract",
        "owner": "the-steward",
        "revision": "rev-pi-bad",
        "problem_statement": "Test problem",
        "problem_evidence": ["test"],
        "affected_users": ["all"],
        "decision": "AUTO_IMPLEMENT_NOW",
        "decision_rationale": "Invalid enum test",
    }
    assert validate_contract_schema("ProductIntentContract", record)


# -----------------------------------------------------------------------------
# 3. ArchitectureComplexityDecision Tests
# -----------------------------------------------------------------------------


def test_architecture_complexity_decision_valid_scale_postures() -> None:
    decision_scale_ready = {
        "schema_version": "orchestra.architecture-complexity-decision.v1",
        "contract_name": "ArchitectureComplexityDecision",
        "owner": "clockwork",
        "revision": "rev-acd-1",
        "requested_change": "Introduce message queue interface with in-process memory adapter",
        "current_architecture": "Direct in-process sync calls",
        "requirement_driver": "Avoid blocking HTTP request thread on email notification dispatch",
        "complexity_added": ["queue"],
        "justification_categories": ["CURRENT_FUNCTIONAL_REQUIREMENT"],
        "scale_posture_after": "SCALE_READY",
        "simpler_alternatives": ["Background thread pool in existing process"],
        "decision": "ACCEPT",
        "constraints": ["Keep in-process broker default until throughput measurements require Redis/RabbitMQ"],
    }
    assert validate_contract_schema("ArchitectureComplexityDecision", decision_scale_ready) == []

    decision_scale_provisioned = dict(decision_scale_ready)
    decision_scale_provisioned["scale_posture_after"] = "SCALE_PROVISIONED"
    decision_scale_provisioned["justification_categories"] = ["MEASURED_PERFORMANCE_BOTTLENECK"]
    assert validate_contract_schema("ArchitectureComplexityDecision", decision_scale_provisioned) == []


def test_architecture_complexity_future_scalability_alone_rejected() -> None:
    """Proves: Invariant FUTURE_SCALABILITY_ALONE_IS_NOT_SUFFICIENT_JUSTIFICATION."""
    premature_decision = {
        "schema_version": "orchestra.architecture-complexity-decision.v1",
        "contract_name": "ArchitectureComplexityDecision",
        "owner": "clockwork",
        "revision": "rev-acd-bad",
        "requested_change": "Deploy Redis cluster and Kubernetes orchestrator",
        "current_architecture": "Single SQLite database with web monolith",
        "requirement_driver": "Add Redis because we might need it later for future scalability alone",
        "complexity_added": ["cache", "orchestrator"],
        "justification_categories": ["CURRENT_FUNCTIONAL_REQUIREMENT"],
        "scale_posture_after": "SCALE_PROVISIONED",
        "simpler_alternatives": ["Maintain current in-memory cache and monolith"],
        "decision": "ACCEPT",
    }
    errors = validate_architecture_complexity_decision(premature_decision)
    assert any("FUTURE_SCALABILITY_ALONE_INSUFFICIENT" in err for err in errors)


def test_architecture_complexity_unsupported_justification_rejected() -> None:
    decision = {
        "schema_version": "orchestra.architecture-complexity-decision.v1",
        "contract_name": "ArchitectureComplexityDecision",
        "owner": "clockwork",
        "revision": "rev-acd-unsupported",
        "requested_change": "Add distributed cache",
        "current_architecture": "Monolith",
        "requirement_driver": "Tech hype",
        "complexity_added": ["cache"],
        "justification_categories": ["POPULAR_FRAMEWORK_FASHION"],
        "scale_posture_after": "SCALE_READY",
        "simpler_alternatives": ["In-memory dict"],
        "decision": "ACCEPT",
    }
    errors = validate_contract_schema("ArchitectureComplexityDecision", decision)
    assert errors, "Expected schema validation error for unsupported justification category"


# -----------------------------------------------------------------------------
# 4. MigrationRiskContract Tests
# -----------------------------------------------------------------------------


def test_migration_risk_contract_engine_agnostic_and_unknown_handling() -> None:
    """Proves: MigrationRiskContract works for any database engine and accepts unknown facts."""
    contract = {
        "schema_version": "orchestra.migration-risk-contract.v1",
        "contract_name": "MigrationRiskContract",
        "owner": "chronicler",
        "revision": "rev-mig-1",
        "database_engine": "PostgreSQL",
        "database_version": "16.2",
        "schema_revision": "20260903_add_tenant_id",
        "migration_tool": "alembic",
        "production_data": True,
        "affected_records": "UNKNOWN",
        "read_traffic": "UNKNOWN",
        "write_traffic": "UNKNOWN",
        "locking_implications": "ACCESS EXCLUSIVE lock on conversations table during column addition; nullable column required.",
        "compatibility_required": True,
        "backfill_required": True,
        "index_operation": "CREATE INDEX CONCURRENTLY",
        "migration_pattern": "EXPAND_CONTRACT",
        "deployment_sequence": ["1. Add nullable column", "2. Batched backfill", "3. Enforce NOT NULL"],
        "rollback_boundary": "Reversible prior to NOT NULL constraint enforcement",
        "risk": "HIGH",
        "human_gate_required": True,
    }
    assert validate_contract_schema("MigrationRiskContract", contract) == []


@pytest.mark.parametrize(
    "pattern",
    [
        "DIRECT",
        "EXPAND_CONTRACT",
        "BATCHED_BACKFILL",
        "DUAL_READ_WRITE",
        "ONLINE_DDL",
        "ENGINE_SPECIFIC",
        "OTHER",
    ],
)
def test_migration_risk_patterns(pattern: str) -> None:
    contract = {
        "schema_version": "orchestra.migration-risk-contract.v1",
        "contract_name": "MigrationRiskContract",
        "owner": "chronicler",
        "revision": "rev-mig-pattern",
        "database_engine": "SQLite",
        "schema_revision": "20260903_local_dev",
        "production_data": False,
        "locking_implications": "Local SQLite file lock during transaction",
        "compatibility_required": False,
        "backfill_required": False,
        "migration_pattern": pattern,
        "risk": "LOW",
        "human_gate_required": False,
    }
    assert validate_contract_schema("MigrationRiskContract", contract) == []


# -----------------------------------------------------------------------------
# 5. ArchitectureGovernanceIntake Tests
# -----------------------------------------------------------------------------


def test_architecture_governance_intake_all_classifier_enums() -> None:
    intake = {
        "schema_version": "orchestra.architecture-governance-intake.v1",
        "contract_name": "ArchitectureGovernanceIntake",
        "owner": "conductor",
        "change_materiality": "ARCHITECTURAL",
        "capacity_relevance": "KNOWN",
        "capacity_context_disposition": "SUFFICIENT",
        "complexity_delta": "MATERIAL",
        "tenancy_impact": "CONFIRMED",
        "persistence_impact": "PRODUCTION_COMPATIBILITY",
        "product_decision": "STRATEGIC_CHANGE",
        "security_impact": "MATERIAL",
        "validation_impact": "CONTRACT_DERIVED",
        "authority_notice": "Routing metadata does not create or expand authority.",
    }
    assert validate_contract_schema("ArchitectureGovernanceIntake", intake) == []


def test_architecture_governance_intake_trivial_case() -> None:
    intake = {
        "schema_version": "orchestra.architecture-governance-intake.v1",
        "contract_name": "ArchitectureGovernanceIntake",
        "owner": "conductor",
        "change_materiality": "TRIVIAL",
        "capacity_relevance": "NONE",
        "capacity_context_disposition": "NOT_REQUIRED",
        "complexity_delta": "NONE",
        "tenancy_impact": "NONE",
        "persistence_impact": "NONE",
        "product_decision": "NONE",
        "security_impact": "NONE",
        "validation_impact": "NORMAL",
    }
    assert validate_contract_schema("ArchitectureGovernanceIntake", intake) == []


# -----------------------------------------------------------------------------
# 6. ArchitectureValidationContract Tests
# -----------------------------------------------------------------------------


def test_architecture_validation_distinct_result_states() -> None:
    """Proves: PROVEN, NOT_PROVEN, NOT_REQUIRED, and FAILED are distinct machine states."""
    states = ["PROVEN", "NOT_PROVEN", "NOT_REQUIRED", "FAILED"]
    assert len(set(states)) == 4

    contract = {
        "schema_version": "orchestra.architecture-validation-contract.v1",
        "contract_name": "ArchitectureValidationContract",
        "owner": "overseer",
        "contract_refs": ["contract:acd:rev-001", "contract:capacity:rev-001"],
        "exact_revision": "rev-val-001",
        "environment_identity": "staging-runner-ubuntu-24.04",
        "functional_validation": "PROVEN",
        "capacity_validation": "NOT_PROVEN",  # Crucial distinction: NOT_PROVEN is not FAILED
        "performance_validation": "NOT_REQUIRED",
        "tenant_isolation_validation": "PROVEN",
        "migration_validation": "FAILED",
        "failure_behavior_validation": "NOT_REQUIRED",
        "compatibility_validation": "PROVEN",
        "limitations": ["No load testing harness available in staging environment"],
        "evidence_refs": ["test-run:pytest-runtime-pass"],
    }
    assert validate_contract_schema("ArchitectureValidationContract", contract) == []


# -----------------------------------------------------------------------------
# 7. ProjectArchitectureGovernanceProfile Tests
# -----------------------------------------------------------------------------


@pytest.mark.parametrize(
    "tenancy",
    [
        "SINGLE_TENANT",
        "MULTI_TENANT",
        "HYBRID",
        "UNDECIDED_BLOCKING",
        "NOT_APPLICABLE",
    ],
)
def test_project_architecture_governance_profile_tenancy_models(tenancy: str) -> None:
    profile = {
        "schema_version": "orchestra.project-architecture-governance-profile.v1",
        "contract_name": "ProjectArchitectureGovernanceProfile",
        "project_identity": "project-example",
        "project_stage": "STANDARD_DEVELOPMENT",
        "architecture_summary": "Modular monolith with PostgreSQL persistence",
        "tenancy_model": tenancy,
        "scale_posture": "SCALE_READY",
        "approved_infrastructure": ["PostgreSQL 16", "Docker"],
        "revision": "rev-prof-001",
        "evidence_refs": ["doc:adr-001"],
    }
    assert validate_contract_schema("ProjectArchitectureGovernanceProfile", profile) == []


def test_project_architecture_governance_profile_does_not_require_capacity() -> None:
    """Proves: capacity values are optional in the profile when not applicable."""
    profile = {
        "schema_version": "orchestra.project-architecture-governance-profile.v1",
        "contract_name": "ProjectArchitectureGovernanceProfile",
        "project_identity": "local-cli-tool",
        "project_stage": "IDEATION_OR_PROTOTYPE",
        "architecture_summary": "Single-binary CLI utility",
        "tenancy_model": "NOT_APPLICABLE",
        "scale_posture": "SCALE_READY",
        "approved_infrastructure": ["Local filesystem"],
        "revision": "rev-prof-cli-1",
    }
    assert validate_contract_schema("ProjectArchitectureGovernanceProfile", profile) == []
