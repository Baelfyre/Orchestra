from __future__ import annotations

import hashlib
import json
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "machine" / "ui" / "uix9-proof-plan.v1.json"
PLAN_SCHEMA_PATH = ROOT / "machine" / "schemas" / "uix-proof-plan.schema.json"
OBSERVATION_SCHEMA_PATH = ROOT / "machine" / "schemas" / "uix-proof-observation.schema.json"
RESULT_SCHEMA_PATH = ROOT / "machine" / "schemas" / "uix-proof-result.schema.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _validator(path: Path) -> jsonschema.Draft202012Validator:
    schema = _load(path)
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


def _validate(path: Path, schema_path: Path) -> dict:
    value = _load(path)
    _validator(schema_path).validate(value)
    return value


def _require_zero_calls(value: dict) -> None:
    for field in ("model_calls", "provider_calls", "external_repo_mutations", "model_self_ratings", "subjective_visual_scores", "endpoint_changes"):
        assert value[field] == 0, f"non-zero dry-run side effect: {field}"


def _validate_bundle(path: Path, expected_kind: str, requirements_digest: str) -> dict:
    bundle = _validate(path, OBSERVATION_SCHEMA_PATH)
    assert bundle["fixture_kind"] == expected_kind
    assert bundle["requirements_digest"] == requirements_digest
    assert bundle["project_fixture_digest"] == requirements_digest
    assert bundle["arms_differ_only_by_uixtreatment"] is True
    _require_zero_calls(bundle["external_side_effects"])

    observations = bundle["observations"]
    assert observations[0]["arm_id"] == "BASELINE_NO_ORCHESTRA_UIX_GUIDANCE"
    assert observations[1]["arm_id"] == "GOVERNED_CANONICAL_UIX_1_8_GUIDANCE"
    for observation in observations:
        assert observation["requirements_digest"] == requirements_digest
        assert observation["project_fixture_digest"] == requirements_digest
        _require_zero_calls(observation["calls"])
        assert observation["evidence"]["observed_from"] == "REPOSITORY_FIXTURE"
        assert observation["evidence"]["model_output_observed"] is False

    if expected_kind == "POSITIVE_VALIDATOR":
        assert all(observation["acceptance"]["status"] == "PASS" for observation in observations)
    else:
        assert any(observation["acceptance"]["status"] == "FAIL_CLOSED" for observation in observations)
    return bundle


def dry_run() -> dict:
    plan = _validate(PLAN_PATH, PLAN_SCHEMA_PATH)
    requirements_path = ROOT / plan["fixtures"]["project_requirements"]
    requirements_digest = hashlib.sha256(requirements_path.read_bytes()).hexdigest()

    positive = _validate_bundle(ROOT / plan["fixtures"]["positive"], "POSITIVE_VALIDATOR", requirements_digest)
    negative = _validate_bundle(ROOT / plan["fixtures"]["negative"], "NEGATIVE_VALIDATOR", requirements_digest)
    observations = positive["observations"] + negative["observations"]

    result = {
        "$schema": "../schemas/uix-proof-result.schema.json",
        "schema_version": "orchestra.uix-proof-result.v1",
        "role": "UIX_9A_CONTROLLED_PROOF_RESULT",
        "entry_baseline": plan["entry_baseline"],
        "status": "UIX_9_PROOF_PREPARED_WAITING_LIVE_CALL_AUTHORIZATION",
        "dry_run": {
            "fixtures_validated": True,
            "positive_validator_case": True,
            "negative_validator_case": True,
            "baseline_governed_requirements_same": True,
            "arms_differ_only_by_uixtreatment": True,
            "live_model_calls": 0,
            "provider_calls": 0,
            "external_repo_mutations": 0,
            "model_self_ratings": 0,
            "subjective_visual_scores": 0,
            "endpoint_changes": 0,
            "write_isolated": True,
        },
        "observation_refs": [observation["observation_id"] for observation in observations],
        "metrics_covered": plan["metrics"],
        "claim_boundary": {
            "behavior_improvement_claimed": False,
            "benefit_established": False,
            "live_call_authorization_required": True,
            "allowed_terminal": "UIX_9_PROOF_PREPARED_WAITING_LIVE_CALL_AUTHORIZATION",
            "rationale": "Repository fixtures validate protocol determinism only; no model or provider behavior was observed.",
        },
        "authority": {
            "live_model_calls_authorized": False,
            "provider_calls_authorized": False,
            "external_repo_mutation_authorized": False,
            "release_authorized": False,
            "deployment_authorized": False,
            "policy_activation_authorized": False,
            "destructive_action_authorized": False,
        },
    }
    _validator(RESULT_SCHEMA_PATH).validate(result)
    return result


if __name__ == "__main__":
    print(json.dumps(dry_run(), indent=2, sort_keys=True))
