from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
CUIR2_PATH = ROOT / "machine" / "provenance" / "cloak-ui-reference-cuir2.v1.json"
CUIR2_SCHEMA_PATH = ROOT / "machine" / "schemas" / "cloak-ui-reference-analysis-record.v1.schema.json"
CUIR1_INDEX_PATH = ROOT / "machine" / "provenance" / "cloak-ui-reference-cuir1.v1.json"

EXPECTED_BASELINE = "8211dd39cbdd6210495a2a82c756b6feb9fb9cee"
EXPECTED_RECORD_COUNT = 23
EXPECTED_NAZIA_COUNT = 20
EXPECTED_ICON_PINS = {
    "simple-icons/simple-icons": ("e3d830c3b553bb657df7389b673d1d78abf5159b", "BRAND_ICONS", "REUSE_WITH_RIGHTS_REVIEW"),
    "tabler/tabler-icons": ("5a0fe38e97784d94279ce4eb1bf85f9a91bf027e", "GENERAL_UI_ICONS", "REUSE_WITH_NOTICE"),
    "lucide-icons/lucide": ("796dad298f8d78c5da204c3e62a5ed93c2bfcd1e", "GENERAL_UI_ICONS", "REUSE_WITH_NOTICE"),
}


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _cuir2() -> dict:
    return _load_json(CUIR2_PATH)


def _records() -> list[dict]:
    data = _cuir2()
    records: list[dict] = []
    for rel in data["analysis_record_files"]:
        batch = _load_json(ROOT / rel)
        assert batch["schema_version"] == "orchestra.cloak-ui-reference-cuir2-analysis-batch.v1"
        assert batch["phase"] == "CUIR-2"
        records.extend(batch["records"])
    return records


def _source_record(record: dict) -> dict:
    return _load_json(ROOT / record["source_record_path"])


def test_cuir2_is_bound_to_canonical_cuir1_and_exact_expected_inputs() -> None:
    data = _cuir2()
    assert data["phase"] == "CUIR-2"
    assert data["status"] == "CUIR_2_STATIC_ANALYSIS_CANDIDATE_PENDING_CANONICALIZATION"
    assert data["orchestra_baseline_sha"] == EXPECTED_BASELINE
    assert data["analysis_record_count"] == EXPECTED_RECORD_COUNT
    assert len(data["analysis_record_files"]) == 3
    boundary = data["input_boundary"]
    assert boundary["required_cuir1_lifecycle"] == "CUIR_1_CANONICAL_MERGED_VERIFIED"
    assert boundary["expected_source_record_count"] == EXPECTED_RECORD_COUNT
    assert boundary["retained_nazia_ui_reference_count"] == EXPECTED_NAZIA_COUNT
    assert boundary["icon_source_count"] == 3
    assert boundary["revision_refresh_performed"] is False


def test_every_analysis_record_validates_and_binds_exactly_to_cuir1() -> None:
    records = _records()
    validator = Draft202012Validator(_load_json(CUIR2_SCHEMA_PATH))
    assert len(records) == EXPECTED_RECORD_COUNT
    assert len({record["analysis_id"] for record in records}) == EXPECTED_RECORD_COUNT
    cuir1 = _load_json(CUIR1_INDEX_PATH)
    assert {record["source_record_path"] for record in records} == set(cuir1["source_record_files"])

    for record in records:
        errors = sorted(validator.iter_errors(record), key=lambda error: list(error.path))
        assert not errors, [error.message for error in errors]
        source = _source_record(record)
        assert record["record_id"] == source["record_id"]
        assert record["repository"] == source["repository"]
        assert record["source_revision"] == source["source_revision"]
        assert record["source_category"] == source["source_category"]
        assert record["inherited_reuse_classification"] == source["reuse_classification"]
        assert record["analysis_mode"] == "STATIC_ONLY"
        assert record["candidate_patterns"]
        assert record["accessibility_note"]


def test_nazia_analysis_remains_reference_only() -> None:
    nazia = [record for record in _records() if record["repository"].startswith("Nazia-99/")]
    assert len(nazia) == EXPECTED_NAZIA_COUNT
    for record in nazia:
        assert record["inherited_reuse_classification"] == "REFERENCE_ONLY"
        source = _source_record(record)
        notice = " ".join(source["attribution_or_notice_requirements"])
        assert "Nazia-99" in notice
        assert source["repository"] in notice


def test_icon_analysis_preserves_exact_pins_categories_and_reuse_classes() -> None:
    records = {record["repository"]: record for record in _records()}
    for repository, (revision, category, reuse) in EXPECTED_ICON_PINS.items():
        record = records[repository]
        assert record["source_revision"] == revision
        assert record["source_category"] == category
        assert record["inherited_reuse_classification"] == reuse

    assert "brand_icon_metadata" in records["simple-icons/simple-icons"]["candidate_patterns"]
    lucide = records["lucide-icons/lucide"]
    source = _source_record(lucide)
    license_text = " ".join(item["notes"] for item in source["license_evidence"]).lower()
    assert "feather" in license_text and "mit" in license_text


def test_static_only_noncopying_and_provider_boundaries_remain_closed() -> None:
    data = _cuir2()
    controls = data["external_execution_controls"]
    for key in (
        "run_build_scripts",
        "install_project_dependencies",
        "execute_application_code",
        "execute_unknown_scripts",
        "mirror_entire_repository",
        "automatic_ingestion",
        "download_or_copy_reference_only_assets",
        "source_code_copied",
        "assets_copied",
        "material_reused",
        "direct_reuse_authorized_by_cuir2",
    ):
        assert controls[key] is False
    assert controls["analysis_mode"] == "STATIC_ONLY"
    assert controls["separate_reuse_gate_required_before_direct_reuse"] is True

    phase = data["phase_boundary"]
    assert phase["cuir2_started"] is True
    assert phase["cuir2_static_analysis_complete_in_candidate"] is True
    assert phase["cuir3_started"] is False
    assert phase["runtime_integration"] is False
    assert phase["code_implementation_authorized_by_cuir2"] is False
    assert phase["automatic_provider_routing"] is False
    assert phase["automatic_provider_fallback"] is False
    assert phase["release_authorized_by_cuir2"] is False
    assert phase["deployment_authorized_by_cuir2"] is False
    assert phase["policy_activation_authorized_by_cuir2"] is False


def test_cuir2_findings_remain_candidate_inputs_not_cuir3_normalization() -> None:
    data = _cuir2()
    assert data["cross_source_findings"]["status"] == "CANDIDATE_FINDINGS_NOT_CUIR3_NORMALIZED"
    assert data["cross_source_findings"]["findings"]
    assert data["phase_boundary"]["cuir3_started"] is False
    assert all(record["review_owner"] == "Cloak" for record in _records())
