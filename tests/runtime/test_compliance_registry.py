import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from scripts import compliance_registry


def _write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _bundle(tmp_path: Path, version="v1.0.0", sequence=1):
    root = tmp_path / f"bundle-{sequence}"
    registry = root / "registry"
    registry.mkdir(parents=True)
    _write_json(registry / "sources.json", {"schema_version": 1, "sources": [{"source_id": "SRC-1", "jurisdiction_ids": ["PH"], "domains": ["privacy"]}]})
    _write_json(registry / "obligations.json", {"schema_version": 1, "obligations": [{"obligation_id": "OBL-1", "source_ids": ["SRC-1"], "jurisdiction_ids": ["PH"], "provider_ids": ["APPLE"], "domains": ["privacy"], "required_evidence": ["test"]}]})
    _write_json(registry / "source-status.json", {"schema_version": 1, "entries": [{"source_id": "SRC-1", "status": "VERIFIED_CURRENT"}]})
    _write_json(registry / "review-due.json", {"schema_version": 1, "entries": []})
    files = {}
    for path in sorted(registry.rglob("*.json")):
        files[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    _write_json(root / "release-manifest.json", {"schema_version": 1, "canonical_repository": compliance_registry.CANONICAL_REPOSITORY, "registry_version": version, "release_sequence": sequence, "status": "TRUSTED_RELEASE", "release_tag": version, "files": files})
    result = tmp_path / f"{version}-{sequence}.zip"
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


def test_older_sequence_requires_explicit_override(tmp_path):
    cache = tmp_path / "cache"
    compliance_registry.install_bundle(_bundle(tmp_path, "v2.0.0", 2), cache, expected_tag="v2.0.0")
    with pytest.raises(compliance_registry.RegistryError, match="rollback rejected"):
        compliance_registry.install_bundle(_bundle(tmp_path, "v1.0.0", 1), cache, expected_tag="v1.0.0")
