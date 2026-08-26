import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/behavior/autonomous-merge-readiness-fixtures.json"


def load_validator():
    path = ROOT / "scripts/validate_autonomous_merge_readiness_contract.py"
    spec = importlib.util.spec_from_file_location("autonomous_merge_readiness", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load_validator()


def fixture_data():
    return json.loads(FIXTURES.read_text(encoding="utf-8"))


def pre_case(case_id):
    data = fixture_data()
    case = next(item for item in data["pre_merge_cases"] if item["id"] == case_id)
    return case, validator.materialize_pre_merge_case(data, case)


def post_case(case_id):
    data = fixture_data()
    return next(item for item in data["post_merge_cases"] if item["id"] == case_id)


def test_real_repository_contract_passes():
    assert validator.validate(ROOT) == []


def test_fully_green_exact_head_is_ready():
    case, snapshot = pre_case("fully-green")
    assert snapshot["mergeable"] is True
    assert snapshot["mergeable_state"] == "clean"
    assert validator.evaluate_pre_merge(snapshot) == case["expected_disposition"]


def test_missing_and_pending_evidence_waits():
    for case_id in (
        "no-check-data",
        "missing-runtime",
        "missing-codeql-compatibility",
        "queued-windows",
        "in-progress-macos",
        "head-not-reconfirmed",
        "mergeability-missing",
        "mergeable-state-missing",
        "mergeable-state-unknown",
        "mergeable-is-not-enough",
    ):
        case, snapshot = pre_case(case_id)
        assert validator.evaluate_pre_merge(snapshot) == "WAIT_FOR_EVIDENCE"
        assert case["expected_disposition"] == "WAIT_FOR_EVIDENCE"


def test_any_required_check_failure_blocks():
    for case_id in (
        "governance-failed",
        "runtime-failed",
        "compatibility-codeql-failed",
        "cross-platform-failed",
        "required-skipped",
        "required-cancelled",
        "required-timed-out",
    ):
        case, snapshot = pre_case(case_id)
        assert validator.evaluate_pre_merge(snapshot) == "BLOCK"
        assert case["expected_disposition"] == "BLOCK"


def test_stale_head_invalidates_prior_evidence():
    _, snapshot = pre_case("stale-head")
    assert validator.evaluate_pre_merge(snapshot) == "STALE_EVIDENCE"


def test_red_canonical_baseline_blocks_next_phase():
    _, snapshot = pre_case("red-main")
    assert validator.evaluate_pre_merge(snapshot) == "REMEDIATE_BASELINE_FIRST"


def test_required_changelog_omission_blocks():
    _, snapshot = pre_case("changelog-missing")
    assert validator.evaluate_pre_merge(snapshot) == "BLOCK"


def test_mergeable_true_cannot_shortcut_missing_checks():
    _, snapshot = pre_case("mergeable-is-not-enough")
    assert snapshot["mergeable"] is True
    assert snapshot["mergeable_state"] == "clean"
    assert validator.evaluate_pre_merge(snapshot) == "WAIT_FOR_EVIDENCE"


def test_merge_conflict_blocks():
    _, snapshot = pre_case("merge-conflict")
    assert validator.evaluate_pre_merge(snapshot) == "BLOCK"


def test_non_clean_mergeable_states_fail_closed():
    for case_id in (
        "mergeable-state-blocked",
        "mergeable-state-behind",
        "mergeable-state-dirty",
        "mergeable-state-unstable",
    ):
        _, snapshot = pre_case(case_id)
        assert snapshot["mergeable"] is True
        assert snapshot["mergeable_state"] != "clean"
        assert validator.evaluate_pre_merge(snapshot) == "BLOCK"


def test_unresolved_blocker_and_thread_block():
    for case_id in ("unresolved-blocker", "unresolved-thread"):
        _, snapshot = pre_case(case_id)
        assert validator.evaluate_pre_merge(snapshot) == "BLOCK"


def test_ruleset_and_merge_method_drift_block():
    for case_id in (
        "approval-requirement-drift",
        "merge-method-drift",
        "duplicate-ubuntu-required-context",
        "retired-codeql-required-contexts",
        "selected-rebase",
        "signature-rule-disabled",
    ):
        _, snapshot = pre_case(case_id)
        assert validator.evaluate_pre_merge(snapshot) == "BLOCK"


def test_required_status_context_profile_is_exact_and_unique():
    contexts = fixture_data()["expected_ruleset"]["required_status_contexts"]
    assert len(contexts) == len(set(contexts))
    assert contexts.count("native-ubuntu-latest") == 1
    assert "Compatibility CodeQL (python)" in contexts
    assert "Analyze (actions)" not in contexts
    assert "Analyze (python)" not in contexts


def test_bypass_capability_is_not_governance_authority():
    _, snapshot = pre_case("bypass-used")
    assert validator.evaluate_pre_merge(snapshot) == "BLOCK"


def test_merge_api_success_alone_is_not_verified():
    case = post_case("api-success-only")
    assert validator.evaluate_post_merge(case["snapshot"]) == "MERGE_STATE_UNVERIFIED"


def test_post_merge_requires_clean_pre_merge_state_and_no_bypass():
    for case_id in ("blocked-pre-merge-state", "bypass-post-merge-state"):
        case = post_case(case_id)
        assert validator.evaluate_post_merge(case["snapshot"]) == "MERGE_STATE_UNVERIFIED"


def test_post_merge_requires_squash_equivalence_and_signature():
    for case_id in (
        "pr-not-merged",
        "wrong-merge-method",
        "tree-mismatch",
        "content-diff-not-empty",
        "parent-drift",
        "unsigned-canonical-commit",
    ):
        case = post_case(case_id)
        assert validator.evaluate_post_merge(case["snapshot"]) == "MERGE_STATE_UNVERIFIED"


def test_verified_squash_post_merge_state_is_accepted():
    case = post_case("verified-squash")
    assert validator.evaluate_post_merge(case["snapshot"]) == "MERGED_VERIFIED"


def test_fixture_expected_result_tampering_fails_validation():
    data = fixture_data()
    case = next(item for item in data["pre_merge_cases"] if item["id"] == "runtime-failed")
    case["expected_disposition"] = "READY_FOR_MERGE"
    errors = validator.validate_fixtures(data)
    assert any("runtime-failed" in error for error in errors)


def test_duplicate_required_check_fails_closed():
    data = fixture_data()
    snapshot = copy.deepcopy(data["base_snapshot"])
    snapshot["checks"].append(copy.deepcopy(snapshot["checks"][0]))
    assert validator.evaluate_pre_merge(snapshot) == "BLOCK"


def test_unknown_required_check_status_fails_closed():
    data = fixture_data()
    snapshot = copy.deepcopy(data["base_snapshot"])
    snapshot["checks"][0]["status"] = "mystery"
    assert validator.evaluate_pre_merge(snapshot) == "BLOCK"
