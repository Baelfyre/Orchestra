from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import pytest

from internal import codex_app_server_bridge as bridge
from orchestra_runtime.specialist_execution import (
    SpecialistExecutionMode,
    SpecialistExecutionRequest,
    SpecialistExecutionStatus,
    SpecialistSideEffectClass,
)


class FakeClient:
    instances: list["FakeClient"] = []
    messages: list[dict[str, object]] = []

    def __init__(self, command: list[str], cwd: Path) -> None:
        self.command = list(command)
        self.cwd = cwd
        self.requests: list[tuple[str, dict[str, object]]] = []
        self.notifications: list[tuple[str, dict[str, object]]] = []
        self.responses: list[tuple[int, dict[str, object]]] = []
        self.interrupted = False
        self._messages = list(type(self).messages)
        type(self).instances.append(self)

    def start(self) -> None:
        pass

    def request(self, method: str, params: dict[str, object], *, timeout: int):
        self.requests.append((method, params))
        if method == "initialize":
            return {"userAgent": "fake-codex"}
        if method == "thread/start":
            return {"thread": {"id": "thread-1"}}
        if method == "turn/start":
            return {"turn": {"id": "turn-1"}}
        if method == "turn/interrupt":
            self.interrupted = True
            return {}
        raise AssertionError(f"unexpected method: {method}")

    def notify(self, method: str, params: dict[str, object]) -> None:
        self.notifications.append((method, params))

    def respond(self, request_id: int, result: dict[str, object]) -> None:
        self.responses.append((request_id, result))

    def next_message(self, *, timeout: float):
        if self._messages:
            return self._messages.pop(0)
        return None

    def stop(self) -> None:
        pass


def _root(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    skill = root / "skills" / "scribe" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("# Scribe\nTrusted scribe fixture guidance.\n", encoding="utf-8")
    return root


def _request(root: Path, *, mode=SpecialistExecutionMode.HOST_NATIVE, command="review-docs", specialist="scribe"):
    skill = root / "skills" / "scribe" / "SKILL.md"
    digest = sha256(skill.read_bytes()).hexdigest()
    return SpecialistExecutionRequest.create(
        run_id="run-e5",
        parent_run_id=None,
        correlation_id="corr-e5",
        adapter_name="codex",
        command_name=command,
        specialist=specialist,
        project_root=str(root),
        skill_source_path="skills/scribe/SKILL.md",
        skill_source_digest=digest,
        task_input="Review the fixture documentation.",
        authority_decision_ref="authority-e5",
        capability_decision_ref="capability-e5",
        governance_status="NOT_REQUIRED",
        evaluated_governance_rules=(),
        execution_constraints=(),
        execution_mode=mode,
    )


def _launcher():
    return bridge.CodexLauncher(
        executable="codex",
        executable_sha256=None,
        command_prefix=("codex",),
        resolution="TEST",
    )


def _runner(*args, **kwargs):
    return "codex-cli 0.test"


def _clean_snapshot(root: Path):
    return ("head", "tree", "")


def _engine(root: Path, **kwargs):
    FakeClient.instances.clear()
    return bridge.CodexAppServerExecutionEngine(
        root,
        client_factory=FakeClient,
        launcher_factory=_launcher,
        snapshot_factory=kwargs.pop("snapshot_factory", _clean_snapshot),
        command_runner=_runner,
        config=kwargs.pop("config", bridge.CodexAppServerConfig()),
        **kwargs,
    )


def _completed_messages(output: dict[str, object] | None = None):
    payload = output or {
        "summary": "Revision mismatch found.",
        "findings": ["REVISION_DECLARED=3 differs from REVISION_FOOTER=4."],
        "evidence": ["CHECKSUM=ALDER-47"],
        "non_mutating": True,
    }
    return [
        {"method": "item/started", "params": {"item": {"type": "commandExecution"}}},
        {"method": "item/completed", "params": {"item": {"type": "commandExecution"}}},
        {
            "method": "item/completed",
            "params": {
                "item": {
                    "type": "agentMessage",
                    "text": json.dumps(payload, sort_keys=True),
                }
            },
        },
        {"method": "turn/completed", "params": {"turn": {"status": "completed"}}},
    ]


def test_config_fails_closed_on_policy_widening():
    with pytest.raises(ValueError):
        bridge.CodexAppServerConfig(approval_policy="on-request")
    with pytest.raises(ValueError):
        bridge.CodexAppServerConfig(sandbox_mode="workspace-write")
    with pytest.raises(ValueError):
        bridge.CodexAppServerConfig(network_access=True)
    with pytest.raises(ValueError):
        bridge.CodexAppServerConfig(turn_timeout_seconds=9)
    with pytest.raises(ValueError):
        bridge.CodexAppServerConfig(model=" ")
    with pytest.raises(ValueError):
        bridge.CodexAppServerConfig(allowed_commands=())


def test_completed_read_only_receipt_binds_host_and_specialist(tmp_path):
    root = _root(tmp_path)
    FakeClient.messages = _completed_messages()
    engine = _engine(root)
    request = _request(root)

    receipt = engine.execute(request)

    assert receipt.status is SpecialistExecutionStatus.COMPLETED
    assert receipt.side_effect_class is SpecialistSideEffectClass.READ_ONLY
    assert receipt.reason_code == "CODEX_READ_ONLY_SPECIALIST_COMPLETED"
    assert receipt.request_id == request.request_id
    assert receipt.request_digest == request.request_digest
    assert receipt.specialist == "scribe"
    assert receipt.command_name == "review-docs"
    assert receipt.engine_id == bridge.ENGINE_ID
    assert receipt.engine_version == bridge.ENGINE_VERSION
    assert receipt.changed_paths == ()
    assert receipt.host_identity == "codex-cli 0.test"
    assert "codex-model:gpt-5.6-sol" in receipt.evidence_refs
    assert f"specialist-source-sha256:{request.skill_source_digest}" in receipt.evidence_refs
    receipt.assert_matches(request, engine_id=engine.engine_id, engine_version=engine.engine_version)

    assert engine.last_request is request
    assert engine.last_receipt is receipt
    assert engine.last_host_version == "codex-cli 0.test"
    assert 'mcp_servers.orchestra.enabled=false' in engine.last_host_command
    assert 'web_search="disabled"' in engine.last_host_command
    assert 'sandbox_mode="read-only"' in engine.last_host_command

    client = FakeClient.instances[-1]
    thread_params = dict(client.requests[1][1])
    assert thread_params["approvalPolicy"] == "never"
    assert thread_params["sandbox"] == "read-only"
    assert thread_params["ephemeral"] is True
    assert request.request_id in str(thread_params["developerInstructions"])
    assert "Trusted scribe fixture guidance" in str(thread_params["developerInstructions"])

    turn_params = dict(client.requests[2][1])
    assert turn_params["sandboxPolicy"] == {"type": "readOnly", "networkAccess": False}
    assert turn_params["approvalPolicy"] == "never"
    assert turn_params["input"] == [{"type": "text", "text": request.task_input}]


def test_reasoning_effort_is_forwarded_only_when_configured(tmp_path):
    root = _root(tmp_path)
    FakeClient.messages = _completed_messages()
    engine = _engine(root, config=bridge.CodexAppServerConfig(reasoning_effort="high"))
    receipt = engine.execute(_request(root))
    assert receipt.status is SpecialistExecutionStatus.COMPLETED
    client = FakeClient.instances[-1]
    assert client.requests[2][1]["effort"] == "high"


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
    FakeClient.messages = _completed_messages()
    engine = _engine(root)
    receipt = engine.execute(_request(root, **request_kwargs))
    assert receipt.status is SpecialistExecutionStatus.FAILED
    assert receipt.reason_code == "HOST_EXECUTION_FAILED"
    assert message in receipt.output
    assert FakeClient.instances == []


def test_project_root_mismatch_fails_closed(tmp_path):
    root = _root(tmp_path)
    other = tmp_path / "other"
    other.mkdir()
    request = _request(root)
    object.__setattr__(request, "project_root", str(other))
    engine = _engine(root)
    receipt = engine.execute(request)
    assert receipt.status is SpecialistExecutionStatus.FAILED
    assert "project root" in receipt.output


def test_missing_or_mismatched_skill_source_fails_closed(tmp_path):
    root = _root(tmp_path)
    request = _request(root)
    (root / "skills" / "scribe" / "SKILL.md").write_text("changed", encoding="utf-8")
    engine = _engine(root)
    receipt = engine.execute(request)
    assert receipt.status is SpecialistExecutionStatus.FAILED
    assert "digest" in receipt.output

    (root / "skills" / "scribe" / "SKILL.md").unlink()
    receipt = engine.execute(request)
    assert receipt.status is SpecialistExecutionStatus.FAILED
    assert "unavailable" in receipt.output


def test_dirty_worktree_is_rejected_before_host_start(tmp_path):
    root = _root(tmp_path)
    engine = _engine(root, snapshot_factory=lambda root: ("head", "tree", " M README.md"))
    receipt = engine.execute(_request(root))
    assert receipt.status is SpecialistExecutionStatus.FAILED
    assert "clean" in receipt.output
    assert FakeClient.instances == []


def test_read_only_execution_detects_repository_state_change(tmp_path):
    root = _root(tmp_path)
    states = iter([("head", "tree", ""), ("head", "tree2", "")])
    FakeClient.messages = _completed_messages()
    engine = _engine(root, snapshot_factory=lambda root: next(states))
    receipt = engine.execute(_request(root))
    assert receipt.status is SpecialistExecutionStatus.FAILED
    assert "changed repository state" in receipt.output


@pytest.mark.parametrize("item_type", ["fileChange", "mcpToolCall", "dynamicToolCall", "collabToolCall", "webSearch"])
def test_denied_host_activity_interrupts_and_fails_closed(tmp_path, item_type):
    root = _root(tmp_path)
    FakeClient.messages = [
        {"method": "item/started", "params": {"item": {"type": item_type}}},
    ]
    engine = _engine(root)
    receipt = engine.execute(_request(root))
    assert receipt.status is SpecialistExecutionStatus.FAILED
    assert item_type in receipt.output
    assert FakeClient.instances[-1].interrupted is True


def test_server_approval_request_is_cancelled_and_fails_closed(tmp_path):
    root = _root(tmp_path)
    FakeClient.messages = [
        {
            "jsonrpc": "2.0",
            "id": 91,
            "method": "item/commandExecution/requestApproval",
            "params": {},
        }
    ]
    engine = _engine(root)
    receipt = engine.execute(_request(root))
    client = FakeClient.instances[-1]
    assert receipt.status is SpecialistExecutionStatus.FAILED
    assert client.responses == [(91, {"decision": "cancel"})]
    assert client.interrupted is True


def test_nonempty_diff_interrupts_and_fails_closed(tmp_path):
    root = _root(tmp_path)
    FakeClient.messages = [
        {"method": "turn/diff/updated", "params": {"diff": "+mutated"}},
    ]
    engine = _engine(root)
    receipt = engine.execute(_request(root))
    assert receipt.status is SpecialistExecutionStatus.FAILED
    assert "non-empty diff" in receipt.output
    assert FakeClient.instances[-1].interrupted is True


@pytest.mark.parametrize(
    "messages",
    [
        [{"_eof": True}],
        [{"_protocol_error": "bad-jsonl"}],
        [{"method": "turn/completed", "params": {"turn": "bad"}}],
        [{"method": "turn/completed", "params": {"turn": {"status": "failed"}}}],
        [{"method": "turn/completed", "params": {"turn": {"status": "completed"}}}],
    ],
)
def test_terminal_protocol_failures_are_not_success(tmp_path, messages):
    root = _root(tmp_path)
    FakeClient.messages = messages
    engine = _engine(root)
    receipt = engine.execute(_request(root))
    assert receipt.status is SpecialistExecutionStatus.FAILED


def test_timeout_maps_to_timed_out_receipt_and_interrupt(tmp_path, monkeypatch):
    root = _root(tmp_path)
    FakeClient.messages = []
    values = iter([0.0, 11.0])
    monkeypatch.setattr(bridge.time, "monotonic", lambda: next(values))
    engine = _engine(root, config=bridge.CodexAppServerConfig(turn_timeout_seconds=10))
    receipt = engine.execute(_request(root))
    assert receipt.status is SpecialistExecutionStatus.TIMED_OUT
    assert receipt.reason_code == "HOST_EXECUTION_TIMED_OUT"
    assert FakeClient.instances[-1].interrupted is True


def test_non_mutating_output_flag_is_required(tmp_path):
    root = _root(tmp_path)
    FakeClient.messages = _completed_messages(
        {
            "summary": "analysis",
            "findings": [],
            "evidence": [],
            "non_mutating": False,
        }
    )
    engine = _engine(root)
    receipt = engine.execute(_request(root))
    assert receipt.status is SpecialistExecutionStatus.FAILED
    assert "non-mutating" in receipt.output


def test_malformed_json_output_fails_closed(tmp_path):
    root = _root(tmp_path)
    FakeClient.messages = [
        {
            "method": "item/completed",
            "params": {"item": {"type": "agentMessage", "text": "not-json"}},
        },
        {"method": "turn/completed", "params": {"turn": {"status": "completed"}}},
    ]
    engine = _engine(root)
    receipt = engine.execute(_request(root))
    assert receipt.status is SpecialistExecutionStatus.FAILED
    assert receipt.reason_code == "HOST_CONSTRAINT_UNENFORCEABLE"
