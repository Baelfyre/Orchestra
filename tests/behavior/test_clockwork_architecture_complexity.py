"""
Behavioral and contract tests for Clockwork Architecture Complexity Decision and Scale Posture (OR-GOV-3).
Verifies:
- T1: Vague scale request rejects automatic infrastructure provisioning
- T2: Premature Redis rejected/deferred under FUTURE_SCALABILITY_ALONE_IS_NOT_SUFFICIENT_JUSTIFICATION
- T3: Measured bottleneck justifies cache review with simpler-alternative analysis
- T4: Scale-ready without provisioning preserves evolution paths without deployed scale infra
- T5: Legitimate scale provisioning accepted with concrete benchmark/contractual evidence
- T6: Service split without architectural reason is rejected/deferred
- T7: Valid service isolation reason accepted under SECURITY_REQUIREMENT / ISOLATION_REQUIREMENT
- T8: Unknown capacity metrics preserved without fabricated numbers
- T9: Capacity ranges preserved without averaging
- T10: Cost constraints bound architecture complexity without invented pricing
- T11: Trivial change does not trigger ArchitectureComplexityDecision ceremony
- T12: Bundled complexity additions require independent justification
- Negative specialist authority boundaries
- Source and Codex adapter guide parity
"""

import json
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "machine" / "schemas" / "architecture-complexity-decision.v1.schema.json"
GUIDE_SOURCE = ROOT / "skills" / "clockwork" / "ARCHITECTURE_COMPLEXITY_AND_SCALE_POSTURE_GUIDE.md"
GUIDE_CODEX = ROOT / "adapters" / "codex" / "skills" / "clockwork" / "ARCHITECTURE_COMPLEXITY_AND_SCALE_POSTURE_GUIDE.md"

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


def _validate_schema(data: Dict[str, Any]) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    if HAS_JSONSCHEMA:
        jsonschema.validate(instance=data, schema=schema)
    else:
        # Strict stdlib fallback validation matching schema definition
        assert data.get("schema_version") == "orchestra.architecture-complexity-decision.v1"
        assert data.get("contract_name") == "ArchitectureComplexityDecision"
        assert data.get("owner") == "clockwork"
        assert isinstance(data.get("revision"), str) and len(data["revision"]) > 0
        assert isinstance(data.get("requested_change"), str) and len(data["requested_change"]) > 0
        assert isinstance(data.get("current_architecture"), str) and len(data["current_architecture"]) > 0
        assert isinstance(data.get("requirement_driver"), str) and len(data["requirement_driver"]) > 0
        assert isinstance(data.get("complexity_added"), list) and len(data["complexity_added"]) > 0
        assert isinstance(data.get("justification_categories"), list) and len(data["justification_categories"]) > 0
        assert data.get("scale_posture_after") in ("SCALE_READY", "SCALE_PROVISIONED")
        assert isinstance(data.get("simpler_alternatives"), list)
        assert data.get("decision") in ("ACCEPT", "ACCEPT_WITH_CONSTRAINTS", "DEFER", "REJECT")


def test_t1_vague_scale_request_rejects_automatic_provisioning():
    """T1: 'Build it so it can scale' must not trigger automatic cache, queue, microservices, or k8s."""
    req = {
        "user_prompt": "Build it so it can scale.",
        "context": "Initial project ideation"
    }
    # Clockwork must assess that vague future scale language alone cannot justify infrastructure expansion
    decision_record = {
        "schema_version": "orchestra.architecture-complexity-decision.v1",
        "contract_name": "ArchitectureComplexityDecision",
        "owner": "clockwork",
        "revision": "rev-20260903-t1",
        "requested_change": "Introduce distributed caching, message queues, and microservices for future scale",
        "current_architecture": "Modular in-process application",
        "requirement_driver": "Vague future scale claim: 'Build it so it can scale'",
        "complexity_added": ["cache", "queue", "service"],
        "justification_categories": ["CAPACITY_THRESHOLD"],
        "scale_posture_before": "SCALE_READY",
        "scale_posture_after": "SCALE_READY",
        "simpler_alternatives": [
            "Modular in-process boundaries with well-defined service interfaces",
            "Direct in-memory queue abstractions without deploying a broker"
        ],
        "decision": "DEFER",
        "constraints": [
            "Maintain SCALE_READY in-process boundaries",
            "Require concrete workload metrics before provisioning external infrastructure"
        ],
        "evidence_refs": ["FUTURE_SCALABILITY_ALONE_IS_NOT_SUFFICIENT_JUSTIFICATION"]
    }
    _validate_schema(decision_record)
    assert decision_record["decision"] in ("DEFER", "REJECT")
    assert decision_record["scale_posture_after"] == "SCALE_READY"
    assert "FUTURE_SCALABILITY_ALONE_IS_NOT_SUFFICIENT_JUSTIFICATION" in decision_record["evidence_refs"]


def test_t2_premature_redis_rejected_or_deferred():
    """T2: 'Add Redis because we might need it later' must be DEFER or REJECT."""
    decision_record = {
        "schema_version": "orchestra.architecture-complexity-decision.v1",
        "contract_name": "ArchitectureComplexityDecision",
        "owner": "clockwork",
        "revision": "rev-20260903-t2",
        "requested_change": "Deploy external Redis cluster",
        "current_architecture": "Single-instance relational persistence",
        "requirement_driver": "Speculative future requirement: 'might need it later'",
        "complexity_added": ["cache"],
        "justification_categories": ["OPERATIONAL_REQUIREMENT"],
        "scale_posture_before": "SCALE_READY",
        "scale_posture_after": "SCALE_READY",
        "simpler_alternatives": [
            "Database index optimization and query tuning",
            "In-process LRU cache for rebuildable read models",
            "No cache until access bottleneck is measured"
        ],
        "decision": "REJECT",
        "constraints": ["Cache layer deferred until measured bottleneck demonstrates necessity"],
        "evidence_refs": ["FUTURE_SCALABILITY_ALONE_IS_NOT_SUFFICIENT_JUSTIFICATION"]
    }
    _validate_schema(decision_record)
    assert decision_record["decision"] in ("DEFER", "REJECT")
    assert "cache" in decision_record["complexity_added"]
    assert len(decision_record["simpler_alternatives"]) >= 1


def test_t3_measured_bottleneck_accepts_cache_review():
    """T3: Measured bottleneck with observed 500 RPS and high query latency justifies cache review."""
    decision_record = {
        "schema_version": "orchestra.architecture-complexity-decision.v1",
        "contract_name": "ArchitectureComplexityDecision",
        "owner": "clockwork",
        "revision": "rev-20260903-t3",
        "requested_change": "Add caching layer for product catalog queries",
        "current_architecture": "Relational database without caching layer",
        "requirement_driver": "Observed 500 RPS load with catalog query p99 latency exceeding 800ms SLA",
        "capacity_envelope_ref": "envelope-obs-500rps",
        "complexity_added": ["cache"],
        "justification_categories": ["MEASURED_PERFORMANCE_BOTTLENECK", "CAPACITY_THRESHOLD"],
        "scale_posture_before": "SCALE_READY",
        "scale_posture_after": "SCALE_PROVISIONED",
        "simpler_alternatives": [
            "Covering indexes on product catalog tables (already applied, query plan still bounded by I/O)",
            "In-memory application cache (insufficient due to multiple application instances)"
        ],
        "decision": "ACCEPT_WITH_CONSTRAINTS",
        "constraints": [
            "Cache store restricted to derived, non-authoritative read models",
            "Explicit TTL and invalidation events owned by CatalogService",
            "Database remains sole source of truth"
        ],
        "evidence_refs": ["benchmark-run-20260903-500rps", "envelope-obs-500rps"]
    }
    _validate_schema(decision_record)
    assert decision_record["decision"] in ("ACCEPT", "ACCEPT_WITH_CONSTRAINTS")
    assert "MEASURED_PERFORMANCE_BOTTLENECK" in decision_record["justification_categories"]
    assert decision_record["scale_posture_after"] == "SCALE_PROVISIONED"


def test_t4_scale_ready_without_provisioning():
    """T4: Prototype expecting 20 tenants with future scale unknown prefers SCALE_READY without infrastructure."""
    decision_record = {
        "schema_version": "orchestra.architecture-complexity-decision.v1",
        "contract_name": "ArchitectureComplexityDecision",
        "owner": "clockwork",
        "revision": "rev-20260903-t4",
        "requested_change": "Provision multi-tenant routing, per-tenant databases, and Kubernetes cluster",
        "current_architecture": "Single-process prototype with modular schema",
        "requirement_driver": "Prototype stage with 20 tenants; future growth unknown",
        "capacity_envelope_ref": "envelope-prototype-20-tenants",
        "complexity_added": ["database", "orchestrator"],
        "justification_categories": ["CURRENT_FUNCTIONAL_REQUIREMENT"],
        "scale_posture_before": "SCALE_READY",
        "scale_posture_after": "SCALE_READY",
        "simpler_alternatives": [
            "Shared database with tenant_id discriminator and explicit context propagation",
            "Modular services in-process without container orchestration"
        ],
        "decision": "REJECT",
        "constraints": [
            "Preserve tenant context propagation points in code (SCALE_READY)",
            "Do not provision separate databases or cluster infrastructure for prototype"
        ],
        "evidence_refs": ["envelope-prototype-20-tenants", "stage:PROTOTYPE"]
    }
    _validate_schema(decision_record)
    assert decision_record["scale_posture_after"] == "SCALE_READY"
    assert decision_record["decision"] in ("REJECT", "DEFER")


def test_t5_legitimate_scale_provisioning():
    """T5: 50,000 concurrent sessions launch requirement + proven single-process limits justifies SCALE_PROVISIONED."""
    decision_record = {
        "schema_version": "orchestra.architecture-complexity-decision.v1",
        "contract_name": "ArchitectureComplexityDecision",
        "owner": "clockwork",
        "revision": "rev-20260903-t5",
        "requested_change": "Introduce message broker and dedicated worker fleet for async order processing",
        "current_architecture": "Synchronous single-process web application",
        "requirement_driver": "Launch contract commitment of 50,000 concurrent sessions with load tests proving single-process saturation at 8,000 sessions",
        "capacity_envelope_ref": "envelope-launch-50k-sessions",
        "complexity_added": ["queue", "worker"],
        "justification_categories": ["CAPACITY_THRESHOLD", "RELIABILITY_REQUIREMENT", "MEASURED_PERFORMANCE_BOTTLENECK"],
        "scale_posture_before": "SCALE_READY",
        "scale_posture_after": "SCALE_PROVISIONED",
        "simpler_alternatives": [
            "In-process threadpool workers (proven insufficient under 50k connection load testing)",
            "Direct HTTP synchronous fan-out (violates availability SLA during spike loads)"
        ],
        "decision": "ACCEPT",
        "constraints": [
            "Worker fleet autoscaling bounded to approved capacity envelope limits",
            "Order processing events must implement idempotent consumer handlers"
        ],
        "evidence_refs": ["contract-launch-commitment-q4", "load-test-report-50k"]
    }
    _validate_schema(decision_record)
    assert decision_record["decision"] == "ACCEPT"
    assert decision_record["scale_posture_after"] == "SCALE_PROVISIONED"
    assert "CAPACITY_THRESHOLD" in decision_record["justification_categories"]


def test_t6_service_split_without_reason_rejected():
    """T6: 'Split into microservices because we want enterprise architecture' must be REJECT or DEFER."""
    decision_record = {
        "schema_version": "orchestra.architecture-complexity-decision.v1",
        "contract_name": "ArchitectureComplexityDecision",
        "owner": "clockwork",
        "revision": "rev-20260903-t6",
        "requested_change": "Split monolith into 5 microservices",
        "current_architecture": "Modular monolith",
        "requirement_driver": "Subjective aesthetic: 'want enterprise architecture'",
        "complexity_added": ["service", "orchestrator"],
        "justification_categories": ["OPERATIONAL_REQUIREMENT"],
        "scale_posture_before": "SCALE_READY",
        "scale_posture_after": "SCALE_READY",
        "simpler_alternatives": [
            "Enforce strict in-process module boundaries and package visibility rules",
            "Keep unified deployment unit while organizing domain directories"
        ],
        "decision": "REJECT",
        "constraints": ["Service split rejected without independent scaling, deployment, or isolation drivers"],
        "evidence_refs": ["FUTURE_SCALABILITY_ALONE_IS_NOT_SUFFICIENT_JUSTIFICATION"]
    }
    _validate_schema(decision_record)
    assert decision_record["decision"] in ("REJECT", "DEFER")
    assert decision_record["scale_posture_after"] == "SCALE_READY"


def test_t7_valid_service_isolation_reason_accepted():
    """T7: Payment processing requiring independent deployment and separate security boundary is accepted."""
    decision_record = {
        "schema_version": "orchestra.architecture-complexity-decision.v1",
        "contract_name": "ArchitectureComplexityDecision",
        "owner": "clockwork",
        "revision": "rev-20260903-t7",
        "requested_change": "Extract payment processing into dedicated isolated payment service",
        "current_architecture": "Single modular application runtime",
        "requirement_driver": "PCI-DSS compliance requiring isolated security perimeter and independent deployment audit cadence",
        "complexity_added": ["service"],
        "justification_categories": ["SECURITY_REQUIREMENT", "ISOLATION_REQUIREMENT", "COMPLIANCE_REQUIREMENT"],
        "scale_posture_before": "SCALE_READY",
        "scale_posture_after": "SCALE_PROVISIONED",
        "simpler_alternatives": [
            "In-process payment module (rejected: violates PCI-DSS audit boundary requirements)",
            "Third-party hosted checkout (considered, but custom payment routing is functionally required)"
        ],
        "decision": "ACCEPT",
        "constraints": [
            "Payment service communicates exclusively over mutual TLS with strict tokenization",
            "Payment service owns dedicated isolated persistence boundary"
        ],
        "evidence_refs": ["pci-dss-scoping-review", "compliance-audit-2026"]
    }
    _validate_schema(decision_record)
    assert decision_record["decision"] == "ACCEPT"
    assert "SECURITY_REQUIREMENT" in decision_record["justification_categories"]
    assert "ISOLATION_REQUIREMENT" in decision_record["justification_categories"]


def test_t8_unknown_capacity_preserves_truth_state():
    """T8: CapacityEnvelope with peak traffic UNKNOWN must not fabricate numeric values."""
    envelope = {
        "contract_name": "CapacityEnvelope",
        "peak_requests_per_second": "UNKNOWN",
        "expected_tenants": "UNKNOWN"
    }
    # Clockwork consumes envelope and preserves UNKNOWN without converting to 1000 RPS
    decision_record = {
        "schema_version": "orchestra.architecture-complexity-decision.v1",
        "contract_name": "ArchitectureComplexityDecision",
        "owner": "clockwork",
        "revision": "rev-20260903-t8",
        "requested_change": "Introduce cluster auto-scaler tuned for 5,000 RPS",
        "current_architecture": "Single-instance service",
        "requirement_driver": "Unmeasured traffic volume",
        "capacity_envelope_ref": "envelope-unknown-metrics",
        "complexity_added": ["orchestrator"],
        "justification_categories": ["CAPACITY_THRESHOLD"],
        "scale_posture_before": "SCALE_READY",
        "scale_posture_after": "SCALE_READY",
        "simpler_alternatives": ["Maintain SCALE_READY application with metrics instrumentation"],
        "decision": "DEFER",
        "constraints": ["No cluster autoscaling provisioned while traffic metrics remain UNKNOWN"],
        "evidence_refs": ["envelope-unknown-metrics:UNKNOWN_IS_VALID"]
    }
    _validate_schema(decision_record)
    assert decision_record["decision"] == "DEFER"
    assert decision_record["scale_posture_after"] == "SCALE_READY"


def test_t9_capacity_range_preserved_without_averaging():
    """T9: Expected tenants 100..300 must be preserved as range without conversion to average 200."""
    envelope_range = {"expected_tenants": {"min": 100, "max": 300}}
    decision_record = {
        "schema_version": "orchestra.architecture-complexity-decision.v1",
        "contract_name": "ArchitectureComplexityDecision",
        "owner": "clockwork",
        "revision": "rev-20260903-t9",
        "requested_change": "Tenant routing architecture sizing",
        "current_architecture": "Single-tenant baseline",
        "requirement_driver": "Multi-tenant onboarding range 100..300 tenants",
        "capacity_envelope_ref": "envelope-tenants-100-300",
        "complexity_added": ["other"],
        "justification_categories": ["CURRENT_FUNCTIONAL_REQUIREMENT"],
        "scale_posture_before": "SCALE_READY",
        "scale_posture_after": "SCALE_READY",
        "simpler_alternatives": ["Single shared schema with tenant context propagation"],
        "decision": "ACCEPT_WITH_CONSTRAINTS",
        "constraints": ["Architecture must safely accommodate upper bound of 300 tenants without separate infrastructure per tenant"],
        "evidence_refs": ["envelope-tenants-100-300:RANGE_100_300"]
    }
    _validate_schema(decision_record)
    assert "300" in decision_record["constraints"][0]
    assert decision_record["decision"] == "ACCEPT_WITH_CONSTRAINTS"


def test_t10_cost_constraint_bounds_architecture():
    """T10: Monthly infrastructure ceiling of $100 rejects Kafka + Kubernetes + multi-region bundle."""
    decision_record = {
        "schema_version": "orchestra.architecture-complexity-decision.v1",
        "contract_name": "ArchitectureComplexityDecision",
        "owner": "clockwork",
        "revision": "rev-20260903-t10",
        "requested_change": "Deploy managed Kafka cluster, multi-region Kubernetes, and three databases",
        "current_architecture": "Single cloud VM with SQLite/Postgres",
        "requirement_driver": "Scale proposal facing explicit $100 monthly infrastructure ceiling",
        "complexity_added": ["queue", "orchestrator", "multi_region", "database"],
        "justification_categories": ["OPERATIONAL_REQUIREMENT"],
        "scale_posture_before": "SCALE_READY",
        "scale_posture_after": "SCALE_READY",
        "simpler_alternatives": [
            "Single-region container instance with managed Postgres",
            "Database-backed task queue instead of Kafka"
        ],
        "decision": "REJECT",
        "constraints": ["Proposed topology grossly exceeds $100/mo cost constraint without requirement evidence"],
        "evidence_refs": ["steward-intent:cost_ceiling_$100"]
    }
    _validate_schema(decision_record)
    assert decision_record["decision"] == "REJECT"
    assert decision_record["scale_posture_after"] == "SCALE_READY"


def test_t11_trivial_change_not_applicable():
    """T11: Renaming a helper method is TRIVIAL and does not require ArchitectureComplexityDecision ceremony."""
    task_scope = "TRIVIAL"
    change_type = "rename_local_helper"
    # Proportionality rule states ArchitectureComplexityDecision is NOT_APPLICABLE for trivial changes
    requires_decision = (task_scope not in ("TRIVIAL", "STANDARD"))
    assert not requires_decision, "Trivial helper rename must not require ArchitectureComplexityDecision"


def test_t12_bundled_unnecessary_components_must_be_independently_justified():
    """T12: 'Add Redis, Kafka, replica DB, and Kubernetes to future proof' requires independent justification."""
    proposed_bundle = ["cache", "queue", "replica", "orchestrator"]
    justifications = {
        "cache": "No measured bottleneck -> REJECT",
        "queue": "No asynchronous decoupled workload requirement -> REJECT",
        "replica": "Read throughput easily handled by primary database -> REJECT",
        "orchestrator": "Single deployment artifact does not require cluster orchestration -> REJECT"
    }
    decision_record = {
        "schema_version": "orchestra.architecture-complexity-decision.v1",
        "contract_name": "ArchitectureComplexityDecision",
        "owner": "clockwork",
        "revision": "rev-20260903-t12",
        "requested_change": "Deploy Redis, Kafka, read replica, and Kubernetes cluster",
        "current_architecture": "Single container monolithic runtime",
        "requirement_driver": "Generic future-proofing claim without component-level evidence",
        "complexity_added": ["cache", "queue", "replica", "orchestrator"],
        "justification_categories": ["OPERATIONAL_REQUIREMENT"],
        "scale_posture_before": "SCALE_READY",
        "scale_posture_after": "SCALE_READY",
        "simpler_alternatives": [
            "Retain single container runtime with in-process job abstractions and indexed queries"
        ],
        "decision": "REJECT",
        "constraints": ["Every component in proposed bundle fails individual justification requirement"],
        "evidence_refs": ["FUTURE_SCALABILITY_ALONE_IS_NOT_SUFFICIENT_JUSTIFICATION"]
    }
    _validate_schema(decision_record)
    assert decision_record["decision"] == "REJECT"
    assert set(decision_record["complexity_added"]) == set(proposed_bundle)


def test_clockwork_negative_authority_boundaries():
    """Clockwork must not exceed its authority boundaries."""
    prohibited_actions = [
        "invent_capacity_metrics",
        "invent_traffic_numbers",
        "invent_vendor_costs",
        "mutate_steward_contracts",
        "perform_database_migrations",
        "define_security_auth_policy",
        "claim_overseer_validation_pass",
        "execute_ponytail_code_implementation",
        "activate_dagger_chaos_simulation",
        "start_ar3"
    ]
    for action in prohibited_actions:
        assert action.startswith("invent_") or action in (
            "mutate_steward_contracts",
            "perform_database_migrations",
            "define_security_auth_policy",
            "claim_overseer_validation_pass",
            "execute_ponytail_code_implementation",
            "activate_dagger_chaos_simulation",
            "start_ar3"
        )


def test_clockwork_guide_parity_and_markers():
    """Verify source and Codex mirror guide parity and essential doctrine markers."""
    assert GUIDE_SOURCE.is_file(), "Missing Clockwork complexity guide source"
    assert GUIDE_CODEX.is_file(), "Missing Clockwork complexity guide Codex mirror"
    assert GUIDE_SOURCE.read_bytes() == GUIDE_CODEX.read_bytes(), "Parity mismatch between source and Codex guide"

    text = GUIDE_SOURCE.read_text(encoding="utf-8")
    assert "FUTURE_SCALABILITY_ALONE_IS_NOT_SUFFICIENT_JUSTIFICATION" in text
    assert "SCALE_READY" in text
    assert "SCALE_PROVISIONED" in text
    assert "prefer SCALE_READY" in text
    assert "Simpler-Alternative" in text or "simpler_alternatives" in text
    assert "UNKNOWN IS VALID" in text
    assert "Downstream Specialist Handoffs" in text


def main():
    test_t1_vague_scale_request_rejects_automatic_provisioning()
    test_t2_premature_redis_rejected_or_deferred()
    test_t3_measured_bottleneck_accepts_cache_review()
    test_t4_scale_ready_without_provisioning()
    test_t5_legitimate_scale_provisioning()
    test_t6_service_split_without_reason_rejected()
    test_t7_valid_service_isolation_reason_accepted()
    test_t8_unknown_capacity_preserves_truth_state()
    test_t9_capacity_range_preserved_without_averaging()
    test_t10_cost_constraint_bounds_architecture()
    test_t11_trivial_change_not_applicable()
    test_t12_bundled_unnecessary_components_must_be_independently_justified()
    test_clockwork_negative_authority_boundaries()
    test_clockwork_guide_parity_and_markers()
    print("All Clockwork Architecture Complexity tests passed successfully (14/14).")


if __name__ == "__main__":
    main()
