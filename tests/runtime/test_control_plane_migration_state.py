from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / "machine" / "migration" / "control-plane.v1.json"
SCHEMA_PATH = ROOT / "machine" / "schemas" / "control-plane-migration.schema.json"
EVIDENCE_PATH = ROOT / "machine" / "release-evidence" / "control-plane-refoundation-p0-p1-p9.json"


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_validation_authority_checkpoint_is_adjacent_and_bounded():
    state = _load(STATE_PATH)
    assert state["schema_version"] == "orchestra.control-plane-migration.v1"
    assert state["stage_order"] == [
        "SHADOW",
        "ADVISORY",
        "VALIDATION_AUTHORITY",
        "CANONICAL_PROMOTION_AUTHORITY",
        "LEGACY_RETIRED",
    ]
    assert state["previous_stage"] == "ADVISORY"
    assert state["current_stage"] == "VALIDATION_AUTHORITY"
    previous_index = state["stage_order"].index(state["previous_stage"])
    current_index = state["stage_order"].index(state["current_stage"])
    assert current_index == previous_index + 1
    assert state["transition_policy"] == {
        "adjacent_stage_only": True,
        "exact_conformance_evidence_required": True,
        "separate_governance_authorization_required": True,
        "automatic_stage_progression_allowed": False,
    }
    assert state["authority_effect"] == {
        "machine_contracts_may_inform_runtime_decisions": True,
        "machine_contracts_are_validation_authority": True,
        "machine_contracts_are_canonical_promotion_authority": False,
        "legacy_runtime_authorities_retired": False,
        "installed_integrations_mutated": False,
    }


def test_validation_authority_transition_preserves_prior_evidence_chain():
    state = _load(STATE_PATH)
    evidence = _load(EVIDENCE_PATH)
    transition = state["transition_evidence"]
    assert transition["integration_pull_request"] == evidence["canonical"]["pull_request"] == 294
    assert transition["integration_canonical_sha"] == evidence["canonical"]["merge_commit_sha"]
    assert transition["post_merge_closeout_sha"] == "452572f16f232147d05fe0202cbaea8e82b88e56"
    assert transition["previous_stage_canonical_sha"] == "2b77ccf1a393030c7d4755e64bc5045385de2fde"
    assert transition["validated_source_head_sha"] == evidence["canonical"]["source_head_sha"]
    assert transition["runtime_evidence_index"] == "machine/release-evidence/control-plane-refoundation-p0-p1-p9.json"
    assert evidence["runtime_evidence"]["result"] == "PASS"
    assert evidence["mutation_evidence"]["result"] == "PASS"
    assert transition["shadow_fixture_suite"] == "PASS"


def test_migration_schema_preserves_order_and_nonautomatic_progression():
    state = _load(STATE_PATH)
    schema = _load(SCHEMA_PATH)
    stage_consts = [item["const"] for item in schema["properties"]["stage_order"]["prefixItems"]]
    assert stage_consts == state["stage_order"]
    assert state["current_stage"] in schema["properties"]["current_stage"]["enum"]
    assert state["previous_stage"] in schema["properties"]["previous_stage"]["enum"]
    assert schema["properties"]["transition_policy"]["properties"]["automatic_stage_progression_allowed"]["const"] is False
    assert schema["properties"]["authority_effect"]["properties"]["installed_integrations_mutated"]["const"] is False
