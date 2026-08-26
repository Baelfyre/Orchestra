import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/behavior/governed-autonomy-candidate-lifecycle-fixtures.json"


def load_validator():
    path = ROOT / "scripts/validate_governed_autonomy_candidate_lifecycle.py"
    spec = importlib.util.spec_from_file_location("governed_autonomy_candidate_lifecycle", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load_validator()
autonomy_validator = validator.load_autonomy_validator(ROOT)


def fixture_data():
    return json.loads(FIXTURES.read_text(encoding="utf-8"))


def case_snapshot(case_id):
    data = fixture_data()
    case = next(item for item in data["cases"] if item["id"] == case_id)
    return case, validator.materialize_case(data, case)


def assert_case(case_id, expected):
    case, snapshot = case_snapshot(case_id)
    assert case["expected_disposition"] == expected
    assert validator.evaluate_candidate_transition(snapshot, autonomy_validator) == expected


def test_repository_contract_passes():
    assert validator.validate(ROOT) == []


def test_authorized_implementation_and_complete_freeze_remove_redundant_pause():
    assert_case("proposed-implement-auto", "AUTO_CONTINUE")
    assert_case("implement-freeze-auto", "AUTO_CONTINUE")


def test_missing_admission_authority_or_freeze_fails_closed():
    assert_case("proposed-missing-admission", "WAIT_FOR_EVIDENCE")
    assert_case("proposed-no-implementation-authority", "ESCALATE_HUMAN")
    assert_case("implement-freeze-incomplete", "WAIT_FOR_EVIDENCE")


def test_qualification_must_complete_before_human_owned_acceptance():
    assert_case("qualification-stale-before-acceptance", "WAIT_FOR_EVIDENCE")
    assert_case("qualification-pending-before-acceptance", "WAIT_FOR_EVIDENCE")
    assert_case("qualification-blocked-stops-acceptance", "STOP")
    assert_case("full-cannot-self-accept", "ESCALATE_HUMAN")
    assert_case("machine-owned-acceptance-escalates", "ESCALATE_HUMAN")
    assert_case("acceptance-record-auto-after-qualified", "AUTO_CONTINUE")


def test_merge_ready_pause_differs_by_profile_without_reusing_qualification():
    assert_case("human-merge-ready-needs-phase-gate", "ESCALATE_HUMAN")
    assert_case("human-merge-ready-with-phase-gate", "AUTO_CONTINUE")
    assert_case("semi-merge-ready-auto", "AUTO_CONTINUE")
    assert_case("merge-readiness-stale-waits", "WAIT_FOR_EVIDENCE")


def test_only_full_autonomous_may_initiate_merge_and_only_with_exact_grant():
    assert_case("semi-cannot-auto-merge-transition", "ESCALATE_HUMAN")
    assert_case("full-merge-needs-exact-grant", "ESCALATE_HUMAN")
    assert_case("full-merge-auto-when-existing-evaluator-passes", "AUTO_CONTINUE")
    assert_case("full-merge-missing-evidence-waits", "WAIT_FOR_EVIDENCE")


def test_observed_human_merge_can_be_recorded_without_retroactive_merge_authority():
    assert_case("human-observed-merge-records-state", "AUTO_CONTINUE")


def test_post_merge_verification_requires_independent_canonical_readback():
    assert_case("merged-readback-auto", "AUTO_CONTINUE")
    assert_case("merged-readback-missing-waits", "WAIT_FOR_EVIDENCE")


def test_retirement_is_record_closeout_not_branch_deletion_authority():
    assert_case("retire-record-auto", "AUTO_CONTINUE")
    assert_case("retirement-cannot-grant-branch-delete", "STOP")


def test_stale_candidate_identity_waits_and_invalid_transitions_stop():
    assert_case("stale-candidate-identity-waits", "WAIT_FOR_EVIDENCE")
    assert_case("skipped-transition-stops", "STOP")
    assert_case("backward-transition-stops", "STOP")


def test_integration_reuses_existing_autonomy_merge_evaluator():
    _, snapshot = case_snapshot("full-merge-auto-when-existing-evaluator-passes")
    merge_snapshot = dict(snapshot)
    merge_snapshot["action"] = "merge"
    assert autonomy_validator.evaluate(merge_snapshot) == "AUTO_CONTINUE"
    assert validator.evaluate_candidate_transition(snapshot, autonomy_validator) == "AUTO_CONTINUE"
