from __future__ import annotations

import copy

import pytest

from orchestra_runtime import registry_adaptive
from orchestra_runtime import registry_o7 as o7


REGISTRY_IDENTITY = {
    "canonical_repository": o7.CANONICAL_REPOSITORY,
    "registry_version": "0.4.0-test",
    "release_sequence": 4,
    "release_tag": "registry-v0.4.0-test",
    "manifest_sha256": "a" * 64,
}


def capability_surface(*, include_index: bool = True, include_budget: bool = True) -> dict:
    capabilities = [
        {
            "capability_id": "cap.query.v1",
            "contract_version": "1.0.0",
            "status": "SUPPORTED",
            "required_records": ["sources", "obligations"],
            "optional": False,
            "fallback": "NONE",
        }
    ]
    for capability_id in (
        "cap.query.projection.v1",
        "cap.query.relationships.v1",
        "cap.query.indexed-read.v1",
        "cap.query.budget.v1",
    ):
        if capability_id == "cap.query.indexed-read.v1" and not include_index:
            continue
        if capability_id == "cap.query.budget.v1" and not include_budget:
            continue
        capabilities.append(
            {
                "capability_id": capability_id,
                "contract_version": "1.0.0",
                "status": "SUPPORTED",
                "required_records": ["sources", "obligations"],
                "optional": True,
                "fallback": "DIRECT_LOCAL_JSON_QUERY",
            }
        )
    return {
        "schema_version": registry_adaptive.CAPABILITY_MANIFEST_SCHEMA,
        "canonical_repository": o7.CANONICAL_REPOSITORY,
        "authority": "DESCRIPTIVE_NON_AUTHORIZING",
        "capabilities": capabilities,
        "authority_boundaries": {
            "legal_interpretation": False,
            "project_applicability": False,
            "orchestra_execution": False,
            "automatic_merge": False,
            "trusted_release_publication": False,
        },
    }


def request(**overrides) -> o7.O7QueryRequest:
    values = {
        "workflow_stage": "steward_requirements_traceability",
        "jurisdictions": ("PH",),
        "domains": ("privacy",),
    }
    values.update(overrides)
    return o7.O7QueryRequest(**values)


def response_for(req: o7.O7QueryRequest, *, backend: str = o7.DIRECT_JSON) -> dict:
    records = [
        {
            "obligation_id": "PH-O",
            "title": "Privacy obligation",
            "summary": "Evidence-bound requirement.",
            "source_ids": ["PH-A"],
            "jurisdiction_ids": ["PH"],
            "provider_ids": [],
            "domains": ["privacy"],
            "source_locator": {"kind": "section", "value": "1"},
            "required_evidence": ["evidence"],
            "interpretation_state": "SOURCE_TEXT_REVIEWED",
            "_source_freshness": [
                {
                    "source_id": "PH-A",
                    "source_status": {"source_id": "PH-A", "status": "VERIFIED_CURRENT"},
                    "review_schedule": {"source_id": "PH-A", "next_review_due": "2027-01-01"},
                }
            ],
        }
    ]
    query = req.gateway_request()
    receipt = {
        "schema_version": o7.R7_RECEIPT_SCHEMA,
        "authority": "NONE_EVIDENCE_ONLY",
        "canonical_repository": o7.CANONICAL_REPOSITORY,
        "registry_authority_realm": "TRUSTED_RELEASE_READ_MODEL",
        "publication_trust": "TRUSTED_RELEASE_IDENTITY_VERIFIED",
        "registry_version": REGISTRY_IDENTITY["registry_version"],
        "release_sequence": REGISTRY_IDENTITY["release_sequence"],
        "release_tag": REGISTRY_IDENTITY["release_tag"],
        "release_manifest_sha256": REGISTRY_IDENTITY["manifest_sha256"],
        "registry_manifest_sha256": "b" * 64,
        "registry_semantic_sha256": "c" * 64,
        "relationship_semantic_sha256": "d" * 64,
        "backend": backend,
        "projection": req.effective_projection,
        "representation": "JSON",
        "query_semantic_sha256": "e" * 64,
        "result_semantic_sha256": o7.stable_digest(records),
        "exact_source_ids": ["PH-A"],
        "exact_obligation_ids": ["PH-O"],
        "freshness_evidence": [
            {
                "source_id": "PH-A",
                "source_status": {"source_id": "PH-A", "status": "VERIFIED_CURRENT"},
                "review_schedule": {"source_id": "PH-A", "next_review_due": "2027-01-01"},
            }
        ],
        "capability_negotiation_evidence": [
            {"capability_id": "cap.query.v1", "contract_version": "1.0.0", "status": "SUPPORTED"},
            {"capability_id": "cap.query.projection.v1", "contract_version": "1.0.0", "status": "SUPPORTED"},
        ],
        "domain_routing_evidence": {"requested_domain": "privacy", "returned_domains": ["privacy"]},
        "next_cursor": None,
        "integrity_disposition": "VERIFIED_INDEX" if backend == o7.DIRECT_INDEXED else "DIRECT_CANONICAL_JSON",
        "authority_expansion": False,
        "model_authored_integrity_repair": False,
        "external_reverification_required_before_trust_or_mutation": True,
        "promotion_from_receipt_forbidden": True,
    }
    return {
        "schema_version": o7.R7_RESPONSE_SCHEMA,
        "authority": "DERIVED_NON_AUTHORITATIVE",
        "backend": backend,
        "projection": req.effective_projection,
        "query": query,
        "total_filtered": 1,
        "count": 1,
        "next_cursor": None,
        "records": records,
        "receipt": receipt,
        "encoded_bytes": 1000,
    }


def test_o7_1_negotiation_recognizes_r7_capabilities_as_optional() -> None:
    negotiation = o7.negotiate_o7_capabilities(capability_surface())
    assert negotiation["disposition"] == "COMPATIBLE"
    assert "cap.query.projection.v1" in negotiation["matched_optional_capability_ids"]
    assert "cap.query.relationships.v1" in negotiation["matched_optional_capability_ids"]
    assert "cap.query.indexed-read.v1" in negotiation["matched_optional_capability_ids"]
    assert "cap.transport.mcp.v1" in negotiation["missing_optional_capability_ids"]


def test_o7_1_optional_r7_absence_uses_current_o1_o6_path() -> None:
    surface = capability_surface()
    surface["capabilities"] = [surface["capabilities"][0]]
    negotiation = o7.negotiate_o7_capabilities(surface)
    plan = o7.select_o7_transport(request(), negotiation, available_transports=(o7.DIRECT_JSON,))
    assert plan.disposition == o7.LEGACY_O1_O6
    assert plan.authority_expansion is False


def test_o7_2_prefers_verified_indexed_gateway_when_advertised_and_bound() -> None:
    negotiation = o7.negotiate_o7_capabilities(capability_surface())
    plan = o7.select_o7_transport(
        request(), negotiation, available_transports=(o7.DIRECT_JSON, o7.DIRECT_INDEXED)
    )
    assert plan.transport == o7.DIRECT_INDEXED


def test_o7_2_falls_back_to_direct_json_when_index_capability_absent() -> None:
    negotiation = o7.negotiate_o7_capabilities(capability_surface(include_index=False))
    plan = o7.select_o7_transport(
        request(), negotiation, available_transports=(o7.DIRECT_JSON, o7.DIRECT_INDEXED)
    )
    assert plan.transport == o7.DIRECT_JSON


def test_o7_3_workflow_projection_defaults_are_bounded() -> None:
    assert o7.O7QueryRequest(workflow_stage="conductor_discovery").effective_projection == "MINIMAL"
    assert o7.O7QueryRequest(workflow_stage="governor_applicability_review").effective_projection == "SUMMARY"
    assert o7.O7QueryRequest(workflow_stage="steward_requirements_traceability").effective_projection == "EVIDENCE"
    assert o7.O7QueryRequest(workflow_stage="explicit_audit_escalation").effective_projection == "FULL"


def test_o7_4_normalizes_r7_result_into_existing_compliance_receipt_identity() -> None:
    req = request()
    negotiation = o7.negotiate_o7_capabilities(capability_surface())
    normalized = o7.normalize_r7_query(
        req,
        response_for(req),
        registry_identity=REGISTRY_IDENTITY,
        negotiation=negotiation,
        transport=o7.DIRECT_JSON,
    )
    receipt = normalized["compliance_query_receipt"]
    assert receipt["source_ids"] == ["PH-A"]
    assert receipt["obligation_ids"] == ["PH-O"]
    assert receipt["manifest_sha256"] == REGISTRY_IDENTITY["manifest_sha256"]
    assert normalized["query_digest"] == "e" * 64
    assert normalized["freshness_evidence"][0]["source_id"] == "PH-A"
    assert normalized["capability_negotiation"]["disposition"] == "COMPATIBLE"
    assert normalized["domain_routing_evidence"]["returned_domains"] == ["privacy"]
    assert normalized["routing"]["specialist_ids"] == ["the-governor"]
    assert normalized["authority_expansion"] is False


def test_o7_5_semantic_request_mismatch_fails_closed_without_legacy_repair() -> None:
    req = request()
    bad = response_for(req)
    bad["query"]["filters"]["domain"] = "security"
    negotiation = o7.negotiate_o7_capabilities(capability_surface())
    with pytest.raises(o7.O7SemanticMismatch):
        o7.normalize_r7_query(
            req,
            bad,
            registry_identity=REGISTRY_IDENTITY,
            negotiation=negotiation,
            transport=o7.DIRECT_JSON,
        )


def test_o7_5_result_digest_mismatch_fails_closed() -> None:
    req = request()
    bad = response_for(req)
    bad["records"][0]["title"] = "tampered"
    negotiation = o7.negotiate_o7_capabilities(capability_surface())
    with pytest.raises(o7.O7SemanticMismatch, match="semantic digest"):
        o7.normalize_r7_query(
            req,
            bad,
            registry_identity=REGISTRY_IDENTITY,
            negotiation=negotiation,
            transport=o7.DIRECT_JSON,
        )


def test_o7_5_index_integrity_failure_falls_back_to_direct_json() -> None:
    req = request()
    calls: list[str] = []

    def gateway(transport: str, _query: dict) -> dict:
        calls.append(transport)
        if transport == o7.DIRECT_INDEXED:
            raise o7.O7IndexIntegrityError("digest mismatch")
        return response_for(req, backend=o7.DIRECT_JSON)

    def legacy(_request: o7.O7QueryRequest) -> dict:
        raise AssertionError("legacy path should not be used when direct JSON fallback is available")

    result = o7.execute_o7_query(
        req,
        capability_surface=capability_surface(),
        registry_identity=REGISTRY_IDENTITY,
        available_transports=(o7.DIRECT_INDEXED, o7.DIRECT_JSON),
        r7_gateway=gateway,
        legacy_query=legacy,
    )
    assert calls == [o7.DIRECT_INDEXED, o7.DIRECT_JSON]
    assert result["transport"] == o7.DIRECT_JSON


def test_o7_6_budget_request_uses_legacy_when_registry_budget_capability_absent() -> None:
    req = request(maximum_context_bytes=4096)
    negotiation = o7.negotiate_o7_capabilities(capability_surface(include_budget=False))
    plan = o7.select_o7_transport(req, negotiation, available_transports=(o7.DIRECT_JSON,))
    assert plan.disposition == o7.LEGACY_O1_O6
    assert plan.reason == "R7_BUDGET_CAPABILITY_ABSENT"


def test_o7_multi_value_filter_preserves_o1_o6_semantics_via_fallback() -> None:
    req = request(jurisdictions=("PH", "SG"))
    negotiation = o7.negotiate_o7_capabilities(capability_surface())
    plan = o7.select_o7_transport(req, negotiation, available_transports=(o7.DIRECT_JSON,))
    assert plan.disposition == o7.LEGACY_O1_O6
    assert plan.reason == "R7_SINGLE_FILTER_CONTRACT_NOT_SUFFICIENT"


def test_o7_required_capability_incompatibility_fails_closed() -> None:
    surface = capability_surface()
    surface["capabilities"] = [
        item for item in surface["capabilities"] if item["capability_id"] != "cap.query.v1"
    ]
    negotiation = o7.negotiate_o7_capabilities(surface)
    with pytest.raises(o7.O7RegistryError, match="FAIL_CLOSED"):
        o7.select_o7_transport(request(), negotiation, available_transports=(o7.DIRECT_JSON,))


def test_o7_model_authored_integrity_repair_is_rejected() -> None:
    req = request()
    bad = copy.deepcopy(response_for(req))
    bad["receipt"]["model_authored_integrity_repair"] = True
    negotiation = o7.negotiate_o7_capabilities(capability_surface())
    with pytest.raises(o7.O7SemanticMismatch, match="prohibited"):
        o7.normalize_r7_query(
            req,
            bad,
            registry_identity=REGISTRY_IDENTITY,
            negotiation=negotiation,
            transport=o7.DIRECT_JSON,
        )
