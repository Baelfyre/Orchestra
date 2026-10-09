import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/behavior/governed-autonomy-modes-fixtures.json"


def load_validator():
    path = ROOT / "scripts/validate_governed_autonomy_modes_contract.py"
    spec = importlib.util.spec_from_file_location("governed_autonomy_modes", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load_validator()


def fixture_data():
    return json.loads(FIXTURES.read_text(encoding="utf-8"))


def case_snapshot(case_id):
    data = fixture_data()
    case = next(item for item in data["cases"] if item["id"] == case_id)
    return case, validator.materialize_case(data, case)


def test_repository_contract_passes():
    assert validator.validate(ROOT) == []


def test_safe_default_and_human_profile_gate_material_writes():
    for case_id in ("no-selection-defaults-human", "human-cannot-auto-commit"):
        case, snapshot = case_snapshot(case_id)
        assert validator.evaluate(snapshot) == case["expected_disposition"] == "ESCALATE_HUMAN"


def test_semi_profile_stops_before_merge():
    commit_case, commit = case_snapshot("semi-can-auto-commit")
    merge_case, merge = case_snapshot("semi-cannot-auto-merge")
    assert validator.evaluate(commit) == commit_case["expected_disposition"] == "AUTO_CONTINUE"
    assert validator.evaluate(merge) == merge_case["expected_disposition"] == "ESCALATE_HUMAN"


def test_full_profile_remains_authority_and_hard_boundary_constrained():
    for case_id in (
        "full-cannot-release",
        "increase-without-authority",
        "child-cannot-exceed-parent",
        "repository-restricts-full",
        "host-cannot-merge",
        "policy-activation-hard-boundary",
    ):
        case, snapshot = case_snapshot(case_id)
        assert validator.evaluate(snapshot) == case["expected_disposition"] == "ESCALATE_HUMAN"


def test_bypass_and_non_squash_paths_stop():
    for case_id in (
        "unauthorized-bypass-rejected",
        "rebase-rejected",
        "merge-commit-rejected",
        "squash-tree-mismatch",
        "squash-parent-mismatch",
        "unsigned-squash",
    ):
        case, snapshot = case_snapshot(case_id)
        assert validator.evaluate(snapshot) == case["expected_disposition"] == "STOP"


def test_missing_stale_or_unverified_evidence_waits():
    for case_id in (
        "ruleset-drift",
        "missing-required-check",
        "pending-required-check",
        "stale-head",
        "unverified-write",
        "resume-profile-mismatch",
    ):
        case, snapshot = case_snapshot(case_id)
        assert validator.evaluate(snapshot) == case["expected_disposition"] == "WAIT_FOR_EVIDENCE"


def test_bounded_caused_defect_is_the_only_automatic_remediation_path():
    allowed_case, allowed = case_snapshot("bounded-caused-remediation")
    blocked_case, blocked = case_snapshot("unrelated-failure-stops")
    assert validator.evaluate(allowed) == allowed_case["expected_disposition"] == "AUTO_REMEDIATE_AND_REVALIDATE"
    assert validator.evaluate(blocked) == blocked_case["expected_disposition"] == "STOP"


def test_profile_reduction_takes_effect_immediately():
    case, snapshot = case_snapshot("reduction-immediate")
    assert validator.evaluate(snapshot) == case["expected_disposition"] == "ESCALATE_HUMAN"


def test_fixture_expectation_tampering_is_detected():
    data = fixture_data()
    case = next(item for item in data["cases"] if item["id"] == "unauthorized-bypass-rejected")
    case["expected_disposition"] = "AUTO_CONTINUE"
    errors = validator.validate_fixture(data)
    assert any("unauthorized-bypass-rejected" in error for error in errors)


def test_unknown_profile_and_action_fail_closed():
    data = fixture_data()
    snapshot = copy.deepcopy(data["base_snapshot"])
    snapshot["selected_profile"] = "UNBOUNDED"
    assert validator.evaluate(snapshot) == "STOP"
    snapshot = copy.deepcopy(data["base_snapshot"])
    snapshot["action"] = "teleport"
    assert validator.evaluate(snapshot) == "STOP"
