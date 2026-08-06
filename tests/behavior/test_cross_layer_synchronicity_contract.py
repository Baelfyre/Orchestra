import copy
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = ROOT / "scripts/validate_cross_layer_synchronicity_contract.py"
FIXTURES_PATH = ROOT / "tests/behavior/cross-layer-synchronicity-fixtures.json"

spec = importlib.util.spec_from_file_location("synchronicity_validator", VALIDATOR_PATH)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def fixtures():
    return json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))


def cases_by_id():
    return {case["id"]: case for case in fixtures()["cases"]}


def test_real_repo_passes():
    assert not validator.validate(ROOT)


def test_happy_path_requires_complete_evidence():
    case = cases_by_id()["happy-path-aligned"]
    assert case["finding_owner"] is None
    assert all(case["evidence"].values())
    assert case["expected_status"] == "CROSS_LAYER_ALIGNMENT_CONFIRMED"


def test_failure_paths_have_single_owners():
    for case in cases_by_id().values():
        if case["expected_status"] != "CROSS_LAYER_ALIGNMENT_CONFIRMED":
            assert case["finding_owner"] in validator.OWNERS


def test_authorization_mismatch_routes_to_cipher():
    case = cases_by_id()["authorization-mismatch"]
    assert case["finding_owner"] == "cipher"
    assert case["expected_reentry"] == ["cipher", "cloak", "overseer"]


def test_stale_identity_reenters_continuity_chain():
    case = cases_by_id()["stale-contract-identity"]
    assert case["expected_reentry"] == ["the-tuner", "overseer", "arbiter"]


def test_unknown_status_fails_closed():
    data = fixtures()
    data["cases"][0]["expected_status"] = "AUTO_CONTINUE_UNKNOWN"
    assert any("unknown status" in error for error in validator.validate_fixtures(data))


def test_missing_executable_evidence_fails_closed():
    data = copy.deepcopy(fixtures())
    case = next(item for item in data["cases"] if item["id"] == "missing-executable-evidence")
    case["evidence"]["executable_workflow"] = True
    assert any("must identify a missing evidence field" in error for error in validator.validate_fixtures(data))


def main():
    test_real_repo_passes()
    test_happy_path_requires_complete_evidence()
    test_failure_paths_have_single_owners()
    test_authorization_mismatch_routes_to_cipher()
    test_stale_identity_reenters_continuity_chain()
    test_unknown_status_fails_closed()
    test_missing_executable_evidence_fails_closed()
    print("Cross-layer synchronicity contract tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
