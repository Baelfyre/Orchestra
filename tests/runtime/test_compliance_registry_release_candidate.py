import hashlib
import json
import zipfile
from pathlib import Path

from scripts import compliance_registry

REGISTRY_VERSION = "0.1.0"
RELEASE_SEQUENCE = 1
RELEASE_TAG = "registry-v0.1.0"
SOURCE_IDS = [
    "PH-DPA-RA10173",
    "PH-DPA-IRR-2016",
    "PH-NPC-CIRC-2023-06",
    "PH-NPC-ADV-2025-02",
]
OBLIGATION_IDS = [
    "PH-PRIVACY-PIA",
    "PH-PRIVACY-MANAGEMENT-PROGRAM",
    "PH-PRIVACY-BY-DESIGN-DEFAULT",
    "PH-PRIVACY-RETENTION",
    "PH-PRIVACY-ACCESS-CONTROL",
    "PH-PRIVACY-BUSINESS-CONTINUITY",
]


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _candidate_bundle(tmp_path: Path, *, overdue_source_id: str | None = None) -> tuple[Path, str]:
    root = tmp_path / "registry-candidate"
    registry = root / "registry"
    registry.mkdir(parents=True)

    _write_json(
        registry / "manifest.json",
        {
            "schema_version": 1,
            "canonical_repository": compliance_registry.CANONICAL_REPOSITORY,
            "registry_version": REGISTRY_VERSION,
            "release_sequence": RELEASE_SEQUENCE,
            "release_tag": RELEASE_TAG,
            "status": "TRUSTED_RELEASE",
            "records": {
                "sources": "registry/sources.json",
                "obligations": "registry/obligations.json",
                "jurisdictions": "registry/jurisdictions.json",
                "providers": "registry/providers.json",
                "source_status": "registry/source-status.json",
                "review_due": "registry/review-due.json",
            },
            "record_counts": {
                "sources": 4,
                "obligations": 6,
                "jurisdictions": 5,
                "providers": 7,
                "source_status": 4,
                "review_due": 4,
            },
        },
    )
    _write_json(
        registry / "sources.json",
        {
            "schema_version": 1,
            "sources": [
                {
                    "source_id": "PH-DPA-RA10173",
                    "jurisdiction_ids": ["PH"],
                    "domains": ["privacy", "data-protection", "personal-data-processing"],
                },
                {
                    "source_id": "PH-DPA-IRR-2016",
                    "jurisdiction_ids": ["PH"],
                    "domains": ["privacy", "data-protection", "personal-data-processing", "security"],
                },
                {
                    "source_id": "PH-NPC-CIRC-2023-06",
                    "jurisdiction_ids": ["PH"],
                    "domains": ["privacy", "data-protection", "security", "privacy-engineering", "business-continuity"],
                },
                {
                    "source_id": "PH-NPC-ADV-2025-02",
                    "jurisdiction_ids": ["PH"],
                    "domains": ["privacy", "privacy-engineering", "systems-lifecycle"],
                },
            ],
        },
    )
    _write_json(
        registry / "obligations.json",
        {
            "schema_version": 1,
            "obligations": [
                {
                    "obligation_id": "PH-PRIVACY-PIA",
                    "source_ids": ["PH-NPC-CIRC-2023-06", "PH-DPA-IRR-2016"],
                    "jurisdiction_ids": ["PH"],
                    "provider_ids": [],
                    "domains": ["privacy", "risk-management", "systems-lifecycle"],
                    "required_evidence": ["privacy_impact_assessment_record"],
                },
                {
                    "obligation_id": "PH-PRIVACY-MANAGEMENT-PROGRAM",
                    "source_ids": ["PH-NPC-CIRC-2023-06"],
                    "jurisdiction_ids": ["PH"],
                    "provider_ids": [],
                    "domains": ["privacy", "governance", "training"],
                    "required_evidence": ["privacy_management_program"],
                },
                {
                    "obligation_id": "PH-PRIVACY-BY-DESIGN-DEFAULT",
                    "source_ids": ["PH-NPC-CIRC-2023-06", "PH-NPC-ADV-2025-02"],
                    "jurisdiction_ids": ["PH"],
                    "provider_ids": [],
                    "domains": ["privacy", "privacy-engineering", "systems-lifecycle"],
                    "required_evidence": ["privacy_requirements_in_system_design"],
                },
                {
                    "obligation_id": "PH-PRIVACY-RETENTION",
                    "source_ids": ["PH-NPC-CIRC-2023-06", "PH-DPA-RA10173"],
                    "jurisdiction_ids": ["PH"],
                    "provider_ids": [],
                    "domains": ["privacy", "data-lifecycle", "retention"],
                    "required_evidence": ["documented_retention_policy"],
                },
                {
                    "obligation_id": "PH-PRIVACY-ACCESS-CONTROL",
                    "source_ids": ["PH-NPC-CIRC-2023-06"],
                    "jurisdiction_ids": ["PH"],
                    "provider_ids": [],
                    "domains": ["privacy", "security", "access-control"],
                    "required_evidence": ["access_control_policy"],
                },
                {
                    "obligation_id": "PH-PRIVACY-BUSINESS-CONTINUITY",
                    "source_ids": ["PH-NPC-CIRC-2023-06"],
                    "jurisdiction_ids": ["PH"],
                    "provider_ids": [],
                    "domains": ["privacy", "security", "business-continuity", "resilience"],
                    "required_evidence": ["business_continuity_plan"],
                },
            ],
        },
    )

    status_entries = []
    due_entries = []
    for source_id in SOURCE_IDS:
        source_status = "REVIEW_OVERDUE" if source_id == overdue_source_id else "VERIFIED_CURRENT"
        status_entries.append({"source_id": source_id, "status": source_status})
        due_entries.append(
            {
                "source_id": source_id,
                "next_review_due": "2000-01-01" if source_id == overdue_source_id else "2099-01-01",
            }
        )
    _write_json(registry / "source-status.json", {"schema_version": 1, "entries": status_entries})
    _write_json(registry / "review-due.json", {"schema_version": 1, "entries": due_entries})
    _write_json(
        registry / "jurisdictions.json",
        {
            "schema_version": 1,
            "jurisdictions": [
                {"jurisdiction_id": "PH", "name": "Philippines"},
                {"jurisdiction_id": "EU-EEA", "name": "European Union / European Economic Area"},
                {"jurisdiction_id": "US", "name": "United States"},
                {"jurisdiction_id": "CA", "name": "Canada"},
                {"jurisdiction_id": "MX", "name": "Mexico"},
            ],
        },
    )
    _write_json(
        registry / "providers.json",
        {
            "schema_version": 1,
            "providers": [
                {"provider_id": "APPLE", "name": "Apple"},
                {"provider_id": "GOOGLE_PLAY", "name": "Google Play"},
                {"provider_id": "MICROSOFT_WINDOWS", "name": "Microsoft / Windows"},
                {"provider_id": "DEBIAN", "name": "Debian"},
                {"provider_id": "FEDORA", "name": "Fedora"},
                {"provider_id": "SNAP", "name": "Snap Store"},
                {"provider_id": "FLATHUB", "name": "Flathub"},
            ],
        },
    )

    files = {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(registry.rglob("*.json"))
    }
    release_manifest = {
        "schema_version": 1,
        "canonical_repository": compliance_registry.CANONICAL_REPOSITORY,
        "registry_version": REGISTRY_VERSION,
        "release_sequence": RELEASE_SEQUENCE,
        "release_tag": RELEASE_TAG,
        "status": "TRUSTED_RELEASE",
        "files": files,
    }
    _write_json(root / "release-manifest.json", release_manifest)
    manifest_sha256 = hashlib.sha256((root / "release-manifest.json").read_bytes()).hexdigest()

    bundle = tmp_path / ("registry-overdue.zip" if overdue_source_id else "registry-current.zip")
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(root.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(root).as_posix())
    return bundle, manifest_sha256


def test_registry_v0_1_candidate_install_query_and_pin(tmp_path: Path) -> None:
    bundle, manifest_sha256 = _candidate_bundle(tmp_path)
    cache = tmp_path / "cache"
    installed = compliance_registry.install_bundle(
        bundle,
        cache,
        expected_manifest_sha256=manifest_sha256,
        expected_tag=RELEASE_TAG,
    )
    assert installed["registry_version"] == REGISTRY_VERSION
    assert installed["release_sequence"] == RELEASE_SEQUENCE
    assert installed["release_tag"] == RELEASE_TAG
    assert installed["manifest_sha256"] == manifest_sha256

    state = compliance_registry.status(cache)
    assert state["registry_status"] == "VERIFIED"
    assert state["freshness"]["state"] == "CURRENT"
    assert state["freshness"]["tracked_source_count"] == 4

    result = compliance_registry.query(cache, jurisdiction="PH", domain="privacy")
    assert sorted(item["source_id"] for item in result["sources"]) == sorted(SOURCE_IDS)
    assert sorted(item["obligation_id"] for item in result["obligations"]) == sorted(OBLIGATION_IDS)

    lock = compliance_registry.pin(cache, tmp_path / "project", ["PH"], ["APPLE", "GOOGLE_PLAY"])
    assert lock["registry_version"] == REGISTRY_VERSION
    assert lock["release_sequence"] == RELEASE_SEQUENCE
    assert lock["release_tag"] == RELEASE_TAG
    assert lock["manifest_sha256"] == manifest_sha256
    assert lock["jurisdictions"] == ["PH"]
    assert lock["providers"] == ["APPLE", "GOOGLE_PLAY"]


def test_registry_v0_1_candidate_preserves_explicit_overdue_state(tmp_path: Path) -> None:
    overdue_source = "PH-NPC-ADV-2025-02"
    bundle, manifest_sha256 = _candidate_bundle(tmp_path, overdue_source_id=overdue_source)
    cache = tmp_path / "cache-overdue"
    compliance_registry.install_bundle(
        bundle,
        cache,
        expected_manifest_sha256=manifest_sha256,
        expected_tag=RELEASE_TAG,
    )
    freshness = compliance_registry.status(cache)["freshness"]
    assert freshness["state"] == "STALE"
    assert freshness["overdue_source_ids"] == [overdue_source]
    assert freshness["stale_source_ids"] == [overdue_source]
    assert freshness["source_states"][overdue_source] == "REVIEW_OVERDUE"
