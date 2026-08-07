import copy
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/behavior/cross-layer-integrity-fixtures.json"
PROFILE_PROTOCOL = ROOT / "docs/validation/CROSS_LAYER_INTEGRITY_PROFILE_PROTOCOL.md"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load_module(
    "cross_layer_integrity_validator",
    ROOT / "scripts/validate_cross_layer_integrity_contract.py",
)
synchronicity_validator = load_module(
    "synchronicity_validator",
    ROOT / "scripts/validate_cross_layer_synchronicity_contract.py",
)


def fixture_data():
    return json.loads(FIXTURES.read_text(encoding="utf-8"))


def protocol_bytes():
    text = PROFILE_PROTOCOL.read_text(encoding="utf-8")
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def test_real_repo_passes():
    assert not validator.validate(ROOT)


def test_original_frontend_backend_contract_still_passes():
    assert not synchronicity_validator.validate(ROOT)


def test_each_profile_covers_exact_status_set():
    data = fixture_data()
    assert set(data["profiles"]) == set(validator.PROFILE_SPECS)
    for name, spec in validator.PROFILE_SPECS.items():
        profile = data["profiles"][name]
        assert tuple(profile["stages"]) == spec["stages"]
        assert set(profile["required_evidence"]) == spec["evidence"]
        assert {case["expected_status"] for case in profile["cases"]} == validator.STATUSES


def test_workflows_cover_exact_profile_stage_order():
    data = fixture_data()
    for name, spec in validator.PROFILE_SPECS.items():
        kinds = set()
        for workflow in data["profiles"][name]["executable_workflows"]:
            kinds.add(workflow["kind"])
            assert [entry["stage"] for entry in workflow["trace"]] == list(spec["stages"])
            assert all(entry["owner"] in validator.OWNERS for entry in workflow["trace"])
        assert kinds == {"HAPPY_PATH", "FAILURE_PATH"}


def test_backend_persistence_ownership():
    cases = {case["id"]: case for case in fixture_data()["profiles"]["backend_persistence"]["cases"]}
    assert cases["backend-contract-mapping-gap"]["finding_owner"] == "chronicler"
    assert cases["backend-transaction-reentry"]["finding_owner"] == "chronicler"
    assert cases["backend-evidence-missing"]["finding_owner"] == "overseer"
    assert cases["backend-persistence-contradiction"]["finding_owner"] == "the-tuner"


def test_cross_module_ownership():
    cases = {case["id"]: case for case in fixture_data()["profiles"]["cross_module_logic"]["cases"]}
    assert cases["cross-module-flow-gap"]["finding_owner"] == "clockwork"
    assert cases["cross-module-side-effect-reentry"]["finding_owner"] == "clockwork"
    assert cases["cross-module-evidence-missing"]["finding_owner"] == "overseer"
    assert cases["cross-module-contradiction"]["finding_owner"] == "the-tuner"


def test_unknown_status_fails_closed():
    data = fixture_data()
    data["profiles"]["backend_persistence"]["cases"][0]["expected_status"] = "UNKNOWN"
    errors = validator.validate_fixtures(data, protocol_bytes())
    assert any("unknown status" in error for error in errors)


def test_unknown_profile_fails_closed():
    data = fixture_data()
    data["profiles"]["unknown"] = copy.deepcopy(data["profiles"]["cross_module_logic"])
    errors = validator.validate_fixtures(data, protocol_bytes())
    assert any("profiles must contain exactly" in error for error in errors)


def test_protocol_hash_mismatch_fails_closed():
    data = fixture_data()
    data["contract_identity"]["protocol_sha256"] = "0" * 64
    errors = validator.validate_fixtures(data, protocol_bytes())
    assert any("protocol_sha256 does not match" in error for error in errors)


def test_missing_executable_evidence_fails_closed():
    data = fixture_data()
    case = next(
        item for item in data["profiles"]["cross_module_logic"]["cases"]
        if item["id"] == "cross-module-evidence-missing"
    )
    case["evidence"]["executable_workflow"] = True
    errors = validator.validate_fixtures(data, protocol_bytes())
    assert any("executable evidence requires workflow_id" in error for error in errors)


def test_incomplete_trace_fails_closed():
    data = fixture_data()
    data["profiles"]["backend_persistence"]["executable_workflows"][0]["trace"].pop()
    errors = validator.validate_fixtures(data, protocol_bytes())
    assert any("trace must contain profile stages in exact order" in error for error in errors)


def test_incomplete_finding_fails_closed():
    data = fixture_data()
    case = next(
        item for item in data["profiles"]["backend_persistence"]["cases"]
        if item["id"] == "backend-contract-mapping-gap"
    )
    del case["finding"]["required_validation"]
    errors = validator.validate_fixtures(data, protocol_bytes())
    assert any("complete finding object" in error for error in errors)


def test_stale_identity_requires_full_continuity_chain():
    data = fixture_data()
    case = next(
        item for item in data["profiles"]["cross_module_logic"]["cases"]
        if item["id"] == "cross-module-contract-stale"
    )
    case["expected_reentry"] = ["the-tuner", "overseer"]
    errors = validator.validate_fixtures(data, protocol_bytes())
    assert any("must re-enter Tuner, Overseer, and Arbiter" in error for error in errors)


def test_contradiction_requires_conductor_reentry():
    data = fixture_data()
    case = next(
        item for item in data["profiles"]["backend_persistence"]["cases"]
        if item["id"] == "backend-persistence-contradiction"
    )
    case["expected_reentry"] = ["clockwork", "chronicler"]
    errors = validator.validate_fixtures(data, protocol_bytes())
    assert any("contradiction must route back through Conductor" in error for error in errors)


def main():
    test_real_repo_passes()
    test_original_frontend_backend_contract_still_passes()
    test_each_profile_covers_exact_status_set()
    test_workflows_cover_exact_profile_stage_order()
    test_backend_persistence_ownership()
    test_cross_module_ownership()
    test_unknown_status_fails_closed()
    test_unknown_profile_fails_closed()
    test_protocol_hash_mismatch_fails_closed()
    test_missing_executable_evidence_fails_closed()
    test_incomplete_trace_fails_closed()
    test_incomplete_finding_fails_closed()
    test_stale_identity_requires_full_continuity_chain()
    test_contradiction_requires_conductor_reentry()
    print("Cross-layer integrity profile tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
