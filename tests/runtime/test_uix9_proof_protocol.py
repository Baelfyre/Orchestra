from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import jsonschema
import pytest

from scripts.uix9_proof_harness import (
    OBSERVATION_SCHEMA_PATH,
    PLAN_PATH,
    PLAN_SCHEMA_PATH,
    RESULT_SCHEMA_PATH,
    dry_run,
)


ROOT = Path(__file__).resolve().parents[2]


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _validator(path: Path) -> jsonschema.Draft202012Validator:
    schema = _load(path)
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


def test_uix9_plan_and_schemas_are_closed_and_entry_bound() -> None:
    plan = _load(PLAN_PATH)
    _validator(PLAN_SCHEMA_PATH).validate(plan)
    _validator(OBSERVATION_SCHEMA_PATH)
    _validator(RESULT_SCHEMA_PATH)
    assert plan["entry_baseline"] == "093babeea188c502cded8756f97648291bc0fea0"
    assert plan["status"] == "PREPARED_WAITING_LIVE_CALL_AUTHORIZATION"
    assert plan["proof_question"]["only_treatment_difference"] == "UIX_GUIDANCE_PRESENT_OR_ABSENT"
    assert plan["harness"]["network_calls"] == 0
    assert plan["harness"]["external_repo_writes"] == 0


def test_uix9_zero_call_dry_run_reaches_authorized_terminal_boundary() -> None:
    result = dry_run()
    assert result["status"] == "UIX_9_PROOF_PREPARED_WAITING_LIVE_CALL_AUTHORIZATION"
    assert len(result["observation_refs"]) == 4
    assert result["dry_run"]["live_model_calls"] == 0
    assert result["dry_run"]["provider_calls"] == 0
    assert result["dry_run"]["external_repo_mutations"] == 0
    assert result["claim_boundary"]["behavior_improvement_claimed"] is False
    assert result["claim_boundary"]["benefit_established"] is False


def test_uix9_positive_and_negative_fixtures_are_deterministic() -> None:
    plan = _load(PLAN_PATH)
    positive = _load(ROOT / plan["fixtures"]["positive"])
    negative = _load(ROOT / plan["fixtures"]["negative"])
    _validator(OBSERVATION_SCHEMA_PATH).validate(positive)
    _validator(OBSERVATION_SCHEMA_PATH).validate(negative)
    assert all(item["acceptance"]["status"] == "PASS" for item in positive["observations"])
    assert any(item["acceptance"]["status"] == "FAIL_CLOSED" for item in negative["observations"])
    assert positive["requirements_digest"] == negative["requirements_digest"]
    assert positive["project_fixture_digest"] == negative["project_fixture_digest"]


def test_uix9_nonzero_call_fixture_is_rejected() -> None:
    candidate = deepcopy(_load(ROOT / "tests/fixtures/ui/uix9-proof-positive.json"))
    candidate["observations"][0]["calls"]["model_calls"] = 1
    with pytest.raises(jsonschema.ValidationError):
        _validator(OBSERVATION_SCHEMA_PATH).validate(candidate)


def test_uix9_authority_expansion_is_rejected() -> None:
    candidate = deepcopy(dry_run())
    candidate["authority"]["live_model_calls_authorized"] = True
    with pytest.raises(jsonschema.ValidationError):
        _validator(RESULT_SCHEMA_PATH).validate(candidate)
