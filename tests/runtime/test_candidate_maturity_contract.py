import importlib.util
import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/behavior/candidate-maturity-record-fixtures.json"
SCHEMA = ROOT / "machine/schemas/candidate-maturity-record.v1.schema.json"


def load_validator():
    path = ROOT / "scripts/validate_candidate_maturity_contract.py"
    spec = importlib.util.spec_from_file_location("candidate_maturity_contract", path)
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


def test_declared_valid_records_pass_schema_and_semantics():
    data = fixture_data()
    schema_validator = Draft202012Validator(schema_data())
    for case in data["valid_record_cases"]:
        record = validator.materialize_record_case(data, case)
        assert list(schema_validator.iter_errors(record)) == [], case["id"]
        assert validator.semantic_record_errors(record) == [], case["id"]


def test_declared_schema_invalid_records_fail():
    data = fixture_data()
    schema_validator = Draft202012Validator(schema_data())
    for case in data["invalid_record_cases"]:
        record = validator.materialize_record_case(data, case)
        assert list(schema_validator.iter_errors(record)), case["id"]


def test_declared_semantic_invalid_records_fail_closed():
    data = fixture_data()
    schema_validator = Draft202012Validator(schema_data())
    for case in data["semantic_invalid_cases"]:
        record = validator.materialize_record_case(data, case)
        assert list(schema_validator.iter_errors(record)) == [], case["id"]
        assert validator.semantic_record_errors(record), case["id"]


def test_maturity_vocabulary_is_separate_from_operational_overlays():
    record = fixture_data()["base_record"]
    assert record["maturity"]["state"] == "FROZEN_CANDIDATE"
    assert record["maturity"]["overlay"] == "WAITING_FOR_EVIDENCE"
    assert "WAITING_FOR_EVIDENCE" not in validator.MATURITY_STATES


def test_freeze_does_not_grant_authority():
    record = fixture_data()["base_record"]
    assert record["freeze"]["status"] == "FROZEN"
    assert all(value is False for value in record["authority"].values())


def test_allowed_remediation_requires_new_candidate_identity():
    data = fixture_data()
    case = case_by_id(data["frozen_change_cases"], "bug-fix-new-identity")
    assert validator.classify_frozen_change(case) == "BOUNDED_REMEDIATION_NEW_IDENTITY_REQUIRED"

    reused = case_by_id(data["frozen_change_cases"], "bug-fix-reuses-identity")
    assert validator.classify_frozen_change(reused) == "INVALID_FROZEN_IDENTITY_REUSE"


def test_frozen_dimension_change_is_not_relabelled_as_remediation():
    data = fixture_data()
    case = case_by_id(data["frozen_change_cases"], "acceptance-criteria-rewritten")
    assert validator.classify_frozen_change(case) == "READMISSION_OR_IMPLEMENTATION_REQUIRED"


def test_forbidden_expansion_and_validator_weakening_are_not_remediation():
    data = fixture_data()
    for case_id in ("new-scope", "architecture-expansion", "validator-weakening"):
        case = case_by_id(data["frozen_change_cases"], case_id)
        assert validator.classify_frozen_change(case) == "PROHIBITED_AS_REMEDIATION"


def test_merge_ready_is_evidence_state_not_authority():
    data = fixture_data()
    case = case_by_id(data["valid_record_cases"], "merge-ready-frozen")
    record = validator.materialize_record_case(data, case)
    assert record["maturity"]["state"] == "MERGE_READY"
    assert record["maturity"]["transition_evidence_refs"]
    assert record["authority"]["merge_ready_grants_merge_authority"] is False
