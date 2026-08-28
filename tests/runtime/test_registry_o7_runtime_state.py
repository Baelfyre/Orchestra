from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / "docs" / "architecture" / "contracts" / "registry-o7-runtime-state.v1.json"


def test_o7_runtime_state_is_bound_to_verified_registry_r7_direct_surface() -> None:
    state = json.loads(STATE.read_text(encoding="utf-8"))
    assert state["schema_version"] == "orchestra.registry-o7-runtime-state.v1"
    assert state["authority"] == "DESCRIPTIVE_NON_AUTHORIZING"
    registry = state["registry_dependency"]
    assert registry["canonical_commit_sha"] == "155c21ab54f704d876ae4a0c2d995f5591f13930"
    assert registry["canonical_tree_sha"] == "ea99fce806a455c4c1e2c912277c44d3595f54d8"
    assert registry["signature"] == "VERIFIED"
    assert registry["canonical_validation"] == "PASS"
    assert registry["entry_condition_satisfied"] is True


def test_o7_runtime_state_preserves_future_release_and_mcp_gates() -> None:
    state = json.loads(STATE.read_text(encoding="utf-8"))
    phases = state["implementation"]["phases"]
    assert all(phases[f"O7.{index}"] == "IMPLEMENTED" for index in range(1, 7))
    assert phases["O7.7"] == "BLOCKED_PENDING_R7_7_AND_TRUSTED_RELEASE_INTEGRATION"
    assert state["transport"]["registry_gateway_semantics_are_reimplemented_in_orchestra"] is False
    assert state["transport"]["mcp_currently_available"] is False
    assert state["release_boundary"]["trusted_registry_v0_4_0_published"] is False
    assert state["release_boundary"]["joint_r7_o7_conformance_complete"] is False
    assert state["authority_expansion"] is False
