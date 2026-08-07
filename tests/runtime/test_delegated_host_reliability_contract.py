import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = ROOT / "scripts/validate_delegated_host_reliability_contract.py"
FIXTURES_PATH = ROOT / "tests/behavior/delegated-host-reliability-fixtures.json"


def _load_validator():
    spec = importlib.util.spec_from_file_location("host_reliability_validator", VALIDATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = _load_validator()


def fixtures():
    return json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))


def case_by_id(data, case_id):
    return next(case for case in data["cases"] if case["id"] == case_id)


def errors_for(data):
    return validator.validate_fixtures(data)


def test_real_repository_contract_passes():
    assert validator.validate(ROOT) == []


def test_all_dispositions_are_covered():
    data = fixtures()
    assert {case["expected_disposition"] for case in data["cases"]} == validator.DISPOSITIONS


def test_repository_evidence_cannot_claim_live_validation():
    data = fixtures()
    data["live_validation"]["status"] = "LIVE_VALIDATED"
    assert any("must not claim live installed-host validation complete" in error for error in errors_for(data))


def test_repository_fixture_cannot_embed_live_records():
    data = fixtures()
    data["live_validation"]["records"] = [{"host": "codex"}]
    assert any("must not contain fabricated live-host evidence" in error for error in errors_for(data))


def test_repository_case_cannot_label_itself_live():
    data = fixtures()
    case_by_id(data, "codex-same-host-reset-resume")["evidence_level"] = validator.LIVE
    assert any("must not fabricate LIVE_HOST_EVIDENCE" in error for error in errors_for(data))


def test_declared_host_maturity_is_frozen_to_current_repo_claims():
    data = fixtures()
    data["declared_hosts"]["claude-code"] = "ACTIVE"
    assert any("declared_hosts must match current Orchestra host maturity" in error for error in errors_for(data))


def test_scaffold_host_never_auto_continues():
    data = fixtures()
    case = case_by_id(data, "claude-code-scaffold-runtime-request")
    case["expected_disposition"] = "AUTO_CONTINUE"
    case["output_envelope_sha256"] = "a" * 64
    assert any("AUTO_CONTINUE requires active source and destination hosts" in error for error in errors_for(data))


def test_stale_identity_cannot_auto_continue():
    data = fixtures()
    case = case_by_id(data, "stale-repository-revision")
    case["expected_disposition"] = "AUTO_CONTINUE"
    case["output_envelope_sha256"] = "b" * 64
    assert any("AUTO_CONTINUE requires current complete safe identity" in error for error in errors_for(data))


def test_unavailable_capacity_cannot_auto_continue():
    data = fixtures()
    case = case_by_id(data, "capacity-interruption-with-valid-checkpoint")
    case["expected_disposition"] = "AUTO_CONTINUE"
    case["output_envelope_sha256"] = "c" * 64
    assert any("AUTO_CONTINUE requires available capacity" in error for error in errors_for(data))


def test_authority_expansion_cannot_auto_continue():
    data = fixtures()
    case = case_by_id(data, "authority-expansion-on-resume")
    case["expected_disposition"] = "AUTO_CONTINUE"
    case["output_envelope_sha256"] = "d" * 64
    assert any("AUTO_CONTINUE requires current complete safe identity" in error for error in errors_for(data))


def test_duplicate_replay_cannot_auto_continue():
    data = fixtures()
    case = case_by_id(data, "duplicate-checkpoint-consumption")
    case["expected_disposition"] = "AUTO_CONTINUE"
    case["output_envelope_sha256"] = "e" * 64
    assert any("AUTO_CONTINUE requires current complete safe identity" in error for error in errors_for(data))


def test_incomplete_checkpoint_cannot_auto_continue():
    data = fixtures()
    case = case_by_id(data, "incomplete-checkpoint")
    case["expected_disposition"] = "AUTO_CONTINUE"
    case["output_envelope_sha256"] = "f" * 64
    assert any("AUTO_CONTINUE requires current complete safe identity" in error for error in errors_for(data))


def test_malformed_hash_fails_closed():
    data = fixtures()
    case_by_id(data, "codex-same-host-reset-resume")["runtime_bundle_sha256"] = "not-a-hash"
    assert any("runtime_bundle_sha256 must be a lowercase SHA-256" in error for error in errors_for(data))


def test_unknown_disposition_fails_closed():
    data = fixtures()
    case_by_id(data, "codex-same-host-reset-resume")["expected_disposition"] = "UNKNOWN"
    assert any("unknown expected_disposition" in error for error in errors_for(data))


def test_auto_continue_requires_matching_repository_lineage():
    data = fixtures()
    case = case_by_id(data, "codex-same-host-reset-resume")
    case["approved_base_sha"] = "9" * 40
    assert any("AUTO_CONTINUE requires approved repository lineage" in error for error in errors_for(data))


def test_wait_for_capacity_requires_otherwise_valid_evidence():
    data = fixtures()
    case = case_by_id(data, "capacity-interruption-with-valid-checkpoint")
    case["authority_preserved"] = False
    assert any("WAIT_FOR_CAPACITY requires otherwise-valid active-host evidence" in error for error in errors_for(data))


def test_wait_for_evidence_requires_stale_or_incomplete_identity():
    data = fixtures()
    case = case_by_id(data, "stale-runtime-bundle")
    case["identity_current"] = True
    assert any("WAIT_FOR_EVIDENCE requires stale identity or incomplete checkpoint" in error for error in errors_for(data))


def test_cases_keep_exact_field_contract():
    data = fixtures()
    mutated = copy.deepcopy(data)
    mutated["cases"][0]["unexpected"] = True
    assert any("case must contain exactly the required fields" in error for error in errors_for(mutated))
