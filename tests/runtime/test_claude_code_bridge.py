from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess

import pytest

from internal import claude_code_bridge as bridge
from orchestra_runtime.specialist_execution import (
    SpecialistExecutionMode,
    SpecialistExecutionRequest,
    SpecialistExecutionStatus,
    SpecialistSideEffectClass,
)


class FakeRunner:
    calls: list[tuple[list[str], dict[str, object]]] = []
    version = "2.1.223 (Claude Code)"
    payload: dict[str, object] = {
        "type": "result",
        "subtype": "success",
        "session_id": "session-1",
        "structured_output": {
            "summary": "Revision mismatch found.",
            "findings": ["REVISION_DECLARED=3 differs from REVISION_FOOTER=4."],
            "evidence": ["CHECKSUM=ALDER-47"],
            "non_mutating": True,
        },
    }
    timeout_on_execution = False
    execution_returncode = 0
    execution_stderr = ""

    @classmethod
    def reset(cls) -> None:
        cls.calls.clear()
        cls.version = "2.1.223 (Claude Code)"
        cls.payload = {
            "type": "result",
            "subtype": "success",
            "session_id": "session-1",
            "structured_output": {
                "summary": "Revision mismatch found.",
                "findings": ["REVISION_DECLARED=3 differs from REVISION_FOOTER=4."],
                "evidence": ["CHECKSUM=ALDER-47"],
                "non_mutating": True,
            },
        }
        cls.timeout_on_execution = False
        cls.execution_returncode = 0
        cls.execution_stderr = ""

    @classmethod
    def run(cls, args: list[str], **kwargs):
        cls.calls.append((list(args), dict(kwargs)))
        if args[-1] == "--version":
            return subprocess.CompletedProcess(args, 0, stdout=cls.version, stderr="")
        if cls.timeout_on_execution:
            raise subprocess.TimeoutExpired(args, kwargs.get("timeout", 0))
        return subprocess.CompletedProcess(
            args,
            cls.execution_returncode,
            stdout=json.dumps(cls.payload),
            stderr=cls.execution_stderr,
        )


def _root(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    skill = root / "skills" / "scribe" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("# Scribe\nTrusted scribe fixture guidance.\n", encoding="utf-8")
    return root


def _request(
    root: Path,
    *,
    mode=SpecialistExecutionMode.HOST_NATIVE,
    command="review-docs",
    specialist="scribe",
):
    skill = root / "skills" / "scribe" / "SKILL.md"
    digest = sha256(skill.read_bytes()).hexdigest()
    return SpecialistExecutionRequest.create(
        run_id="run-p2-2a",
        parent_run_id=None,
        correlation_id="corr-p2-2a",
        adapter_name="claude-code",
        command_name=command,
        specialist=specialist,
        project_root=str(root),
        skill_source_path="skills/scribe/SKILL.md",
        skill_source_digest=digest,
        task_input="Review the fixture documentation.",
        authority_decision_ref="authority-p2-2a",
        capability_decision_ref="capability-p2-2a",
        governance_status="NOT_REQUIRED",
        evaluated_governance_rules=(),
        execution_constraints=(),
        execution_mode=mode,
    )


def _launcher():
    return bridge.ClaudeLauncher(
        executable="claude",
        executable_sha256=None,
        command_prefix=("claude",),
        resolution="TEST",
    )


def _clean_snapshot(root: Path):
    return ("head", "tree", "")


def _engine(root: Path, **kwargs):
    FakeRunner.reset()
    return bridge.ClaudeCodeExecutionEngine(
        root,
        config=kwargs.pop("config", bridge.ClaudeCodeConfig(model="claude-test-model")),
        launcher_factory=kwargs.pop("launcher_factory", _launcher),
        snapshot_factory=kwargs.pop("snapshot_factory", _clean_snapshot),
        command_runner=kwargs.pop("command_runner", FakeRunner.run),
        **kwargs,
    )


def _flag_value(command: tuple[str, ...], flag: str) -> str:
    index = command.index(flag)
    return command[index + 1]


def test_config_fails_closed_on_policy_widening():
    with pytest.raises(ValueError):
        bridge.ClaudeCodeConfig(model="")
    with pytest.raises(ValueError):
        bridge.ClaudeCodeConfig(model="unsafe\nmodel")
    with pytest.raises(ValueError):
        bridge.ClaudeCodeConfig(model="claude", turn_timeout_seconds=9)
    with pytest.raises(ValueError):
        bridge.ClaudeCodeConfig(model="claude", permission_mode="bypassPermissions")
    with pytest.raises(ValueError):
        bridge.ClaudeCodeConfig(model="claude", tools=("Read", "Edit"))
    with pytest.raises(ValueError):
        bridge.ClaudeCodeConfig(model="claude", allowed_commands=())


def test_completed_read_only_receipt_binds_host_specialist_and_invocation_policy(tmp_path):
    root = _root(tmp_path)
    engine = _engine(root)
    request = _request(root)

    receipt = engine.execute(request)

    assert receipt.status is SpecialistExecutionStatus.COMPLETED
    assert receipt.side_effect_class is SpecialistSideEffectClass.READ_ONLY
    assert receipt.reason_code == "CLAUDE_CODE_READ_ONLY_SPECIALIST_COMPLETED"
    assert receipt.request_id == request.request_id
    assert receipt.request_digest == request.request_digest
    assert receipt.specialist == "scribe"
    assert receipt.command_name == "review-docs"
    assert receipt.engine_id == bridge.ENGINE_ID
    assert receipt.engine_version == bridge.ENGINE_VERSION
    assert receipt.changed_paths == ()
    assert receipt.host_identity == "2.1.223 (Claude Code)"
    assert "claude-model:claude-test-model" in receipt.evidence_refs
    assert "claude-permission:plan" in receipt.evidence_refs
    assert "claude-tools:Glob,Grep,Read" in receipt.evidence_refs
    assert "claude-mcp:denied" in receipt.evidence_refs
    assert f"specialist-source-sha256:{request.skill_source_digest}" in receipt.evidence_refs
    receipt.assert_matches(request, engine_id=engine.engine_id, engine_version=engine.engine_version)

    command = engine.last_host_command
    assert command[:2] == ("claude", "-p")
    assert _flag_value(command, "--model") == "claude-test-model"
    assert _flag_value(command, "--permission-mode") == "plan"
    assert _flag_value(command, "--tools") == "Read,Glob,Grep"
    assert _flag_value(command, "--disallowedTools") == "mcp__*"
    assert "--safe-mode" in command
    assert "--no-chrome" in command
    assert "--no-session-persistence" in command
    assert "--dangerously-skip-permissions" not in command
    assert "--fallback-model" not in command
    assert _flag_value(command, "--append-system-prompt-file").endswith("skills/scribe/SKILL.md")
    assert request.request_id in _flag_value(command, "--append-system-prompt")


def test_structured_output_is_normalized_and_only_final_payload_is_persisted(tmp_path):
    root = _root(tmp_path)
    engine = _engine(root)
    receipt = engine.execute(_request(root))
    parsed = json.loads(receipt.output)
    assert parsed == FakeRunner.payload["structured_output"]
    assert "session-1" not in receipt.output
    assert receipt.host_execution_id == "claude-code.session-1"


@pytest.mark.parametrize(
    ("request_kwargs", "message"),
    [
        ({"mode": SpecialistExecutionMode.DETERMINISTIC_TEST_ENGINE}, "HOST_NATIVE"),
        ({"specialist": "clockwork"}, "specialist is not allowed"),
        ({"command": "implement-code"}, "command is not allowed"),
    ],
)
def test_request_boundary_rejects_wrong_execution_identity(tmp_path, request_kwargs, message):
    root = _root(tmp_path)
    engine = _engine(root)
    receipt = engine.execute(_request(root, **request_kwargs))
    assert receipt.status is SpecialistExecutionStatus.FAILED
    assert receipt.reason_code == "HOST_EXECUTION_FAILED"
    assert message in receipt.output
    assert FakeRunner.calls == []


def test_project_root_mismatch_fails_closed_before_host_invocation(tmp_path):
    root = _root(tmp_path)
    other = tmp_path / "other"
    other.mkdir()
    request = _request(root)
    object.__setattr__(request, "project_root", str(other))
    engine = _engine(root)
    receipt = engine.execute(request)
    assert receipt.status is SpecialistExecutionStatus.FAILED
    assert "project root" in receipt.output
    assert FakeRunner.calls == []


def test_skill_digest_mismatch_fails_closed_before_host_invocation(tmp_path):
    root = _root(tmp_path)
    request = _request(root)
    object.__setattr__(request, "skill_source_digest", "0" * 64)
    engine = _engine(root)
    receipt = engine.execute(request)
    assert receipt.status is SpecialistExecutionStatus.FAILED
    assert "digest" in receipt.output
    assert FakeRunner.calls == []


def test_dirty_worktree_fails_before_launcher_or_provider_call(tmp_path):
    root = _root(tmp_path)
    engine = _engine(root, snapshot_factory=lambda _: ("head", "tree", " M tracked.md"))
    receipt = engine.execute(_request(root))
    assert receipt.status is SpecialistExecutionStatus.FAILED
    assert "worktree must be clean" in receipt.output
    assert FakeRunner.calls == []


def test_cli_version_below_structured_output_floor_fails_before_provider_call(tmp_path):
    root = _root(tmp_path)
    engine = _engine(root)
    FakeRunner.version = "2.1.204 (Claude Code)"
    receipt = engine.execute(_request(root))
    assert receipt.status is SpecialistExecutionStatus.FAILED
    assert "below required version 2.1.205" in receipt.output
    assert len(FakeRunner.calls) == 1
    assert FakeRunner.calls[0][0][-1] == "--version"


def test_unparseable_cli_version_fails_closed(tmp_path):
    root = _root(tmp_path)
    engine = _engine(root)
    FakeRunner.version = "Claude Code current"
    receipt = engine.execute(_request(root))
    assert receipt.status is SpecialistExecutionStatus.FAILED
    assert "version could not be parsed" in receipt.output
    assert len(FakeRunner.calls) == 1


def test_timeout_maps_to_typed_terminal_receipt(tmp_path):
    root = _root(tmp_path)
    engine = _engine(root)
    FakeRunner.timeout_on_execution = True
    receipt = engine.execute(_request(root))
    assert receipt.status is SpecialistExecutionStatus.TIMED_OUT
    assert receipt.reason_code == "HOST_EXECUTION_TIMED_OUT"
    assert receipt.side_effect_class is SpecialistSideEffectClass.NONE


def test_nonzero_host_exit_fails_closed(tmp_path):
    root = _root(tmp_path)
    engine = _engine(root)
    FakeRunner.execution_returncode = 2
    FakeRunner.execution_stderr = "host failure"
    receipt = engine.execute(_request(root))
    assert receipt.status is SpecialistExecutionStatus.FAILED
    assert receipt.reason_code == "HOST_EXECUTION_FAILED"
    assert "host failure" in receipt.output


def test_missing_structured_output_fails_closed(tmp_path):
    root = _root(tmp_path)
    engine = _engine(root)
    FakeRunner.payload = {"type": "result", "subtype": "success"}
    receipt = engine.execute(_request(root))
    assert receipt.status is SpecialistExecutionStatus.FAILED
    assert "structured_output" in receipt.output


def test_non_mutating_affirmation_is_required(tmp_path):
    root = _root(tmp_path)
    engine = _engine(root)
    FakeRunner.payload["structured_output"] = {
        "summary": "Changed something.",
        "findings": [],
        "evidence": [],
        "non_mutating": False,
    }
    receipt = engine.execute(_request(root))
    assert receipt.status is SpecialistExecutionStatus.FAILED
    assert "non-mutating" in receipt.output


def test_unsuccessful_result_subtype_fails_closed(tmp_path):
    root = _root(tmp_path)
    engine = _engine(root)
    FakeRunner.payload["subtype"] = "error_max_turns"
    receipt = engine.execute(_request(root))
    assert receipt.status is SpecialistExecutionStatus.FAILED
    assert "error_max_turns" in receipt.output


def test_repository_state_drift_after_execution_fails_closed(tmp_path):
    root = _root(tmp_path)
    snapshots = iter((
        ("head", "tree", ""),
        ("head", "tree", "?? unexpected.txt"),
    ))
    engine = _engine(root, snapshot_factory=lambda _: next(snapshots))
    receipt = engine.execute(_request(root))
    assert receipt.status is SpecialistExecutionStatus.FAILED
    assert "changed repository state" in receipt.output
    assert receipt.side_effect_class is SpecialistSideEffectClass.NONE
