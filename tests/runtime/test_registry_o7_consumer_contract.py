import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "docs/architecture/contracts/registry-o7-consumer-contract.v1.json"
SCHEMA = ROOT / "docs/architecture/contracts/registry-o7-consumer-contract.schema.json"
HUMAN_DOC = ROOT / "docs/architecture/REGISTRY_QUERY_OPTIMIZATION_O7.md"

EXPECTED_OPTIONAL_CAPABILITIES = {
    "cap.query.projection.v1",
    "cap.query.relationships.v1",
    "cap.query.indexed-read.v1",
    "cap.query.budget.v1",
    "cap.transport.mcp.v1",
}
EXPECTED_RECEIPT_FIELDS = {
    "registry_repository",
    "registry_version",
    "release_sequence",
    "release_tag",
    "release_manifest_digest",
    "query_digest",
    "source_ids",
    "obligation_ids",
    "freshness_evidence",
    "capability_negotiation",
    "domain_routing_evidence",
}


def contract_data():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def schema_data():
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def schema_errors(value):
    return list(Draft202012Validator(schema_data()).iter_errors(value))


def test_repository_contract_passes_schema():
    schema = schema_data()
    Draft202012Validator.check_schema(schema)
    assert schema_errors(contract_data()) == []


def test_source_contract_is_bound_to_reviewed_signed_r7_architecture():
    source = contract_data()["source_contract"]
    assert source["repository"] == "Baelfyre/Orchestra-Compliance-Registry"
    assert source["reviewed_commit_sha"] == "c1910806ed3ea9147af96b1c49a9f72aef75e0f6"
    assert source["reviewed_tree_sha"] == "0c37d7bf47fc20b49b26fea156c8e180db57b4a3"
    assert source["r7_document_blob_sha"] == "9f24a10f455a77509ec5246e6981ca2672624ca1"
    assert source["r7_status"] == "APPROVED_PLANNED_NOT_IMPLEMENTED"


def test_schema_rejects_claim_that_r7_is_implemented():
    mutated = copy.deepcopy(contract_data())
    mutated["source_contract"]["r7_status"] = "IMPLEMENTED"
    assert schema_errors(mutated)


def test_required_floor_and_optional_capability_set_are_exact():
    compatibility = contract_data()["compatibility"]
    assert compatibility["required_capability_floor"] == {
        "capability_id": "cap.query.v1",
        "minimum_contract_version": "1.0.0",
    }
    optional = compatibility["optional_capabilities"]
    assert {item["capability_id"] for item in optional} == EXPECTED_OPTIONAL_CAPABILITIES
    assert all(item["minimum_contract_version"] == "1.0.0" for item in optional)
    assert compatibility["optional_absence_disposition"] == "USE_CURRENT_O1_O6_PATH"
    assert compatibility["required_incompatibility_disposition"] == "FAIL_CLOSED"
    assert compatibility["existing_o1_o6_semantics_preserved"] is True


def test_transport_order_and_projection_defaults_are_frozen():
    data = contract_data()
    assert data["transport"]["preference_order"] == [
        "DIRECT_LOCAL_INDEXED_GATEWAY",
        "DIRECT_LOCAL_JSON_QUERY",
        "OPTIONAL_MCP_TRANSPORT",
    ]
    assert data["transport"]["mcp_required_for_internal_orchestra"] is False
    assert data["projections"]["allowed"] == ["MINIMAL", "SUMMARY", "EVIDENCE", "FULL"]
    assert data["projections"]["workflow_defaults"] == {
        "conductor_discovery": ["MINIMAL"],
        "governor_applicability_review": ["SUMMARY", "EVIDENCE"],
        "steward_requirements_traceability": ["EVIDENCE"],
        "explicit_audit_escalation": ["FULL"],
    }


def test_receipt_normalization_preserves_existing_evidence_identity():
    receipt = contract_data()["receipt_normalization"]
    assert receipt["target_model"] == "ComplianceQueryReceipt"
    assert set(receipt["preserve"]) == EXPECTED_RECEIPT_FIELDS
    assert receipt["downstream_set_equality_required"] is True
    assert receipt["authority_expansion"] is False


def test_integrity_and_context_budget_fail_closed():
    data = contract_data()
    assert data["integrity"]["semantic_query_mismatch"] == "FAIL_CLOSED"
    assert data["integrity"]["required_capability_incompatibility"] == "FAIL_CLOSED"
    assert data["integrity"]["model_authored_integrity_repair_allowed"] is False
    assert data["context_budget"]["projection_selection_creates_budget_authority"] is False
    assert data["context_budget"]["toon_selection_requires_measured_savings"] is True
    assert data["context_budget"]["token_or_workflow_savings_claim_requires_measurement"] is True


def test_o7_1_plus_remains_blocked_until_registry_r7_is_implemented():
    gates = contract_data()["phase_gates"]
    assert gates["o7_0_contract_freeze_complete"] is True
    assert gates["o7_1_plus_runtime_implementation_authorized"] is False
    assert gates["o7_1_plus_entry_condition"] == "IMPLEMENTED_STABLE_REGISTRY_R7_SURFACE_REQUIRED"
    assert gates["joint_conformance_required_before_o7_completion"] is True
    assert gates["trusted_immutable_registry_release_required_before_release_integration"] is True


def test_all_authority_expansion_flags_remain_false():
    assert all(value is False for value in contract_data()["authority"].values())


def test_schema_rejects_authority_expansion():
    mutated = copy.deepcopy(contract_data())
    mutated["authority"]["transport_grants_authority"] = True
    assert schema_errors(mutated)


def test_schema_rejects_transport_precedence_drift():
    mutated = copy.deepcopy(contract_data())
    mutated["transport"]["preference_order"][0:2] = list(
        reversed(mutated["transport"]["preference_order"][0:2])
    )
    assert schema_errors(mutated)


def test_schema_rejects_optional_capability_drop():
    mutated = copy.deepcopy(contract_data())
    mutated["compatibility"]["optional_capabilities"].pop()
    assert schema_errors(mutated)


def test_human_o7_document_points_to_frozen_contract_and_preserves_runtime_gate():
    text = HUMAN_DOC.read_text(encoding="utf-8")
    assert "O7_0_CONTRACT_FROZEN_RUNTIME_NOT_IMPLEMENTED" in text
    assert "docs/architecture/contracts/registry-o7-consumer-contract.v1.json" in text
    assert "IMPLEMENTED_STABLE_REGISTRY_R7_SURFACE_REQUIRED" in text
    assert "O7.1+" in text
    assert "must remain blocked" in text
