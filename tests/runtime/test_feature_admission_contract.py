import importlib.util
import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/behavior/feature-decision-record-fixtures.json"
SCHEMA = ROOT / "machine/schemas/feature-decision-record.v1.schema.json"


def load_validator():
    path = ROOT / "scripts/validate_feature_admission_contract.py"
    spec = importlib.util.spec_from_file_location("feature_admission_contract", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load_validator()


def fixture_data():
    return json.loads(FIXTURES.read_text(encoding="utf-8"))


def schema_data():
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def case_by_id(collection, case_id):
    return next(item for item in collection if item["id"] == case_id)


def test_repository_contract_passes():
    assert validator.validate(ROOT) == []


def test_schema_is_draft_2020_12_and_valid():
    schema = schema_data()
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    Draft202012Validator.check_schema(schema)


def test_all_declared_valid_records_validate():
    data = fixture_data()
    schema = schema_data()
    schema_validator = Draft202012Validator(schema)
    for case in data["valid_record_cases"]:
        record = validator.materialize_record_case(data, case)
        assert list(schema_validator.iter_errors(record)) == [], case["id"]


def test_all_declared_invalid_records_fail():
    data = fixture_data()
    schema_validator = Draft202012Validator(schema_data())
    for case in data["invalid_record_cases"]:
        record = validator.materialize_record_case(data, case)
        assert list(schema_validator.iter_errors(record)), case["id"]


def test_admission_can_be_followed_by_negative_promotion():
    data = fixture_data()
    case = case_by_id(data["valid_record_cases"], "admitted-later-rejected-no-value")
    record = validator.materialize_record_case(data, case)
    assert record["admission"]["disposition"] == "ADMIT"
    assert record["promotion"]["disposition"] == "REJECT_NO_MEASURABLE_VALUE"


def test_record_and_dispositions_do_not_grant_authority():
    record = fixture_data()["base_record"]
    assert all(value is False for value in record["authority"].values())


def test_rejected_admission_requires_promotion_not_applicable():
    data = fixture_data()
    valid = case_by_id(data["valid_record_cases"], "rejected-not-applicable-promotion")
    valid_record = validator.materialize_record_case(data, valid)
    assert not list(Draft202012Validator(schema_data()).iter_errors(valid_record))

    invalid = case_by_id(data["invalid_record_cases"], "rejected-but-promotion-pending")
    invalid_record = validator.materialize_record_case(data, invalid)
    assert list(Draft202012Validator(schema_data()).iter_errors(invalid_record))


def test_inline_truth_and_parity_corrections_are_eligible():
    data = fixture_data()
    for case_id in ("truth-correction", "parity-refresh"):
        case = case_by_id(data["inline_rationale_cases"], case_id)
        assert validator.classify_inline_rationale(case) == "INLINE_RATIONALE_ALLOWED"


def test_inline_bug_and_test_restoration_require_accepted_requirement():
    data = fixture_data()
    allowed = case_by_id(data["inline_rationale_cases"], "bounded-bug-fix")
    blocked = case_by_id(data["inline_rationale_cases"], "bug-fix-without-requirement")
    assert validator.classify_inline_rationale(allowed) == "INLINE_RATIONALE_ALLOWED"
    assert validator.classify_inline_rationale(blocked) == "FULL_RECORD_REQUIRED"


def test_inline_fast_path_cannot_hide_new_capability_policy_or_authority_change():
    data = fixture_data()
    for case_id in ("new-capability", "policy-change", "authority-change"):
        case = case_by_id(data["inline_rationale_cases"], case_id)
        assert validator.classify_inline_rationale(case) == "FULL_RECORD_REQUIRED"
