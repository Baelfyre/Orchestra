from __future__ import annotations

import hashlib
import json
from pathlib import Path

import jsonschema
import pytest

from scripts import uix9_static_evidence_v2 as evidence

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / evidence.SCHEMA


def _manifest(path: str, content: bytes) -> dict:
    canonical = content.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    sha = hashlib.sha256(canonical).hexdigest()
    material = {"path": path, "role": "TEST_GUIDANCE", "revision_identity": "candidate-fixture-v1", "sha256": sha}
    return {
        "canonical_sha": evidence.FROZEN_SOURCE_SHA,
        "materials": [{**material, "canonical_blob_digest": sha}],
        "guidance_digest": evidence._records_digest([material]),
    }


def test_frozen_v1_uses_immutable_manifest_and_material_objects() -> None:
    context = evidence.guidance_context(ROOT, evidence.FROZEN_HISTORICAL_V1)
    assert context["guidance_digest"] == evidence.FROZEN_GUIDANCE_DIGEST
    assert context["manifest_snapshot_sha"] == evidence.FROZEN_MANIFEST_SHA
    assert evidence.frozen_source_digest(ROOT, "evaluator") == "d585010eb83ec23b1df2c3512868e9ff5285e7dced1393dcafb0233b835f7ae1"
    assert evidence.frozen_source_digest(ROOT, "validator") == "285494688ef105c813ef5f449f1e13b75529c8cddbf8a42ea76d283a9d5eecf3"


def test_candidate_guidance_has_distinct_v2_identity() -> None:
    frozen = evidence.guidance_context(ROOT, evidence.FROZEN_HISTORICAL_V1)
    candidate = evidence.guidance_context(ROOT, evidence.CANDIDATE_STATIC_V2)
    assert candidate["guidance_digest"] == "2d0c03e755b830e749ed9842d84cb6263d1aa81bea38c1cec43ac7c321bd060c"
    assert candidate["guidance_digest"] != frozen["guidance_digest"]
    assert candidate["context"] == evidence.CANDIDATE_STATIC_V2


def test_unknown_context_fails_closed() -> None:
    with pytest.raises(evidence.EvidenceError, match="unsupported guidance context"):
        evidence.guidance_context(ROOT, "CANDIDATE_V1_APPROVED")


def test_candidate_guidance_material_tampering_fails_closed(tmp_path: Path) -> None:
    material = tmp_path / "material.md"
    material.write_bytes(b"approved guidance\n")
    manifest = _manifest("material.md", material.read_bytes())
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    assert evidence._candidate_context(tmp_path, "manifest.json")["guidance_digest"] == manifest["guidance_digest"]
    material.write_bytes(b"tampered guidance\n")
    with pytest.raises(evidence.EvidenceError, match="material digest mismatch"):
        evidence._candidate_context(tmp_path, "manifest.json")


def test_candidate_manifest_path_traversal_is_rejected(tmp_path: Path) -> None:
    manifest = _manifest("../outside.md", b"outside\n")
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(evidence.EvidenceError, match="path traversal"):
        evidence._candidate_context(tmp_path, "manifest.json")


def test_symlink_material_is_rejected(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    material = tmp_path / "linked.md"
    material.write_bytes(b"linked content\n")
    manifest = _manifest("linked.md", material.read_bytes())
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    original = Path.is_symlink
    monkeypatch.setattr(Path, "is_symlink", lambda path: path.name == "linked.md" or original(path))
    with pytest.raises(evidence.EvidenceError, match="symlink input rejected"):
        evidence._candidate_context(tmp_path, "manifest.json")


def test_candidate_evidence_binds_worktree_and_preserves_human_hold() -> None:
    record = evidence.build_candidate_evidence(ROOT)
    evidence.validate_candidate_evidence(ROOT, record, SCHEMA)
    assert record["status"] == "DRAFT_DIAGNOSTIC"
    assert record["authority"]["human_review"] == "PENDING"
    assert record["frozen_predecessor"]["historical_approval_inherited"] is False
    assert record["authority"]["live_uix9b_authorized"] is False


def test_candidate_evidence_rejects_changed_fingerprint() -> None:
    record = evidence.build_candidate_evidence(ROOT)
    record["candidate"]["content_fingerprint"] = "0" * 64
    with pytest.raises(evidence.EvidenceError, match="candidate binding changed"):
        evidence.validate_candidate_evidence(ROOT, record, SCHEMA)


def test_candidate_evidence_rejects_changed_frozen_manifest_hash() -> None:
    record = evidence.build_candidate_evidence(ROOT)
    record["frozen_predecessor"]["manifest_sha256"] = "0" * 64
    with pytest.raises(evidence.EvidenceError, match="predecessor binding"):
        evidence.validate_candidate_evidence(ROOT, record, SCHEMA)


def test_candidate_evidence_rejects_validator_version_substitution() -> None:
    record = evidence.build_candidate_evidence(ROOT)
    record["implementation"]["validator"]["version"] = "unverified"
    with pytest.raises(evidence.EvidenceError, match="implementation identity"):
        evidence.validate_candidate_evidence(ROOT, record, SCHEMA)


def test_candidate_evidence_rejects_forged_merge_approval() -> None:
    record = evidence.build_candidate_evidence(ROOT)
    record["authority"]["merge_authorized"] = True
    with pytest.raises(evidence.EvidenceError, match="schema failure"):
        evidence.validate_candidate_evidence(ROOT, record, SCHEMA)


def test_candidate_evidence_rejects_approved_status() -> None:
    record = evidence.build_candidate_evidence(ROOT)
    record["status"] = "G8_APPROVED"
    with pytest.raises(evidence.EvidenceError, match="schema failure"):
        evidence.validate_candidate_evidence(ROOT, record, SCHEMA)


def test_external_test_log_tampering_is_detected(tmp_path: Path) -> None:
    log = tmp_path / "pytest.log"
    log.write_bytes(b"observed output\n")
    digest = hashlib.sha256(log.read_bytes()).hexdigest()
    evidence._external_file(ROOT, str(log), digest)
    log.write_bytes(b"changed output\n")
    with pytest.raises(evidence.EvidenceError, match="external test evidence mismatch"):
        evidence._external_file(ROOT, str(log), digest)


def test_external_test_artifact_with_symlinked_parent_is_rejected(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    parent = tmp_path / "linked-parent"
    parent.mkdir()
    artifact = parent / "pytest.log"
    artifact.write_bytes(b"evidence\n")
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    original = Path.is_symlink
    monkeypatch.setattr(Path, "is_symlink", lambda path: path.name == "linked-parent" or original(path))
    with pytest.raises(evidence.EvidenceError, match="not symlinked"):
        evidence._external_file(ROOT, str(artifact), digest)


def test_schema_rejects_unknown_properties_and_versions() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    validator = jsonschema.Draft202012Validator(schema)
    record = evidence.build_candidate_evidence(ROOT)
    record["unexpected"] = True
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(record)
    record.pop("unexpected")
    record["schema_version"] = "uix9.candidate-static-evidence.v1"
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(record)