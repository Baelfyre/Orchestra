from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import threading
import time
from typing import Any, Callable

from orchestra_runtime.interfaces import ISpecialistExecutionEngine
from orchestra_runtime.specialist_execution import (
    SPECIALIST_EXECUTION_RECEIPT_VERSION,
    SpecialistExecutionMode,
    SpecialistExecutionReceipt,
    SpecialistExecutionRequest,
    SpecialistExecutionStatus,
    SpecialistSideEffectClass,
)


ENGINE_ID = "orchestra.codex-app-server"
ENGINE_VERSION = "1"
_DENIED_ITEM_TYPES = {
    "fileChange",
    "mcpToolCall",
    "dynamicToolCall",
    "collabToolCall",
    "webSearch",
}
_APPROVAL_REQUESTS = {
    "item/commandExecution/requestApproval",
    "item/fileChange/requestApproval",
    "item/permissions/requestApproval",
    "mcpServer/elicitation/request",
}
_OUTPUT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "summary": {"type": "string"},
        "findings": {"type": "array", "items": {"type": "string"}},
        "evidence": {"type": "array", "items": {"type": "string"}},
        "non_mutating": {"type": "boolean"},
    },
    "required": ["summary", "findings", "evidence", "non_mutating"],
}


class CodexAppServerError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class CodexLauncher:
    executable: str
    executable_sha256: str | None
    command_prefix: tuple[str, ...]
    resolution: str


@dataclass(frozen=True, slots=True)
class CodexAppServerConfig:
    model: str = "gpt-5.6-sol"
    reasoning_effort: str | None = None
    turn_timeout_seconds: int = 180
    require_clean_worktree: bool = True
    approval_policy: str = "never"
    sandbox_mode: str = "read-only"
    network_access: bool = False
    allowed_specialists: tuple[str, ...] = ("scribe",)
    allowed_commands: tuple[str, ...] = ("review-docs",)

    def __post_init__(self) -> None:
        if self.approval_policy != "never":
            raise ValueError("Codex specialist execution requires approval_policy='never'")
        if self.sandbox_mode != "read-only":
            raise ValueError("Codex specialist execution requires sandbox_mode='read-only'")
        if self.network_access:
            raise ValueError("Codex read-only specialist execution cannot enable network access")
        if self.turn_timeout_seconds < 10:
            raise ValueError("turn_timeout_seconds must be at least 10")
        if not self.model.strip():
            raise ValueError("model must be non-empty")
        if not self.allowed_specialists or not self.allowed_commands:
            raise ValueError("allowed specialist and command sets must be non-empty")


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run_text(args: list[str], *, cwd: Path | None = None, timeout: int = 30) -> str:
    completed = subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False,
        check=False,
        timeout=timeout,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()[-1200:]
        raise CodexAppServerError(f"command failed ({completed.returncode}): {detail}")
    return (completed.stdout or "").strip()


def _repo_snapshot(root: Path) -> tuple[str, str, str]:
    head = _run_text(["git", "-C", str(root), "rev-parse", "HEAD"])
    tree = _run_text(["git", "-C", str(root), "rev-parse", "HEAD^{tree}"])
    status = _run_text(["git", "-C", str(root), "status", "--porcelain=v1", "--untracked-files=all"])
    return head, tree, status


def discover_codex() -> CodexLauncher:
    candidates: list[Path] = []
    if os.name == "nt":
        try:
            output = _run_text(["where.exe", "codex"], timeout=10)
            candidates.extend(Path(line.strip()) for line in output.splitlines() if line.strip())
        except Exception:
            pass
        for name in ("codex.exe", "codex.cmd", "codex.bat", "codex.ps1"):
            value = shutil.which(name)
            if value:
                candidates.append(Path(value))
    else:
        value = shutil.which("codex")
        if value:
            candidates.append(Path(value))

    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate).casefold()
        if key not in seen and candidate.exists():
            seen.add(key)
            unique.append(candidate)
    if not unique:
        raise CodexAppServerError("Codex CLI was not found in PATH")

    preferred = next(
        (item for item in unique if item.suffix.casefold() in {".exe", ".cmd", ".bat"}),
        unique[0],
    )
    suffix = preferred.suffix.casefold()
    if os.name == "nt" and suffix in {".cmd", ".bat"}:
        comspec = os.environ.get("COMSPEC", r"C:\Windows\System32\cmd.exe")
        prefix = (comspec, "/d", "/s", "/c", str(preferred))
        resolution = "WINDOWS_CMD_WRAPPER"
    elif os.name == "nt" and suffix == ".ps1":
        powershell = shutil.which("powershell.exe") or shutil.which("pwsh.exe")
        if not powershell:
            raise CodexAppServerError("PowerShell is required for the Codex .ps1 launcher")
        prefix = (
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(preferred),
        )
        resolution = "POWERSHELL_WRAPPER"
    else:
        prefix = (str(preferred),)
        resolution = "DIRECT_EXECUTABLE"
    return CodexLauncher(
        executable=str(preferred.resolve()),
        executable_sha256=_sha256_file(preferred) if preferred.is_file() else None,
        command_prefix=prefix,
        resolution=resolution,
    )


class _JsonlAppServer:
    def __init__(self, command: list[str], cwd: Path) -> None:
        self.command = command
        self.cwd = cwd
        self.proc: subprocess.Popen[str] | None = None
        self.messages: queue.Queue[dict[str, Any]] = queue.Queue()
        self._responses: dict[int, dict[str, Any]] = {}
        self._condition = threading.Condition()
        self._request_id = 0

    def start(self) -> None:
        self.proc = subprocess.Popen(
            self.command,
            cwd=str(self.cwd),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            shell=False,
        )
        threading.Thread(target=self._read_stdout, daemon=True).start()

    def _read_stdout(self) -> None:
        assert self.proc and self.proc.stdout
        for line in self.proc.stdout:
            text = line.strip()
            if not text:
                continue
            try:
                message = json.loads(text)
            except json.JSONDecodeError:
                self.messages.put({"_protocol_error": "invalid JSON from Codex App Server"})
                continue
            if isinstance(message, dict) and isinstance(message.get("id"), int) and (
                "result" in message or "error" in message
            ):
                with self._condition:
                    self._responses[int(message["id"])] = message
                    self._condition.notify_all()
            elif isinstance(message, dict):
                self.messages.put(message)
        self.messages.put({"_eof": True})

    def _send(self, payload: dict[str, Any]) -> None:
        if not self.proc or not self.proc.stdin:
            raise CodexAppServerError("Codex App Server is not running")
        self.proc.stdin.write(json.dumps(payload, separators=(",", ":")) + "\n")
        self.proc.stdin.flush()

    def request(self, method: str, params: dict[str, Any], *, timeout: int) -> dict[str, Any]:
        self._request_id += 1
        request_id = self._request_id
        self._send({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        deadline = time.monotonic() + timeout
        with self._condition:
            while request_id not in self._responses:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise CodexAppServerError(f"App Server request timed out: {method}")
                self._condition.wait(remaining)
            message = self._responses.pop(request_id)
        if "error" in message:
            raise CodexAppServerError(f"App Server request failed: {method}: {message['error']}")
        result = message.get("result")
        return result if isinstance(result, dict) else {}

    def notify(self, method: str, params: dict[str, Any]) -> None:
        self._send({"jsonrpc": "2.0", "method": method, "params": params})

    def respond(self, request_id: int, result: dict[str, Any]) -> None:
        self._send({"jsonrpc": "2.0", "id": request_id, "result": result})

    def next_message(self, *, timeout: float) -> dict[str, Any] | None:
        try:
            return self.messages.get(timeout=timeout)
        except queue.Empty:
            return None

    def stop(self) -> None:
        if not self.proc:
            return
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=5)


ClientFactory = Callable[[list[str], Path], Any]
LauncherFactory = Callable[[], CodexLauncher]
SnapshotFactory = Callable[[Path], tuple[str, str, str]]
CommandRunner = Callable[..., str]


class CodexAppServerExecutionEngine(ISpecialistExecutionEngine):
    """Bounded read-only Codex host bridge for E5 specialist execution."""

    def __init__(
        self,
        repo_root: Path | str,
        *,
        config: CodexAppServerConfig | None = None,
        client_factory: ClientFactory = _JsonlAppServer,
        launcher_factory: LauncherFactory = discover_codex,
        snapshot_factory: SnapshotFactory = _repo_snapshot,
        command_runner: CommandRunner = _run_text,
    ) -> None:
        self._root = Path(repo_root).resolve()
        self._config = config or CodexAppServerConfig()
        self._client_factory = client_factory
        self._launcher_factory = launcher_factory
        self._snapshot_factory = snapshot_factory
        self._command_runner = command_runner
        self._last_request: SpecialistExecutionRequest | None = None
        self._last_receipt: SpecialistExecutionReceipt | None = None
        self._last_host_command: tuple[str, ...] = ()
        self._last_host_version: str | None = None

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

    @property
    def engine_id(self) -> str:
        return ENGINE_ID

    @property
    def engine_version(self) -> str:
        return ENGINE_VERSION

    def _receipt(
        self,
        request: SpecialistExecutionRequest,
        *,
        status: SpecialistExecutionStatus,
        reason_code: str,
        output: str,
        host_execution_id: str,
        evidence_refs: tuple[str, ...] = (),
        host_identity: str | None = None,
    ) -> SpecialistExecutionReceipt:
        return SpecialistExecutionReceipt(
            receipt_version=SPECIALIST_EXECUTION_RECEIPT_VERSION,
            receipt_id=f"codex-receipt.{request.request_digest[:24]}",
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
                SpecialistSideEffectClass.READ_ONLY
                if status is SpecialistExecutionStatus.COMPLETED
                else SpecialistSideEffectClass.NONE
            ),
            host_identity=host_identity,
            sandbox_identity="read-only;network=false",
            approval_policy_identity="never",
            changed_paths=(),
        )

    def execute(self, request: SpecialistExecutionRequest) -> SpecialistExecutionReceipt:
        self._last_request = request
        self._last_receipt = None
        self._last_host_command = ()
        self._last_host_version = None
        host_execution_id = f"codex-app-server.{request.request_digest[:16]}"
        try:
            receipt = self._execute(request, host_execution_id=host_execution_id)
        except TimeoutError:
            receipt = self._receipt(
                request,
                status=SpecialistExecutionStatus.TIMED_OUT,
                reason_code="HOST_EXECUTION_TIMED_OUT",
                output="Codex host execution timed out and was interrupted.",
                host_execution_id=host_execution_id,
            )
        except CodexAppServerError as exc:
            receipt = self._receipt(
                request,
                status=SpecialistExecutionStatus.FAILED,
                reason_code="HOST_EXECUTION_FAILED",
                output=str(exc),
                host_execution_id=host_execution_id,
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            receipt = self._receipt(
                request,
                status=SpecialistExecutionStatus.FAILED,
                reason_code="HOST_CONSTRAINT_UNENFORCEABLE",
                output=f"{type(exc).__name__}: {exc}",
                host_execution_id=host_execution_id,
            )
        self._last_receipt = receipt
        return receipt

    def _execute(
        self,
        request: SpecialistExecutionRequest,
        *,
        host_execution_id: str,
    ) -> SpecialistExecutionReceipt:
        if request.execution_mode is not SpecialistExecutionMode.HOST_NATIVE:
            raise CodexAppServerError("Codex host bridge requires HOST_NATIVE execution mode")
        if request.specialist not in self._config.allowed_specialists:
            raise CodexAppServerError(f"specialist is not allowed by this bridge: {request.specialist}")
        if request.command_name not in self._config.allowed_commands:
            raise CodexAppServerError(f"command is not allowed by this bridge: {request.command_name}")
        if Path(request.project_root).resolve() != self._root:
            raise CodexAppServerError("request project root does not match the configured bridge root")

        skill_path = (self._root / request.skill_source_path).resolve()
        try:
            skill_path.relative_to(self._root)
        except ValueError as exc:
            raise CodexAppServerError("specialist source escaped the configured project root") from exc
        if not skill_path.is_file():
            raise CodexAppServerError("specialist source file is unavailable")
        if _sha256_file(skill_path) != request.skill_source_digest:
            raise CodexAppServerError("specialist source digest does not match the request")
        skill_text = skill_path.read_text(encoding="utf-8")

        before = self._snapshot_factory(self._root)
        if self._config.require_clean_worktree and before[2].strip():
            raise CodexAppServerError("worktree must be clean before read-only host execution")

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
            'sandbox_mode="read-only"',
            "app-server",
            "--listen",
            "stdio://",
        ]
        self._last_host_command = tuple(command)
        client = self._client_factory(command, self._root)
        thread_id = ""
        turn_id = ""
        try:
            client.start()
            client.request(
                "initialize",
                {
                    "clientInfo": {
                        "name": "orchestra_specialist_host_bridge",
                        "title": "Orchestra Specialist Host Bridge",
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
                    "sandbox": "read-only",
                    "ephemeral": True,
                    "serviceName": "orchestra_specialist_host_bridge",
                    "developerInstructions": self._developer_instructions(request, skill_text),
                },
                timeout=30,
            )
            thread_obj = thread.get("thread")
            if not isinstance(thread_obj, dict) or not thread_obj.get("id"):
                raise CodexAppServerError("thread/start returned no thread id")
            thread_id = str(thread_obj["id"])

            turn_params: dict[str, Any] = {
                "threadId": thread_id,
                "input": [{"type": "text", "text": request.task_input}],
                "cwd": str(self._root),
                "approvalPolicy": "never",
                "sandboxPolicy": {"type": "readOnly", "networkAccess": False},
                "model": self._config.model,
                "outputSchema": _OUTPUT_SCHEMA,
            }
            if self._config.reasoning_effort:
                turn_params["effort"] = self._config.reasoning_effort
            turn = client.request("turn/start", turn_params, timeout=30)
            turn_obj = turn.get("turn")
            if not isinstance(turn_obj, dict) or not turn_obj.get("id"):
                raise CodexAppServerError("turn/start returned no turn id")
            turn_id = str(turn_obj["id"])

            output, item_types = self._wait_for_turn(
                client,
                thread_id=thread_id,
                turn_id=turn_id,
            )
        finally:
            client.stop()

        after = self._snapshot_factory(self._root)
        if after != before:
            raise CodexAppServerError("read-only Codex execution changed repository state")

        parsed = json.loads(output)
        if parsed.get("non_mutating") is not True:
            raise CodexAppServerError("host output did not affirm the non-mutating boundary")
        normalized = json.dumps(parsed, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        host_execution_id = f"codex-app-server.{thread_id}.{turn_id}"
        return self._receipt(
            request,
            status=SpecialistExecutionStatus.COMPLETED,
            reason_code="CODEX_READ_ONLY_SPECIALIST_COMPLETED",
            output=normalized,
            host_execution_id=host_execution_id,
            evidence_refs=(
                f"codex-model:{self._config.model}",
                "codex-sandbox:read-only",
                "codex-network:false",
                "codex-approval:never",
                f"codex-item-types:{','.join(sorted(item_types))}",
                f"specialist-source-sha256:{request.skill_source_digest}",
            ),
            host_identity=version[:300],
        )

    def _developer_instructions(
        self,
        request: SpecialistExecutionRequest,
        skill_text: str,
    ) -> str:
        return (
            "You are executing as an explicitly routed Orchestra specialist. "
            "The host does not grant authority. Remain read-only. Do not modify files, "
            "use network access, call MCP tools, delegate to subagents, or request broader permissions. "
            f"Command={request.command_name}; Specialist={request.specialist}; "
            f"Request={request.request_id}. Apply the trusted specialist guidance below.\n\n"
            "----- TRUSTED SPECIALIST GUIDANCE -----\n"
            f"{skill_text}\n"
            "----- END TRUSTED SPECIALIST GUIDANCE -----"
        )

    def _wait_for_turn(
        self,
        client: Any,
        *,
        thread_id: str,
        turn_id: str,
    ) -> tuple[str, set[str]]:
        deadline = time.monotonic() + self._config.turn_timeout_seconds
        agent_text: str | None = None
        item_types: set[str] = set()
        while time.monotonic() < deadline:
            message = client.next_message(timeout=0.5)
            if message is None:
                continue
            if message.get("_eof"):
                raise CodexAppServerError("Codex App Server closed before turn completion")
            if message.get("_protocol_error"):
                raise CodexAppServerError(str(message["_protocol_error"]))

            method = message.get("method")
            params = message.get("params") if isinstance(message.get("params"), dict) else {}
            if method and isinstance(message.get("id"), int):
                if method in _APPROVAL_REQUESTS:
                    client.respond(int(message["id"]), {"decision": "cancel"})
                self._interrupt(client, thread_id=thread_id, turn_id=turn_id)
                raise CodexAppServerError(f"host requested authority escalation: {method}")

            if method in {"item/started", "item/completed"}:
                item = params.get("item")
                if isinstance(item, dict):
                    item_type = str(item.get("type") or "")
                    if item_type:
                        item_types.add(item_type)
                    if item_type in _DENIED_ITEM_TYPES:
                        self._interrupt(client, thread_id=thread_id, turn_id=turn_id)
                        raise CodexAppServerError(f"denied host activity observed: {item_type}")
                    if method == "item/completed" and item_type == "agentMessage":
                        text = item.get("text")
                        if isinstance(text, str):
                            agent_text = text

            if method == "turn/diff/updated":
                diff = params.get("diff")
                if isinstance(diff, str) and diff.strip():
                    self._interrupt(client, thread_id=thread_id, turn_id=turn_id)
                    raise CodexAppServerError("non-empty diff observed during read-only execution")

            if method == "turn/completed":
                completed = params.get("turn")
                if not isinstance(completed, dict):
                    raise CodexAppServerError("turn/completed payload was malformed")
                status = str(completed.get("status") or "")
                if status == "completed":
                    if agent_text is None:
                        raise CodexAppServerError("completed turn returned no final agent message")
                    return agent_text, item_types
                if status == "interrupted":
                    raise CodexAppServerError("Codex host execution was interrupted")
                raise CodexAppServerError(f"Codex host execution ended with status: {status or 'unknown'}")

        self._interrupt(client, thread_id=thread_id, turn_id=turn_id)
        raise TimeoutError("Codex host execution exceeded the configured timeout")

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
