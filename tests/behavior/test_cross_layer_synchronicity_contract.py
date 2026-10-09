import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = ROOT / "scripts/validate_cross_layer_synchronicity_contract.py"
FIXTURES_PATH = ROOT / "tests/behavior/cross-layer-synchronicity-fixtures.json"
PROTOCOL_PATH = ROOT / "docs/validation/CROSS_MODULE_LOGIC_AUDIT_PROTOCOL.md"
INTEGRITY_TEST_PATH = ROOT / "tests/behavior/test_cross_layer_integrity_contract.py"

spec = importlib.util.spec_from_file_location("synchronicity_validator", VALIDATOR_PATH)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def fixtures():
    return json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))


def protocol_bytes():
    text = PROTOCOL_PATH.read_text(encoding="utf-8")
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def cases_by_id():
    return {case["id"]: case for case in fixtures()["cases"]}


def test_real_repo_passes():
    assert not validator.validate(ROOT)


def test_all_statuses_have_cases():
    statuses = {case["expected_status"] for case in fixtures()["cases"]}
    assert statuses == validator.REQUIRED_STATUSES


def test_executable_workflows_trace_all_stages():
    for workflow in fixtures()["executable_workflows"]:
        assert [entry["stage"] for entry in workflow["trace"]] == list(validator.REQUIRED_STAGES)
        assert all(entry["source_ref"] for entry in workflow["trace"])
        assert all(entry["evidence_ref"] for entry in workflow["trace"])
        assert all(entry["result"] for entry in workflow["trace"])


def test_happy_path_requires_complete_evidence():
    case = cases_by_id()["happy-path-aligned"]
    assert case["finding_owner"] is None
    assert case["finding"] is None
    assert all(case["evidence"].values())
    assert case["workflow_id"] == "profile-update-happy-path"
    assert case["expected_status"] == "CROSS_LAYER_ALIGNMENT_CONFIRMED"


def test_failure_paths_have_complete_single_owner_findings():
    for case in cases_by_id().values():
        if case["expected_status"] == "CROSS_LAYER_ALIGNMENT_CONFIRMED":
            continue
        assert case["finding_owner"] in validator.OWNERS
        assert case["finding"]["owner"] == case["finding_owner"]
        assert set(case["finding"]) == validator.FINDING_FIELDS
        assert case["finding"]["affected_stages"]


def test_authorization_mismatch_routes_to_cipher():
    case = cases_by_id()["authorization-mismatch"]
    assert case["finding_owner"] == "cipher"
    assert case["workflow_id"] == "admin-update-authorization-failure"
    assert case["expected_reentry"] == ["cipher", "cloak", "overseer"]


def test_stale_identity_reenters_continuity_chain():
    case = cases_by_id()["stale-contract-identity"]
    assert case["expected_reentry"] == ["the-tuner", "overseer", "arbiter"]


def test_unknown_status_fails_closed():
    data = fixtures()
    data["cases"][0]["expected_status"] = "AUTO_CONTINUE_UNKNOWN"
    assert any("unknown status" in error for error in validator.validate_fixtures(data, protocol_bytes()))


def test_missing_executable_evidence_fails_closed():
    data = copy.deepcopy(fixtures())
    case = next(item for item in data["cases"] if item["id"] == "missing-executable-evidence")
    case["evidence"]["executable_workflow"] = True
    assert any(
        "executable evidence requires workflow_id" in error
        for error in validator.validate_fixtures(data, protocol_bytes())
    )


def test_protocol_hash_mismatch_fails_closed():
    data = fixtures()
    data["contract_identity"]["protocol_sha256"] = "0" * 64
    assert any(
        "protocol_sha256 does not match" in error
        for error in validator.validate_fixtures(data, protocol_bytes())
    )


def test_incomplete_trace_fails_closed():
    data = fixtures()
    data["executable_workflows"][0]["trace"].pop()
    assert any(
        "canonical stages in exact order" in error
        for error in validator.validate_fixtures(data, protocol_bytes())
    )


def test_incomplete_finding_fails_closed():
    data = fixtures()
    case = next(item for item in data["cases"] if item["id"] == "request-field-mismatch")
    del case["finding"]["required_validation"]
    assert any(
        "complete finding object" in error
        for error in validator.validate_fixtures(data, protocol_bytes())
    )


def test_unknown_reentry_owner_fails_closed():
    data = fixtures()
    case = next(item for item in data["cases"] if item["id"] == "persistence-scope-expansion")
    case["expected_reentry"].append("unknown-specialist")
    assert any(
        "unique valid specialist list" in error
        for error in validator.validate_fixtures(data, protocol_bytes())
    )


def test_f2_integrity_profile_suite():
    result = subprocess.run(
        [sys.executable, str(INTEGRITY_TEST_PATH)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(
            "F2 cross-layer integrity profile suite failed:\n"
            + result.stdout
            + result.stderr
        )


def main():
    test_real_repo_passes()
    test_all_statuses_have_cases()
    test_executable_workflows_trace_all_stages()
    test_happy_path_requires_complete_evidence()
    test_failure_paths_have_complete_single_owner_findings()
    test_authorization_mismatch_routes_to_cipher()
    test_stale_identity_reenters_continuity_chain()
    test_unknown_status_fails_closed()
    test_missing_executable_evidence_fails_closed()
    test_protocol_hash_mismatch_fails_closed()
    test_incomplete_trace_fails_closed()
    test_incomplete_finding_fails_closed()
    test_unknown_reentry_owner_fails_closed()
    test_f2_integrity_profile_suite()
    print("Cross-layer synchronicity contract tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
