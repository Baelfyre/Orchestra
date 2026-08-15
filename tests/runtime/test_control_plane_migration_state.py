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


def test_advisory_migration_checkpoint_is_adjacent_and_non_authorizing():
    state = _load(STATE_PATH)
    assert state["schema_version"] == "orchestra.control-plane-migration.v1"
    assert state["stage_order"] == [
        "SHADOW",
        "ADVISORY",
        "VALIDATION_AUTHORITY",
        "CANONICAL_PROMOTION_AUTHORITY",
        "LEGACY_RETIRED",
    ]
    assert state["previous_stage"] == "SHADOW"
    assert state["current_stage"] == "ADVISORY"
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
        "machine_contracts_are_validation_authority": False,
        "machine_contracts_are_canonical_promotion_authority": False,
        "legacy_runtime_authorities_retired": False,
        "installed_integrations_mutated": False,
    }


def test_advisory_transition_references_the_canonical_integrated_evidence():
    state = _load(STATE_PATH)
    evidence = _load(EVIDENCE_PATH)
    transition = state["transition_evidence"]
    assert transition["integration_pull_request"] == evidence["canonical"]["pull_request"] == 294
    assert transition["integration_canonical_sha"] == evidence["canonical"]["merge_commit_sha"]
    assert transition["validated_source_head_sha"] == evidence["canonical"]["source_head_sha"]
    assert transition["runtime_evidence_index"] == "machine/release-evidence/control-plane-refoundation-p0-p1-p9.json"
    assert evidence["runtime_evidence"]["result"] == "PASS"
    assert evidence["mutation_evidence"]["result"] == "PASS"
    assert evidence["boundaries"]["p9_migration_stage"] == "SHADOW"
    assert transition["shadow_fixture_suite"] == "PASS"


def test_migration_schema_encodes_the_same_advisory_boundary():
    state = _load(STATE_PATH)
    schema = _load(SCHEMA_PATH)
    stage_consts = [item["const"] for item in schema["properties"]["stage_order"]["prefixItems"]]
    assert stage_consts == state["stage_order"]
    assert schema["properties"]["current_stage"]["const"] == state["current_stage"]
    assert schema["properties"]["previous_stage"]["const"] == state["previous_stage"]
    assert schema["properties"]["authority_effect"]["properties"]["installed_integrations_mutated"]["const"] is False
