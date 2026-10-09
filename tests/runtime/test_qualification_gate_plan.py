import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/behavior/qualification-gate-plan-fixtures.json"
SCHEMA = ROOT / "machine/schemas/qualification-gate-plan.v1.schema.json"


def load_validator():
    path = ROOT / "scripts/validate_qualification_gate_plan.py"
    spec = importlib.util.spec_from_file_location("qualification_gate_plan", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load_validator()


def fixture_data():
    return json.loads(FIXTURES.read_text(encoding="utf-8"))


def schema_data():
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def case_record(case_id):
    data = fixture_data()
    case = next(item for item in data["cases"] if item["id"] == case_id)
    return case, validator.materialize_case(data, case)


def test_repository_contract_passes():
    assert validator.validate(ROOT) == []


def test_bounded_fix_can_qualify_without_forcing_every_gate():
    case, record = case_record("bounded-fix-qualified")
    assert validator.validate_record(record, schema_data()) == []
    assert case["expected_qualification"] == "QUALIFIED"
    assert record["gates"]["security_governance"]["applicability"] == "NOT_APPLICABLE"
    assert record["gates"]["independent_audit"]["applicability"] == "NOT_APPLICABLE"


def test_pending_required_gate_keeps_candidate_pending():
    case, record = case_record("pending-required-gate")
    assert validator.validate_record(record, schema_data()) == []
    assert validator.derive_qualification(record) == case["expected_qualification"] == "QUALIFICATION_PENDING"


def test_material_risk_cannot_be_hidden_with_na():
    for case_id in (
        "runtime-change-cannot-skip-regression",
        "governance-change-cannot-skip-security-gate",
        "trust-boundary-requires-independent-audit",
        "adaptive-promotion-cannot-use-deterministic-only",
        "trivial-correction-cannot-hide-runtime-change",
    ):
        _, record = case_record(case_id)
        assert validator.validate_record(record, schema_data())


def test_adaptive_promotion_requires_controlled_evaluation_and_audit():
    case, record = case_record("adaptive-experiment-qualified")
    assert validator.validate_record(record, schema_data()) == []
    assert record["evaluation"]["disposition"] == "EXPERIMENT_REQUIRED"
    assert record["gates"]["controlled_evaluation"]["applicability"] == "REQUIRED"
    assert record["gates"]["independent_audit"]["applicability"] == "REQUIRED"
    assert case["expected_qualification"] == "QUALIFIED"


def test_experiment_protocol_is_preregistered_and_preserves_negative_evidence():
    for case_id in (
        "experiment-requires-preregistered-protocol",
        "experiment-must-preserve-negative-evidence",
    ):
        _, record = case_record(case_id)
        assert validator.validate_record(record, schema_data())


def test_failed_required_gate_derives_blocked():
    invalid_case, invalid = case_record("failed-required-gate-must-block")
    valid_case, valid = case_record("failed-required-gate-records-blocked")
    assert validator.validate_record(invalid, schema_data())
    assert validator.validate_record(valid, schema_data()) == []
    assert validator.derive_qualification(valid) == valid_case["expected_qualification"] == "BLOCKED"
    assert invalid_case["valid"] is False


def test_independent_audit_first_pass_is_read_only():
    _, record = case_record("audit-first-pass-must-be-read-only")
    assert validator.validate_record(record, schema_data())


def test_qualification_record_never_grants_protected_authority():
    _, record = case_record("bounded-fix-qualified")
    assert set(record["authority"].values()) == {False}
