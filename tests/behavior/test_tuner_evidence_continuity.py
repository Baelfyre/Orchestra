import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = ROOT / "scripts/validate_tuner_evidence_continuity.py"
FIXTURES_PATH = ROOT / "tests/behavior/tuner-evidence-continuity-fixtures.json"

spec = importlib.util.spec_from_file_location("tuner_evidence_continuity", VALIDATOR_PATH)
validator = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = validator
spec.loader.exec_module(validator)


def fixtures_by_id():
    data = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
    return {item["id"]: item for item in data}


def test_fixture_contract_is_complete():
    fixtures = list(fixtures_by_id().values())
    assert validator.validate_fixtures(fixtures) == []


def test_current_evidence_can_continue():
    fixture = fixtures_by_id()["current-evidence-auto-continue"]
    disposition, findings = validator.evaluate_continuity(fixture["packet"])
    assert disposition == "AUTO_CONTINUE"
    assert findings == []


def test_identity_mismatches_wait_for_evidence():
    fixtures = fixtures_by_id()
    for fixture_id in (
        "obsolete-contract-hash",
        "tracked-patch-mismatch",
        "staged-patch-mismatch",
        "untracked-manifest-incomplete",
        "added-blob-omitted",
        "open-invalidation-event",
        "unknown-canonicalization-fails-closed",
        "unknown-packet-status-fails-closed",
    ):
        disposition, findings = validator.evaluate_continuity(fixtures[fixture_id]["packet"])
        assert disposition == "WAIT_FOR_EVIDENCE"
        assert findings


def test_minimal_reentry_uses_declared_dependency_edges_only():
    fixture = fixtures_by_id()["minimal-security-reentry"]
    result = validator.minimal_reentry(
        fixture["trigger_contracts"],
        fixture["dependency_edges"],
        fixture["contract_owners"],
    )
    assert result == ["clockwork", "overseer"]
    assert "chronicler" not in result


def test_manual_and_delegated_reentry_parity():
    fixtures = fixtures_by_id()
    incomplete, _ = validator.evaluate_continuity(fixtures["manual-reentry-incomplete"]["packet"])
    manual_complete, _ = validator.evaluate_continuity(fixtures["manual-reentry-complete"]["packet"])
    delegated_complete, _ = validator.evaluate_continuity(fixtures["delegated-reentry-within-envelope"]["packet"])
    delegated_expansion, _ = validator.evaluate_continuity(fixtures["delegated-scope-expansion"]["packet"])
    assert incomplete == "WAIT_FOR_EVIDENCE"
    assert manual_complete == "AUTO_CONTINUE"
    assert delegated_complete == "AUTO_CONTINUE"
    assert delegated_expansion == "ESCALATE_HUMAN"


def test_artifact_lifecycle_protects_preexisting_state():
    fixtures = fixtures_by_id()
    preserved, _ = validator.evaluate_continuity(fixtures["preexisting-ignored-artifact-preserved"]["packet"])
    unauthorized_cleanup, findings = validator.evaluate_continuity(fixtures["cleanup-without-authority"]["packet"])
    uninspected, _ = validator.evaluate_continuity(fixtures["generated-artifact-uninspected"]["packet"])
    assert preserved == "AUTO_CONTINUE"
    assert unauthorized_cleanup == "WAIT_FOR_EVIDENCE"
    assert any("cleanup lacks authority" in item for item in findings)
    assert uninspected == "WAIT_FOR_EVIDENCE"


def test_dagger_and_external_actions_remain_separately_authorized():
    fixtures = fixtures_by_id()
    dagger, _ = validator.evaluate_continuity(fixtures["dagger-remains-blocked"]["packet"])
    external, _ = validator.evaluate_continuity(fixtures["external-action-default-deny"]["packet"])
    assert dagger == "STOP"
    assert external == "ESCALATE_HUMAN"


def main():
    test_fixture_contract_is_complete()
    test_current_evidence_can_continue()
    test_identity_mismatches_wait_for_evidence()
    test_minimal_reentry_uses_declared_dependency_edges_only()
    test_manual_and_delegated_reentry_parity()
    test_artifact_lifecycle_protects_preexisting_state()
    test_dagger_and_external_actions_remain_separately_authorized()
    print("Tuner evidence continuity tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
