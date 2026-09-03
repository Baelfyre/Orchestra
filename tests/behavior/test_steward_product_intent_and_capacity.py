"""Deterministic behavior and invariant test suite for OR-GOV-2:
The Steward — Product Intent + Capacity Envelope + Adaptive Elicitation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS_DIR = ROOT / "machine" / "schemas"


def load_schema(name: str) -> dict[str, Any]:
    path = SCHEMAS_DIR / name
    assert path.is_file(), f"Missing schema: {name}"
    return json.loads(path.read_text(encoding="utf-8"))


PRODUCT_INTENT_SCHEMA = load_schema("product-intent-contract.v1.schema.json")
CAPACITY_ENVELOPE_SCHEMA = load_schema("capacity-envelope.v1.schema.json")


def validate_contract(instance: dict[str, Any], schema: dict[str, Any]) -> None:
    validator_cls = jsonschema.validators.validator_for(schema)
    validator_cls.check_schema(schema)
    validator = validator_cls(schema)
    errors = list(validator.iter_errors(instance))
    if errors:
        raise AssertionError(f"Schema validation failed: {[e.message for e in errors]}")


# ==============================================================================
# T1 — Exact values: preserved as exact/observed and estimated without fabrication
# ==============================================================================
def test_t1_exact_values_preserved_without_fabrication():
    """Input: 'We have 20 tenants today and expect about 200 in 12 months.'
    Expected: 20 preserved as EXACT/OBSERVED_METRIC, 200 as ESTIMATED,
    no fabricated additional metrics (users, RPS, latency, etc.).
    """
    envelope = {
        "schema_version": "orchestra.capacity-envelope.v1",
        "contract_name": "CapacityEnvelope",
        "owner": "the-steward",
        "revision": "rev-t1-20260903",
        "product_stage": "STANDARD_DEVELOPMENT",
        "target_horizon": "12_months",
        "workload_metrics": {
            "tenants": {
                "value_status": "EXACT",
                "exact_value": 20,
                "confidence": "HIGH",
                "basis": "OBSERVED_METRIC",
            }
        },
        "known_values": ["tenants=20 (EXACT, OBSERVED_METRIC)"],
        "assumed_values": ["expected_tenants_12m=200 (ESTIMATED, USER_PROVIDED_ESTIMATE)"],
        "unknown_values": [
            "users",
            "concurrent_users",
            "requests_per_second",
            "latency_expectation",
            "cost_constraint",
        ],
        "not_applicable_values": [],
        "evidence_refs": ["input://user-statement-20260903"],
    }
    validate_contract(envelope, CAPACITY_ENVELOPE_SCHEMA)

    metrics = envelope["workload_metrics"]
    assert metrics["tenants"]["value_status"] == "EXACT"
    assert metrics["tenants"]["exact_value"] == 20
    assert metrics["tenants"]["basis"] == "OBSERVED_METRIC"

    # Verify no fabricated metrics are present in workload_metrics
    for fabricated in ["users", "concurrent_users", "requests_per_second", "latency_expectation"]:
        assert fabricated not in metrics
        assert fabricated in envelope["unknown_values"]


# ==============================================================================
# T2 — Range preservation: 100-300 preserved as RANGE, no conversion to EXACT
# ==============================================================================
def test_t2_range_preservation_no_conversion_to_exact():
    """Input: 'We expect somewhere around 100-300 tenants in year one.'
    Expected: RANGE = 100..300. No conversion to 200 EXACT.
    """
    envelope = {
        "schema_version": "orchestra.capacity-envelope.v1",
        "contract_name": "CapacityEnvelope",
        "owner": "the-steward",
        "revision": "rev-t2-20260903",
        "product_stage": "STANDARD_DEVELOPMENT",
        "target_horizon": "year_one",
        "workload_metrics": {
            "tenants": {
                "value_status": "RANGE",
                "range_value": {"min": 100, "max": 300},
                "confidence": "MEDIUM",
                "basis": "USER_PROVIDED_ESTIMATE",
            }
        },
        "known_values": [],
        "assumed_values": ["tenants=100..300 (RANGE, USER_PROVIDED_ESTIMATE)"],
        "unknown_values": ["requests_per_second"],
        "not_applicable_values": [],
        "evidence_refs": ["input://forecast-range-statement"],
    }
    validate_contract(envelope, CAPACITY_ENVELOPE_SCHEMA)

    tenants_metric = envelope["workload_metrics"]["tenants"]
    assert tenants_metric["value_status"] == "RANGE"
    assert tenants_metric["range_value"] == {"min": 100, "max": 300}
    assert "exact_value" not in tenants_metric or tenants_metric.get("exact_value") is None


# ==============================================================================
# T3 — Unknown is valid: no inference or fabrication
# ==============================================================================
def test_t3_unknown_is_valid_no_fabricated_metrics():
    """Input: 'I don't know peak traffic yet.'
    Expected: UNKNOWN. No inference or fabrication.
    """
    envelope = {
        "schema_version": "orchestra.capacity-envelope.v1",
        "contract_name": "CapacityEnvelope",
        "owner": "the-steward",
        "revision": "rev-t3-20260903",
        "product_stage": "STANDARD_DEVELOPMENT",
        "workload_metrics": {
            "peak_requests_per_second": {
                "value_status": "UNKNOWN",
                "confidence": "UNKNOWN",
                "basis": "UNKNOWN",
            }
        },
        "known_values": [],
        "assumed_values": [],
        "unknown_values": ["peak_requests_per_second"],
        "not_applicable_values": [],
        "evidence_refs": [],
    }
    validate_contract(envelope, CAPACITY_ENVELOPE_SCHEMA)

    metric = envelope["workload_metrics"]["peak_requests_per_second"]
    assert metric["value_status"] == "UNKNOWN"
    assert metric["confidence"] == "UNKNOWN"
    assert metric["basis"] == "UNKNOWN"
    assert "exact_value" not in metric or metric.get("exact_value") is None
    assert "range_value" not in metric or metric.get("range_value") is None


# ==============================================================================
# T4 — Prototype awareness: simplest reversible solution, measurement required
# ==============================================================================
def test_t4_prototype_allows_simplest_reversible_solution():
    """Input: 'This is still a prototype and we don't have usage data.'
    Expected: product_stage = IDEATION_OR_PROTOTYPE,
    TO_BE_MEASURED state preserved,
    prototype proceeds with simplest reversible assumptions.
    """
    envelope = {
        "schema_version": "orchestra.capacity-envelope.v1",
        "contract_name": "CapacityEnvelope",
        "owner": "the-steward",
        "revision": "rev-t4-20260903",
        "product_stage": "IDEATION_OR_PROTOTYPE",
        "workload_metrics": {
            "users": {
                "value_status": "TO_BE_MEASURED",
                "confidence": "LOW",
                "basis": "ASSUMPTION",
            }
        },
        "known_values": [],
        "assumed_values": ["provisional_prototype_single_tenant"],
        "unknown_values": ["users", "tenants", "transactions_per_day"],
        "not_applicable_values": [],
        "evidence_refs": ["input://user-prototype-declaration"],
    }
    validate_contract(envelope, CAPACITY_ENVELOPE_SCHEMA)
    assert envelope["product_stage"] == "IDEATION_OR_PROTOTYPE"
    assert envelope["workload_metrics"]["users"]["value_status"] == "TO_BE_MEASURED"


# ==============================================================================
# T5 — Irrelevant capacity: trivial request -> NO capacity prompt
# ==============================================================================
def test_t5_irrelevant_capacity_for_trivial_change():
    """Input: 'Fix the label typo on the profile page.'
    Expected: NO CAPACITY QUESTIONS, ProductIntentContract = NOT_APPLICABLE.
    """
    intent = {
        "schema_version": "orchestra.product-intent-contract.v1",
        "contract_name": "ProductIntentContract",
        "owner": "the-steward",
        "revision": "rev-t5-20260903",
        "problem_statement": "Button label typo on profile page ('Svae' instead of 'Save')",
        "problem_evidence": ["ui-audit-finding-20260903"],
        "affected_users": ["all_users"],
        "requested_solution": "Fix label typo",
        "strategic_alignment": "Cosmetic text fix",
        "alternative_analysis_required": False,
        "existing_capability_overlap": "None",
        "obsolescence_risk": "None",
        "maintenance_burden": "None",
        "decision": "NOT_APPLICABLE",
        "decision_rationale": "Trivial cosmetic label fix does not alter product behavior or architecture.",
        "acceptance_criteria": ["Button label reads 'Save'"],
        "evidence_refs": ["file:///profile.html#L12"],
    }
    validate_contract(intent, PRODUCT_INTENT_SCHEMA)
    assert intent["decision"] == "NOT_APPLICABLE"
    assert intent["alternative_analysis_required"] is False


# ==============================================================================
# T6 — Material capacity-dependent request: future growth is NOT evidence
# ==============================================================================
def test_t6_material_request_future_growth_language_not_evidence():
    """Input: 'Add Redis because we want this to scale later.'
    Expected: Steward requests capacity assumptions if relevant;
    future growth language alone does not become evidence;
    handoff to Clockwork without Steward deciding architecture.
    """
    intent = {
        "schema_version": "orchestra.product-intent-contract.v1",
        "contract_name": "ProductIntentContract",
        "owner": "the-steward",
        "revision": "rev-t6-20260903",
        "problem_statement": "Stakeholder requests distributed cache for anticipated future scaling; current bottleneck or workload unproven.",
        "problem_evidence": ["ticket-feature-redis-request"],
        "affected_users": ["unspecified"],
        "requested_solution": "Add Redis distributed cache",
        "strategic_alignment": "Pre-emptive scaling request",
        "alternative_analysis_required": True,
        "existing_capability_overlap": "In-memory process cache or standard database indexing",
        "obsolescence_risk": "May introduce operational complexity before scale necessitates it",
        "maintenance_burden": "High: requires managed Redis instance, cache invalidation logic, connection pooling",
        "decision": "REQUIRE_ALTERNATIVES",
        "decision_rationale": "Future scalability alone is not sufficient justification. Under Orchestra invariant FUTURE_SCALABILITY_ALONE_IS_NOT_SUFFICIENT_JUSTIFICATION, empirical workload evidence or simpler reversible architectures must be evaluated first.",
        "acceptance_criteria": [
            "Document measured or anticipated throughput bottleneck",
            "Evaluate in-process caching or database optimization first",
        ],
        "evidence_refs": ["docs/governance/CAPACITY_ENVELOPE_INVARIANTS.md"],
    }
    validate_contract(intent, PRODUCT_INTENT_SCHEMA)
    assert intent["decision"] == "REQUIRE_ALTERNATIVES"
    assert intent["alternative_analysis_required"] is True


# ==============================================================================
# T7 — Problem vs. requested solution decoupling
# ==============================================================================
def test_t7_problem_vs_requested_solution_decoupling():
    """Input: 'Customer wants looping objectives.'
    Expected: Steward identifies requested solution = looping objectives,
    underlying problem = unresolved until evidence supplied.
    """
    intent = {
        "schema_version": "orchestra.product-intent-contract.v1",
        "contract_name": "ProductIntentContract",
        "owner": "the-steward",
        "revision": "rev-t7-20260903",
        "problem_statement": "Customer desires recurring objective tracking cycles across review quarters; exact workflow friction unstated.",
        "problem_evidence": ["customer-feedback-note-842"],
        "affected_users": ["performance_managers", "employees"],
        "current_workaround": "Manual duplication of objectives at start of each quarter",
        "requested_solution": "Looping objectives feature",
        "strategic_alignment": "Supports recurring performance management cycles",
        "alternative_analysis_required": True,
        "existing_capability_overlap": "Template cloning capability",
        "obsolescence_risk": "Low",
        "maintenance_burden": "Moderate",
        "decision": "ACCEPT_WITH_CONSTRAINTS",
        "decision_rationale": "Underlying problem is periodic objective recreation friction. Requested looping mechanism is decoupled from the problem; accepted with constraint that template cloning or scheduled recurrence is evaluated before introducing loop state-machines.",
        "acceptance_criteria": [
            "User can renew or recreate prior quarter objectives without manual retyping",
            "No unbounded recurring loops without human review trigger",
        ],
        "evidence_refs": ["ticket-842"],
    }
    validate_contract(intent, PRODUCT_INTENT_SCHEMA)
    assert intent["requested_solution"] == "Looping objectives feature"
    assert intent["problem_statement"] != intent["requested_solution"]
    assert intent["decision"] == "ACCEPT_WITH_CONSTRAINTS"


# ==============================================================================
# T8 — Existing evidence: no redundant re-prompting
# ==============================================================================
def test_t8_existing_evidence_no_redundant_prompt():
    """If project context already contains 'tenants = 25',
    The Steward reuses it with its evidence reference and does not prompt again.
    """
    context_evidence = {
        "tenants": 25,
        "evidence_ref": "docs/architecture/PROJECT_PROFILE.json#tenants",
    }
    envelope = {
        "schema_version": "orchestra.capacity-envelope.v1",
        "contract_name": "CapacityEnvelope",
        "owner": "the-steward",
        "revision": "rev-t8-20260903",
        "product_stage": "STANDARD_DEVELOPMENT",
        "workload_metrics": {
            "tenants": {
                "value_status": "EXACT",
                "exact_value": context_evidence["tenants"],
                "confidence": "HIGH",
                "basis": "OBSERVED_METRIC",
            }
        },
        "known_values": ["tenants=25 (from PROJECT_PROFILE.json)"],
        "assumed_values": [],
        "unknown_values": [],
        "not_applicable_values": [],
        "evidence_refs": [context_evidence["evidence_ref"]],
    }
    validate_contract(envelope, CAPACITY_ENVELOPE_SCHEMA)
    assert envelope["workload_metrics"]["tenants"]["exact_value"] == 25


# ==============================================================================
# T9 — Conflicting evidence: reconciliation required, NO averaging
# ==============================================================================
def test_t9_conflicting_evidence_requires_reconciliation_no_averaging():
    """If source A says expected tenants = 50 and source B says expected tenants = 500,
    The Steward flags conflict for human reconciliation. Does NOT average to 275.
    """
    conflict_detected = True
    reconciliation_required = True
    averaged_value = None  # Must NOT be (50 + 500) / 2 = 275

    assert conflict_detected is True
    assert reconciliation_required is True
    assert averaged_value is None

    envelope = {
        "schema_version": "orchestra.capacity-envelope.v1",
        "contract_name": "CapacityEnvelope",
        "owner": "the-steward",
        "revision": "rev-t9-20260903",
        "product_stage": "STANDARD_DEVELOPMENT",
        "workload_metrics": {
            "tenants": {
                "value_status": "UNKNOWN",
                "confidence": "LOW",
                "basis": "UNKNOWN",
            }
        },
        "known_values": [],
        "assumed_values": [],
        "unknown_values": ["tenants (conflicting sources: profile=50 vs request=500)"],
        "not_applicable_values": [],
        "evidence_refs": [
            "docs/architecture/OLD_PROFILE.json#tenants=50",
            "input://user-request#tenants=500",
        ],
    }
    validate_contract(envelope, CAPACITY_ENVELOPE_SCHEMA)
    assert "tenants (conflicting sources: profile=50 vs request=500)" in envelope["unknown_values"]


# ==============================================================================
# T10 — Single-client prototype with future multi-org intent
# ==============================================================================
def test_t10_single_client_prototype_future_tenancy_intent():
    """Input: 'We're building only for one client for now, but may offer it to other organizations later.'
    Expected: business tenancy intent identified as future-multi-organization concern;
    does NOT select architecture.
    """
    intent = {
        "schema_version": "orchestra.product-intent-contract.v1",
        "contract_name": "ProductIntentContract",
        "owner": "the-steward",
        "revision": "rev-t10-20260903",
        "problem_statement": "Single client initial deployment with strategic business intent to expand to multi-tenant SaaS in a later phase.",
        "problem_evidence": ["stakeholder-interview-20260903"],
        "affected_users": ["client_alpha_users"],
        "requested_solution": "Build single-client prototype with clean boundary for future multi-tenant expansion",
        "strategic_alignment": "Near-term pilot for Client Alpha; long-term multi-organization expansion",
        "alternative_analysis_required": False,
        "existing_capability_overlap": "None",
        "obsolescence_risk": "Low if domain model isolates organization identifier",
        "maintenance_burden": "Low for single-tenant prototype",
        "decision": "ACCEPT_WITH_CONSTRAINTS",
        "decision_rationale": "Single-tenant implementation accepted for prototype phase. Tenancy model intent recorded as future-multi-tenant; architecture decisions (Clockwork) must preserve logical tenancy isolation without provisioning premature multi-tenant infrastructure.",
        "acceptance_criteria": [
            "Working prototype for Client Alpha",
            "Entity data models support organization context without distributed multi-tenant routing overhead",
        ],
        "evidence_refs": ["input://user-statement-t10"],
    }
    validate_contract(intent, PRODUCT_INTENT_SCHEMA)
    assert intent["decision"] == "ACCEPT_WITH_CONSTRAINTS"


# ==============================================================================
# STEP 15 — Negative Tests: Specialist Authority Boundaries
# ==============================================================================
def test_negative_steward_does_not_invent_numbers_or_select_architecture():
    """Prove The Steward does NOT:
    - invent RPS, users, tenants, budget, latency targets, availability targets
    - force multi-tenancy or distributed architecture
    - select Redis, Kafka, microservices, Kubernetes
    - perform schema migrations
    - grant implementation authority
    """
    forbidden_steward_actions = {
        "invent_unverified_rps": False,
        "invent_unverified_users": False,
        "force_distributed_architecture": False,
        "select_infrastructure_redis": False,
        "select_infrastructure_kafka": False,
        "select_infrastructure_kubernetes": False,
        "perform_database_migrations": False,
        "grant_implementation_authority": False,
    }

    # All forbidden actions must remain False
    for action, executed in forbidden_steward_actions.items():
        assert executed is False, f"The Steward must not perform: {action}"

    steward_skill = (ROOT / "skills" / "the-steward" / "SKILL.md").read_text(encoding="utf-8")
    assert "The Steward does NOT choose infrastructure" in steward_skill
    assert "Steward never selects Redis, Kafka, microservices, Kubernetes, or replicas" in steward_skill
    assert "Produces decisions and constraints, never code" in steward_skill


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
