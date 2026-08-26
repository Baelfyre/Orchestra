import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/behavior/repository-recovery-retirement-fixtures.json"


def load_validator():
    path = ROOT / "scripts/validate_repository_recovery_retirement_plan.py"
    spec = importlib.util.spec_from_file_location("repository_recovery_retirement", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load_validator()


def fixture_data():
    return json.loads(FIXTURES.read_text(encoding="utf-8"))


def case_record(case_id):
    data = fixture_data()
    case = next(item for item in data["cases"] if item["id"] == case_id)
    return case, validator.materialize_case(data, case)


def test_repository_contract_passes():
    assert validator.validate(ROOT) == []


def test_low_risk_prestate_can_use_sha_tree_evidence_only():
    case, record = case_record("low-risk-sha-tree-evidence-only")
    schema = validator.load_json(ROOT / "machine/schemas/repository-recovery-retirement-plan.v1.schema.json")
    assert case["valid"] is True
    assert validator.validate_record(record, schema) == []
    assert record["prestate"]["temporary_ref_policy"] == "EVIDENCE_ONLY"


def test_high_risk_prestate_requires_bounded_temporary_ref():
    data = fixture_data()
    schema = validator.load_json(ROOT / "machine/schemas/repository-recovery-retirement-plan.v1.schema.json")
    invalid_case, invalid_record = case_record("high-risk-requires-temporary-ref")
    valid_case, valid_record = case_record("high-risk-with-temporary-ref")
    assert invalid_case["valid"] is False
    assert validator.validate_record(invalid_record, schema)
    assert valid_case["valid"] is True
    assert validator.validate_record(valid_record, schema) == []
    assert valid_record["prestate"]["retention_days"] >= 30


def test_open_pr_and_unique_work_are_preserved():
    schema = validator.load_json(ROOT / "machine/schemas/repository-recovery-retirement-plan.v1.schema.json")
    _, open_record = case_record("open-pr-is-always-kept")
    _, unique_record = case_record("unmerged-unique-is-never-auto-eligible")
    assert validator.validate_record(open_record, schema) == []
    assert open_record["branches"][1]["recommended_action"] == "KEEP"
    assert validator.validate_record(unique_record, schema) == []
    assert unique_record["branches"][1]["recommended_action"] == "KEEP"


def test_canonical_equivalence_only_yields_separate_authorization_eligibility():
    schema = validator.load_json(ROOT / "machine/schemas/repository-recovery-retirement-plan.v1.schema.json")
    _, cooled = case_record("canonical-equivalent-after-cooling-is-eligible-only")
    _, cooling = case_record("canonical-equivalent-before-cooling-quarantines")
    assert validator.validate_record(cooled, schema) == []
    assert cooled["branches"][1]["recommended_action"] == "ELIGIBLE_FOR_SEPARATE_AUTHORIZATION"
    assert validator.validate_record(cooling, schema) == []
    assert cooling["branches"][1]["recommended_action"] == "QUARANTINE"


def test_recovery_ref_expiry_does_not_create_deletion_authority():
    schema = validator.load_json(ROOT / "machine/schemas/repository-recovery-retirement-plan.v1.schema.json")
    _, record = case_record("recovery-ref-after-retention-is-eligible-only")
    assert validator.validate_record(record, schema) == []
    assert record["branches"][1]["recommended_action"] == "ELIGIBLE_FOR_SEPARATE_AUTHORIZATION"
    assert record["authority"]["eligibility_grants_deletion_authority"] is False


def test_unknown_age_never_becomes_deletion_proof():
    schema = validator.load_json(ROOT / "machine/schemas/repository-recovery-retirement-plan.v1.schema.json")
    _, record = case_record("unknown-remains-quarantined-after-time")
    assert validator.validate_record(record, schema) == []
    assert record["branches"][1]["age_days"] == 365
    assert record["branches"][1]["recommended_action"] == "QUARANTINE"


def test_dry_run_cannot_delete_or_rewrite_history():
    schema = validator.load_json(ROOT / "machine/schemas/repository-recovery-retirement-plan.v1.schema.json")
    for case_id in (
        "dry-run-cannot-perform-deletion",
        "eligibility-cannot-grant-deletion-authority",
        "recovery-cannot-reset-main-backward",
    ):
        case, record = case_record(case_id)
        assert case["valid"] is False
        assert validator.validate_record(record, schema)
