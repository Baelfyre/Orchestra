from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import tempfile

import pytest

from orchestra_runtime import registry_adaptive as adaptive


def capability_surface() -> dict:
    return {
        "schema_version": adaptive.CAPABILITY_MANIFEST_SCHEMA,
        "canonical_repository": adaptive.CANONICAL_REPOSITORY,
        "authority": "DESCRIPTIVE_NON_AUTHORIZING",
        "capabilities": [
            {
                "capability_id": "cap.query.v1",
                "contract_version": "1.0.0",
                "status": "SUPPORTED",
                "required_records": ["sources", "obligations"],
                "optional": False,
                "fallback": "NONE",
            }
        ],
        "authority_boundaries": {
            "legal_interpretation": False,
            "project_applicability": False,
            "orchestra_execution": False,
            "automatic_merge": False,
            "trusted_release_publication": False,
        },
    }


def valid_delta() -> dict:
    value = {
        "schema_version": adaptive.RELEASE_DELTA_SCHEMA,
        "authority": "EVIDENCE_ONLY_NON_AUTHORIZING",
        "base": {"registry_version": "0.2.0", "release_sequence": 2, "manifest_sha256": "a" * 64},
        "target": {"registry_version": "0.3.0", "release_sequence": 3, "manifest_sha256": "b" * 64},
        "disposition": "UNCHANGED",
        "changed_record_types": [],
        "affected": {
            "capability_ids": [],
            "domains": [],
            "jurisdiction_ids": [],
            "provider_ids": [],
            "source_ids": [],
            "obligation_ids": [],
        },
        "structural_changes": [],
        "requires_human_review": False,
    }
    value["digest"] = adaptive.stable_digest(value)
    return value


def write_capability(root: Path, value: object) -> None:
    registry = root / "registry"
    registry.mkdir(parents=True, exist_ok=True)
    (registry / "capabilities.json").write_text(json.dumps(value), encoding="utf-8")


def test_id_and_version_normalizers_fail_closed_on_bad_values() -> None:
    assert adaptive._ids(None, "values") == ()
    with pytest.raises(adaptive.RegistryAdaptiveError):
        adaptive._ids(["ok", ""], "values")
    with pytest.raises(adaptive.RegistryAdaptiveError):
        adaptive._version("1.0", "version")
    with pytest.raises(adaptive.RegistryAdaptiveError):
        adaptive._version("1.x.0", "version")
    assert adaptive._version_compatible("1.2.0", "1.1.0") is True
    assert adaptive._version_compatible("2.0.0", "1.0.0") is False


def test_capability_loader_rejects_malformed_and_wrong_contracts() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        registry = root / "registry"
        registry.mkdir()
        path = registry / "capabilities.json"
        path.write_text("{", encoding="utf-8")
        with pytest.raises(adaptive.RegistryAdaptiveError):
            adaptive.load_capability_surface(root, "0.3.0")
        path.write_text("[]", encoding="utf-8")
        with pytest.raises(adaptive.RegistryAdaptiveError):
            adaptive.load_capability_surface(root, "0.3.0")
        for field, bad in (
            ("schema_version", "wrong"),
            ("canonical_repository", "other/repo"),
            ("authority", "AUTHORIZING"),
        ):
            value = capability_surface()
            value[field] = bad
            write_capability(root, value)
            with pytest.raises(adaptive.RegistryAdaptiveError):
                adaptive.load_capability_surface(root, "0.3.0")
        value = capability_surface()
        value["authority_boundaries"]["orchestra_execution"] = True
        write_capability(root, value)
        with pytest.raises(adaptive.RegistryAdaptiveError):
            adaptive.load_capability_surface(root, "0.3.0")
        value = capability_surface()
        value["authority_boundaries"] = []
        write_capability(root, value)
        with pytest.raises(adaptive.RegistryAdaptiveError):
            adaptive.load_capability_surface(root, "0.3.0")


def test_negotiation_rejects_malformed_entries_and_duplicate_ids() -> None:
    bad = capability_surface()
    bad["capabilities"] = "not-an-array"
    with pytest.raises(adaptive.RegistryAdaptiveError):
        adaptive.negotiate_capabilities(bad)
    bad = capability_surface()
    bad["capabilities"] = ["not-an-object"]
    with pytest.raises(adaptive.RegistryAdaptiveError):
        adaptive.negotiate_capabilities(bad)
    bad = capability_surface()
    bad["capabilities"] = [{}]
    with pytest.raises(adaptive.RegistryAdaptiveError):
        adaptive.negotiate_capabilities(bad)
    bad = capability_surface()
    bad["capabilities"] = bad["capabilities"] * 2
    with pytest.raises(adaptive.RegistryAdaptiveError):
        adaptive.negotiate_capabilities(bad)


def test_negotiation_classifies_unsupported_status_and_bad_versions() -> None:
    surface = capability_surface()
    surface["capabilities"][0]["status"] = "DEPRECATED"
    result = adaptive.negotiate_capabilities(surface, optional={})
    assert result["missing_required_capability_ids"] == ["cap.query.v1"]
    surface = capability_surface()
    surface["capabilities"][0]["contract_version"] = "invalid"
    result = adaptive.negotiate_capabilities(surface, optional={})
    assert result["incompatible_required_capability_ids"] == ["cap.query.v1"]
    surface = capability_surface()
    surface["capabilities"][0]["contract_version"] = "2.0.0"
    result = adaptive.negotiate_capabilities(surface, optional={})
    assert result["incompatible_required_capability_ids"] == ["cap.query.v1"]


def test_query_selection_exercises_exact_filters_and_malformed_source_refs() -> None:
    sources = [
        {"source_id": "S1"},
        {"source_id": "S2"},
    ]
    obligations = [
        {"obligation_id": "O1", "source_ids": ["S1"], "jurisdiction_ids": ["PH"], "provider_ids": ["P1"], "domains": ["privacy"]},
        {"obligation_id": "O2", "source_ids": ["S2"], "jurisdiction_ids": ["SG"], "provider_ids": ["P2"], "domains": ["security"]},
        {"obligation_id": "BROKEN", "source_ids": "S1", "jurisdiction_ids": ["PH"], "provider_ids": ["P1"], "domains": ["privacy"]},
    ]
    selected_sources, selected = adaptive.select_query_records(
        sources,
        obligations,
        jurisdictions=["PH"],
        providers=["P1"],
        domains=["privacy"],
        source_id="S1",
        obligation_id="O1",
    )
    assert [item["obligation_id"] for item in selected] == ["O1"]
    assert [item["source_id"] for item in selected_sources] == ["S1"]
    _, selected = adaptive.select_query_records(sources, obligations, source_id="S1")
    assert [item["obligation_id"] for item in selected] == ["O1"]
    _, selected = adaptive.select_query_records(sources, obligations, providers=["missing"])
    assert selected == []
    _, selected = adaptive.select_query_records(sources, obligations, domains=["missing"])
    assert selected == []


def test_freshness_covers_empty_attention_overdue_and_invalid_date() -> None:
    empty = adaptive.evaluate_query_scoped_freshness([], [], [], today=date(2026, 8, 20))
    assert empty["state"] == "NO_REQUIRED_SOURCES"
    attention = adaptive.evaluate_query_scoped_freshness(
        ["S1"],
        [{"source_id": "S1", "status": "CURRENT_WITH_PENDING_CHANGE"}],
        [{"source_id": "S1", "next_review_due": "2027-01-01"}],
        today=date(2026, 8, 20),
    )
    assert attention["state"] == "REVIEW_REQUIRED"
    overdue = adaptive.evaluate_query_scoped_freshness(
        ["S1"],
        [{"source_id": "S1", "status": "VERIFIED_CURRENT"}],
        [{"source_id": "S1", "next_review_due": "2026-01-01"}],
        today=date(2026, 8, 20),
    )
    assert overdue["state"] == "STALE"
    with pytest.raises(adaptive.RegistryAdaptiveError):
        adaptive.evaluate_query_scoped_freshness(
            ["S1"],
            [{"source_id": "S1", "status": "VERIFIED_CURRENT"}],
            [{"source_id": "S1", "next_review_due": "not-a-date"}],
            today=date(2026, 8, 20),
        )


def test_release_delta_closed_contract_rejections_cover_all_primary_guards() -> None:
    value = valid_delta()
    value["extra"] = True
    with pytest.raises(adaptive.RegistryAdaptiveError):
        adaptive.assess_release_delta(value)
    value = valid_delta()
    value["schema_version"] = "wrong"
    value["digest"] = adaptive.stable_digest({key: item for key, item in value.items() if key != "digest"})
    with pytest.raises(adaptive.RegistryAdaptiveError):
        adaptive.assess_release_delta(value)
    value = valid_delta()
    value["authority"] = "AUTHORIZING"
    value["digest"] = adaptive.stable_digest({key: item for key, item in value.items() if key != "digest"})
    with pytest.raises(adaptive.RegistryAdaptiveError):
        adaptive.assess_release_delta(value)
    value = valid_delta()
    value["disposition"] = "UNKNOWN"
    value["digest"] = adaptive.stable_digest({key: item for key, item in value.items() if key != "digest"})
    with pytest.raises(adaptive.RegistryAdaptiveError):
        adaptive.assess_release_delta(value)
    value = valid_delta()
    value["affected"] = []
    value["digest"] = adaptive.stable_digest({key: item for key, item in value.items() if key != "digest"})
    with pytest.raises(adaptive.RegistryAdaptiveError):
        adaptive.assess_release_delta(value)


def test_release_delta_non_list_affected_value_is_fail_safe_empty_scope() -> None:
    value = valid_delta()
    value["affected"]["domains"] = "privacy"
    value["digest"] = adaptive.stable_digest({key: item for key, item in value.items() if key != "digest"})
    result = adaptive.assess_release_delta(value)
    assert result["affected"]["domains"] == []
    assert result["routing"]["specialist_ids"] == []


def test_specialist_resolution_mixes_known_and_unknown_domains() -> None:
    result = adaptive.resolve_specialists(["privacy", "unknown-domain"])
    assert result["specialist_ids"] == ["the-governor"]
    assert result["unresolved_domains"] == ["unknown-domain"]
    assert result["disposition"] == "HUMAN_ROUTING_REQUIRED"


def test_adaptive_receipt_rejects_wrong_registry_and_binds_release_impact() -> None:
    with pytest.raises(adaptive.RegistryAdaptiveError):
        adaptive.build_adaptive_receipt(
            registry_identity={"canonical_repository": "other/repo"},
            filters={},
            source_ids=[],
            obligation_ids=[],
            negotiation={},
            freshness={},
            routing={},
        )
    receipt = adaptive.build_adaptive_receipt(
        registry_identity={
            "canonical_repository": adaptive.CANONICAL_REPOSITORY,
            "registry_version": "0.3.0",
            "release_sequence": 3,
            "release_tag": "registry-v0.3.0",
            "manifest_sha256": "f" * 64,
        },
        filters={"domains": ["privacy"]},
        source_ids=["S1"],
        obligation_ids=["O1"],
        negotiation={"digest": "n" * 64},
        freshness={"digest": "f" * 64},
        routing={"digest": "r" * 64},
        release_impact={"digest": "d" * 64},
    )
    assert receipt["release_impact_digest"] == "d" * 64
    assert receipt["authority_expansion"] is False
