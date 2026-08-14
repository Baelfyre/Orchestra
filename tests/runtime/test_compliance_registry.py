import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from scripts import compliance_registry


def _write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _bundle(
    tmp_path: Path,
    version="1.0.0",
    sequence=1,
    *,
    tag=None,
    canonical_repository=None,
    source_status="VERIFIED_CURRENT",
    next_review_due=None,
    tamper_after_manifest=False,
    add_unlisted_file=False,
):
    root = tmp_path / f"bundle-{sequence}-{len(list(tmp_path.glob('bundle-*')))}"
    registry = root / "registry"
    registry.mkdir(parents=True)
    _write_json(
        registry / "sources.json",
        {"schema_version": 1, "sources": [{"source_id": "SRC-1", "jurisdiction_ids": ["PH"], "domains": ["privacy"]}]},
    )
    _write_json(
        registry / "obligations.json",
        {
            "schema_version": 1,
            "obligations": [
                {
                    "obligation_id": "OBL-1",
                    "source_ids": ["SRC-1"],
                    "jurisdiction_ids": ["PH"],
                    "provider_ids": ["APPLE"],
                    "domains": ["privacy"],
                    "required_evidence": ["test"],
                }
            ],
        },
    )
    _write_json(
        registry / "source-status.json",
        {"schema_version": 1, "entries": [{"source_id": "SRC-1", "status": source_status}]},
    )
    due_entries = [] if next_review_due is None else [{"source_id": "SRC-1", "next_review_due": next_review_due}]
    _write_json(registry / "review-due.json", {"schema_version": 1, "entries": due_entries})
    _write_json(
        registry / "jurisdictions.json",
        {"schema_version": 1, "jurisdictions": [{"jurisdiction_id": "PH", "name": "Philippines"}]},
    )
    _write_json(
        registry / "providers.json",
        {"schema_version": 1, "providers": [{"provider_id": "APPLE", "name": "Apple"}]},
    )
    files = {}
    for path in sorted(registry.rglob("*.json")):
        files[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    release_tag = tag or f"v{version}"
    _write_json(
        root / "release-manifest.json",
        {
            "schema_version": 1,
            "canonical_repository": canonical_repository or compliance_registry.CANONICAL_REPOSITORY,
            "registry_version": version,
            "release_sequence": sequence,
            "status": "TRUSTED_RELEASE",
            "release_tag": release_tag,
            "files": files,
        },
    )
    if tamper_after_manifest:
        _write_json(registry / "sources.json", {"schema_version": 1, "sources": []})
    if add_unlisted_file:
        (root / "unexpected.txt").write_text("not covered by the release manifest\n", encoding="utf-8")
    result = tmp_path / f"bundle-{sequence}-{len(list(tmp_path.glob('*.zip')))}.zip"
    with zipfile.ZipFile(result, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in root.rglob("*"):
            if path.is_file():
                archive.write(path, path.relative_to(root).as_posix())
    return result


def test_status_without_registry(tmp_path):
    assert compliance_registry.status(tmp_path / "cache")["registry_status"] == "NO_REGISTRY"


def test_local_install_query_and_pin(tmp_path):
    cache = tmp_path / "cache"
    compliance_registry.install_bundle(_bundle(tmp_path), cache, expected_tag="v1.0.0")
    result = compliance_registry.query(cache, jurisdiction="PH", provider="APPLE", domain="privacy")
    assert [item["obligation_id"] for item in result["obligations"]] == ["OBL-1"]
    lock = compliance_registry.pin(cache, tmp_path / "project", ["PH"], ["APPLE"])
    assert Path(lock["lockfile"]).is_file()
    assert lock["release_tag"] == "v1.0.0"


def test_older_sequence_requires_explicit_override(tmp_path):
    cache = tmp_path / "cache"
    compliance_registry.install_bundle(_bundle(tmp_path, "2.0.0", 2), cache, expected_tag="v2.0.0")
    with pytest.raises(compliance_registry.RegistryError, match="rollback rejected"):
        compliance_registry.install_bundle(_bundle(tmp_path, "1.0.0", 1), cache, expected_tag="v1.0.0")


def test_release_sequence_collision_is_rejected(tmp_path):
    cache = tmp_path / "cache"
    compliance_registry.install_bundle(_bundle(tmp_path, "1.0.0", 1), cache, expected_tag="v1.0.0")
    with pytest.raises(compliance_registry.RegistryError, match="release sequence collision"):
        compliance_registry.install_bundle(_bundle(tmp_path, "1.0.1", 1), cache, expected_tag="v1.0.1")


def test_wrong_canonical_repository_is_rejected(tmp_path):
    with pytest.raises(compliance_registry.RegistryError, match="canonical_repository mismatch"):
        compliance_registry.install_bundle(
            _bundle(tmp_path, canonical_repository="example/attacker"),
            tmp_path / "cache",
            expected_tag="v1.0.0",
        )


def test_content_hash_tampering_is_rejected(tmp_path):
    with pytest.raises(compliance_registry.RegistryError, match="hash mismatch"):
        compliance_registry.install_bundle(
            _bundle(tmp_path, tamper_after_manifest=True),
            tmp_path / "cache",
            expected_tag="v1.0.0",
        )


def test_unlisted_bundle_file_is_rejected(tmp_path):
    with pytest.raises(compliance_registry.RegistryError, match="file inventory mismatch"):
        compliance_registry.install_bundle(
            _bundle(tmp_path, add_unlisted_file=True),
            tmp_path / "cache",
            expected_tag="v1.0.0",
        )


def test_unsafe_archive_path_is_rejected(tmp_path):
    archive = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("../escape.txt", "escape")
    with pytest.raises(compliance_registry.RegistryError, match="unsafe ZIP path"):
        compliance_registry.install_bundle(archive, tmp_path / "cache")


def test_unsafe_registry_version_is_rejected_before_install_path_use(tmp_path):
    with pytest.raises(compliance_registry.RegistryError, match="safe version token"):
        compliance_registry.install_bundle(
            _bundle(tmp_path, version="../escape", tag="v1.0.0"),
            tmp_path / "cache",
            expected_tag="v1.0.0",
        )


def test_release_tag_mismatch_is_rejected(tmp_path):
    with pytest.raises(compliance_registry.RegistryError, match="release tag"):
        compliance_registry.install_bundle(_bundle(tmp_path), tmp_path / "cache", expected_tag="v9.9.9")


def test_malformed_active_state_fails_closed(tmp_path):
    cache = tmp_path / "cache"
    compliance_registry.install_bundle(_bundle(tmp_path), cache, expected_tag="v1.0.0")
    active_path = cache / "active.json"
    active = json.loads(active_path.read_text(encoding="utf-8"))
    active["release_sequence"] = "1"
    _write_json(active_path, active)
    assert compliance_registry.status(cache)["registry_status"] == "INTEGRITY_FAILED"


def test_non_current_source_state_requires_review(tmp_path):
    cache = tmp_path / "cache"
    compliance_registry.install_bundle(
        _bundle(tmp_path, source_status="CURRENT_WITH_PENDING_CHANGE"),
        cache,
        expected_tag="v1.0.0",
    )
    summary = compliance_registry.status(cache)["freshness"]
    assert summary["state"] == "REVIEW_REQUIRED"
    assert summary["attention_source_ids"] == ["SRC-1"]


def test_overdue_source_is_stale(tmp_path):
    cache = tmp_path / "cache"
    compliance_registry.install_bundle(
        _bundle(tmp_path, next_review_due="2000-01-01"),
        cache,
        expected_tag="v1.0.0",
    )
    summary = compliance_registry.status(cache)["freshness"]
    assert summary["state"] == "STALE"
    assert summary["overdue_source_ids"] == ["SRC-1"]


def test_pin_rejects_unknown_taxonomy_ids(tmp_path):
    cache = tmp_path / "cache"
    compliance_registry.install_bundle(_bundle(tmp_path), cache, expected_tag="v1.0.0")
    with pytest.raises(compliance_registry.RegistryError, match="unknown jurisdiction"):
        compliance_registry.pin(cache, tmp_path / "project", ["ZZ"], ["APPLE"])


def test_update_check_compares_release_tag_not_registry_version(tmp_path, monkeypatch):
    cache = tmp_path / "cache"
    compliance_registry.install_bundle(_bundle(tmp_path, version="1.0.0", tag="v1.0.0"), cache, expected_tag="v1.0.0")
    monkeypatch.setattr(compliance_registry, "_latest_release", lambda: {"tag_name": "v1.0.0"})
    result = compliance_registry.update_check(cache)
    assert result["active_version"] == "1.0.0"
    assert result["active_tag"] == "v1.0.0"
    assert result["update_available"] is False
