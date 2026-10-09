from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import time
from typing import Any, Callable

from internal.codex_app_server_bridge import (
    CodexAppServerError,
    CodexLauncher,
    _JsonlAppServer,
    _run_text,
    _sha256_file,
    discover_codex,
)
from orchestra_runtime.interfaces import ISpecialistExecutionEngine
from orchestra_runtime.specialist_execution import (
    SPECIALIST_EXECUTION_RECEIPT_VERSION,
    SpecialistExecutionMode,
    SpecialistExecutionReceipt,
    SpecialistExecutionRequest,
    SpecialistExecutionStatus,
    SpecialistSideEffectClass,
)


ENGINE_ID = "orchestra.codex-app-server-mutation-assessment"
ENGINE_VERSION = "1"
_APPROVAL_REQUESTS = {
    "item/commandExecution/requestApproval",
    "item/fileChange/requestApproval",
    "item/permissions/requestApproval",
    "mcpServer/elicitation/request",
}
_DENIED_ITEM_TYPES = {
    "commandExecution",
    "mcpToolCall",
    "dynamicToolCall",
    "collabToolCall",
    "webSearch",
}
_OUTPUT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "summary": {"type": "string"},
        "changed_paths": {"type": "array", "items": {"type": "string"}},
        "validation": {"type": "array", "items": {"type": "string"}},
        "mutation_completed": {"type": "boolean"},
    },
    "required": ["summary", "changed_paths", "validation", "mutation_completed"],
}
_REQUIRED_CONSTRAINTS = {
    ("AUTHORITY", "mutation"): ("EXACT", ("ALLOW",)),
    ("CAPABILITY", "network"): ("EXACT", ("DENY",)),
    ("CAPABILITY", "process_execution"): ("EXACT", ("DENY",)),
    ("CAPABILITY", "delegation"): ("EXACT", ("DENY",)),
}


class CodexMutationAssessmentError(CodexAppServerError):
    pass


class CodexMutationCancelled(CodexMutationAssessmentError):
    pass


@dataclass(frozen=True, slots=True)
class CodexMutationAssessmentConfig:
    model: str = "gpt-5.6-sol"
    reasoning_effort: str | None = None
    turn_timeout_seconds: int = 240
    approval_policy: str = "never"
    sandbox_mode: str = "workspace-write"
    network_access: bool = False
    writable_root: str = "mutation"
    allowed_relative_paths: tuple[str, ...] = ("mutation/target.md",)
    allowed_specialists: tuple[str, ...] = ("ponytail",)
    allowed_commands: tuple[str, ...] = ("ponytail",)

    def __post_init__(self) -> None:
        if self.approval_policy != "never":
            raise ValueError("mutation assessment requires approval_policy='never'")
        if self.sandbox_mode != "workspace-write":
            raise ValueError("mutation assessment requires sandbox_mode='workspace-write'")
        if self.network_access:
            raise ValueError("mutation assessment cannot enable network access")
        if self.turn_timeout_seconds < 10:
            raise ValueError("turn_timeout_seconds must be at least 10")
        if not self.model.strip():
            raise ValueError("model must be non-empty")
        if not self.allowed_specialists or not self.allowed_commands:
            raise ValueError("allowed specialist and command sets must be non-empty")

        writable_root = _normalize_relative(self.writable_root)
        allowed = tuple(sorted({_normalize_relative(item) for item in self.allowed_relative_paths}))
        if not allowed:
            raise ValueError("allowed_relative_paths must be non-empty")
        for item in allowed:
            if item == writable_root or not item.startswith(writable_root + "/"):
                raise ValueError("every allowed path must be beneath writable_root")
        object.__setattr__(self, "writable_root", writable_root)
        object.__setattr__(self, "allowed_relative_paths", allowed)


def _normalize_relative(value: str) -> str:
    text = str(value or "").replace("\\", "/").strip()
    path = PurePosixPath(text)
    if not text or text.startswith("/") or ":" in path.parts[0]:
        raise ValueError("path must be repository-relative")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("path contains an unsafe segment")
    return path.as_posix()


def _repo_snapshot(root: Path) -> tuple[str, str, str]:
    head = _run_text(["git", "-C", str(root), "rev-parse", "HEAD"])
    tree = _run_text(["git", "-C", str(root), "rev-parse", "HEAD^{tree}"])
    status = _run_text(["git", "-C", str(root), "status", "--porcelain=v1", "--untracked-files=all"])
    return head, tree, status


def _changed_paths(root: Path) -> tuple[str, ...]:
    modified = _run_text(["git", "-C", str(root), "diff", "--name-only", "--"])
    untracked = _run_text(
        ["git", "-C", str(root), "ls-files", "--others", "--exclude-standard"]
    )
    staged = _run_text(["git", "-C", str(root), "diff", "--cached", "--name-only", "--"])
    paths = {
        line.replace("\\", "/").strip()
        for block in (modified, untracked, staged)
        for line in block.splitlines()
        if line.strip()
    }
    return tuple(sorted(paths))


ClientFactory = Callable[[list[str], Path], Any]
LauncherFactory = Callable[[], CodexLauncher]
SnapshotFactory = Callable[[Path], tuple[str, str, str]]
ChangedPathsFactory = Callable[[Path], tuple[str, ...]]
CommandRunner = Callable[..., str]


class CodexAppServerMutationAssessmentEngine(ISpecialistExecutionEngine):
    """Experimental E6 host-mutation assessment engine.

    This engine is intentionally separate from the E5 read-only bridge. It is
    not a promoted runtime path and does not change default route-only behavior.
    """

    def __init__(
        self,
        repo_root: Path | str,
        *,
        config: CodexMutationAssessmentConfig | None = None,
        client_factory: ClientFactory = _JsonlAppServer,
        launcher_factory: LauncherFactory = discover_codex,
        snapshot_factory: SnapshotFactory = _repo_snapshot,
        changed_paths_factory: ChangedPathsFactory = _changed_paths,
        command_runner: CommandRunner = _run_text,
    ) -> None:
        self._root = Path(repo_root).resolve()
        self._config = config or CodexMutationAssessmentConfig()
        self._client_factory = client_factory
        self._launcher_factory = launcher_factory
        self._snapshot_factory = snapshot_factory
        self._changed_paths_factory = changed_paths_factory
        self._command_runner = command_runner
        self._last_request: SpecialistExecutionRequest | None = None
        self._last_receipt: SpecialistExecutionReceipt | None = None
        self._last_host_command: tuple[str, ...] = ()
        self._last_host_version: str | None = None

    @property
    def engine_id(self) -> str:
        return ENGINE_ID

    @property
    def engine_version(self) -> str:
        return ENGINE_VERSION

    @property
    def last_request(self) -> SpecialistExecutionRequest | None:
        return self._last_request

    @property
    def last_receipt(self) -> SpecialistExecutionReceipt | None:
        return self._last_receipt

    @property
    def last_host_command(self) -> tuple[str, ...]:
        return self._last_host_command

    @property
    def last_host_version(self) -> str | None:
        return self._last_host_version

    def _safe_changed_paths(self) -> tuple[str, ...]:
        try:
            return tuple(self._changed_paths_factory(self._root))
        except Exception:
            return ()

    def _receipt(
        self,
        request: SpecialistExecutionRequest,
        *,
        status: SpecialistExecutionStatus,
        reason_code: str,
        output: str,
        host_execution_id: str,
        changed_paths: tuple[str, ...] = (),
        evidence_refs: tuple[str, ...] = (),
        host_identity: str | None = None,
    ) -> SpecialistExecutionReceipt:
        return SpecialistExecutionReceipt(
            receipt_version=SPECIALIST_EXECUTION_RECEIPT_VERSION,
            receipt_id=f"codex-mutation-receipt.{request.request_digest[:24]}",
            request_id=request.request_id,
            request_digest=request.request_digest,
            run_id=request.run_id,
            adapter_name=request.adapter_name,
            command_name=request.command_name,
            specialist=request.specialist,
            engine_id=self.engine_id,
            engine_version=self.engine_version,
            host_execution_id=host_execution_id,
            status=status,
            reason_code=reason_code,
            output=output,
            evidence_refs=evidence_refs,
            side_effect_class=(
                SpecialistSideEffectClass.FILE_MUTATION
                if changed_paths
                else SpecialistSideEffectClass.NONE
            ),
            host_identity=host_identity,
            sandbox_identity=(
                f"workspace-write;network=false;writable-root={self._config.writable_root}"
            ),
            approval_policy_identity="never",
            changed_paths=changed_paths,
        )

    def execute(self, request: SpecialistExecutionRequest) -> SpecialistExecutionReceipt:
        self._last_request = request
        self._last_receipt = None
        self._last_host_command = ()
        self._last_host_version = None
        host_execution_id = f"codex-mutation.{request.request_digest[:16]}"
        try:
            receipt = self._execute(request, host_execution_id=host_execution_id)
        except TimeoutError:
            changed = self._safe_changed_paths()
            receipt = self._receipt(
                request,
                status=SpecialistExecutionStatus.TIMED_OUT,
                reason_code="HOST_MUTATION_TIMED_OUT",
                output="Codex mutation assessment timed out and was interrupted.",
                host_execution_id=host_execution_id,
                changed_paths=changed,
            )
        except CodexMutationCancelled as exc:
            changed = self._safe_changed_paths()
            receipt = self._receipt(
                request,
                status=SpecialistExecutionStatus.CANCELLED,
                reason_code="HOST_MUTATION_CANCELLED",
                output=str(exc),
                host_execution_id=host_execution_id,
                changed_paths=changed,
            )
        except CodexMutationAssessmentError as exc:
            changed = self._safe_changed_paths()
            receipt = self._receipt(
                request,
                status=SpecialistExecutionStatus.FAILED,
                reason_code="HOST_MUTATION_CONSTRAINT_FAILED",
                output=str(exc),
                host_execution_id=host_execution_id,
                changed_paths=changed,
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            changed = self._safe_changed_paths()
            receipt = self._receipt(
                request,
                status=SpecialistExecutionStatus.FAILED,
                reason_code="HOST_MUTATION_CONSTRAINT_UNENFORCEABLE",
                output=f"{type(exc).__name__}: {exc}",
                host_execution_id=host_execution_id,
                changed_paths=changed,
            )
        self._last_receipt = receipt
        return receipt

    def _require_request_constraints(self, request: SpecialistExecutionRequest) -> None:
        observed = {
            (item.source, item.key): (item.kind, item.values)
            for item in request.execution_constraints
        }
        for key, expected in _REQUIRED_CONSTRAINTS.items():
            if observed.get(key) != expected:
                raise CodexMutationAssessmentError(
                    f"required execution constraint missing or mismatched: {key[0]}:{key[1]}"
                )
        write_scope = observed.get(("CAPABILITY", "write_scope"))
        expected_paths = self._config.allowed_relative_paths
        if write_scope != ("ALLOWED_SET", expected_paths):
            raise CodexMutationAssessmentError(
                "CAPABILITY:write_scope must exactly match the configured allowed paths"
            )

    def _execute(
        self,
        request: SpecialistExecutionRequest,
        *,
        host_execution_id: str,
    ) -> SpecialistExecutionReceipt:
        if request.execution_mode is not SpecialistExecutionMode.HOST_NATIVE:
            raise CodexMutationAssessmentError("mutation assessment requires HOST_NATIVE mode")
        if request.specialist not in self._config.allowed_specialists:
            raise CodexMutationAssessmentError(
                f"specialist is not allowed by this assessment: {request.specialist}"
            )
        if request.command_name not in self._config.allowed_commands:
            raise CodexMutationAssessmentError(
                f"command is not allowed by this assessment: {request.command_name}"
            )
        if Path(request.project_root).resolve() != self._root:
            raise CodexMutationAssessmentError(
                "request project root does not match the assessment root"
            )
        self._require_request_constraints(request)

        skill_path = (self._root / request.skill_source_path).resolve()
        try:
            skill_path.relative_to(self._root)
        except ValueError as exc:
            raise CodexMutationAssessmentError(
                "specialist source escaped the assessment root"
            ) from exc
        if not skill_path.is_file():
            raise CodexMutationAssessmentError("specialist source file is unavailable")
        if _sha256_file(skill_path) != request.skill_source_digest:
            raise CodexMutationAssessmentError(
                "specialist source digest does not match the request"
            )
        skill_text = skill_path.read_text(encoding="utf-8")

        writable_root = (self._root / self._config.writable_root).resolve()
        try:
            writable_root.relative_to(self._root)
        except ValueError as exc:
            raise CodexMutationAssessmentError("writable root escaped assessment root") from exc
        if not writable_root.is_dir():
            raise CodexMutationAssessmentError("configured writable root is unavailable")

        for relative in self._config.allowed_relative_paths:
            target = (self._root / relative).resolve()
            try:
                target.relative_to(writable_root)
            except ValueError as exc:
                raise CodexMutationAssessmentError(
                    f"allowed path escaped writable root: {relative}"
                ) from exc
            if not target.is_file():
                raise CodexMutationAssessmentError(
                    f"allowed mutation target is unavailable: {relative}"
                )

        before = self._snapshot_factory(self._root)
        if before[2].strip():
            raise CodexMutationAssessmentError(
                "assessment worktree must be clean before host mutation"
            )

        launcher = self._launcher_factory()
        version = self._command_runner(
            [*launcher.command_prefix, "--version"],
            cwd=self._root,
            timeout=20,
        )
        self._last_host_version = version[:300]
        command = [
            *launcher.command_prefix,
            "-c",
            'mcp_servers.orchestra.enabled=false',
            "-c",
            'web_search="disabled"',
            "-c",
            'approval_policy="never"',
            "-c",
            'sandbox_mode="workspace-write"',
            "app-server",
            "--listen",
            "stdio://",
        ]
        self._last_host_command = tuple(command)
        client = self._client_factory(command, self._root)
        thread_id = ""
        turn_id = ""
        observed_file_paths: set[str] = set()
        try:
            client.start()
            client.request(
                "initialize",
                {
                    "clientInfo": {
                        "name": "orchestra_e6_mutation_assessment",
                        "title": "Orchestra E6 Mutation Assessment",
                        "version": ENGINE_VERSION,
                    }
                },
                timeout=20,
            )
            client.notify("initialized", {})
            thread = client.request(
                "thread/start",
                {
                    "model": self._config.model,
                    "cwd": str(self._root),
                    "approvalPolicy": "never",
                    "sandbox": "workspace-write",
                    "ephemeral": True,
                    "serviceName": "orchestra_e6_mutation_assessment",
                    "developerInstructions": self._developer_instructions(
                        request, skill_text
                    ),
                },
                timeout=30,
            )
            thread_obj = thread.get("thread")
            if not isinstance(thread_obj, dict) or not thread_obj.get("id"):
                raise CodexMutationAssessmentError(
                    "thread/start returned no thread id"
                )
            thread_id = str(thread_obj["id"])

            turn_params: dict[str, Any] = {
                "threadId": thread_id,
                "input": [{"type": "text", "text": request.task_input}],
                "cwd": str(self._root),
                "approvalPolicy": "never",
                "sandboxPolicy": {
                    "type": "workspaceWrite",
                    "writableRoots": [str(writable_root)],
                    "networkAccess": False,
                    "excludeTmpdirEnvVar": True,
                    "excludeSlashTmp": True,
                },
                "model": self._config.model,
                "outputSchema": _OUTPUT_SCHEMA,
            }
            if self._config.reasoning_effort:
                turn_params["effort"] = self._config.reasoning_effort
            turn = client.request("turn/start", turn_params, timeout=30)
            turn_obj = turn.get("turn")
            if not isinstance(turn_obj, dict) or not turn_obj.get("id"):
                raise CodexMutationAssessmentError(
                    "turn/start returned no turn id"
                )
            turn_id = str(turn_obj["id"])

            output, observed_file_paths = self._wait_for_turn(
                client,
                thread_id=thread_id,
                turn_id=turn_id,
            )
        finally:
            client.stop()

        after = self._snapshot_factory(self._root)
        if after[0] != before[0] or after[1] != before[1]:
            raise CodexMutationAssessmentError(
                "host mutation changed committed HEAD or tree identity"
            )
        changed_paths = tuple(self._changed_paths_factory(self._root))
        if not changed_paths:
            raise CodexMutationAssessmentError("no file mutation was observed")
        allowed = set(self._config.allowed_relative_paths)
        unexpected = sorted(set(changed_paths) - allowed)
        if unexpected:
            raise CodexMutationAssessmentError(
                f"out-of-scope repository changes observed: {unexpected}"
            )
        if observed_file_paths and not observed_file_paths.issubset(allowed):
            raise CodexMutationAssessmentError(
                "App Server reported an out-of-scope file change"
            )

        parsed = json.loads(output)
        if parsed.get("mutation_completed") is not True:
            raise CodexMutationAssessmentError(
                "host output did not affirm mutation completion"
            )
        reported = tuple(
            sorted(
                _normalize_relative(item)
                for item in parsed.get("changed_paths", [])
                if str(item).strip()
            )
        )
        if reported != changed_paths:
            raise CodexMutationAssessmentError(
                "host output changed_paths did not match Git evidence"
            )

        normalized = json.dumps(
            parsed,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
        host_execution_id = f"codex-mutation.{thread_id}.{turn_id}"
        return self._receipt(
            request,
            status=SpecialistExecutionStatus.COMPLETED,
            reason_code="CODEX_BOUNDED_FILE_MUTATION_COMPLETED",
            output=normalized,
            host_execution_id=host_execution_id,
            changed_paths=changed_paths,
            evidence_refs=(
                f"codex-model:{self._config.model}",
                "codex-sandbox:workspace-write",
                f"codex-writable-root:{self._config.writable_root}",
                "codex-network:false",
                "codex-approval:never",
                "codex-process-execution:denied",
                "codex-delegation:denied",
                f"specialist-source-sha256:{request.skill_source_digest}",
            ),
            host_identity=version[:300],
        )

    def _developer_instructions(
        self,
        request: SpecialistExecutionRequest,
        skill_text: str,
    ) -> str:
        allowed = ", ".join(self._config.allowed_relative_paths)
        return (
            "You are executing an explicitly bounded Orchestra E6 mutation assessment. "
            "The host does not grant authority. You may modify only the exact allowed "
            f"path(s): {allowed}. Do not create additional files. Do not use shell or "
            "process execution, network access, MCP tools, dynamic tools, delegation, "
            "subagents, or request broader permissions. Use only the host-native "
            "file-change/patch mechanism. Do not commit, stage, revert, reset, clean, "
            "delete branches, or alter Git metadata. "
            f"Command={request.command_name}; Specialist={request.specialist}; "
            f"Request={request.request_id}. Apply the trusted specialist guidance below.\n\n"
            "----- TRUSTED SPECIALIST GUIDANCE -----\n"
            f"{skill_text}\n"
            "----- END TRUSTED SPECIALIST GUIDANCE -----"
        )

    def _normalize_reported_path(self, value: str) -> str:
        text = str(value or "").strip()
        if not text:
            raise CodexMutationAssessmentError("host reported an empty file-change path")
        candidate = Path(text)
        if candidate.is_absolute():
            resolved = candidate.resolve()
            try:
                return resolved.relative_to(self._root).as_posix()
            except ValueError as exc:
                raise CodexMutationAssessmentError(
                    f"host reported file change outside assessment root: {text}"
                ) from exc
        return _normalize_relative(text)

    def _wait_for_turn(
        self,
        client: Any,
        *,
        thread_id: str,
        turn_id: str,
    ) -> tuple[str, set[str]]:
        deadline = time.monotonic() + self._config.turn_timeout_seconds
        agent_text: str | None = None
        observed_file_paths: set[str] = set()
        allowed = set(self._config.allowed_relative_paths)
        while time.monotonic() < deadline:
            message = client.next_message(timeout=0.5)
            if message is None:
                continue
            if message.get("_eof"):
                raise CodexMutationAssessmentError(
                    "Codex App Server closed before turn completion"
                )
            if message.get("_protocol_error"):
                raise CodexMutationAssessmentError(str(message["_protocol_error"]))

            method = message.get("method")
            params = (
                message.get("params")
                if isinstance(message.get("params"), dict)
                else {}
            )
            if method and isinstance(message.get("id"), int):
                if method in _APPROVAL_REQUESTS:
                    client.respond(int(message["id"]), {"decision": "cancel"})
                self._interrupt(client, thread_id=thread_id, turn_id=turn_id)
                raise CodexMutationAssessmentError(
                    f"host requested authority escalation: {method}"
                )

            if method in {"item/started", "item/completed"}:
                item = params.get("item")
                if isinstance(item, dict):
                    item_type = str(item.get("type") or "")
                    if item_type in _DENIED_ITEM_TYPES:
                        self._interrupt(client, thread_id=thread_id, turn_id=turn_id)
                        raise CodexMutationAssessmentError(
                            f"denied host activity observed: {item_type}"
                        )
                    if item_type == "fileChange":
                        changes = item.get("changes")
                        if isinstance(changes, list):
                            for change in changes:
                                if not isinstance(change, dict):
                                    continue
                                relative = self._normalize_reported_path(
                                    str(change.get("path") or "")
                                )
                                observed_file_paths.add(relative)
                                if relative not in allowed:
                                    self._interrupt(
                                        client,
                                        thread_id=thread_id,
                                        turn_id=turn_id,
                                    )
                                    raise CodexMutationAssessmentError(
                                        f"out-of-scope file change requested: {relative}"
                                    )
                    if method == "item/completed" and item_type == "agentMessage":
                        text = item.get("text")
                        if isinstance(text, str):
                            agent_text = text

            if method == "turn/completed":
                completed = params.get("turn")
                if not isinstance(completed, dict):
                    raise CodexMutationAssessmentError(
                        "turn/completed payload was malformed"
                    )
                status = str(completed.get("status") or "")
                if status == "completed":
                    if agent_text is None:
                        raise CodexMutationAssessmentError(
                            "completed turn returned no final agent message"
                        )
                    return agent_text, observed_file_paths
                if status == "interrupted":
                    raise CodexMutationCancelled(
                        "Codex host mutation was interrupted; sandbox is preserved"
                    )
                raise CodexMutationAssessmentError(
                    f"Codex host mutation ended with status: {status or 'unknown'}"
                )

        self._interrupt(client, thread_id=thread_id, turn_id=turn_id)
        raise TimeoutError("Codex mutation assessment exceeded the configured timeout")

    @staticmethod
    def _interrupt(client: Any, *, thread_id: str, turn_id: str) -> None:
        try:
            client.request(
                "turn/interrupt",
                {"threadId": thread_id, "turnId": turn_id},
                timeout=10,
            )
        except Exception:
            pass
