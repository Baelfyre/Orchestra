from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
INDEX_PATH = ROOT / "machine" / "provenance" / "cloak-ui-reference-cuir1.v1.json"
SCHEMA_PATH = ROOT / "machine" / "schemas" / "cloak-ui-reference-source-record.v1.schema.json"

EXPECTED_BASELINE = "85c6b38e574e2355d67f35b768b9432dc26de358"
EXPECTED_ACCOUNT_COUNT = 144
EXPECTED_RETAINED_NAZIA_COUNT = 20
EXPECTED_ICON_RECORD_COUNT = 3
EXPECTED_TOTAL_SOURCE_RECORDS = 23
EXPECTED_IDENTITY_SHA256 = "9679989b604ef0db201ba9d9860a0e6d9e62f2b9dd62556dbb1e75f96453d904"

EXPECTED_ICON_PINS = {
    "simple-icons/simple-icons": ("e3d830c3b553bb657df7389b673d1d78abf5159b", "CC0-1.0", "REUSE_WITH_RIGHTS_REVIEW"),
    "tabler/tabler-icons": ("5a0fe38e97784d94279ce4eb1bf85f9a91bf027e", "MIT", "REUSE_WITH_NOTICE"),
    "lucide-icons/lucide": ("796dad298f8d78c5da204c3e62a5ed93c2bfcd1e", "ISC", "REUSE_WITH_NOTICE"),
}

def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def _index() -> dict:
    return _load_json(INDEX_PATH)

def _records(index: dict) -> list[dict]:
    return [_load_json(ROOT / path) for path in index["source_record_files"]]

def test_snapshot_is_complete_deduplicated_and_not_hardcoded_as_permanent_truth() -> None:
    data = _index()
    assert data["orchestra_baseline_sha"] == EXPECTED_BASELINE
    assert data["discovery"]["page_sizes"] == [100, 44, 0]
    assert data["discovery"]["public_repository_count"] == EXPECTED_ACCOUNT_COUNT
    assert data["discovery"]["identity_sha256"] == EXPECTED_IDENTITY_SHA256
    assert "not a permanent" in data["discovery"]["snapshot_note"].lower()

    identities = [
        repo
        for repos in data["account_dispositions"].values()
        for repo in repos
    ]
    assert len(identities) == EXPECTED_ACCOUNT_COUNT
    assert len(set(identities)) == EXPECTED_ACCOUNT_COUNT
    digest = hashlib.sha256("\n".join(sorted(identities)).encode("utf-8")).hexdigest()
    assert digest == EXPECTED_IDENTITY_SHA256

def test_retention_and_exclusion_counts_are_explicit() -> None:
    data = _index()
    groups = data["account_dispositions"]
    assert len(groups["DISTINCT_GENERALIZABLE_UI_PATTERN"]) == EXPECTED_RETAINED_NAZIA_COUNT
    assert len(groups["REDUNDANT_OR_LOWER_PRIORITY_VARIANT_NOT_RETAINED"]) == 107
    assert len(groups["DECORATIVE_OR_SCENE_ANIMATION_NOT_RETAINED"]) == 9
    assert len(groups["BRAND_OR_MEDIA_SPECIFIC_EXAMPLE_NOT_NEEDED_FOR_GENERAL_PATTERN"]) == 5
    assert len(groups["NON_UI_MEDIA_REPOSITORY"]) == 1
    assert len(groups["EMPTY_REPOSITORY_METADATA_SIZE_ZERO"]) == 2
    assert "Nazia-99/video" in groups["NON_UI_MEDIA_REPOSITORY"]
    assert "Nazia-99/Animated-Floating-Tab-Bar" in groups["EMPTY_REPOSITORY_METADATA_SIZE_ZERO"]
    assert "Nazia-99/E-commerce-Product-Card" in groups["EMPTY_REPOSITORY_METADATA_SIZE_ZERO"]

def test_all_source_record_files_exist_and_validate_against_canonical_schema() -> None:
    data = _index()
    schema = _load_json(SCHEMA_PATH)
    validator = Draft202012Validator(schema)
    paths = data["source_record_files"]
    assert len(paths) == EXPECTED_TOTAL_SOURCE_RECORDS
    assert len(set(paths)) == EXPECTED_TOTAL_SOURCE_RECORDS

    for rel in paths:
        path = ROOT / rel
        assert path.is_file(), rel
        record = _load_json(path)
        errors = sorted(validator.iter_errors(record), key=lambda error: list(error.path))
        assert not errors, f"{rel}: {[error.message for error in errors]}"

def test_nazia_records_are_reference_only_under_ambiguous_license_metadata() -> None:
    data = _index()
    records = _records(data)
    nazia = [record for record in records if record["owner"] == "Nazia-99"]
    assert len(nazia) == EXPECTED_RETAINED_NAZIA_COUNT

    for record in nazia:
        assert record["source_category"] == "UI_REFERENCE"
        assert record["license_identifier"] == "AMBIGUOUS"
        assert record["reuse_classification"] == "REFERENCE_ONLY"
        assert re.fullmatch(r"[0-9a-f]{40}", record["source_revision"])
        notice = " ".join(record["attribution_or_notice_requirements"])
        assert "Nazia-99" in notice
        assert record["repository"] in notice
        evidence = record["license_evidence"]
        assert evidence and evidence[0]["type"] == "REPOSITORY_METADATA"
        assert "license=null" in evidence[0]["notes"]
        assert "not an exhaustive" in evidence[0]["notes"].lower()
        copied = " ".join(record["what_was_not_copied"]).lower()
        assert "no source code" in copied
        assert "executed" in copied

def test_retained_account_map_matches_nazia_source_records() -> None:
    data = _index()
    retained = set(data["account_dispositions"]["DISTINCT_GENERALIZABLE_UI_PATTERN"])
    records = _records(data)
    nazia_repositories = {record["repository"] for record in records if record["owner"] == "Nazia-99"}
    assert retained == nazia_repositories

def test_icon_pins_and_license_treatments_are_exact() -> None:
    data = _index()
    records = {record["repository"]: record for record in _records(data)}
    for repository, (revision, license_id, reuse) in EXPECTED_ICON_PINS.items():
        record = records[repository]
        assert record["source_revision"] == revision
        assert record["license_identifier"] == license_id
        assert record["reuse_classification"] == reuse

    simple = records["simple-icons/simple-icons"]
    assert simple["source_category"] == "BRAND_ICONS"
    assert "trademark" in " ".join(simple["attribution_or_notice_requirements"]).lower()

    lucide = records["lucide-icons/lucide"]
    evidence_types = {item["type"] for item in lucide["license_evidence"]}
    assert "LICENSE_FILE" in evidence_types
    assert "ARTIFACT_LICENSE_MAP" in evidence_types
    assert "feather" in " ".join(
        item["notes"] for item in lucide["license_evidence"]
    ).lower()
    assert "mit" in " ".join(
        item["notes"] for item in lucide["license_evidence"]
    ).lower()

def test_external_execution_and_provider_boundaries_remain_closed() -> None:
    data = _index()
    controls = data["external_execution_controls"]
    assert controls["run_build_scripts"] is False
    assert controls["install_project_dependencies"] is False
    assert controls["execute_application_code"] is False
    assert controls["execute_unknown_scripts"] is False
    assert controls["mirror_entire_repository"] is False
    assert controls["automatic_ingestion"] is False

    boundary = data["phase_boundary"]
    assert boundary["cuir2_started"] is False
    assert boundary["live_vscode_provider_observations"] == "PENDING_USER_ASSISTED"
    assert boundary["automatic_provider_routing"] is False
    assert boundary["automatic_provider_fallback"] is False
