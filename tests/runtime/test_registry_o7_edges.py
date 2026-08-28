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


def capability_surface(*, include_index: bool = True, include_budget: bool = True, include_mcp: bool = False) -> dict:
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
        "cap.transport.mcp.v1",
    ):
        if capability_id == "cap.query.indexed-read.v1" and not include_index:
            continue
        if capability_id == "cap.query.budget.v1" and not include_budget:
            continue
        if capability_id == "cap.transport.mcp.v1" and not include_mcp:
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
        "query": req.gateway_request(),
        "total_filtered": 1,
        "count": 1,
        "next_cursor": None,
        "records": records,
        "receipt": receipt,
        "encoded_bytes": 1000,
    }


def normalize(req: o7.O7QueryRequest, response: dict, *, transport: str = o7.DIRECT_JSON, identity: dict | None = None) -> dict:
    return o7.normalize_r7_query(
        req,
        response,
        registry_identity=identity or REGISTRY_IDENTITY,
        negotiation=o7.negotiate_o7_capabilities(capability_surface(include_mcp=True)),
        transport=transport,
    )


@pytest.mark.parametrize(
    "overrides",
    [
        {"workflow_stage": ""},
        {"workflow_stage": "unknown"},
        {"source_id": ""},
        {"obligation_id": ""},
        {"projection": "tiny"},
        {"limit": False},
        {"limit": 0},
        {"limit": 1001},
        {"maximum_context_bytes": False},
        {"maximum_context_bytes": 0},
        {"representation": "yaml"},
        {"explicit_mcp": "yes"},
    ],
)
def test_request_validation_fails_closed(overrides: dict) -> None:
    with pytest.raises(o7.O7RegistryError):
        request(**overrides)


def test_request_normalizes_projection_representation_ids_and_filters() -> None:
    req = request(
        providers=("provider-b", "provider-a", "provider-a"),
        source_id="PH-A",
        obligation_id="PH-O",
        projection="summary",
        maximum_context_bytes=4096,
        limit=10,
        cursor="10",
        representation="json",
    )
    assert req.projection == "SUMMARY"
    assert req.representation == "JSON"
    assert req.providers == ("provider-a", "provider-b")
    assert req.receipt_filters()["source_id"] == "PH-A"
    assert req.receipt_filters()["obligation_id"] == "PH-O"
    assert req.gateway_request()["maximum_context_bytes"] == 4096
    assert req.gateway_request()["cursor"] == "10"


def test_gateway_request_rejects_multi_value_filter() -> None:
    req = request(jurisdictions=("PH", "SG"))
    with pytest.raises(o7.O7RegistryError, match="at most one"):
        req.gateway_request()


def test_private_normalizers_reject_empty_and_bad_digest_and_accept_none_values() -> None:
    assert o7._values(None, "test") == ()
    with pytest.raises(o7.O7RegistryError, match="non-empty"):
        o7._text("", "test")
    with pytest.raises(o7.O7RegistryError, match="SHA-256"):
        o7._sha("ABC", "test")


def test_transport_plan_serialization_is_non_authorizing() -> None:
    plan = o7.O7TransportPlan("R7_OPTIMIZED", o7.DIRECT_JSON, "SUMMARY", "TEST")
    value = plan.to_dict()
    assert value["schema_version"] == o7.O7_RUNTIME_SCHEMA
    assert value["authority_expansion"] is False


def test_transport_rejects_malformed_negotiation_optional_array() -> None:
    negotiation = {"disposition": "COMPATIBLE", "matched_optional_capability_ids": "bad"}
    with pytest.raises(o7.O7RegistryError, match="must be an array"):
        o7.select_o7_transport(request(), negotiation, available_transports=(o7.DIRECT_JSON,))


@pytest.mark.parametrize(
    ("available", "expected_transport", "expected_disposition", "expected_reason"),
    [
        ((o7.OPTIONAL_MCP, o7.DIRECT_JSON), o7.OPTIONAL_MCP, "R7_OPTIMIZED", "EXPLICIT_MCP_SELECTED"),
        ((o7.DIRECT_JSON,), o7.DIRECT_JSON, "R7_OPTIMIZED", "MCP_UNAVAILABLE_DIRECT_FALLBACK"),
        ((), o7.LEGACY_O1_O6, o7.LEGACY_O1_O6, "MCP_AND_R7_DIRECT_UNAVAILABLE"),
    ],
)
def test_explicit_mcp_transport_paths(available: tuple[str, ...], expected_transport: str, expected_disposition: str, expected_reason: str) -> None:
    negotiation = o7.negotiate_o7_capabilities(capability_surface(include_mcp=True))
    plan = o7.select_o7_transport(request(explicit_mcp=True), negotiation, available_transports=available)
    assert plan.transport == expected_transport
    assert plan.disposition == expected_disposition
    assert plan.reason == expected_reason


def test_transport_unavailable_uses_legacy_path() -> None:
    negotiation = o7.negotiate_o7_capabilities(capability_surface())
    plan = o7.select_o7_transport(request(), negotiation, available_transports=())
    assert plan.disposition == o7.LEGACY_O1_O6
    assert plan.reason == "R7_TRANSPORT_UNAVAILABLE"


@pytest.mark.parametrize(
    ("target", "key", "value", "match"),
    [
        ("receipt", "canonical_repository", "other/repo", "canonical repository mismatch"),
        ("identity", "canonical_repository", "other/repo", "active Registry canonical repository mismatch"),
        ("receipt", "registry_version", "9.9.9", "registry_version"),
        ("receipt", "release_sequence", 99, "release_sequence"),
        ("receipt", "release_tag", "registry-v9.9.9", "release_tag"),
        ("receipt", "release_manifest_sha256", "f" * 64, "release_manifest_sha256"),
    ],
)
def test_registry_identity_mismatch_fails_closed(target: str, key: str, value: object, match: str) -> None:
    req = request()
    response = response_for(req)
    identity = copy.deepcopy(REGISTRY_IDENTITY)
    if target == "receipt":
        response["receipt"][key] = value
    else:
        identity[key] = value
    with pytest.raises(o7.O7SemanticMismatch, match=match):
        normalize(req, response, identity=identity)


@pytest.mark.parametrize(
    ("mutation", "match"),
    [
        ("missing_query", "missing query echo"),
        ("record_type", "record_type"),
        ("projection", "projection"),
        ("include_freshness", "include_freshness"),
        ("limit", "limit"),
        ("cursor", "cursor"),
        ("maximum_context_bytes", "maximum_context_bytes"),
        ("filters", "filters"),
    ],
)
def test_query_echo_mismatches_fail_closed(mutation: str, match: str) -> None:
    req = request(maximum_context_bytes=4096, cursor="10")
    response = response_for(req)
    if mutation == "missing_query":
        response["query"] = None
    elif mutation == "filters":
        response["query"]["filters"]["domain"] = "security"
    else:
        response["query"][mutation] = "wrong" if mutation not in {"include_freshness", "limit", "maximum_context_bytes"} else -1
    with pytest.raises(o7.O7SemanticMismatch, match=match):
        normalize(req, response)


@pytest.mark.parametrize(
    ("key", "value", "match"),
    [
        ("schema_version", "wrong", "unsupported R7 query response schema"),
        ("authority", "AUTHORITATIVE", "attempted authority expansion"),
        ("projection", "FULL", "projection mismatch"),
        ("backend", o7.DIRECT_INDEXED, "backend mismatch"),
    ],
)
def test_response_envelope_mismatches_fail_closed(key: str, value: object, match: str) -> None:
    req = request()
    response = response_for(req)
    response[key] = value
    with pytest.raises(o7.O7SemanticMismatch, match=match):
        normalize(req, response)


@pytest.mark.parametrize(
    ("mutation", "value", "match"),
    [
        ("missing", None, "missing a supported receipt"),
        ("schema_version", "wrong", "missing a supported receipt"),
        ("authority", "EXECUTION", "attempted authority expansion"),
        ("authority_expansion", True, "attempted authority expansion"),
        ("external_reverification_required_before_trust_or_mutation", False, "reverification boundary"),
        ("promotion_from_receipt_forbidden", False, "promotion authority"),
        ("publication_trust", "DRAFT", "trusted Registry release identity"),
        ("registry_authority_realm", "DRAFT", "trusted release read model"),
        ("query_semantic_sha256", "bad", "SHA-256"),
        ("result_semantic_sha256", "bad", "SHA-256"),
    ],
)
def test_receipt_boundary_mismatches_fail_closed(mutation: str, value: object, match: str) -> None:
    req = request()
    response = response_for(req)
    if mutation == "missing":
        response["receipt"] = None
    else:
        response["receipt"][mutation] = value
    with pytest.raises((o7.O7SemanticMismatch, o7.O7RegistryError), match=match):
        normalize(req, response)


@pytest.mark.parametrize("records", ["bad", ["bad"]])
def test_records_must_be_array_of_objects(records: object) -> None:
    req = request()
    response = response_for(req)
    response["records"] = records
    with pytest.raises(o7.O7SemanticMismatch, match="records must be an array of objects"):
        normalize(req, response)


def test_exact_obligation_identity_mismatch_fails_closed() -> None:
    req = request()
    response = response_for(req)
    response["receipt"]["exact_obligation_ids"] = ["OTHER"]
    with pytest.raises(o7.O7SemanticMismatch, match="exact obligation identity"):
        normalize(req, response)


def test_response_count_mismatch_fails_closed() -> None:
    req = request()
    response = response_for(req)
    response["count"] = 2
    with pytest.raises(o7.O7SemanticMismatch, match="count mismatch"):
        normalize(req, response)


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("freshness_evidence", "bad", "freshness evidence"),
        ("freshness_evidence", ["bad"], "freshness evidence"),
        ("capability_negotiation_evidence", "bad", "capability evidence"),
        ("capability_negotiation_evidence", ["bad"], "capability evidence"),
        ("domain_routing_evidence", "bad", "domain-routing evidence"),
    ],
)
def test_receipt_evidence_shapes_fail_closed(field: str, value: object, match: str) -> None:
    req = request()
    response = response_for(req)
    response["receipt"][field] = value
    with pytest.raises(o7.O7SemanticMismatch, match=match):
        normalize(req, response)


def test_freshness_must_cover_exact_source_set() -> None:
    req = request()
    response = response_for(req)
    response["receipt"]["freshness_evidence"] = [
        {"source_id": "OTHER", "source_status": {}, "review_schedule": {}}
    ]
    with pytest.raises(o7.O7SemanticMismatch, match="exact source set"):
        normalize(req, response)


def test_routing_uses_returned_domain_when_request_domain_is_empty() -> None:
    req = request(domains=())
    response = response_for(req)
    normalized = normalize(req, response)
    assert normalized["routing"]["specialist_ids"] == ["the-governor"]


def test_execute_legacy_plan_calls_existing_o1_o6_path() -> None:
    surface = capability_surface()
    surface["capabilities"] = [surface["capabilities"][0]]
    calls: list[str] = []

    def legacy(_request: o7.O7QueryRequest) -> dict:
        calls.append("legacy")
        return {"legacy": True}

    result = o7.execute_o7_query(
        request(),
        capability_surface=surface,
        registry_identity=REGISTRY_IDENTITY,
        available_transports=(o7.DIRECT_JSON,),
        r7_gateway=None,
        legacy_query=legacy,
    )
    assert calls == ["legacy"]
    assert result["mode"] == o7.LEGACY_O1_O6


def test_execute_unbound_gateway_falls_back_to_existing_o1_o6_path() -> None:
    result = o7.execute_o7_query(
        request(),
        capability_surface=capability_surface(),
        registry_identity=REGISTRY_IDENTITY,
        available_transports=(o7.DIRECT_JSON,),
        r7_gateway=None,
        legacy_query=lambda _request: {"legacy": True},
    )
    assert result["mode"] == o7.LEGACY_O1_O6
    assert result["transport_plan"]["reason"] == "R7_GATEWAY_NOT_BOUND"


def test_execute_index_integrity_failure_without_direct_json_uses_legacy() -> None:
    calls: list[str] = []

    def gateway(transport: str, _query: dict) -> dict:
        calls.append(transport)
        raise o7.O7IndexIntegrityError("index mismatch")

    result = o7.execute_o7_query(
        request(),
        capability_surface=capability_surface(),
        registry_identity=REGISTRY_IDENTITY,
        available_transports=(o7.DIRECT_INDEXED,),
        r7_gateway=gateway,
        legacy_query=lambda _request: {"legacy": True},
    )
    assert calls == [o7.DIRECT_INDEXED]
    assert result["mode"] == o7.LEGACY_O1_O6
    assert result["transport_plan"]["reason"] == "INDEX_INTEGRITY_REJECTED_FALLBACK"


def test_execute_direct_json_success_normalizes_result_and_transport_plan() -> None:
    req = request()

    def gateway(transport: str, _query: dict) -> dict:
        assert transport == o7.DIRECT_JSON
        return response_for(req)

    result = o7.execute_o7_query(
        req,
        capability_surface=capability_surface(include_index=False),
        registry_identity=REGISTRY_IDENTITY,
        available_transports=(o7.DIRECT_JSON,),
        r7_gateway=gateway,
        legacy_query=lambda _request: pytest.fail("legacy path must not run"),
    )
    assert result["mode"] == "R7_OPTIMIZED"
    assert result["transport"] == o7.DIRECT_JSON
    assert result["transport_plan"]["reason"] == "NORMALIZED_R7_RESULT"
