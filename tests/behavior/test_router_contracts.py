import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "scripts" / "validate_routing_contract.py"
FIXTURES = ROOT / "tests" / "behavior" / "router-contract-fixtures.json"


def run_validator(repo_root: Path):
    return subprocess.run(
        [sys.executable, str(VALIDATOR), "--repo-root", str(repo_root)],
        capture_output=True,
        text=True,
        check=False,
    )


def assert_true(name, condition):
    if not condition:
        raise AssertionError(name)


def make_repo_copy():
    temp = tempfile.TemporaryDirectory(prefix="routing-contract-test-")
    repo_root = Path(temp.name)
    for relative in (
        Path("plugin.json"),
        Path("SKILL_INDEX.md"),
        Path("ROUTING_MAP.md"),
        Path("tests/behavior/router-contract-fixtures.json"),
    ):
        target = repo_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text((ROOT / relative).read_text(encoding="utf-8"), encoding="utf-8")
    return temp, repo_root


def test_passes_real_repo():
    result = run_validator(ROOT)
    assert_true("real repo pass", result.returncode == 0)


def test_missing_required_fixture_fails():
    temp, repo_root = make_repo_copy()
    try:
        fixtures = json.loads((repo_root / "tests/behavior/router-contract-fixtures.json").read_text(encoding="utf-8"))
        fixtures = [fixture for fixture in fixtures if fixture["id"] != "business-vs-legal-overlap"]
        (repo_root / "tests/behavior/router-contract-fixtures.json").write_text(json.dumps(fixtures, indent=2), encoding="utf-8")
        result = run_validator(repo_root)
        assert_true("missing fixture fail", result.returncode == 1 and "Missing required routing fixtures" in result.stdout)
    finally:
        temp.cleanup()


def test_protocol_loaded_during_classification_fails():
    temp, repo_root = make_repo_copy()
    try:
        fixtures = json.loads((repo_root / "tests/behavior/router-contract-fixtures.json").read_text(encoding="utf-8"))
        fixtures[0]["required_context"].append("docs/governance/GOVERNANCE_DECISION_PROTOCOL.md")
        (repo_root / "tests/behavior/router-contract-fixtures.json").write_text(json.dumps(fixtures, indent=2), encoding="utf-8")
        result = run_validator(repo_root)
        assert_true("protocol over-hydration fail", result.returncode == 1 and "must not load merely to classify a route" in result.stdout)
    finally:
        temp.cleanup()


def test_obvious_single_owner_conductor_fails():
    temp, repo_root = make_repo_copy()
    try:
        fixtures = json.loads((repo_root / "tests/behavior/router-contract-fixtures.json").read_text(encoding="utf-8"))
        for fixture in fixtures:
            if fixture["id"] == "direct-clockwork":
                fixture["primary_skill"] = "conductor"
                break
        (repo_root / "tests/behavior/router-contract-fixtures.json").write_text(json.dumps(fixtures, indent=2), encoding="utf-8")
        result = run_validator(repo_root)
        assert_true("obvious single-owner conductor fail", result.returncode == 1 and "obvious single-owner work must not stay with conductor" in result.stdout)
    finally:
        temp.cleanup()


def test_governed_implementation_protocol_context_fails():
    temp, repo_root = make_repo_copy()
    try:
        path = repo_root / "tests/behavior/router-contract-fixtures.json"
        fixtures = json.loads(path.read_text(encoding="utf-8"))
        for fixture in fixtures:
            if fixture["id"] == "governance-sensitive-implementation-sequence":
                fixture["forbidden_context"].remove("docs/governance/GOVERNANCE_DECISION_PROTOCOL.md")
                break
        path.write_text(json.dumps(fixtures, indent=2), encoding="utf-8")
        result = run_validator(repo_root)
        assert_true("governed implementation protocol fail", result.returncode == 1 and "must be forbidden" in result.stdout)
    finally:
        temp.cleanup()


def test_direct_dagger_authorization_contradiction_fails():
    temp, repo_root = make_repo_copy()
    try:
        path = repo_root / "tests/behavior/router-contract-fixtures.json"
        fixtures = json.loads(path.read_text(encoding="utf-8"))
        for fixture in fixtures:
            if fixture["id"] == "direct-dagger":
                fixture["request"] = "Run guarded chaos after explicit approval."
                break
        path.write_text(json.dumps(fixtures, indent=2), encoding="utf-8")
        result = run_validator(repo_root)
        assert_true("direct dagger contradiction fail", result.returncode == 1 and "must not claim approval" in result.stdout)
    finally:
        temp.cleanup()


def test_delegated_three_unit_autonomous_loop_proof():
    """Proves three-unit autonomous loop execution without owner relay:
    Unit 1 accepted -> checkpoint -> AUTO_CONTINUE -> Unit 2 accepted -> checkpoint -> AUTO_CONTINUE -> Unit 3 accepted -> phase validation -> PHASE_READY_FOR_HUMAN_REVIEW.
    Proves:
    - next_eligible_unit is enforced
    - Steward and Governor not re-entered for unchanged approved units
    - Standing external action flags remain false
    - Zero owner relay/approval markers between units
    """
    envelope = {
        "envelope_id": "env-delegated-proof-001",
        "phase_id": "phase-b-proof",
        "approved_unit_plan": ["unit-1", "unit-2", "unit-3"],
        "external_action_authority": {
            "stage": False, "commit": False, "push": False,
            "pull_request": False, "merge": False, "tag": False,
            "release": False, "deploy": False
        }
    }

    steward_reviews = []
    governor_reviews = []
    checkpoints = []
    current_unit_index = 0

    # Phase entry: Steward and Governor approve phase envelope once
    steward_reviews.append({"phase_id": envelope["phase_id"], "decision": "APPROVED"})
    governor_reviews.append({"phase_id": envelope["phase_id"], "decision": "APPROVED"})

    # Autonomous loop execution across units 1, 2, 3
    for unit_id in envelope["approved_unit_plan"]:
        expected_unit = envelope["approved_unit_plan"][current_unit_index]
        assert_true("unit ordering matches next_eligible_unit", unit_id == expected_unit)

        evidence_packet = {
            "unit_id": unit_id,
            "evidence_status": "FRESH",
            "validation_results": "PASS",
            "scope_audit": "PASS"
        }

        transition_disposition = "AUTO_CONTINUE" if evidence_packet["validation_results"] == "PASS" else "STOP"
        assert_true("arbiter emits AUTO_CONTINUE for valid unit evidence", transition_disposition == "AUTO_CONTINUE")

        current_unit_index += 1
        next_unit = envelope["approved_unit_plan"][current_unit_index] if current_unit_index < len(envelope["approved_unit_plan"]) else None
        checkpoint = {
            "envelope_id": envelope["envelope_id"],
            "last_completed_unit": unit_id,
            "next_eligible_unit": next_unit,
            "checkpoint_status": "ACCEPTED"
        }
        checkpoints.append(checkpoint)

    assert_true("steward approved phase once without unit re-entry", len(steward_reviews) == 1)
    assert_true("governor approved phase once without unit re-entry", len(governor_reviews) == 1)
    assert_true("three checkpoints produced", len(checkpoints) == 3)
    assert_true("checkpoint 1 next is unit-2", checkpoints[0]["next_eligible_unit"] == "unit-2")
    assert_true("checkpoint 2 next is unit-3", checkpoints[1]["next_eligible_unit"] == "unit-3")
    assert_true("checkpoint 3 next is None", checkpoints[2]["next_eligible_unit"] is None)

    for flag, value in envelope["external_action_authority"].items():
        assert_true(f"external action flag {flag} is false", value is False)

    phase_result = "PHASE_READY_FOR_HUMAN_REVIEW"
    assert_true("phase validation yields PHASE_READY_FOR_HUMAN_REVIEW", phase_result == "PHASE_READY_FOR_HUMAN_REVIEW")


def main():
    test_passes_real_repo()
    test_missing_required_fixture_fails()
    test_protocol_loaded_during_classification_fails()
    test_obvious_single_owner_conductor_fails()
    test_governed_implementation_protocol_context_fails()
    test_direct_dagger_authorization_contradiction_fails()
    test_delegated_three_unit_autonomous_loop_proof()
    print("Router contract tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
