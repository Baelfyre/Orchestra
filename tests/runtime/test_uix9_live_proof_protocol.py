from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys

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


def test_v2_identity_gate_separates_frozen_base_from_current_canonical() -> None:
    report = v2_runner.verify_frozen_identities()

    assert report["canonical_sha"] == "bf6f14316fa8814eeac91440c4a7d70be0d04b9e"
    assert report["frozen_experiment_base_sha"] == report["canonical_sha"]
    assert report["current_canonical_preparation_sha"] == "7e08a1d4aa09cbdf7632f5a86461fb3cd3e50fe9"
    assert report["reviewed_canonical_sha"] == report["current_canonical_preparation_sha"]
    assert report["canonical_lineage_verified"] is True
    assert report["preparation_content_verified"] is True


def test_canonical_preparation_drift_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(v2_runner, "canonical_fixture_digest", lambda _revision: "0" * 64)

    with pytest.raises(RuntimeError, match="CANONICAL_FIXTURE_DRIFT"):
        v2_runner.verify_frozen_identities()


def test_default_execute_path_refuses_before_codex(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(v2_runner, "run_codex_session", lambda *_args: (_ for _ in ()).throw(AssertionError("Codex must not run")))
    monkeypatch.setattr(sys, "argv", ["uix9b_live_proof_runner_v2.py", "execute"])

    assert v2_runner.main() == 2
    captured = capsys.readouterr()
    assert "UIX_9C_EXECUTION_REFUSED_EXPLICIT_LIVE_GATE_REQUIRED" in captured.out


def test_explicit_live_gate_still_requires_approved_authorization(monkeypatch: pytest.MonkeyPatch) -> None:
    called = False

    def never_run(*_args: object) -> dict:
        nonlocal called
        called = True
        raise AssertionError("Codex must not run")

    with pytest.raises(v2_runner.ExecutionRefused, match="HUMAN_LIVE_AUTHORIZATION_REQUIRED"):
        v2_runner.execute_campaign(live_call_gate=True, session_runner=never_run)
    assert called is False


def test_arm_prompts_preserve_treatment_boundary() -> None:
    arm_a, digest_a = v2_runner.build_prompt("BASELINE_NO_ORCHESTRA_UIX_GUIDANCE")
    arm_b, digest_b = v2_runner.build_prompt("GOVERNED_CANONICAL_UIX_1_8_GUIDANCE")

    assert digest_a != digest_b
    assert "canonical UIX-1 through UIX-8" not in arm_a
    assert "UIX_1_DESIGN_CONTRACT" not in arm_a
    assert "canonical UIX-1 through UIX-8" in arm_b
    assert not any(marker in arm_b.lower() for marker in v2_runner.UIX9_RESULT_LOGIC_MARKERS)


def test_codex_command_is_bounded_and_provider_fixed() -> None:
    workspace = ROOT / "tests" / "fixtures" / "ui" / "uix9-live-project" / "project"
    command = v2_runner.build_codex_command(prompt="task", workspace_dir=workspace)

    assert command[:4] == ["codex", "--ask-for-approval", "never", "exec"]
    assert "--ephemeral" in command
    assert command[command.index("--sandbox") + 1] == "workspace-write"
    assert command[command.index("--model") + 1] == "gpt-5.6-luna"
    assert command[command.index("--cd") + 1] == str(workspace.resolve())
    assert "--dangerously-bypass-approvals-and-sandbox" not in command
    assert "--yolo" not in command
    assert "--ignore-rules" not in command


def test_observation_schema_accepts_zero_call_canary_and_one_future_session() -> None:
    schema = _load(ROOT / "machine/schemas/uix9b-live-proof-observation.v2.schema.json")
    assert schema["properties"]["model_call_count"] == {"type": "integer", "minimum": 0, "maximum": 1}
    assert schema["properties"]["provider_call_count"] == {"type": "integer", "minimum": 0, "maximum": 1}
    assert schema["$defs"]["sideEffects"]["properties"]["model_calls"] == {"type": "integer", "minimum": 0, "maximum": 1}
    assert schema["$defs"]["sideEffects"]["properties"]["provider_calls"] == {"type": "integer", "minimum": 0, "maximum": 1}


def validate_json_value(value: dict, schema_path: Path) -> None:
    schema = _load(schema_path)
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(value)


def _valid_validator(fixture_root: Path, candidate_root: Path, run_root: Path) -> dict:
    identity = _load(ROOT / "machine/ui/uix9b-live-proof-v2-identity.json")
    check_names = _load(ROOT / "machine/schemas/uix9b-validator-result.v2.schema.json")["properties"]["checks"]["required"]
    result = {
        "$schema": "../../../machine/schemas/uix9b-validator-result.v2.schema.json",
        "schema_version": "orchestra.uix9b-validator-result.v2",
        "role": "UIX_9B_INDEPENDENT_VALIDATOR_RESULT",
        "candidate_tree_digest": v2_runner.evaluator.tree_digest(candidate_root),
        "fixture_digest": identity["fixture_digest"],
        "validator_digest": identity["validator_digest"],
        "dependency_manifest_digest": v2_runner.evaluator.digest_file(fixture_root / "project/package-lock.json"),
        "asset_manifest_digest": v2_runner.evaluator.digest_file(fixture_root / "asset-manifest.json"),
        "component_map_digest": v2_runner.evaluator.digest_file(fixture_root / "component-map.json"),
        "design_token_digest": v2_runner.evaluator.digest_file(fixture_root / "design-tokens.json"),
        "checks": {name: {"status": "PASS", "deterministic": True, "details": "synthetic zero-call validation"} for name in check_names},
        "model_calls": 0,
        "provider_calls": 0,
        "network_access": 0,
        "external_repo_mutations": 0,
    }
    v2_runner._atomic_json(run_root / "validator-result.json", result)
    return result


def _valid_metric(fixture_root: Path, candidate_root: Path, _validator_path: Path, _identity_path: Path) -> dict:
    identity = _load(ROOT / "machine/ui/uix9b-live-proof-v2-identity.json")
    metrics = {
        "COMPONENT_REUSE": True,
        "DUPLICATE_COMPONENT_COUNT": 0,
        "TOKEN_VIOLATIONS": 0,
        "ARBITRARY_STYLE_DRIFT": 0,
        "STATE_COVERAGE": 1.0,
        "ASSET_PROVENANCE": True,
        "ASSET_SUBSTITUTION": False,
        "RESPONSIVE_CONTAINMENT": True,
        "ACCESSIBILITY_INVARIANTS": True,
        "UNRESOLVED_MAPPINGS": 0,
        "REVISION_MISMATCH": False,
        "VISUAL_BASELINE_REPLACEMENT": False,
        "DETERMINISTIC_ACCEPTANCE": True,
    }
    result = {
        "$schema": "../../../machine/schemas/uix9b-live-metric-result.v2.schema.json",
        "schema_version": "orchestra.uix9b-live-metric-result.v2",
        "role": "UIX_9B_LIVE_METRIC_RESULT",
        "evaluator_version": identity["evaluator_version"],
        "evaluator_digest": identity["evaluator_digest"],
        "fixture_digest": identity["fixture_digest"],
        "task_digest": identity["task_digest"],
        "validator_digest": identity["validator_digest"],
        "uix_guidance_digest": identity["uix_guidance_digest"],
        "candidate_tree_digest": v2_runner.evaluator.tree_digest(candidate_root),
        "metric_result_digest": None,
        "status": "PASS",
        "failure_codes": [],
        "metrics": metrics,
        "deterministic": True,
    }
    result["metric_result_digest"] = v2_runner.evaluator.metric_payload_digest("PASS", result["candidate_tree_digest"], metrics, [])
    return result


def _session_success(_workspace: Path, _prompt: str) -> dict:
    return {"classification": "OUTPUT_CAPTURED_PENDING_VALIDATOR", "parsed": {}}


def _pipeline_case(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, validator_runner=_valid_validator, evaluator_runner=_valid_metric):
    monkeypatch.setattr(v2_runner, "EVIDENCE_ROOT", tmp_path)
    run = v2_runner.arm_for_run("A1")
    stage = tmp_path / "staging" / "pairs" / "PAIR_1" / "A1"
    workspace = stage / "fixture"
    workspace.parent.mkdir(parents=True)
    import shutil
    shutil.copytree(v2_runner.FIXTURE_ROOT, workspace, ignore=shutil.ignore_patterns("dist", "node_modules"))
    prompt, prompt_digest = v2_runner.build_prompt(run["arm_id"])
    observation = v2_runner._run_session_pipeline(
        run=run,
        prompt_digest=prompt_digest,
        workspace=workspace,
        stage_root=stage,
        raw_result=_session_success(workspace, prompt),
        validator_runner=validator_runner,
        evaluator_runner=evaluator_runner,
    )
    return stage, observation


def _campaign(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, session_runner=_session_success, validator_runner=_valid_validator, evaluator_runner=_valid_metric, adjudicator_runner=None):
    monkeypatch.setattr(v2_runner, "EVIDENCE_ROOT", tmp_path)
    monkeypatch.setattr(v2_runner, "_authorize_live", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(v2_runner, "verify_frozen_identities", lambda: {"synthetic": True})
    kwargs = {
        "evidence_root": tmp_path,
        "live_call_gate": True,
        "session_runner": session_runner,
        "validator_runner": validator_runner,
        "evaluator_runner": evaluator_runner,
    }
    if adjudicator_runner is not None:
        kwargs["adjudicator_runner"] = adjudicator_runner
    return v2_runner.execute_campaign(**kwargs)


def test_successful_codex_exit_alone_does_not_count_as_valid(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def reject_adjudication(_baseline: dict, _governed: dict) -> dict:
        raise RuntimeError("synthetic adjudication failure")

    with pytest.raises(v2_runner.ProtocolBreach, match="ADJUDICATION_PIPELINE_FAILURE"):
        _campaign(tmp_path, monkeypatch, adjudicator_runner=reject_adjudication)
    state = _load(tmp_path / "campaign-state.json")
    assert all(not run["valid_session"] for run in state["runs"].values())


def test_evaluator_failure_is_invalid_session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_evaluator(*_args: object) -> dict:
        raise RuntimeError("synthetic evaluator failure")

    with pytest.raises(v2_runner.ProtocolBreach, match="EVIDENCE_PIPELINE_FAILURE"):
        _campaign(tmp_path, monkeypatch, evaluator_runner=fail_evaluator)
    assert _load(tmp_path / "campaign-state.json")["runs"]["A1"]["valid_session"] is False


def test_incomplete_metric_vector_is_invalid_session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def incomplete_metric(*args: object) -> dict:
        result = _valid_metric(*args)
        result["metrics"] = {"COMPONENT_REUSE": True}
        return result

    with pytest.raises(v2_runner.ProtocolBreach, match="EVIDENCE_PIPELINE_FAILURE"):
        _campaign(tmp_path, monkeypatch, evaluator_runner=incomplete_metric)


def test_observation_schema_failure_is_invalid_session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def malformed_observation(**_args: object) -> dict:
        return {}

    monkeypatch.setattr(v2_runner, "_build_observation", malformed_observation)
    with pytest.raises(v2_runner.ProtocolBreach, match="EVIDENCE_PIPELINE_FAILURE"):
        _campaign(tmp_path, monkeypatch)


def test_persistence_failure_is_invalid_session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(v2_runner, "persist_evaluated_artifacts", lambda *_args: (_ for _ in ()).throw(RuntimeError("synthetic persistence failure")))
    with pytest.raises(v2_runner.ProtocolBreach, match="EVIDENCE_PIPELINE_FAILURE"):
        _campaign(tmp_path, monkeypatch)


def test_missing_final_artifact_is_invalid_session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def no_supplemental(_stage: Path, **_kwargs: object) -> dict:
        return {}

    monkeypatch.setattr(v2_runner, "capture_supplemental_ui_evidence", no_supplemental)
    with pytest.raises(v2_runner.ProtocolBreach, match="MISSING_FINAL_ARTIFACT"):
        _campaign(tmp_path, monkeypatch)


def test_malformed_session_evidence_is_invalid_session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(v2_runner.ProtocolBreach, match="SESSION_NOT_VALID:PROTOCOL_BREACH"):
        _campaign(tmp_path, monkeypatch, session_runner=lambda _workspace, _prompt: [])


def test_process_failure_is_invalid_and_retries_only_under_frozen_policy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    def process_failure(_workspace: Path, _prompt: str) -> dict:
        nonlocal calls
        calls += 1
        raise OSError("synthetic process failure")

    with pytest.raises(v2_runner.ProtocolBreach, match="SESSION_NOT_VALID:HOST_CRASH"):
        _campaign(tmp_path, monkeypatch, session_runner=process_failure)

    state = _load(tmp_path / "campaign-state.json")
    assert calls == 2
    assert state["counters"] == {"model_calls": 2, "provider_calls": 2, "provider_interactions": 2, "invalid_retries": 1}
    assert state["runs"]["A1"]["valid_session"] is False


def test_malformed_raw_output_is_invalid_session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(v2_runner.ProtocolBreach, match="SESSION_NOT_VALID:PROTOCOL_BREACH"):
        _campaign(tmp_path, monkeypatch, session_runner=lambda _workspace, _prompt: {"stdout": "not-a-session"})


def test_invalid_candidate_tree_is_invalid_session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def remove_project(workspace: Path, _prompt: str) -> dict:
        import shutil
        shutil.rmtree(workspace / "project")
        return {"classification": "OUTPUT_CAPTURED_PENDING_VALIDATOR", "parsed": {}}

    with pytest.raises(v2_runner.ProtocolBreach, match="EVIDENCE_PIPELINE_FAILURE"):
        _campaign(tmp_path, monkeypatch, session_runner=remove_project, validator_runner=v2_runner.run_independent_validator)
    assert _load(tmp_path / "campaign-state.json")["runs"]["A1"]["valid_session"] is False


def test_incomplete_validator_evidence_is_invalid_session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(v2_runner.ProtocolBreach, match="EVIDENCE_PIPELINE_FAILURE"):
        _campaign(tmp_path, monkeypatch, validator_runner=lambda *_args: {})


def test_complete_valid_chain_sets_valid_session_only_after_adjudication(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _campaign(tmp_path, monkeypatch)
    state = _load(tmp_path / "campaign-state.json")
    assert all(state["runs"][run_id]["valid_session"] for run_id in v2_runner.EXECUTION_ORDER)
    assert (tmp_path / "pairs" / "PAIR_1" / "pair-adjudication.json").is_file()
    assert (tmp_path / "pairs" / "PAIR_3" / "pair-adjudication.json").is_file()


def test_partial_evidence_is_never_counted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(v2_runner, "persist_evaluated_artifacts", lambda *_args: None)
    with pytest.raises(v2_runner.ProtocolBreach, match="MISSING_FINAL_ARTIFACT"):
        _campaign(tmp_path, monkeypatch)
    state = _load(tmp_path / "campaign-state.json")
    assert all(not run["valid_session"] for run in state["runs"].values())
    assert not list((tmp_path / "pairs").glob("PAIR_*")) or not list((tmp_path / "pairs").glob("PAIR_*/pair-adjudication.json"))


def test_incomplete_evidence_surface_is_invalid_session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def persist_only_observation(root: Path, run_id: str, observation: dict, _metric_result: dict) -> None:
        v2_runner._atomic_json(root / "observations" / f"{run_id}.json", observation)

    monkeypatch.setattr(v2_runner, "persist_evaluated_artifacts", persist_only_observation)
    with pytest.raises(v2_runner.ProtocolBreach, match="MISSING_FINAL_ARTIFACT"):
        _campaign(tmp_path, monkeypatch)
    state = _load(tmp_path / "campaign-state.json")
    assert state["runs"]["A1"]["valid_session"] is False
    assert not (tmp_path / "pairs" / "PAIR_1").exists()


def test_simulated_crash_before_pair_finalization_is_invalid_and_not_promoted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    original_replace = os.replace

    def crash_before_finalization(source: str | bytes | os.PathLike, destination: str | bytes | os.PathLike) -> None:
        if Path(source).name == "PAIR_1":
            raise OSError("synthetic crash before finalization")
        original_replace(source, destination)

    monkeypatch.setattr(v2_runner.os, "replace", crash_before_finalization)
    with pytest.raises(v2_runner.ProtocolBreach, match="ADJUDICATION_PIPELINE_FAILURE"):
        _campaign(tmp_path, monkeypatch)
    state = _load(tmp_path / "campaign-state.json")
    assert all(not run["valid_session"] for run in state["runs"].values())
    assert not (tmp_path / "pairs" / "PAIR_1").exists()


def test_restart_with_partial_state_is_rejected_without_session_call(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    v2_runner._atomic_json(tmp_path / "campaign-state.json", {
        "schema_version": v2_runner.EVIDENCE_STATE_VERSION,
        "runs": {"A1": {"status": "STARTED", "valid_session": False}},
        "counters": {"model_calls": 1, "provider_calls": 1, "provider_interactions": 1, "invalid_retries": 0},
    })
    called = False

    def never_run(_workspace: Path, _prompt: str) -> dict:
        nonlocal called
        called = True
        raise AssertionError("partial recovery must not invoke a session")

    with pytest.raises(v2_runner.ExecutionRefused, match="RECOVERY_REQUIRES_AUDIT_NO_DOUBLE_COUNT"):
        _campaign(tmp_path, monkeypatch, session_runner=never_run)
    assert called is False
    assert _load(tmp_path / "campaign-state.json")["runs"]["A1"]["valid_session"] is False


def test_counter_overflow_attempt_is_rejected_without_advancing_counters(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    v2_runner._atomic_json(tmp_path / "campaign-state.json", {
        "schema_version": v2_runner.EVIDENCE_STATE_VERSION,
        "runs": {},
        "counters": {"model_calls": v2_runner.MAX_TOTAL_MODEL_CALLS, "provider_calls": v2_runner.MAX_PROVIDER_CALLS, "provider_interactions": v2_runner.MAX_TOTAL_PROVIDER_INTERACTIONS, "invalid_retries": 0},
    })
    with pytest.raises(v2_runner.ExecutionRefused, match="IMMUTABLE_PROVIDER_CEILING_REACHED"):
        _campaign(tmp_path, monkeypatch, session_runner=lambda *_args: (_ for _ in ()).throw(AssertionError("ceiling must stop before session")))
    state = _load(tmp_path / "campaign-state.json")
    assert state["counters"] == {"model_calls": 6, "provider_calls": 6, "provider_interactions": 7, "invalid_retries": 0}
    assert state["runs"]["A1"]["valid_session"] is False


def test_wrong_frozen_identity_is_rejected_before_session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(v2_runner, "verify_frozen_identities", lambda: (_ for _ in ()).throw(RuntimeError("FROZEN_BASE_IDENTITY_MISMATCH")))
    monkeypatch.setattr(v2_runner, "_authorize_live", lambda *_args, **_kwargs: None)
    called = False

    def never_run(_workspace: Path, _prompt: str) -> dict:
        nonlocal called
        called = True
        raise AssertionError("identity failure must precede session")

    with pytest.raises(RuntimeError, match="FROZEN_BASE_IDENTITY_MISMATCH"):
        v2_runner.execute_campaign(evidence_root=tmp_path, live_call_gate=True, session_runner=never_run)
    assert called is False


def test_wrong_preparation_identity_is_rejected_before_session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(v2_runner, "verify_frozen_identities", lambda: (_ for _ in ()).throw(RuntimeError("CANONICAL_PREPARATION_LINEAGE_DRIFT")))
    monkeypatch.setattr(v2_runner, "_authorize_live", lambda *_args, **_kwargs: None)
    called = False

    def never_run(_workspace: Path, _prompt: str) -> dict:
        nonlocal called
        called = True
        raise AssertionError("preparation identity failure must precede session")

    with pytest.raises(RuntimeError, match="CANONICAL_PREPARATION_LINEAGE_DRIFT"):
        v2_runner.execute_campaign(evidence_root=tmp_path, live_call_gate=True, session_runner=never_run)
    assert called is False


def test_restart_cannot_double_count_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _campaign(tmp_path, monkeypatch)
    state_before = _load(tmp_path / "campaign-state.json")
    called = False

    def never_run(_workspace: Path, _prompt: str) -> dict:
        nonlocal called
        called = True
        raise AssertionError("restart must not invoke session")

    with pytest.raises(v2_runner.ExecutionRefused, match="RECOVERY_REQUIRES_AUDIT_NO_DOUBLE_COUNT"):
        _campaign(tmp_path, monkeypatch, session_runner=never_run)
    assert called is False
    assert _load(tmp_path / "campaign-state.json") == state_before


def test_campaign_counters_are_experimental_only_and_historical_counters_unchanged(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    authorization_before = _load(ROOT / "machine/ui/uix9b-live-call-authorization-request.v2.json")
    _campaign(tmp_path, monkeypatch)
    state = _load(tmp_path / "campaign-state.json")
    assert state["counters"] == {"model_calls": 6, "provider_calls": 6, "provider_interactions": 6, "invalid_retries": 0}
    authorization_after = _load(ROOT / "machine/ui/uix9b-live-call-authorization-request.v2.json")
    assert authorization_after["historical_counters"] == authorization_before["historical_counters"]
    assert authorization_after["new_campaign_authorization_counters"] == authorization_before["new_campaign_authorization_counters"]


def test_codex_0148_approval_flag_precedes_exec_and_rules_apply() -> None:
    command = v2_runner.build_codex_command(prompt="task", workspace_dir=ROOT)
    assert command[:4] == ["codex", "--ask-for-approval", "never", "exec"]
    assert "--ignore-rules" not in command
