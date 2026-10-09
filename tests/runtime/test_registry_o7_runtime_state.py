from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / "docs" / "architecture" / "contracts" / "registry-o7-runtime-state.v1.json"


def test_o7_runtime_state_is_bound_to_verified_registry_r7_trusted_surface() -> None:
    state = json.loads(STATE.read_text(encoding="utf-8"))
    assert state["schema_version"] == "orchestra.registry-o7-runtime-state.v1"
    assert state["authority"] == "DESCRIPTIVE_NON_AUTHORIZING"
    registry = state["registry_dependency"]
    assert registry["canonical_commit_sha"] == "4926a3b5f48122dd45f3c8e83a12b8d071dd5387"
    assert registry["canonical_tree_sha"] == "01be27bde90f6faa59ab74d60ba13af480c11b1d"
    assert registry["signature"] == "VERIFIED"
    assert registry["canonical_validation"] == "PASS"
    assert registry["entry_condition_satisfied"] is True
    release = state["trusted_release"]
    assert release["release_tag"] == "registry-v0.4.0"
    assert release["registry_version"] == "0.4.0"
    assert release["release_sequence"] == 4
    assert release["publication_state"] == "PUBLISHED_IMMUTABLE_VERIFIED"
    assert release["immutable"] is True


def test_o7_runtime_state_records_verified_joint_conformance_without_authority_expansion() -> None:
    state = json.loads(STATE.read_text(encoding="utf-8"))
    assert state["implementation"]["status"] == "CANONICAL_MERGED_VERIFIED"
    phases = state["implementation"]["phases"]
    assert all(phases[f"O7.{index}"] == "CANONICAL_MERGED_VERIFIED" for index in range(1, 8))
    assert state["transport"]["registry_gateway_semantics_are_reimplemented_in_orchestra"] is False
    assert state["transport"]["mcp_currently_available"] is True
    assert state["transport"]["mcp_read_only"] is True
    assert state["release_boundary"]["trusted_registry_v0_4_0_published"] is True
    assert state["release_boundary"]["trusted_registry_v0_4_0_immutable_verified"] is True
    assert state["release_boundary"]["joint_r7_o7_conformance_complete"] is True
    assert state["release_boundary"]["orchestra_release_integration_authorized_by_this_state"] is False
    assert state["joint_conformance"]["latest_evidence_status"] == "PASS"
    assert state["authority_expansion"] is False
