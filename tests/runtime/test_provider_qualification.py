from __future__ import annotations

import json
from pathlib import Path

import pytest

from orchestra_runtime.provider_qualification import (
    PROVIDER_QUALIFICATION_RECEIPT_VERSION,
    VSCODE_PROVIDER_OBSERVATION_VERSION,
    VSCODE_PROVIDER_QUALIFICATION_FIXTURE_ID,
    VSCODE_PROVIDER_QUALIFICATION_FIXTURE_SHA256,
    ProviderQualificationClassification,
    ProviderQualificationContractError,
    VSCodeProviderObservation,
    qualify_vscode_provider_observation,
)
from scripts.qualify_vscode_provider import main as qualify_cli_main


ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_SHA = "1" * 40


def observation_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": VSCODE_PROVIDER_OBSERVATION_VERSION,
        "host_id": "vscode",
        "harness_id": "copilot",
        "provider_source_id": "copilot",
        "provider_id": "anthropic",
        "model_id": "claude-sonnet-test",
        "execution_environment": "CURRENT_WORKSPACE",
        "repository_sha": REPOSITORY_SHA,
        "fixture_id": VSCODE_PROVIDER_QUALIFICATION_FIXTURE_ID,
        "fixture_sha256": VSCODE_PROVIDER_QUALIFICATION_FIXTURE_SHA256,
        "live_model_execution": False,
        "session_target_observed": False,
        "model_identity_observed": False,
        "provider_source_observed": False,
        "fixture_result_observed": False,
        "worktree_clean_before": True,
        "worktree_clean_after": True,
        "result": "NOT_RUN",
        "evidence_refs": [],
        "limitations": ["static configuration evidence only"],
    }
    payload.update(overrides)
    return payload


def live_payload(**overrides: object) -> dict[str, object]:
    payload = observation_payload(
        live_model_execution=True,
        session_target_observed=True,
        model_identity_observed=True,
        provider_source_observed=True,
        fixture_result_observed=True,
        result="PASS",
        evidence_refs=["operator-evidence:vscode-session-001"],
        limitations=["manual VS Code observation"],
    )
    payload.update(overrides)
    return payload


def test_static_configuration_is_not_live_qualification() -> None:
    receipt = qualify_vscode_provider_observation(observation_payload())

    assert receipt.schema_version == PROVIDER_QUALIFICATION_RECEIPT_VERSION
    assert receipt.classification is ProviderQualificationClassification.STATIC_CONFIGURATION_ONLY
    assert receipt.live_model_path_observed is False
    assert receipt.provider_native_harness_path_observed is False
    assert receipt.automatic_routing_authorized is False
    assert receipt.provider_execution_authority is False
    assert receipt.release_authorized is False


def test_copilot_routed_claude_is_host_routed_not_provider_native() -> None:
    receipt = qualify_vscode_provider_observation(live_payload())

    assert receipt.classification is ProviderQualificationClassification.LIVE_HOST_ROUTED_MODEL_OBSERVED
    assert receipt.provider_id == "anthropic"
    assert receipt.provider_source_id == "copilot"
    assert receipt.live_model_path_observed is True
    assert receipt.provider_native_harness_path_observed is False


def test_claude_harness_with_anthropic_source_is_provider_native_observation() -> None:
    receipt = qualify_vscode_provider_observation(
        live_payload(
            harness_id="claude",
            provider_source_id="anthropic",
            provider_id="anthropic",
        )
    )

    assert receipt.classification is ProviderQualificationClassification.LIVE_PROVIDER_NATIVE_HARNESS_OBSERVED
    assert receipt.live_model_path_observed is True
    assert receipt.provider_native_harness_path_observed is True


def test_claude_harness_with_copilot_source_remains_host_routed() -> None:
    receipt = qualify_vscode_provider_observation(
        live_payload(
            harness_id="claude",
            provider_source_id="copilot",
            provider_id="anthropic",
        )
    )

    assert receipt.classification is ProviderQualificationClassification.LIVE_HOST_ROUTED_MODEL_OBSERVED
    assert receipt.provider_native_harness_path_observed is False


def test_codex_harness_with_chatgpt_source_is_provider_native_observation() -> None:
    receipt = qualify_vscode_provider_observation(
        live_payload(
            harness_id="codex",
            provider_source_id="chatgpt",
            provider_id="openai",
            model_id="gpt-test",
        )
    )

    assert receipt.classification is ProviderQualificationClassification.LIVE_PROVIDER_NATIVE_HARNESS_OBSERVED
    assert receipt.provider_native_harness_path_observed is True


def test_google_model_through_copilot_is_host_routed() -> None:
    receipt = qualify_vscode_provider_observation(
        live_payload(
            harness_id="copilot",
            provider_source_id="copilot",
            provider_id="google",
            model_id="gemini-test",
        )
    )

    assert receipt.classification is ProviderQualificationClassification.LIVE_HOST_ROUTED_MODEL_OBSERVED
    assert receipt.provider_native_harness_path_observed is False


def test_failed_live_path_does_not_count_as_live_qualification() -> None:
    receipt = qualify_vscode_provider_observation(
        live_payload(
            result="FAIL",
            fixture_result_observed=False,
            worktree_clean_after=False,
            limitations=["host execution failed"],
        )
    )

    assert receipt.classification is ProviderQualificationClassification.LIVE_MODEL_PATH_FAILED
    assert receipt.live_model_path_observed is False
    assert receipt.provider_native_harness_path_observed is False


def test_anthropic_source_cannot_claim_openai_provider() -> None:
    with pytest.raises(ProviderQualificationContractError) as exc_info:
        VSCodeProviderObservation.from_dict(
            live_payload(
                harness_id="claude",
                provider_source_id="anthropic",
                provider_id="openai",
            )
        )

    assert exc_info.value.reason_code == "VSCODE_PROVIDER_SOURCE_PROVIDER_MISMATCH"


def test_chatgpt_source_cannot_claim_anthropic_provider() -> None:
    with pytest.raises(ProviderQualificationContractError) as exc_info:
        VSCodeProviderObservation.from_dict(
            live_payload(
                harness_id="codex",
                provider_source_id="chatgpt",
                provider_id="anthropic",
            )
        )

    assert exc_info.value.reason_code == "VSCODE_PROVIDER_SOURCE_PROVIDER_MISMATCH"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("fixture_id", "substitute-fixture"),
        ("fixture_sha256", "3" * 64),
    ],
)
def test_observation_rejects_substitute_fixture(field: str, value: object) -> None:
    with pytest.raises(ProviderQualificationContractError) as exc_info:
        VSCodeProviderObservation.from_dict(observation_payload(**{field: value}))

    assert exc_info.value.reason_code == "VSCODE_QUALIFICATION_FIXTURE_MISMATCH"


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("session_target_observed", False, "LIVE_PROVIDER_IDENTITY_INCOMPLETE"),
        ("model_identity_observed", False, "LIVE_PROVIDER_IDENTITY_INCOMPLETE"),
        ("provider_source_observed", False, "LIVE_PROVIDER_IDENTITY_INCOMPLETE"),
        ("fixture_result_observed", False, "LIVE_PROVIDER_FIXTURE_RESULT_REQUIRED"),
        ("worktree_clean_before", False, "LIVE_PROVIDER_REPOSITORY_STATE_UNSAFE"),
        ("worktree_clean_after", False, "LIVE_PROVIDER_REPOSITORY_STATE_UNSAFE"),
    ],
)
def test_live_pass_requires_complete_observation(field: str, value: object, reason: str) -> None:
    with pytest.raises(ProviderQualificationContractError) as exc_info:
        VSCodeProviderObservation.from_dict(live_payload(**{field: value}))

    assert exc_info.value.reason_code == reason


def test_live_observation_requires_evidence_refs() -> None:
    with pytest.raises(ProviderQualificationContractError) as exc_info:
        VSCodeProviderObservation.from_dict(live_payload(evidence_refs=[]))

    assert exc_info.value.reason_code == "LIVE_PROVIDER_EVIDENCE_REQUIRED"


def test_non_live_observation_must_use_not_run() -> None:
    with pytest.raises(ProviderQualificationContractError) as exc_info:
        VSCodeProviderObservation.from_dict(observation_payload(result="PASS"))

    assert exc_info.value.reason_code == "INVALID_VSCODE_PROVIDER_OBSERVATION"


def test_live_observation_cannot_use_not_run() -> None:
    with pytest.raises(ProviderQualificationContractError) as exc_info:
        VSCodeProviderObservation.from_dict(live_payload(result="NOT_RUN"))

    assert exc_info.value.reason_code == "INVALID_VSCODE_PROVIDER_OBSERVATION"


def test_observation_rejects_unknown_fields() -> None:
    payload = observation_payload()
    payload["routing_authorized"] = True

    with pytest.raises(ProviderQualificationContractError) as exc_info:
        VSCodeProviderObservation.from_dict(payload)

    assert exc_info.value.reason_code == "INVALID_VSCODE_PROVIDER_OBSERVATION"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("repository_sha", "abc"),
        ("fixture_sha256", "abc"),
        ("provider_id", "Anthropic Provider"),
        ("model_id", "bad\nmodel"),
        ("host_id", "not-vscode"),
        ("harness_id", "gemini"),
        ("execution_environment", "UNKNOWN"),
        ("schema_version", "orchestra.vscode-provider-observation.v0"),
    ],
)
def test_observation_rejects_malformed_identity_or_version(field: str, value: object) -> None:
    with pytest.raises(ProviderQualificationContractError):
        VSCodeProviderObservation.from_dict(observation_payload(**{field: value}))


def test_observation_rejects_non_boolean_flags() -> None:
    with pytest.raises(ProviderQualificationContractError) as exc_info:
        VSCodeProviderObservation.from_dict(observation_payload(live_model_execution=1))

    assert exc_info.value.reason_code == "INVALID_VSCODE_PROVIDER_OBSERVATION"


def test_observation_rejects_duplicate_evidence_refs() -> None:
    with pytest.raises(ProviderQualificationContractError) as exc_info:
        VSCodeProviderObservation.from_dict(
            live_payload(evidence_refs=["operator-evidence:one", "operator-evidence:one"])
        )

    assert exc_info.value.reason_code == "INVALID_VSCODE_PROVIDER_OBSERVATION"


def test_observation_digest_is_deterministic_and_identity_sensitive() -> None:
    first = VSCodeProviderObservation.from_dict(observation_payload())
    second = VSCodeProviderObservation.from_dict(observation_payload())
    changed = VSCodeProviderObservation.from_dict(observation_payload(model_id="another-model"))

    assert first.observation_digest == second.observation_digest
    assert first.observation_digest != changed.observation_digest
    assert len(first.observation_digest) == 64


def test_receipt_serialization_preserves_non_authorizing_flags() -> None:
    receipt = qualify_vscode_provider_observation(live_payload())
    payload = receipt.to_dict()

    assert payload["automatic_routing_authorized"] is False
    assert payload["provider_execution_authority"] is False
    assert payload["release_authorized"] is False
    assert payload["classification"] == "LIVE_HOST_ROUTED_MODEL_OBSERVED"
    assert payload["observation_digest"]


def test_cli_writes_qualification_receipt(tmp_path: Path) -> None:
    input_path = tmp_path / "observation.json"
    output_path = tmp_path / "receipt.json"
    input_path.write_text(json.dumps(live_payload()), encoding="utf-8")

    assert qualify_cli_main(["--input", str(input_path), "--output", str(output_path)]) == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["classification"] == "LIVE_HOST_ROUTED_MODEL_OBSERVED"
    assert payload["automatic_routing_authorized"] is False


def test_cli_fails_closed_for_invalid_observation(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    input_path = tmp_path / "observation.json"
    input_path.write_text(json.dumps(live_payload(evidence_refs=[])), encoding="utf-8")

    assert qualify_cli_main(["--input", str(input_path)]) == 2
    captured = capsys.readouterr()
    assert "LIVE_PROVIDER_EVIDENCE_REQUIRED" in captured.err


def test_machine_schemas_preserve_authority_and_classification_boundaries() -> None:
    observation_schema = json.loads(
        (ROOT / "machine/schemas/vscode-provider-observation.v1.schema.json").read_text(encoding="utf-8")
    )
    receipt_schema = json.loads(
        (ROOT / "machine/schemas/provider-qualification-receipt.v1.schema.json").read_text(encoding="utf-8")
    )

    assert observation_schema["properties"]["harness_id"]["enum"] == ["local", "copilot", "claude", "codex"]
    assert receipt_schema["properties"]["automatic_routing_authorized"]["const"] is False
    assert receipt_schema["properties"]["provider_execution_authority"]["const"] is False
    assert receipt_schema["properties"]["release_authorized"]["const"] is False
    assert "LIVE_PROVIDER_NATIVE_HARNESS_OBSERVED" in receipt_schema["properties"]["classification"]["enum"]
