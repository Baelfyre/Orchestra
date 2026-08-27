from __future__ import annotations

import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from internal import uix9c_v3_stdin_transport as v3


def test_frozen_prompt_digests_remain_exact() -> None:
    a_prompt, a_digest = v3.v2.build_prompt("BASELINE_NO_ORCHESTRA_UIX_GUIDANCE")
    b_prompt, b_digest = v3.v2.build_prompt("GOVERNED_CANONICAL_UIX_1_8_GUIDANCE")
    assert a_prompt
    assert b_prompt
    assert a_digest == v3.EXPECTED_A_PROMPT_DIGEST
    assert b_digest == v3.EXPECTED_B_PROMPT_DIGEST


def test_stdin_command_excludes_prompt_and_uses_forced_sentinel() -> None:
    workspace = v3.v2.FIXTURE_ROOT / "project"
    a_prompt, _ = v3.v2.build_prompt("BASELINE_NO_ORCHESTRA_UIX_GUIDANCE")
    b_prompt, _ = v3.v2.build_prompt("GOVERNED_CANONICAL_UIX_1_8_GUIDANCE")
    command = v3.build_stdin_command(workspace_dir=workspace)

    assert command[-1] == "-"
    assert a_prompt not in command
    assert b_prompt not in command
    assert v3.v2.EXPECTED_MODEL in command
    assert f'model_reasoning_effort="{v3.v2.EXPECTED_REASONING_EFFORT}"' in command
    assert sum(len(item) + 1 for item in command) < 8192


def test_session_runner_sends_exact_prompt_over_utf8_stdin(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    prompt = "governed prompt with Unicode: ”"
    captured: dict = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured.update(kwargs)
        stdout = "\n".join(
            [
                json.dumps({"type": "thread.started"}),
                json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "done"}}),
                json.dumps({"type": "turn.completed", "usage": {"input_tokens": 3, "output_tokens": 2, "total_tokens": 5}}),
            ]
        )
        return SimpleNamespace(returncode=0, stdout=stdout, stderr="")

    monkeypatch.setattr(v3.v2, "verify_codex_cli_version", lambda: v3.v2.EXPECTED_CODEX_CLI_VERSION)
    monkeypatch.setattr(v3.subprocess, "run", fake_run)

    result = v3.run_codex_session_stdin(tmp_path, prompt)

    assert result["classification"] == "OUTPUT_CAPTURED_PENDING_VALIDATOR"
    assert result["prompt_transport"] == "STDIN_UTF8"
    assert result["command"][-1] == "-"
    assert prompt not in result["command"]
    assert captured["input"] == prompt
    assert captured["text"] is True
    assert captured["encoding"] == "utf-8"
    assert captured["errors"] == "strict"
    assert captured["shell"] is False
    assert captured["check"] is False


def test_materialized_authorization_is_exact_and_requires_explicit_live_gate() -> None:
    authorization = v3._load_authorization()
    assert authorization["authorization_status"] == "APPROVED"
    assert authorization["authority_class"] == "HUMAN_SCIENTIFIC_AUTHORIZATION"
    assert authorization["authority_boundary"]["live_execution_authorized"] is True
    with pytest.raises(v3.V3ExecutionRefused, match="V3_EXPLICIT_LIVE_GATE_REQUIRED"):
        v3._authorize_live_v3(authorization, live_call_gate=False)
    v3._authorize_live_v3(authorization, live_call_gate=True)


def test_approved_authorization_does_not_invoke_campaign_without_explicit_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    called = False

    def should_not_execute(**_kwargs):
        nonlocal called
        called = True
        raise AssertionError("campaign must not execute without the explicit V3 live gate")

    monkeypatch.setattr(v3.v2, "execute_campaign", should_not_execute)
    with pytest.raises(v3.V3ExecutionRefused, match="V3_EXPLICIT_LIVE_GATE_REQUIRED"):
        v3.execute_v3(live_call_gate=False)
    assert called is False


def _approved_authorization() -> dict:
    authorization = copy.deepcopy(v3._load_authorization())
    authorization["authorization_status"] = "APPROVED"
    authorization["authority_class"] = "HUMAN_SCIENTIFIC_AUTHORIZATION"
    authorization["authority_boundary"]["live_execution_authorized"] = True
    return authorization


def test_approved_status_without_human_scientific_authority_class_is_refused() -> None:
    authorization = _approved_authorization()
    authorization["authority_class"] = "HUMAN_SCIENTIFIC_AUTHORIZATION_REQUIRED"
    with pytest.raises(v3.V3ExecutionRefused, match="V3_HUMAN_SCIENTIFIC_AUTHORITY_CLASS_REQUIRED"):
        v3._authorize_live_v3(authorization, live_call_gate=True)


def test_approved_v3_envelope_supersedes_only_v2_call_ceiling_gate_and_restores_globals(monkeypatch: pytest.MonkeyPatch) -> None:
    authorization = _approved_authorization()
    originals = {
        "max_model": v3.v2.MAX_TOTAL_MODEL_CALLS,
        "max_provider": v3.v2.MAX_PROVIDER_CALLS,
        "max_interactions": v3.v2.MAX_TOTAL_PROVIDER_INTERACTIONS,
        "max_retries": v3.v2.MAX_RETRIES_FOR_INVALID_RUN,
        "authorize_live": v3.v2._authorize_live,
    }
    observed: dict = {}

    def fake_execute_campaign(**kwargs):
        observed.update(kwargs)
        assert v3.v2.MAX_TOTAL_MODEL_CALLS == 7
        assert v3.v2.MAX_PROVIDER_CALLS == 7
        assert v3.v2.MAX_TOTAL_PROVIDER_INTERACTIONS == 7
        assert v3.v2.MAX_RETRIES_FOR_INVALID_RUN == 1
        v3.v2._authorize_live({}, live_call_gate=True)
        assert callable(kwargs["session_runner"])
        return {"status": "MOCK_EXECUTION_BOUND_TO_V3_ENVELOPE"}

    monkeypatch.setattr(v3, "_load_authorization", lambda: authorization)
    monkeypatch.setattr(v3.v2, "execute_campaign", fake_execute_campaign)

    result = v3.execute_v3(live_call_gate=True)

    assert result == {"status": "MOCK_EXECUTION_BOUND_TO_V3_ENVELOPE"}
    assert observed["evidence_root"] == v3.EVIDENCE_ROOT
    assert observed["live_call_gate"] is True
    assert v3.v2.MAX_TOTAL_MODEL_CALLS == originals["max_model"]
    assert v3.v2.MAX_PROVIDER_CALLS == originals["max_provider"]
    assert v3.v2.MAX_TOTAL_PROVIDER_INTERACTIONS == originals["max_interactions"]
    assert v3.v2.MAX_RETRIES_FOR_INVALID_RUN == originals["max_retries"]
    assert v3.v2._authorize_live is originals["authorize_live"]


def test_v3_envelope_restores_v2_globals_after_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    authorization = _approved_authorization()
    original_authorize = v3.v2._authorize_live
    original_model_ceiling = v3.v2.MAX_TOTAL_MODEL_CALLS

    def fail_campaign(**_kwargs):
        assert v3.v2.MAX_TOTAL_MODEL_CALLS == 7
        raise RuntimeError("synthetic failure")

    monkeypatch.setattr(v3, "_load_authorization", lambda: authorization)
    monkeypatch.setattr(v3.v2, "execute_campaign", fail_campaign)

    with pytest.raises(RuntimeError, match="synthetic failure"):
        v3.execute_v3(live_call_gate=True)

    assert v3.v2.MAX_TOTAL_MODEL_CALLS == original_model_ceiling
    assert v3.v2._authorize_live is original_authorize


def test_single_invalid_replacement_is_campaign_global(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    sequence = iter(
        [
            {"classification": "HOST_CRASH"},
            {"classification": "OUTPUT_CAPTURED_PENDING_VALIDATOR"},
            {"classification": "PROVIDER_OUTAGE"},
        ]
    )
    original_retry_ceiling = v3.v2.MAX_RETRIES_FOR_INVALID_RUN
    v3.v2.MAX_RETRIES_FOR_INVALID_RUN = 1
    try:
        monkeypatch.setattr(v3, "run_codex_session_stdin", lambda _workspace, _prompt: next(sequence))
        runner = v3._single_replacement_session_runner()

        first = runner(tmp_path, "prompt")
        assert first["classification"] == "HOST_CRASH"
        assert v3.v2.MAX_RETRIES_FOR_INVALID_RUN == 1

        replacement = runner(tmp_path, "prompt")
        assert replacement["classification"] == "OUTPUT_CAPTURED_PENDING_VALIDATOR"
        assert v3.v2.MAX_RETRIES_FOR_INVALID_RUN == 0

        later_invalid = runner(tmp_path, "prompt")
        assert later_invalid["classification"] == "PROVIDER_OUTAGE"
        assert v3.v2.MAX_RETRIES_FOR_INVALID_RUN == 0
    finally:
        v3.v2.MAX_RETRIES_FOR_INVALID_RUN = original_retry_ceiling


def test_v3_evidence_root_is_fresh_and_separate() -> None:
    assert v3.EVIDENCE_ROOT != v3.v2.EVIDENCE_ROOT
    assert v3.v2.EVIDENCE_ROOT.resolve() in v3.EVIDENCE_ROOT.resolve().parents
    authorization = v3._load_authorization()
    assert authorization["evidence_policy"]["reuse_prior_a1_observation"] is False
    assert authorization["evidence_policy"]["preserve_all_prior_invalid_evidence"] is True
    assert authorization["evidence_policy"]["prior_invalid_evidence_is_scientific_result"] is False


def test_v3_proposed_ceiling_cannot_create_seventh_valid_observation() -> None:
    authorization = v3._load_authorization()
    ceiling = authorization["fresh_campaign_proposed_ceiling"]
    assert ceiling["max_new_model_calls"] == 7
    assert ceiling["max_new_provider_calls"] == 7
    assert ceiling["max_new_provider_interactions"] == 7
    assert ceiling["max_invalid_infrastructure_replacements"] == 1
    assert ceiling["max_valid_observations"] == 6
    assert ceiling["seventh_valid_observation_authorized"] is False
    assert ceiling["additional_ceiling_expansion_authorized"] is False
