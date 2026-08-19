from __future__ import annotations

from datetime import date
from pathlib import Path
import tempfile

import pytest

from orchestra_runtime import registry_adaptive as adaptive
from scripts import compliance_registry_adaptive


CAPABILITIES = {
    "schema_version": adaptive.CAPABILITY_MANIFEST_SCHEMA,
    "canonical_repository": adaptive.CANONICAL_REPOSITORY,
    "authority": "DESCRIPTIVE_NON_AUTHORIZING",
    "capabilities": [
        {
            "capability_id": capability_id,
            "contract_version": version,
            "status": "SUPPORTED",
            "required_records": ["sources"],
            "optional": capability_id != "cap.query.v1",
            "fallback": "NONE",
        }
        for capability_id, version in {**adaptive.REQUIRED_CAPABILITIES, **adaptive.OPTIONAL_CAPABILITIES}.items()
    ],
    "authority_boundaries": {
        "legal_interpretation": False,
        "project_applicability": False,
        "orchestra_execution": False,
        "automatic_merge": False,
        "trusted_release_publication": False,
    },
}

SOURCES = [
    {"source_id": "PH-A", "jurisdiction_ids": ["PH"], "domains": ["privacy"]},
    {"source_id": "SG-A", "jurisdiction_ids": ["SG"], "domains": ["privacy"]},
    {"source_id": "EU-A", "jurisdiction_ids": ["EU-EEA"], "domains": ["security"]},
]
OBLIGATIONS = [
    {
        "obligation_id": "PH-O",
        "source_ids": ["PH-A"],
        "jurisdiction_ids": ["PH"],
        "provider_ids": [],
        "domains": ["privacy", "retention"],
    },
    {
        "obligation_id": "SG-O",
        "source_ids": ["SG-A"],
        "jurisdiction_ids": ["SG"],
        "provider_ids": [],
        "domains": ["privacy", "access-control"],
    },
    {
        "obligation_id": "EU-O",
        "source_ids": ["EU-A"],
        "jurisdiction_ids": ["EU-EEA"],
        "provider_ids": [],
        "domains": ["security"],
    },
]
STATUS = [
    {"source_id": "PH-A", "status": "VERIFIED_CURRENT"},
    {"source_id": "SG-A", "status": "VERIFIED_CURRENT"},
    {"source_id": "EU-A", "status": "SOURCE_UNAVAILABLE"},
]
DUE = [
    {"source_id": "PH-A", "next_review_due": "2027-01-01"},
    {"source_id": "SG-A", "next_review_due": "2027-01-01"},
    {"source_id": "EU-A", "next_review_due": "2027-01-01"},
]


def make_delta(disposition: str, *, domains: list[str] | None = None, authority: str = "EVIDENCE_ONLY_NON_AUTHORIZING") -> dict:
    value = {
        "schema_version": adaptive.RELEASE_DELTA_SCHEMA,
        "authority": authority,
        "base": {"registry_version": "0.2.0", "release_sequence": 2, "manifest_sha256": "a" * 64},
        "target": {"registry_version": "0.3.0", "release_sequence": 3, "manifest_sha256": "b" * 64},
        "disposition": disposition,
        "changed_record_types": ["obligations"] if disposition != "UNCHANGED" else [],
        "affected": {
            "capability_ids": [],
            "domains": domains or [],
            "jurisdiction_ids": ["PH"] if domains else [],
            "provider_ids": [],
            "source_ids": ["PH-A"] if domains else [],
            "obligation_ids": ["PH-O"] if domains else [],
        },
        "structural_changes": [],
        "requires_human_review": disposition == "HUMAN_REVIEW_REQUIRED",
    }
    value["digest"] = adaptive.stable_digest(value)
    return value


def test_o1_declared_capability_negotiation_success() -> None:
    result = adaptive.negotiate_capabilities(CAPABILITIES)
    assert result["disposition"] == "COMPATIBLE"
    assert result["missing_required_capability_ids"] == []
    assert result["authority_expansion"] is False


def test_o1_missing_required_capability_fails_closed() -> None:
    surface = {**CAPABILITIES, "capabilities": [item for item in CAPABILITIES["capabilities"] if item["capability_id"] != "cap.query.v1"]}
    result = adaptive.negotiate_capabilities(surface)
    assert result["disposition"] == "INCOMPATIBLE_REQUIRED_CAPABILITY"
    assert result["missing_required_capability_ids"] == ["cap.query.v1"]


def test_o1_optional_capability_absence_does_not_break_required_surface() -> None:
    surface = {**CAPABILITIES, "capabilities": [CAPABILITIES["capabilities"][0]]}
    result = adaptive.negotiate_capabilities(surface)
    assert result["disposition"] == "COMPATIBLE"
    assert result["missing_optional_capability_ids"]


def test_o2_trusted_v0_2_legacy_profile_is_explicit_not_invented_manifest() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        (root / "registry").mkdir()
        surface = adaptive.load_capability_surface(root, "0.2.0")
    assert surface["capability_source"] == "LEGACY_V0_2_COMPATIBILITY_PROFILE"
    result = adaptive.negotiate_capabilities(surface)
    assert result["disposition"] == "COMPATIBLE"
    assert result["matched_required_capability_ids"] == ["cap.query.v1"]
    assert "cap.release-delta.v1" in result["missing_optional_capability_ids"]


def test_o2_missing_manifest_on_unknown_future_release_fails_closed() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        (root / "registry").mkdir()
        with pytest.raises(adaptive.RegistryAdaptiveError):
            adaptive.load_capability_surface(root, "0.3.0")


def test_o3_multi_jurisdiction_query_preserves_source_provenance() -> None:
    sources, obligations = adaptive.select_query_records(SOURCES, OBLIGATIONS, jurisdictions=["PH", "SG"])
    assert [item["obligation_id"] for item in obligations] == ["PH-O", "SG-O"]
    assert {item["source_id"] for item in sources} == {"PH-A", "SG-A"}


def test_o4_query_scoped_freshness_ignores_unrelated_stale_source() -> None:
    result = adaptive.evaluate_query_scoped_freshness(["PH-A", "SG-A"], STATUS, DUE, today=date(2026, 8, 20))
    assert result["state"] == "CURRENT"
    assert "EU-A" not in result["stale_source_ids"]


def test_o4_required_stale_source_fails_scoped_freshness() -> None:
    result = adaptive.evaluate_query_scoped_freshness(["EU-A"], STATUS, DUE, today=date(2026, 8, 20))
    assert result["state"] == "STALE"
    assert result["stale_source_ids"] == ["EU-A"]


def test_o4_untracked_required_source_fails_closed() -> None:
    result = adaptive.evaluate_query_scoped_freshness(["UNKNOWN"], STATUS, DUE, today=date(2026, 8, 20))
    assert result["state"] == "INCOMPLETE"
    assert result["untracked_source_ids"] == ["UNKNOWN"]


def test_o5_compatible_delta_produces_scoped_revalidation() -> None:
    result = adaptive.assess_release_delta(make_delta("COMPATIBLE_SCOPED_CHANGE", domains=["privacy"]))
    assert result["recommended_action"] == "SCOPED_REVALIDATION"
    assert result["routing"]["specialist_ids"] == ["the-governor"]


def test_o5_breaking_capability_delta_fails_closed() -> None:
    result = adaptive.assess_release_delta(make_delta("UNSUPPORTED_CAPABILITY_CHANGE", domains=["security"]))
    assert result["recommended_action"] == "FULL_REVALIDATION_FAIL_CLOSED"


def test_o5_delta_digest_tampering_is_rejected() -> None:
    delta = make_delta("UNCHANGED")
    delta["digest"] = "0" * 64
    with pytest.raises(adaptive.RegistryAdaptiveError):
        adaptive.assess_release_delta(delta)


def test_o5_source_monitor_or_other_registry_evidence_cannot_expand_authority() -> None:
    delta = make_delta("HUMAN_REVIEW_REQUIRED", domains=["privacy"], authority="EXECUTION_AUTHORITY")
    delta["digest"] = adaptive.stable_digest({key: value for key, value in delta.items() if key != "digest"})
    with pytest.raises(adaptive.RegistryAdaptiveError):
        adaptive.assess_release_delta(delta)


def test_o6_dynamic_domain_specialist_resolution_is_deterministic() -> None:
    result = adaptive.resolve_specialists(["retention", "security", "privacy"])
    assert result["specialist_ids"] == ["the-governor", "cipher", "chronicler"]
    assert result["disposition"] == "ROUTED"
    assert result["router"] == "conductor"


def test_o6_unresolved_domain_escalates_without_agent_creation() -> None:
    result = adaptive.resolve_specialists(["unknown-future-domain"])
    assert result["specialist_ids"] == []
    assert result["unresolved_domains"] == ["unknown-future-domain"]
    assert result["disposition"] == "HUMAN_ROUTING_REQUIRED"
    assert result["authority_expansion"] is False


def test_adaptive_receipt_binds_exact_consumed_sets_and_digests() -> None:
    negotiation = adaptive.negotiate_capabilities(CAPABILITIES)
    freshness = adaptive.evaluate_query_scoped_freshness(["PH-A"], STATUS, DUE, today=date(2026, 8, 20))
    routing = adaptive.resolve_specialists(["privacy"])
    receipt = adaptive.build_adaptive_receipt(
        registry_identity={
            "canonical_repository": adaptive.CANONICAL_REPOSITORY,
            "registry_version": "0.2.0",
            "release_sequence": 2,
            "release_tag": "registry-v0.2.0",
            "manifest_sha256": "a" * 64,
        },
        filters={"jurisdictions": ["PH"]},
        source_ids=["PH-A"],
        obligation_ids=["PH-O"],
        negotiation=negotiation,
        freshness=freshness,
        routing=routing,
    )
    assert receipt["source_ids"] == ["PH-A"]
    assert receipt["obligation_ids"] == ["PH-O"]
    assert receipt["authority_expansion"] is False
    assert len(receipt["digest"]) == 64


def test_adaptive_cli_module_imports_without_network_or_model_calls() -> None:
    parser = compliance_registry_adaptive.build_parser()
    args = parser.parse_args(["query", "--jurisdiction", "PH", "--jurisdiction", "SG"])
    assert args.jurisdiction == ["PH", "SG"]
