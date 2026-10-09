from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from typing import Callable

from orchestra_runtime.interfaces import ISpecialistExecutionEngine
from orchestra_runtime.specialist_execution import (
    SPECIALIST_EXECUTION_RECEIPT_VERSION,
    SpecialistExecutionMode,
    SpecialistExecutionReceipt,
    SpecialistExecutionRequest,
    SpecialistExecutionStatus,
    SpecialistSideEffectClass,
)


ENGINE_ID = "orchestra.claude-code"
ENGINE_VERSION = "1"
MINIMUM_CLAUDE_CODE_VERSION = (2, 1, 205)
READ_ONLY_TOOLS = ("Read", "Glob", "Grep")
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


class ClaudeCodeBridgeError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class ClaudeLauncher:
    executable: str
    executable_sha256: str | None
    command_prefix: tuple[str, ...]
    resolution: str


@dataclass(frozen=True, slots=True)
class ClaudeCodeConfig:
    model: str
    turn_timeout_seconds: int = 180
    require_clean_worktree: bool = True
    permission_mode: str = "plan"
    tools: tuple[str, ...] = READ_ONLY_TOOLS
    allowed_specialists: tuple[str, ...] = ("scribe",)
    allowed_commands: tuple[str, ...] = ("review-docs",)

    def __post_init__(self) -> None:
        if not self.model.strip():
            raise ValueError("model must be non-empty")
        if any(character in self.model for character in ("\r", "\n", "\x00")):
            raise ValueError("model must not contain control characters")
        if self.turn_timeout_seconds < 10:
            raise ValueError("turn_timeout_seconds must be at least 10")
        if self.permission_mode != "plan":
            raise ValueError("Claude Code specialist execution requires permission_mode='plan'")
        if tuple(self.tools) != READ_ONLY_TOOLS:
            raise ValueError("Claude Code specialist execution requires the fixed read-only tool set")
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
        raise ClaudeCodeBridgeError(f"command failed ({completed.returncode}): {detail}")
    return (completed.stdout or "").strip()


def _repo_snapshot(root: Path) -> tuple[str, str, str]:
    head = _run_text(["git", "-C", str(root), "rev-parse", "HEAD"])
    tree = _run_text(["git", "-C", str(root), "rev-parse", "HEAD^{tree}"])
    status = _run_text(["git", "-C", str(root), "status", "--porcelain=v1", "--untracked-files=all"])
    return head, tree, status


def discover_claude() -> ClaudeLauncher:
    candidates: list[Path] = []
    if os.name == "nt":
        try:
            output = _run_text(["where.exe", "claude"], timeout=10)
            candidates.extend(Path(line.strip()) for line in output.splitlines() if line.strip())
        except Exception:
            pass
        for name in ("claude.exe", "claude.cmd", "claude.bat", "claude.ps1"):
            value = shutil.which(name)
            if value:
                candidates.append(Path(value))
    else:
        value = shutil.which("claude")
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
        raise ClaudeCodeBridgeError("Claude Code CLI was not found in PATH")

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
            raise ClaudeCodeBridgeError("PowerShell is required for the Claude Code .ps1 launcher")
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
    return ClaudeLauncher(
        executable=str(preferred.resolve()),
        executable_sha256=_sha256_file(preferred) if preferred.is_file() else None,
        command_prefix=prefix,
        resolution=resolution,
    )


def _parse_version(text: str) -> tuple[int, int, int]:
    match = re.search(r"(?<!\d)(\d+)\.(\d+)\.(\d+)(?!\d)", text)
    if match is None:
        raise ClaudeCodeBridgeError("Claude Code CLI version could not be parsed")
    major, minor, patch = match.groups()
    return int(major), int(minor), int(patch)


CommandRunner = Callable[..., subprocess.CompletedProcess[str]]
LauncherFactory = Callable[[], ClaudeLauncher]
SnapshotFactory = Callable[[Path], tuple[str, str, str]]


class ClaudeCodeExecutionEngine(ISpecialistExecutionEngine):
    """Bounded read-only Claude Code host bridge for provider-native specialist execution."""

    def __init__(
        self,
        repo_root: Path | str,
        *,
        config: ClaudeCodeConfig,
        launcher_factory: LauncherFactory = discover_claude,
        snapshot_factory: SnapshotFactory = _repo_snapshot,
        command_runner: CommandRunner = subprocess.run,
    ) -> None:
        self._root = Path(repo_root).resolve()
        self._config = config
        self._launcher_factory = launcher_factory
        self._snapshot_factory = snapshot_factory
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
            receipt_id=f"claude-receipt.{request.request_digest[:24]}",
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
            sandbox_identity="read-only-tools:Read,Glob,Grep;safe-mode=true;mcp=denied;chrome=false",
            approval_policy_identity="plan",
            changed_paths=(),
        )

    def execute(self, request: SpecialistExecutionRequest) -> SpecialistExecutionReceipt:
        self._last_request = request
        self._last_receipt = None
        self._last_host_command = ()
        self._last_host_version = None
        host_execution_id = f"claude-code.{request.request_digest[:16]}"
        try:
            receipt = self._execute(request, host_execution_id=host_execution_id)
        except subprocess.TimeoutExpired:
            receipt = self._receipt(
                request,
                status=SpecialistExecutionStatus.TIMED_OUT,
                reason_code="HOST_EXECUTION_TIMED_OUT",
                output="Claude Code host execution timed out and was terminated.",
                host_execution_id=host_execution_id,
            )
        except ClaudeCodeBridgeError as exc:
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
            raise ClaudeCodeBridgeError("Claude Code host bridge requires HOST_NATIVE execution mode")
        if request.specialist not in self._config.allowed_specialists:
            raise ClaudeCodeBridgeError(f"specialist is not allowed by this bridge: {request.specialist}")
        if request.command_name not in self._config.allowed_commands:
            raise ClaudeCodeBridgeError(f"command is not allowed by this bridge: {request.command_name}")
        if Path(request.project_root).resolve() != self._root:
            raise ClaudeCodeBridgeError("request project root does not match the configured bridge root")

        skill_path = (self._root / request.skill_source_path).resolve()
        try:
            skill_path.relative_to(self._root)
        except ValueError as exc:
            raise ClaudeCodeBridgeError("specialist source escaped the configured project root") from exc
        if not skill_path.is_file():
            raise ClaudeCodeBridgeError("specialist source file is unavailable")
        if _sha256_file(skill_path) != request.skill_source_digest:
            raise ClaudeCodeBridgeError("specialist source digest does not match the request")

        before = self._snapshot_factory(self._root)
        if self._config.require_clean_worktree and before[2].strip():
            raise ClaudeCodeBridgeError("worktree must be clean before read-only host execution")

        launcher = self._launcher_factory()
        version_result = self._command_runner(
            [*launcher.command_prefix, "--version"],
            cwd=str(self._root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=False,
            check=False,
            timeout=20,
        )
        if version_result.returncode != 0:
            detail = (version_result.stderr or version_result.stdout or "").strip()[-1200:]
            raise ClaudeCodeBridgeError(
                f"Claude Code version probe failed ({version_result.returncode}): {detail}"
            )
        version = (version_result.stdout or version_result.stderr or "").strip()
        self._last_host_version = version[:300]
        if _parse_version(version) < MINIMUM_CLAUDE_CODE_VERSION:
            minimum = ".".join(str(item) for item in MINIMUM_CLAUDE_CODE_VERSION)
            raise ClaudeCodeBridgeError(
                f"Claude Code CLI {version or 'unknown'} is below required version {minimum}"
            )

        schema = json.dumps(_OUTPUT_SCHEMA, sort_keys=True, separators=(",", ":"))
        guardrail = (
            "You are executing as an explicitly routed Orchestra specialist. "
            "Host capability is not authority. Remain read-only. Use only the provided "
            "read-only tools. Do not modify files, run commands, use browser or network tools, "
            "call MCP tools, delegate, resume another session, or request broader permissions. "
            f"Command={request.command_name}; Specialist={request.specialist}; Request={request.request_id}. "
            "Set non_mutating=true only if you made no changes."
        )
        command = [
            *launcher.command_prefix,
            "-p",
            request.task_input,
            "--output-format",
            "json",
            "--json-schema",
            schema,
            "--model",
            self._config.model,
            "--permission-mode",
            self._config.permission_mode,
            "--tools",
            ",".join(self._config.tools),
            "--disallowedTools",
            "mcp__*",
            "--safe-mode",
            "--no-chrome",
            "--no-session-persistence",
            "--append-system-prompt",
            guardrail,
            "--append-system-prompt-file",
            str(skill_path),
        ]
        self._last_host_command = tuple(command)
        completed = self._command_runner(
            command,
            cwd=str(self._root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=False,
            check=False,
            timeout=self._config.turn_timeout_seconds,
        )
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "").strip()[-2000:]
            raise ClaudeCodeBridgeError(
                f"Claude Code execution failed ({completed.returncode}): {detail}"
            )

        payload = json.loads(completed.stdout or "")
        if not isinstance(payload, dict):
            raise ClaudeCodeBridgeError("Claude Code JSON result was not an object")
        subtype = payload.get("subtype")
        if subtype is not None and subtype != "success":
            raise ClaudeCodeBridgeError(f"Claude Code execution ended with subtype: {subtype}")
        structured = payload.get("structured_output")
        if not isinstance(structured, dict):
            raise ClaudeCodeBridgeError("Claude Code result did not contain structured_output")
        if structured.get("non_mutating") is not True:
            raise ClaudeCodeBridgeError("Claude Code output did not affirm the non-mutating boundary")
        for key in ("summary", "findings", "evidence"):
            if key not in structured:
                raise ClaudeCodeBridgeError(f"Claude Code structured output is missing {key}")

        after = self._snapshot_factory(self._root)
        if after != before:
            raise ClaudeCodeBridgeError("read-only Claude Code execution changed repository state")

        normalized = json.dumps(
            structured,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
        session_id = payload.get("session_id")
        if isinstance(session_id, str) and session_id.strip():
            host_execution_id = f"claude-code.{session_id.strip()}"
        return self._receipt(
            request,
            status=SpecialistExecutionStatus.COMPLETED,
            reason_code="CLAUDE_CODE_READ_ONLY_SPECIALIST_COMPLETED",
            output=normalized,
            host_execution_id=host_execution_id,
            evidence_refs=(
                f"claude-model:{self._config.model}",
                "claude-permission:plan",
                "claude-tools:Glob,Grep,Read",
                "claude-mcp:denied",
                "claude-browser:false",
                "claude-session-persistence:false",
                f"specialist-source-sha256:{request.skill_source_digest}",
            ),
            host_identity=version[:300],
        )
