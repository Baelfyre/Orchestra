from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import jsonschema
import pytest

from scripts import uix9b_live_proof_runner_v2 as v2_runner
from scripts.uix9_live_proof_runner import (
    OBSERVATION_SCHEMA_PATH,
    PLAN_PATH,
    RESULT_SCHEMA_PATH,
    validate_canary_bundle,
    validate_json,
    validate_zero_call_canaries,
)


ROOT = Path(__file__).resolve().parents[2]


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_uix9b_plan_is_closed_and_frozen() -> None:
    plan = validate_json(PLAN_PATH, ROOT / "machine/schemas/uix-live-proof-plan.schema.json")
    assert plan["status"] == "UIX_9B_HOST_REMEDIATION_COMPLETE_WAITING_UIX_9C_AUTHORIZATION"
    assert plan["execution_order"] == ["A1", "B1", "B2", "A2", "A3", "B3"]
    assert plan["resource_ceiling_proposal"]["experimental_sessions_per_run"] == 1
    assert plan["resource_ceiling_proposal"]["max_valid_experimental_sessions"] == 6
    assert plan["resource_ceiling_proposal"]["token_ceiling_mode"] == "OBSERVATIONAL_RESOURCE_CEILING"
    assert plan["retry_policy"]["valid_unfavorable_output"] == "KEEP_RESULT_NO_RETRY_FOR_OUTCOME"
    assert plan["primary_endpoints"] == ["OBJECTIVE_UI_FIDELITY_METRICS"]
    assert plan["provider_preparation"]["model"] == "gpt-5.6-luna"
    assert plan["provider_preparation"]["reasoning_effort"] == "xhigh"
    assert plan["provider_preparation"]["model_availability"] == "AVAILABLE"
    assert plan["availability_probe"]["probe_status"] == "PASS"
    assert plan["authority"]["live_model_calls_authorized"] is False


def test_uix9b_guidance_and_authorization_manifests_are_closed() -> None:
    validate_json(ROOT / "machine/ui/uix9-live-guidance-manifest.v1.json", ROOT / "machine/schemas/uix-live-guidance-manifest.schema.json")
    validate_json(ROOT / "machine/ui/uix9-live-call-authorization-request.v1.json", ROOT / "machine/schemas/uix-live-call-authorization.schema.json")


def test_uix9b_zero_call_canaries_pass() -> None:
    assert validate_zero_call_canaries() == {
        "S0_POSITIVE_VALIDATOR_CANARY": "PASS",
        "S1_NEGATIVE_VALIDATOR_CANARY": "PASS",
    }


def test_uix9b_malformed_evidence_and_arm_identity_fail_closed() -> None:
    positive = _load(ROOT / "tests/fixtures/ui/uix9-live-positive.json")
    missing = deepcopy(positive)
    del missing["validator_result"]
    with pytest.raises(jsonschema.ValidationError):
        validate_json_value(missing, OBSERVATION_SCHEMA_PATH)

    invalid_arm = deepcopy(positive)
    invalid_arm["arm_id"] = "GOVERNED_WITHOUT_MANIFEST"
    with pytest.raises(jsonschema.ValidationError):
        validate_json_value(invalid_arm, OBSERVATION_SCHEMA_PATH)


def test_uix9b_fixture_digest_equality_is_cross_field_enforced() -> None:
    positive = _load(ROOT / "tests/fixtures/ui/uix9-live-positive.json")
    mutated = deepcopy(positive)
    mutated["starting_fixture_digest"] = "0" * 64
    with pytest.raises(AssertionError):
        validate_canary_bundle(mutated, "ZERO_CALL_CANARY_PASS", "NONE")


def test_uix9b_result_classification_is_closed() -> None:
    schema = _load(RESULT_SCHEMA_PATH)
    assert schema["properties"]["result_classification"]["enum"] == [
        "BENEFIT_ESTABLISHED",
        "NO_BENEFIT_ESTABLISHED",
        "MIXED_OR_INCONCLUSIVE",
        "PROTOCOL_INVALID",
    ]


def test_v2_identity_gate_binds_to_canonical_base_not_candidate_head(monkeypatch: pytest.MonkeyPatch) -> None:
    plan = _load(ROOT / "machine/ui/uix9b-live-proof-plan.v2.json")
    calls: list[tuple[str, ...]] = []

    def fake_git_value(*arguments: str) -> str:
        calls.append(arguments)
        assert arguments == ("rev-parse", "origin/main")
        return plan["canonical_sha"]

    monkeypatch.setattr(v2_runner, "git_value", fake_git_value)
    report = v2_runner.verify_frozen_identities()

    assert report["canonical_sha"] == plan["canonical_sha"]
    assert calls == [("rev-parse", "origin/main")]


def validate_json_value(value: dict, schema_path: Path) -> None:
    schema = _load(schema_path)
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(value)
