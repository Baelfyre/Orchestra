import copy
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = ROOT / "scripts/validate_cross_layer_integrity_contract.py"
SYNCHRONICITY_VALIDATOR_PATH = ROOT / "scripts/validate_cross_layer_synchronicity_contract.py"
FIXTURES_PATH = ROOT / "tests/behavior/cross-layer-integrity-fixtures.json"
PROFILE_PROTOCOL_PATH = ROOT / "docs/validation/CROSS_LAYER_INTEGRITY_PROFILE_PROTOCOL.md"


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = _load_module("cross_layer_integrity_validator", VALIDATOR_PATH)
synchronicity_validator = _load_module(
    "synchronicity_validator", SYNCHRONICITY_VALIDATOR_PATH
)


def fixtures():
    return json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))


def protocol_bytes():
    text = PROFILE_PROTOCOL_PATH.read_text(encoding="utf-8")
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def profile_cases(profile_name):
    return {
        case["id"]: case
        for case in fixtures()["profiles"][profile_name]["cases"]
    }


def test_real_repo_passes():
    assert not validator.validate(ROOT)


def test_original_frontend_backend_contract_still_passes():
    assert not synchronicity_validator.validate(ROOT)


def test_profiles_cover_exact_status_set():
    data = fixtures()
    assert set(data["profiles"]) == set(validator.PROFILE_SPECS)
    for name, spec in validator.PROFILE_SPECS.items():
        profile = data["profiles"][name]
        assert tuple(profile["stages"]) == spec["stages"]
        assert set(profile["required_evidence"]) == spec["evidence"]
        assert {
            case["expected_status"] for case in profile["cases"]
        } == validator.REQUIRED_STATUSES


def test_workflows_trace_profile_stages_in_order():
    data = fixtures()
    for name, spec in validator.PROFILE_SPECS.items():
        for workflow in data["profiles"][name]["executable_workflows"]:
            assert [entry["stage"] for entry in workflow["trace"]] == list(
                spec["stages"]
            )
            assert all(entry["owner"] in validator.OWNERS for entry in workflow["trace"])
            assert all(entry["source_ref"] for entry in workflow["trace"])
            assert all(entry["evidence_ref"] for entry in workflow["trace"])
            assert all(entry["result"] for entry in workflow["trace"])


def test_backend_persistence_owner_boundaries():
    cases = profile_cases("backend_persistence")
    assert cases["backend-contract-mapping-gap"]["finding_owner"] == "chronicler"
    assert cases["backend-transaction-reentry"]["finding_owner"] == "chronicler"
    assert cases["backend-evidence-missing"]["finding_owner"] == "overseer"
    assert cases["backend-persistence-contradiction"]["finding_owner"] == "the-tuner"


def test_cross_module_owner_boundaries():
    cases = profile_cases("cross_module_logic")
    assert cases["cross-module-flow-gap"]["finding_owner"] == "clockwork"
    assert cases["cross-module-side-effect-reentry"]["finding_owner"] == "clockwork"
    assert cases["cross-module-evidence-missing"]["finding_owner"] == "overseer"
    assert cases["cross-module-contradiction"]["finding_owner"] == "the-tuner"


def test_confirmed_cases_require_complete_evidence_and_no_finding():
    data = fixtures()
    for profile in data["profiles"].values():
        confirmed = next(
            case
            for case in profile["cases"]
            if case["expected_status"] == "CROSS_LAYER_ALIGNMENT_CONFIRMED"
        )
        assert confirmed["finding_owner"] is None
        assert confirmed["finding"] is None
        assert all(confirmed["evidence"].values())
        assert confirmed["workflow_id"]
        assert confirmed["expected_reentry"] == []


def test_non_confirmed_cases_have_complete_single_owner_findings():
    data = fixtures()
    for profile in data["profiles"].values():
        for case in profile["cases"]:
            if case["expected_status"] == "CROSS_LAYER_ALIGNMENT_CONFIRMED":
                continue
            assert case["finding_owner"] in validator.OWNERS
            assert case["finding"]["owner"] == case["finding_owner"]
            assert set(case["finding"]) == validator.FINDING_FIELDS
            assert case["finding"]["affected_stages"]


def test_unknown_status_fails_closed():
    data = fixtures()
    data["profiles"]["backend_persistence"]["cases"][0][
        "expected_status"
    ] = "AUTO_CONTINUE_UNKNOWN"
    assert any(
        "unknown status" in error
        for error in validator.validate_fixtures(data, protocol_bytes())
    )


def test_unknown_profile_fails_closed():
    data = fixtures()
    data["profiles"]["unknown"] = copy.deepcopy(data["profiles"]["cross_module_logic"])
    assert any(
        "profiles must contain exactly" in error
        for error in validator.validate_fixtures(data, protocol_bytes())
    )


def test_protocol_hash_mismatch_fails_closed():
    data = fixtures()
    data["contract_identity"]["protocol_sha256"] = "0" * 64
    assert any(
        "protocol_sha256 does not match" in error
        for error in validator.validate_fixtures(data, protocol_bytes())
    )


def test_missing_executable_evidence_fails_closed():
    data = fixtures()
    case = next(
        item
        for item in data["profiles"]["cross_module_logic"]["cases"]
        if item["id"] == "cross-module-evidence-missing"
    )
    case["evidence"]["executable_workflow"] = True
    assert any(
        "executable evidence requires workflow_id" in error
        for error in validator.validate_fixtures(data, protocol_bytes())
    )


def test_incomplete_trace_fails_closed():
    data = fixtures()
    data["profiles"]["backend_persistence"]["executable_workflows"][0][
        "trace"
    ].pop()
    assert any(
        "trace must contain profile stages in exact order" in error
        for error in validator.validate_fixtures(data, protocol_bytes())
    )


def test_incomplete_finding_fails_closed():
    data = fixtures()
    case = next(
        item
        for item in data["profiles"]["backend_persistence"]["cases"]
        if item["id"] == "backend-contract-mapping-gap"
    )
    del case["finding"]["required_validation"]
    assert any(
        "complete finding object" in error
        for error in validator.validate_fixtures(data, protocol_bytes())
    )


def test_stale_identity_requires_full_continuity_chain():
    data = fixtures()
    case = next(
        item
        for item in data["profiles"]["cross_module_logic"]["cases"]
        if item["id"] == "cross-module-contract-stale"
    )
    case["expected_reentry"] = ["the-tuner", "overseer"]
    assert any(
        "must re-enter Tuner, Overseer, and Arbiter" in error
        for error in validator.validate_fixtures(data, protocol_bytes())
    )


def test_contradiction_requires_conductor_reentry():
    data = fixtures()
    case = next(
        item
        for item in data["profiles"]["backend_persistence"]["cases"]
        if item["id"] == "backend-persistence-contradiction"
    )
    case["expected_reentry"] = ["clockwork", "chronicler"]
    assert any(
        "contradiction must route back through Conductor" in error
        for error in validator.validate_fixtures(data, protocol_bytes())
    )


def main():
    test_real_repo_passes()
    test_original_frontend_backend_contract_still_passes()
    test_profiles_cover_exact_status_set()
    test_workflows_trace_profile_stages_in_order()
    test_backend_persistence_owner_boundaries()
    test_cross_module_owner_boundaries()
    test_confirmed_cases_require_complete_evidence_and_no_finding()
    test_non_confirmed_cases_have_complete_single_owner_findings()
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
