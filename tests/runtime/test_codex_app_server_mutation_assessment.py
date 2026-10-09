from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import pytest

from internal import codex_app_server_mutation_assessment as mutation
from internal.codex_app_server_bridge import CodexLauncher
from orchestra_runtime.specialist_execution import (
    SpecialistExecutionConstraint,
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
        self.responses: list[tuple[int, dict[str, object]]] = []
        self._messages = list(type(self).messages)
        self.interrupted = False
        type(self).instances.append(self)

    def start(self) -> None:
        pass

    def request(self, method: str, params: dict[str, object], *, timeout: int):
        self.requests.append((method, params))
        if method == "initialize":
            return {"userAgent": "fake-codex"}
        if method == "thread/start":
            return {"thread": {"id": "thread-e6"}}
        if method == "turn/start":
            return {"turn": {"id": "turn-e6"}}
        if method == "turn/interrupt":
            self.interrupted = True
            return {}
        raise AssertionError(f"unexpected method: {method}")

    def notify(self, method: str, params: dict[str, object]) -> None:
        pass

    def respond(self, request_id: int, result: dict[str, object]) -> None:
        self.responses.append((request_id, result))

    def next_message(self, *, timeout: float):
        if self._messages:
            return self._messages.pop(0)
        return None

    def stop(self) -> None:
        pass


def _root(tmp_path: Path) -> Path:
    root = tmp_path / "fixture"
    skill = root / "skills" / "ponytail" / "SKILL.md"
    target = root / "mutation" / "target.md"
    protected = root / "protected" / "DO_NOT_TOUCH.md"
    skill.parent.mkdir(parents=True)
    target.parent.mkdir(parents=True)
    protected.parent.mkdir(parents=True)
    skill.write_text("# Ponytail\nTrusted implementation guidance.\n", encoding="utf-8")
    target.write_text("STATUS=BEFORE\n", encoding="utf-8")
    protected.write_text("MUST_REMAIN=UNCHANGED\n", encoding="utf-8")
    return root


def _constraints(write_scope: tuple[str, ...] = ("mutation/target.md",)):
    return (
        SpecialistExecutionConstraint(
            "AUTHORITY", "mutation", "EXACT", ("ALLOW",)
        ),
        SpecialistExecutionConstraint(
            "CAPABILITY", "write_scope", "ALLOWED_SET", write_scope
        ),
        SpecialistExecutionConstraint(
            "CAPABILITY", "network", "EXACT", ("DENY",)
        ),
        SpecialistExecutionConstraint(
            "CAPABILITY", "process_execution", "EXACT", ("DENY",)
        ),
        SpecialistExecutionConstraint(
            "CAPABILITY", "delegation", "EXACT", ("DENY",)
        ),
    )


def _request(
    root: Path,
    *,
    constraints=None,
    mode=SpecialistExecutionMode.HOST_NATIVE,
    specialist="ponytail",
    command="ponytail",
):
    skill = root / "skills" / "ponytail" / "SKILL.md"
    return SpecialistExecutionRequest.create(
        run_id="run-e6",
        parent_run_id=None,
        correlation_id="corr-e6",
        adapter_name="codex",
        command_name=command,
        specialist=specialist,
        project_root=str(root),
        skill_source_path="skills/ponytail/SKILL.md",
        skill_source_digest=sha256(skill.read_bytes()).hexdigest(),
        task_input="Modify only mutation/target.md.",
        authority_decision_ref="authority-e6",
        capability_decision_ref="capability-e6",
        governance_status="AUTHORIZED_BOUNDED_ASSESSMENT",
        evaluated_governance_rules=("e6",),
        execution_constraints=(
            _constraints() if constraints is None else constraints
        ),
        execution_mode=mode,
    )


def _launcher():
    return CodexLauncher(
        executable="codex",
        executable_sha256=None,
        command_prefix=("codex",),
        resolution="TEST",
    )


def _runner(*args, **kwargs):
    return "codex-cli 0.test"


def _engine(root: Path, snapshots=None, changed_paths=("mutation/target.md",), **kwargs):
    FakeClient.instances.clear()
    snapshot_values = iter(
        snapshots
        or [
            ("head", "tree", ""),
            ("head", "tree", " M mutation/target.md"),
        ]
    )
    return mutation.CodexAppServerMutationAssessmentEngine(
        root,
        client_factory=FakeClient,
        launcher_factory=_launcher,
        snapshot_factory=lambda root: next(snapshot_values),
        changed_paths_factory=lambda root: tuple(changed_paths),
        command_runner=_runner,
        config=kwargs.pop(
            "config", mutation.CodexMutationAssessmentConfig()
        ),
        **kwargs,
    )


def _completed_messages(path="mutation/target.md"):
    output = {
        "summary": "Updated the isolated fixture.",
        "changed_paths": [path],
        "validation": ["STATUS=AFTER"],
        "mutation_completed": True,
    }
    return [
        {
            "method": "item/started",
            "params": {
                "item": {
                    "type": "fileChange",
                    "changes": [
                        {"path": path, "kind": "update", "diff": "+STATUS=AFTER"}
                    ],
                }
            },
        },
        {
            "method": "item/completed",
            "params": {
                "item": {
                    "type": "fileChange",
                    "changes": [
                        {"path": path, "kind": "update", "diff": "+STATUS=AFTER"}
                    ],
                }
            },
        },
        {
            "method": "item/completed",
            "params": {
                "item": {
                    "type": "agentMessage",
                    "text": json.dumps(output, sort_keys=True),
                }
            },
        },
        {
            "method": "turn/completed",
            "params": {"turn": {"status": "completed"}},
        },
    ]


def test_config_fails_closed_on_policy_widening_and_path_escape():
    with pytest.raises(ValueError):
        mutation.CodexMutationAssessmentConfig(
            approval_policy="on-request"
        )
    with pytest.raises(ValueError):
        mutation.CodexMutationAssessmentConfig(sandbox_mode="read-only")
    with pytest.raises(ValueError):
        mutation.CodexMutationAssessmentConfig(network_access=True)
    with pytest.raises(ValueError):
        mutation.CodexMutationAssessmentConfig(
            allowed_relative_paths=("../escape.md",)
        )
    with pytest.raises(ValueError):
        mutation.CodexMutationAssessmentConfig(
            writable_root="mutation",
            allowed_relative_paths=("protected/file.md",),
        )


def test_completed_mutation_receipt_binds_scope_and_host(tmp_path):
    root = _root(tmp_path)
    FakeClient.messages = _completed_messages()
    engine = _engine(root)
    request = _request(root)

    receipt = engine.execute(request)

    assert receipt.status is SpecialistExecutionStatus.COMPLETED
    assert receipt.reason_code == "CODEX_BOUNDED_FILE_MUTATION_COMPLETED"
    assert receipt.side_effect_class is SpecialistSideEffectClass.FILE_MUTATION
    assert receipt.changed_paths == ("mutation/target.md",)
    assert receipt.host_identity == "codex-cli 0.test"
    assert receipt.sandbox_identity == (
        "workspace-write;network=false;writable-root=mutation"
    )
    assert receipt.approval_policy_identity == "never"
    receipt.assert_matches(
        request,
        engine_id=engine.engine_id,
        engine_version=engine.engine_version,
    )

    assert 'mcp_servers.orchestra.enabled=false' in engine.last_host_command
    assert 'web_search="disabled"' in engine.last_host_command
    assert 'sandbox_mode="workspace-write"' in engine.last_host_command

    client = FakeClient.instances[-1]
    thread_params = client.requests[1][1]
    assert thread_params["sandbox"] == "workspace-write"
    assert thread_params["approvalPolicy"] == "never"

    turn_params = client.requests[2][1]
    sandbox = turn_params["sandboxPolicy"]
    assert sandbox["type"] == "workspaceWrite"
    assert sandbox["networkAccess"] is False
    assert sandbox["excludeTmpdirEnvVar"] is True
    assert sandbox["excludeSlashTmp"] is True
    assert sandbox["writableRoots"] == [str((root / "mutation").resolve())]


@pytest.mark.parametrize(
    "item_type",
    [
        "commandExecution",
        "mcpToolCall",
        "dynamicToolCall",
        "collabToolCall",
        "webSearch",
    ],
)
def test_denied_activity_interrupts_and_fails_closed(tmp_path, item_type):
    root = _root(tmp_path)
    FakeClient.messages = [
        {
            "method": "item/started",
            "params": {"item": {"type": item_type}},
        }
    ]
    engine = _engine(
        root,
        snapshots=[("head", "tree", "")],
        changed_paths=(),
    )
    receipt = engine.execute(_request(root))
    assert receipt.status is SpecialistExecutionStatus.FAILED
    assert item_type in receipt.output
    assert FakeClient.instances[-1].interrupted is True


def test_out_of_scope_file_change_interrupts_before_success(tmp_path):
    root = _root(tmp_path)
    FakeClient.messages = _completed_messages("protected/DO_NOT_TOUCH.md")
    engine = _engine(
        root,
        snapshots=[("head", "tree", "")],
        changed_paths=(),
    )
    receipt = engine.execute(_request(root))
    assert receipt.status is SpecialistExecutionStatus.FAILED
    assert "out-of-scope" in receipt.output
    assert FakeClient.instances[-1].interrupted is True


def test_request_requires_explicit_authority_and_capability_constraints(tmp_path):
    root = _root(tmp_path)
    FakeClient.messages = _completed_messages()
    engine = _engine(
        root,
        snapshots=[("head", "tree", "")],
        changed_paths=(),
    )
    receipt = engine.execute(_request(root, constraints=()))
    assert receipt.status is SpecialistExecutionStatus.FAILED
    assert "required execution constraint" in receipt.output
    assert FakeClient.instances == []

    bad_scope = tuple(
        item
        for item in _constraints(("mutation/target.md", "mutation/extra.md"))
    )
    receipt = engine.execute(_request(root, constraints=bad_scope))
    assert receipt.status is SpecialistExecutionStatus.FAILED
    assert "write_scope" in receipt.output


def test_dirty_workspace_is_rejected_before_host_start(tmp_path):
    root = _root(tmp_path)
    engine = _engine(
        root,
        snapshots=[("head", "tree", " M mutation/target.md")],
        changed_paths=("mutation/target.md",),
    )
    receipt = engine.execute(_request(root))
    assert receipt.status is SpecialistExecutionStatus.FAILED
    assert "clean before host mutation" in receipt.output
    assert receipt.changed_paths == ("mutation/target.md",)
    assert FakeClient.instances == []


def test_post_execution_scope_drift_fails_closed_and_is_reported(tmp_path):
    root = _root(tmp_path)
    FakeClient.messages = _completed_messages()
    engine = _engine(
        root,
        changed_paths=("mutation/target.md", "mutation/extra.md"),
    )
    receipt = engine.execute(_request(root))
    assert receipt.status is SpecialistExecutionStatus.FAILED
    assert "out-of-scope repository changes" in receipt.output
    assert receipt.side_effect_class is SpecialistSideEffectClass.FILE_MUTATION
    assert receipt.changed_paths == (
        "mutation/extra.md",
        "mutation/target.md",
    )


def test_head_or_tree_mutation_fails_closed(tmp_path):
    root = _root(tmp_path)
    FakeClient.messages = _completed_messages()
    engine = _engine(
        root,
        snapshots=[
            ("head", "tree", ""),
            ("head2", "tree2", " M mutation/target.md"),
        ],
    )
    receipt = engine.execute(_request(root))
    assert receipt.status is SpecialistExecutionStatus.FAILED
    assert "committed HEAD or tree identity" in receipt.output


def test_approval_escalation_is_cancelled_and_fails_closed(tmp_path):
    root = _root(tmp_path)
    FakeClient.messages = [
        {
            "jsonrpc": "2.0",
            "id": 41,
            "method": "item/fileChange/requestApproval",
            "params": {},
        }
    ]
    engine = _engine(
        root,
        snapshots=[("head", "tree", "")],
        changed_paths=(),
    )
    receipt = engine.execute(_request(root))
    client = FakeClient.instances[-1]
    assert receipt.status is SpecialistExecutionStatus.FAILED
    assert client.responses == [(41, {"decision": "cancel"})]
    assert client.interrupted is True


def test_interrupted_turn_maps_to_cancelled_and_preserves_partial_mutation(tmp_path):
    root = _root(tmp_path)
    FakeClient.messages = [
        {
            "method": "turn/completed",
            "params": {"turn": {"status": "interrupted"}},
        }
    ]
    engine = _engine(
        root,
        snapshots=[("head", "tree", "")],
        changed_paths=("mutation/target.md",),
    )
    receipt = engine.execute(_request(root))
    assert receipt.status is SpecialistExecutionStatus.CANCELLED
    assert receipt.reason_code == "HOST_MUTATION_CANCELLED"
    assert receipt.side_effect_class is SpecialistSideEffectClass.FILE_MUTATION
    assert receipt.changed_paths == ("mutation/target.md",)


def test_timeout_maps_to_timed_out_and_preserves_partial_mutation(
    tmp_path, monkeypatch
):
    root = _root(tmp_path)
    FakeClient.messages = []
    values = iter([0.0, 11.0])
    monkeypatch.setattr(mutation.time, "monotonic", lambda: next(values))
    engine = _engine(
        root,
        snapshots=[("head", "tree", "")],
        changed_paths=("mutation/target.md",),
        config=mutation.CodexMutationAssessmentConfig(
            turn_timeout_seconds=10
        ),
    )
    receipt = engine.execute(_request(root))
    assert receipt.status is SpecialistExecutionStatus.TIMED_OUT
    assert receipt.side_effect_class is SpecialistSideEffectClass.FILE_MUTATION
    assert receipt.changed_paths == ("mutation/target.md",)
    assert FakeClient.instances[-1].interrupted is True


@pytest.mark.parametrize(
    "request_kwargs",
    [
        {"mode": SpecialistExecutionMode.DETERMINISTIC_TEST_ENGINE},
        {"specialist": "scribe"},
        {"command": "review-docs"},
    ],
)
def test_wrong_execution_identity_fails_before_host(tmp_path, request_kwargs):
    root = _root(tmp_path)
    engine = _engine(
        root,
        snapshots=[("head", "tree", "")],
        changed_paths=(),
    )
    receipt = engine.execute(_request(root, **request_kwargs))
    assert receipt.status is SpecialistExecutionStatus.FAILED
    assert FakeClient.instances == []
