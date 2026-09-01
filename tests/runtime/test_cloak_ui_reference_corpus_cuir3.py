from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = ROOT / "machine" / "knowledge" / "cloak-ui-reference-cuir3.v1.json"
PATTERN_SCHEMA_PATH = ROOT / "machine" / "schemas" / "cloak-ui-normalized-pattern.v1.schema.json"
CUIR2_PATH = ROOT / "machine" / "provenance" / "cloak-ui-reference-cuir2.v1.json"
HUMAN_RECORD_PATH = ROOT / "docs" / "project" / "CLOAK_UI_REFERENCE_CORPUS_CUIR3_NORMALIZATION.md"

EXPECTED_CUIR2_IMPLEMENTATION = "298f7be98b4d2c55cb48f98c0ddeafaf848e53b0"
EXPECTED_CUIR2_IMPLEMENTATION_TREE = "50bfea14a68096bb7c507bb0db8e81ff5a050065"
EXPECTED_CUIR2_CLOSEOUT = "24d356ec5d6aa16e1f80ccdbd04a0e00c9fe0e5a"
EXPECTED_CUIR2_CLOSEOUT_TREE = "c6034dec375f8dc62554fbc957833bd85c8249de"
EXPECTED_ANALYSIS_COUNT = 23
EXPECTED_PATTERN_COUNT = 16


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _catalog() -> dict:
    return _load_json(CATALOG_PATH)


def _cuir2_records() -> list[dict]:
    index = _load_json(CUIR2_PATH)
    records: list[dict] = []
    for rel in index["analysis_record_files"]:
        batch = _load_json(ROOT / rel)
        assert batch["schema_version"] == "orchestra.cloak-ui-reference-cuir2-analysis-batch.v1"
        assert batch["phase"] == "CUIR-2"
        records.extend(batch["records"])
    return records


def _analysis_map() -> dict[str, dict]:
    return {record["analysis_id"]: record for record in _cuir2_records()}


def test_cuir3_is_bound_to_exact_canonical_cuir2_without_refresh() -> None:
    catalog = _catalog()
    assert catalog["schema_version"] == "orchestra.cloak-ui-reference-cuir3.v1"
    assert catalog["phase"] == "CUIR-3"
    assert catalog["status"] == "CUIR_3_NORMALIZATION_CANDIDATE_PENDING_CANONICALIZATION"
    assert catalog["authority_class"] == "NORMALIZED_REFERENCE_KNOWLEDGE_ONLY"

    source = catalog["canonical_cuir2_input"]
    assert source["implementation_commit"] == EXPECTED_CUIR2_IMPLEMENTATION
    assert source["implementation_tree"] == EXPECTED_CUIR2_IMPLEMENTATION_TREE
    assert source["lifecycle_closeout_commit"] == EXPECTED_CUIR2_CLOSEOUT
    assert source["lifecycle_closeout_tree"] == EXPECTED_CUIR2_CLOSEOUT_TREE
    assert source["analysis_record_count"] == EXPECTED_ANALYSIS_COUNT
    assert len(source["analysis_record_files"]) == 3
    assert source["revision_refresh_performed"] is False

    policy = catalog["normalization_policy"]
    assert policy["mode"] == "ORCHESTRA_NATIVE_CONCEPT_NORMALIZATION"
    assert policy["new_external_source_inspection"] is False
    assert policy["source_or_asset_copying"] is False
    assert policy["external_code_execution"] is False
    assert policy["external_dependency_installation"] is False
    assert policy["runtime_integration"] is False
    assert policy["automatic_retrieval"] is False


def test_every_normalized_pattern_validates_and_preserves_exact_provenance() -> None:
    catalog = _catalog()
    patterns = catalog["patterns"]
    validator = Draft202012Validator(_load_json(PATTERN_SCHEMA_PATH))
    source_by_analysis = _analysis_map()

    assert len(patterns) == EXPECTED_PATTERN_COUNT
    assert len({pattern["pattern_id"] for pattern in patterns}) == EXPECTED_PATTERN_COUNT

    for pattern in patterns:
        errors = sorted(validator.iter_errors(pattern), key=lambda error: list(error.path))
        assert not errors, [error.message for error in errors]

        analysis_ids = pattern["source_analysis_ids"]
        assert pattern["evidence_count"] == len(set(analysis_ids))
        assert set(analysis_ids) <= set(source_by_analysis)

        expected_paths = {source_by_analysis[analysis_id]["source_record_path"] for analysis_id in analysis_ids}
        expected_reuse = {
            source_by_analysis[analysis_id]["inherited_reuse_classification"] for analysis_id in analysis_ids
        }
        assert set(pattern["source_record_paths"]) == expected_paths
        assert set(pattern["reuse_classifications"]) == expected_reuse
        assert pattern["orchestra_native_normalization"] is True
        assert pattern["implementation_authority"] is False


def test_all_23_cuir2_records_are_accounted_for_without_unknown_sources() -> None:
    catalog = _catalog()
    source_ids = set(_analysis_map())
    coverage = catalog["coverage"]
    pattern_ids = {
        analysis_id
        for pattern in catalog["patterns"]
        for analysis_id in pattern["source_analysis_ids"]
    }

    assert len(source_ids) == EXPECTED_ANALYSIS_COUNT
    assert coverage["expected_cuir2_analysis_count"] == EXPECTED_ANALYSIS_COUNT
    assert coverage["normalized_pattern_count"] == EXPECTED_PATTERN_COUNT
    assert coverage["all_cuir2_records_accounted_for"] is True
    assert set(coverage["promoted_analysis_ids"]) == source_ids
    assert coverage["not_promoted_analysis_ids"] == []
    assert pattern_ids == source_ids


def test_reference_only_ui_patterns_remain_concept_only() -> None:
    source_by_analysis = _analysis_map()
    catalog = _catalog()
    for pattern in catalog["patterns"]:
        source_records = [source_by_analysis[analysis_id] for analysis_id in pattern["source_analysis_ids"]]
        if any(record["repository"].startswith("Nazia-99/") for record in source_records):
            assert pattern["reuse_classifications"] == ["REFERENCE_ONLY"]

    policy = catalog["normalization_policy"]
    assert policy["source_or_asset_copying"] is False
    assert policy["preserve_reuse_classification"] is True


def test_general_icons_and_brand_icons_remain_separate_rights_classes() -> None:
    patterns = {pattern["pattern_id"]: pattern for pattern in _catalog()["patterns"]}

    general_icons = patterns["cuir3.general_ui_icon_system"]
    assert set(general_icons["source_analysis_ids"]) == {
        "tabler.tabler-icons.cuir2",
        "lucide-icons.lucide.cuir2",
    }
    assert general_icons["reuse_classifications"] == ["REUSE_WITH_NOTICE"]

    brand_icons = patterns["cuir3.brand_icon_traceability_and_rights"]
    assert brand_icons["source_analysis_ids"] == ["simple-icons.simple-icons.cuir2"]
    assert brand_icons["reuse_classifications"] == ["REUSE_WITH_RIGHTS_REVIEW"]
    assert "trademark" in brand_icons["recommended_behavior"].lower()


def test_accessibility_defects_are_rejected_not_normalized_as_recommendations() -> None:
    catalog = _catalog()
    patterns = {pattern["pattern_id"]: pattern for pattern in catalog["patterns"]}
    baseline = patterns["cuir3.semantic_control_accessibility_baseline"]
    motion = patterns["cuir3.motion_as_secondary_state_feedback"]

    assert "native links, buttons, inputs, labels, radio controls, checkboxes, and disclosure semantics" in baseline[
        "recommended_behavior"
    ]
    constraints = " ".join(baseline["accessibility_constraints"]).lower()
    assert "generic click targets" in constraints
    assert "placeholder-only" in constraints
    assert "accessible naming" in constraints

    motion_text = (motion["recommended_behavior"] + " " + " ".join(motion["accessibility_constraints"])).lower()
    assert "sole" in motion["recommended_behavior"].lower()
    assert "reduced-motion" in motion_text
    assert "animation disabled" in motion_text

    for pattern in catalog["patterns"]:
        recommendation = pattern["recommended_behavior"].lower()
        assert "use clickable div" not in recommendation
        assert "use clickable list item" not in recommendation
        assert "use placeholder-only" not in recommendation


def test_cuir3_is_knowledge_only_and_cuir4_remains_closed() -> None:
    catalog = _catalog()
    boundary = catalog["phase_boundary"]
    assert boundary["cuir3_started"] is True
    assert boundary["cuir3_normalization_complete_in_candidate"] is True
    assert boundary["cuir4_started"] is False
    assert boundary["runtime_integration"] is False
    assert boundary["automatic_retrieval"] is False
    assert boundary["automatic_provider_routing"] is False
    assert boundary["implementation_authority"] is False
    assert boundary["release_authority"] is False
    assert boundary["deployment_authority"] is False
    assert boundary["policy_activation_authority"] is False

    expected_boundaries = {
        "NO_NEW_EXTERNAL_SOURCE_DISCOVERY",
        "NO_SOURCE_REVISION_REFRESH",
        "NO_SOURCE_OR_ASSET_COPYING",
        "NO_EXTERNAL_CODE_EXECUTION",
        "NO_EXTERNAL_DEPENDENCY_INSTALLATION",
        "NO_AUTOMATIC_INGESTION",
        "NO_CLOAK_RUNTIME_INTEGRATION",
        "NO_AUTOMATIC_PATTERN_RETRIEVAL",
        "NO_PROVIDER_ROUTING_OR_FALLBACK",
        "NO_IMPLEMENTATION_AUTHORITY",
        "NO_RELEASE_OR_TAG_MOVEMENT",
        "NO_DEPLOYMENT_OR_PRODUCTION_MUTATION",
        "NO_POLICY_OR_RULESET_ACTIVATION",
    }
    assert set(catalog["protected_boundaries"]) == expected_boundaries


def test_human_record_preserves_normalization_and_cuir4_boundary() -> None:
    text = HUMAN_RECORD_PATH.read_text(encoding="utf-8")
    assert "CUIR_3_NORMALIZATION_CANDIDATE_PENDING_CANONICALIZATION" in text
    assert "23 canonical CUIR-2 analysis IDs" in text
    assert "REFERENCE_ONLY remains REFERENCE_ONLY" in text
    assert "REUSE_WITH_NOTICE remains REUSE_WITH_NOTICE" in text
    assert "REUSE_WITH_RIGHTS_REVIEW remains REUSE_WITH_RIGHTS_REVIEW" in text
    assert "CUIR4_STARTED = false" in text
    assert "automatic pattern retrieval" in text
