from __future__ import annotations

from datetime import date
import json
from pathlib import Path

import pytest

from orchestra_runtime import registry_adaptive as adaptive

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "compliance-registry" / "r5-capabilities.json"


def load_r5() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def delta(disposition: str, domains: list[str]) -> dict:
    value = {
        "schema_version": adaptive.RELEASE_DELTA_SCHEMA,
        "authority": "EVIDENCE_ONLY_NON_AUTHORIZING",
        "base": {"registry_version": "0.2.0", "release_sequence": 2, "manifest_sha256": "1" * 64},
        "target": {"registry_version": "0.3.0", "release_sequence": 3, "manifest_sha256": "2" * 64},
        "disposition": disposition,
        "changed_record_types": ["source_status"] if disposition != "UNCHANGED" else [],
        "affected": {
            "capability_ids": [],
            "domains": domains,
            "jurisdiction_ids": ["PH"] if domains else [],
            "provider_ids": [],
            "source_ids": ["PH-SOURCE"] if domains else [],
            "obligation_ids": [],
        },
        "structural_changes": [],
        "requires_human_review": disposition == "HUMAN_REVIEW_REQUIRED",
    }
    value["digest"] = adaptive.stable_digest(value)
    return value


def test_joint_r5_exact_registry_candidate_fixture_negotiates() -> None:
    result = adaptive.negotiate_capabilities(load_r5())
    assert result["disposition"] == "COMPATIBLE"
    assert set(result["matched_required_capability_ids"]) == set(adaptive.REQUIRED_CAPABILITIES)
    assert set(result["matched_optional_capability_ids"]) == set(adaptive.OPTIONAL_CAPABILITIES)


def test_joint_r5_fixture_cannot_grant_downstream_authority() -> None:
    fixture = load_r5()
    assert fixture["authority"] == "DESCRIPTIVE_NON_AUTHORIZING"
    assert all(value is False for value in fixture["authority_boundaries"].values())


def test_joint_multi_jurisdiction_and_scoped_freshness_simulation() -> None:
    sources = [
        {"source_id": "PH-SOURCE", "jurisdiction_ids": ["PH"], "domains": ["privacy"]},
        {"source_id": "SG-SOURCE", "jurisdiction_ids": ["SG"], "domains": ["privacy"]},
        {"source_id": "EU-UNRELATED", "jurisdiction_ids": ["EU-EEA"], "domains": ["security"]},
    ]
    obligations = [
        {"obligation_id": "PH-O", "source_ids": ["PH-SOURCE"], "jurisdiction_ids": ["PH"], "provider_ids": [], "domains": ["privacy"]},
        {"obligation_id": "SG-O", "source_ids": ["SG-SOURCE"], "jurisdiction_ids": ["SG"], "provider_ids": [], "domains": ["privacy"]},
        {"obligation_id": "EU-O", "source_ids": ["EU-UNRELATED"], "jurisdiction_ids": ["EU-EEA"], "provider_ids": [], "domains": ["security"]},
    ]
    selected_sources, selected_obligations = adaptive.select_query_records(
        sources, obligations, jurisdictions=["PH", "SG"]
    )
    selected_ids = [item["source_id"] for item in selected_sources]
    status = [
        {"source_id": "PH-SOURCE", "status": "VERIFIED_CURRENT"},
        {"source_id": "SG-SOURCE", "status": "VERIFIED_CURRENT"},
        {"source_id": "EU-UNRELATED", "status": "SOURCE_UNAVAILABLE"},
    ]
    review_due = [
        {"source_id": "PH-SOURCE", "next_review_due": "2027-01-01"},
        {"source_id": "SG-SOURCE", "next_review_due": "2027-01-01"},
        {"source_id": "EU-UNRELATED", "next_review_due": "2027-01-01"},
    ]
    freshness = adaptive.evaluate_query_scoped_freshness(
        selected_ids, status, review_due, today=date(2026, 8, 20)
    )
    assert {item["obligation_id"] for item in selected_obligations} == {"PH-O", "SG-O"}
    assert freshness["state"] == "CURRENT"
    assert "EU-UNRELATED" not in freshness["source_ids"]


def test_joint_required_stale_source_blocks_only_affected_query() -> None:
    status = [{"source_id": "PH-SOURCE", "status": "SOURCE_MOVED"}]
    due = [{"source_id": "PH-SOURCE", "next_review_due": "2027-01-01"}]
    result = adaptive.evaluate_query_scoped_freshness(["PH-SOURCE"], status, due, today=date(2026, 8, 20))
    assert result["state"] == "STALE"


def test_joint_compatible_delta_routes_only_affected_domain() -> None:
    result = adaptive.assess_release_delta(delta("COMPATIBLE_SCOPED_CHANGE", ["database-security"]))
    assert result["recommended_action"] == "SCOPED_REVALIDATION"
    assert result["routing"]["specialist_ids"] == ["cipher", "chronicler"]


def test_joint_breaking_delta_never_becomes_execution_authority() -> None:
    result = adaptive.assess_release_delta(delta("UNSUPPORTED_CAPABILITY_CHANGE", ["privacy"]))
    assert result["recommended_action"] == "FULL_REVALIDATION_FAIL_CLOSED"
    assert result["authority_expansion"] is False


def test_joint_unresolved_registry_domain_escalates_to_human_routing() -> None:
    result = adaptive.resolve_specialists(["future-unknown-domain"])
    assert result["disposition"] == "HUMAN_ROUTING_REQUIRED"
    assert result["specialist_ids"] == []
    assert result["router"] == "conductor"


def test_joint_malformed_or_authorizing_delta_is_rejected() -> None:
    value = delta("HUMAN_REVIEW_REQUIRED", ["privacy"])
    value["authority"] = "AUTOMATIC_LEGAL_AUTHORITY"
    value["digest"] = adaptive.stable_digest({key: item for key, item in value.items() if key != "digest"})
    with pytest.raises(adaptive.RegistryAdaptiveError):
        adaptive.assess_release_delta(value)
