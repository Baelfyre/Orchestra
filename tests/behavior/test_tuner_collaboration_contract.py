import copy
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = ROOT / "scripts/validate_tuner_collaboration_contract.py"
FIXTURES_PATH = ROOT / "tests/behavior/tuner-collaboration-fixtures.json"

spec = importlib.util.spec_from_file_location("tuner_validator", VALIDATOR_PATH)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def fixtures_by_id():
    data = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
    return {item["id"]: item for item in data}


def test_real_repo_passes():
    assert not validator.validate(ROOT)


def test_direct_routes_bypass_tuner():
    fixtures = fixtures_by_id()
    for fixture_id in ("direct-scribe-bypass", "direct-ponytail-bypass"):
        fixture = fixtures[fixture_id]
        assert fixture["activation_decision"] == "BYPASS_SINGLE_OWNER"
        assert "the-tuner" not in fixture["required_specialists"]


def test_active_coordination_remains_with_conductor():
    for fixture in fixtures_by_id().values():
        if fixture["activation_decision"] == "BYPASS_SINGLE_OWNER":
            continue
        assert fixture["primary_router"] == "conductor"
        assert "the-tuner" in fixture["required_specialists"]


def test_contradiction_is_detected_not_resolved():
    fixture = fixtures_by_id()["cipher-cloak-contradiction"]
    assert fixture["expected_status"] == "CONTRADICTED"
    assert fixture["expected_gate"] == "CROSS_SPECIALIST_CONTRADICTION_REVIEW_REQUIRED"
    assert "the-tuner-never-resolves" in fixture["authority_assertions"]


def test_ready_is_not_implementation_authority():
    fixture = fixtures_by_id()["complete-contract-ready"]
    assert fixture["expected_gate"] == "CROSS_LAYER_CONTRACT_READY"
    assert "ready-is-not-implementation-authority" in fixture["authority_assertions"]


def test_minimal_reentry():
    fixture = fixtures_by_id()["security-rule-invalidates-architecture"]
    assert fixture["expected_reentry"] == ["clockwork", "overseer"]


def test_unknown_status_fails_closed():
    assert "AUTO_PROCEED_UNKNOWN" not in validator.REQUIRED_STATUSES


def main():
    test_real_repo_passes()
    test_direct_routes_bypass_tuner()
    test_active_coordination_remains_with_conductor()
    test_contradiction_is_detected_not_resolved()
    test_ready_is_not_implementation_authority()
    test_minimal_reentry()
    test_unknown_status_fails_closed()
    print("Tuner collaboration contract tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
