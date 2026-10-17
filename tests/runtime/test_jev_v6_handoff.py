from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from orchestra_runtime.application.services.jev_v6_handoff import (
    JevV6HandoffError,
    adapt_v6_r2_evidence_packet,
)


_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
_PACKET_PATH = _FIXTURES / "jev_v6_r2_packet.json"
_MANIFEST_PATH = _FIXTURES / "jev_v6_r2_manifest.json"


def _fixture() -> tuple[bytes, dict[str, object], dict[str, object]]:
    packet_bytes = _PACKET_PATH.read_bytes()
    packet = json.loads(packet_bytes)
    manifest = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
    assert hashlib.sha256(packet_bytes).hexdigest() == manifest["fixture_sha256"]
    return packet_bytes, packet, manifest


def _adapt(
    packet_bytes: bytes,
    packet: dict[str, object],
    manifest: dict[str, object],
):
    return adapt_v6_r2_evidence_packet(
        packet_bytes,
        trusted_packet_sha256=manifest["fixture_sha256"],
        trusted_candidate_binding=manifest["candidate_binding"],
    )


def test_v6_fixture_provenance_and_candidate_identity_are_pinned() -> None:
    packet_bytes, packet, manifest = _fixture()
    assert manifest["source_packet_sha256"] == (
        "3695867befaf8bdd6687e2f25d63f898d17537379586cfe98cdfac73d77d6d2c"
    )
    assert packet["candidate"]["head"] == manifest["candidate_binding"]["commit"]
    assert packet["candidate"]["repository"] == (
        "candidate://"
        + manifest["candidate_binding"]["repository"].rsplit("/", 1)[-1].casefold()
    )
    impeccable_input = next(
        item for item in packet["specialist_inputs"] if item["id"] == "IMPECCABLE-V6-R2"
    )
    assert "sha256" not in impeccable_input
    assert manifest["source_evidence"]["impeccable_critique_sha256"] == (
        "dd62b843b6f51214634dd0a869c291cef6affcd2f717695a654258aa9fb18a6c"
    )
    result = _adapt(packet_bytes, packet, manifest)
    assert result.packet_sha256 == manifest["fixture_sha256"]
    assert result.sections["candidate"] == {
        "repository": "Baelfyre/Sinag",
        "commit": "2b6b611fa39418777a3e3353adcde64e5d3a8eee",
        "tree": "63bcf1151d811be73ae8125a0e58d25e128b1c94",
    }


def test_real_v6_shape_maps_to_nine_sections_and_structured_gaps() -> None:
    packet_bytes, packet, manifest = _fixture()
    result = _adapt(packet_bytes, packet, manifest)
    payload = result.to_dict()
    sections = payload["sections"]

    assert result.state_created is False
    assert result.state is None
    assert set(sections) == {
        "contract",
        "candidate",
        "task",
        "findings",
        "verification",
        "overseer_assessment",
        "mitigation_options",
        "dissent",
        "constraints",
    }
    assert sections["contract"] == "orchestra.jev.adjudication.v1"
    assert [item["id"] for item in sections["findings"]] == [
        "C1-I1",
        "C2-I3",
        "I2",
        "I4",
        "I-DETECTOR",
    ]
    assert all(item["status"] == "UNVERIFIED" for item in sections["findings"])
    assert sections["findings"][0]["producer"] == "Cloak"
    assert sections["findings"][3]["producer"] == "Impeccable"
    assert any("artifact:CLOAK-HOST-NATIVE:sha256:" in ref for ref in sections["findings"][0]["evidence_refs"])
    assert "acceptance target (not completed verification)=" in sections["findings"][0]["summary"]
    assert (
        f"packet:sha256:{manifest['fixture_sha256']}#/specialist_inputs/1"
        in sections["findings"][4]["evidence_refs"]
    )
    assert sections["task"] == {"domain": "user_interface"}
    assert sections["verification"] == []
    assert sections["overseer_assessment"] is None
    assert sections["mitigation_options"] == []
    assert sections["dissent"][0]["id"] == "I2"
    assert "Do not treat as confirmed overflow" in sections["dissent"][0]["summary"]
    assert sections["constraints"] == {
        "protected_policy_change_allowed": False,
        "authority_change_allowed": False,
        "scope_expansion_allowed": False,
    }
    assert payload["source_restrictions"] == packet["restrictions"]

    gaps = {item["field_path"]: item for item in payload["missing_evidence"]}
    assert {
        "findings",
        "task.risk_level",
        "task.assurance_depth",
        "verification",
        "overseer_assessment",
        "mitigation_options",
        "specialist_inputs.IMPECCABLE-V6-R2.sha256",
    } <= set(gaps)
    assert "not task risk" in gaps["task.risk_level"]["reason"]
    assert "acceptance text is not a completed check" in gaps["verification"]["reason"].lower()
    assert "overseer assessment" in gaps["overseer_assessment"]["reason"].lower()
    assert "tradeoffs" in gaps["mitigation_options"]["reason"].lower()
    assert gaps["specialist_inputs.IMPECCABLE-V6-R2.sha256"]["source_refs"] == [
        f"packet:sha256:{manifest['fixture_sha256']}#/specialist_inputs/1"
    ]
    serialized = json.dumps(payload)
    assert "D:/Dev" not in serialized
    assert "assessment-a" not in serialized
    assert "assessment_agents" not in serialized


def test_packet_hash_mismatch_fails_before_mapping() -> None:
    packet_bytes, packet, _manifest = _fixture()
    with pytest.raises(JevV6HandoffError) as caught:
        adapt_v6_r2_evidence_packet(
            packet_bytes,
            trusted_packet_sha256="0" * 64,
            trusted_candidate_binding={
                "repository": "Baelfyre/Sinag",
                "commit": "2b6b611fa39418777a3e3353adcde64e5d3a8eee",
                "tree": "63bcf1151d811be73ae8125a0e58d25e128b1c94",
            },
        )
    assert caught.value.code == "PACKET_HASH_MISMATCH"


def test_candidate_identity_is_bound_to_trusted_evidence_and_git_facts() -> None:
    packet_bytes, packet, manifest = _fixture()
    packet["candidate"]["repository"] = "candidate://forged"
    packet["candidate"]["head"] = "c" * 40
    packet["candidate"]["tree"] = "d" * 40
    forged_bytes = json.dumps(packet, separators=(",", ":")).encode("utf-8")
    with pytest.raises(JevV6HandoffError) as wrong_repository:
        adapt_v6_r2_evidence_packet(
            forged_bytes,
            trusted_packet_sha256=hashlib.sha256(forged_bytes).hexdigest(),
            trusted_candidate_binding=manifest["candidate_binding"],
        )
    assert wrong_repository.value.code == "CANDIDATE_REPOSITORY_MISMATCH"

    changed_candidate = dict(manifest["candidate_binding"])
    changed_candidate["commit"] = "c" * 40
    with pytest.raises(JevV6HandoffError) as changed_commit:
        adapt_v6_r2_evidence_packet(
            packet_bytes,
            trusted_packet_sha256=manifest["fixture_sha256"],
            trusted_candidate_binding=changed_candidate,
        )
    assert changed_commit.value.code == "CANDIDATE_COMMIT_MISMATCH"

    with pytest.raises(JevV6HandoffError) as unavailable_binding:
        adapt_v6_r2_evidence_packet(
            packet_bytes,
            trusted_packet_sha256=manifest["fixture_sha256"],
            trusted_candidate_binding=None,
        )
    assert unavailable_binding.value.code == "INVALID_CANDIDATE_BINDING"


def test_packet_tree_mismatch_fails_closed_when_source_supplies_tree() -> None:
    _packet_bytes, packet, manifest = _fixture()
    packet["candidate"]["tree"] = "c" * 40
    changed_bytes = json.dumps(packet, separators=(",", ":")).encode("utf-8")
    with pytest.raises(JevV6HandoffError) as caught:
        adapt_v6_r2_evidence_packet(
            changed_bytes,
            trusted_packet_sha256=hashlib.sha256(changed_bytes).hexdigest(),
            trusted_candidate_binding=manifest["candidate_binding"],
        )
    assert caught.value.code == "CANDIDATE_TREE_MISMATCH"


def test_relaxed_source_restriction_fails_closed() -> None:
    _packet_bytes, packet, manifest = _fixture()
    packet["restrictions"]["no_provider_calls"] = False
    changed_bytes = json.dumps(packet, separators=(",", ":")).encode("utf-8")
    with pytest.raises(JevV6HandoffError) as caught:
        adapt_v6_r2_evidence_packet(
            changed_bytes,
            trusted_packet_sha256=hashlib.sha256(changed_bytes).hexdigest(),
            trusted_candidate_binding=manifest["candidate_binding"],
        )
    assert caught.value.code == "INVALID_CONSTRAINT_SOURCE"


def test_unmapped_or_ambiguous_packet_shape_is_not_silently_normalized() -> None:
    packet_bytes, packet, manifest = _fixture()
    packet["normalized_findings"][0]["id"] = "UNKNOWN-1"
    changed_bytes = json.dumps(packet, separators=(",", ":")).encode("utf-8")
    with pytest.raises(JevV6HandoffError) as caught:
        adapt_v6_r2_evidence_packet(
            changed_bytes,
            trusted_packet_sha256=hashlib.sha256(changed_bytes).hexdigest(),
            trusted_candidate_binding=manifest["candidate_binding"],
        )
    assert caught.value.code == "UNMAPPED_FINDING_SOURCE"

    packet["normalized_findings"][0]["id"] = "C1-I1"
    packet["normalized_findings"][1]["id"] = "C1-I1"
    duplicate_bytes = json.dumps(packet, separators=(",", ":")).encode("utf-8")
    with pytest.raises(JevV6HandoffError) as duplicate_id:
        adapt_v6_r2_evidence_packet(
            duplicate_bytes,
            trusted_packet_sha256=hashlib.sha256(duplicate_bytes).hexdigest(),
            trusted_candidate_binding=manifest["candidate_binding"],
        )
    assert duplicate_id.value.code == "INVALID_FINDING_RECORD"

    packet["unexpected"] = "not part of the V6-R2 packet contract"
    invalid_schema_bytes = json.dumps(packet, separators=(",", ":")).encode("utf-8")
    with pytest.raises(JevV6HandoffError) as invalid_schema:
        adapt_v6_r2_evidence_packet(
            invalid_schema_bytes,
            trusted_packet_sha256=hashlib.sha256(invalid_schema_bytes).hexdigest(),
            trusted_candidate_binding=manifest["candidate_binding"],
        )
    assert invalid_schema.value.code == "INVALID_PACKET_SCHEMA"

    duplicate_key_bytes = b'{"task_id":"override",' + packet_bytes[1:]
    with pytest.raises(JevV6HandoffError) as duplicate_key:
        adapt_v6_r2_evidence_packet(
            duplicate_key_bytes,
            trusted_packet_sha256=hashlib.sha256(duplicate_key_bytes).hexdigest(),
            trusted_candidate_binding=manifest["candidate_binding"],
        )
    assert duplicate_key.value.code == "INVALID_PACKET"
