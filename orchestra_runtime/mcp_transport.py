from __future__ import annotations

from collections.abc import Callable
import json
from pathlib import Path
import sys
from typing import TextIO
from uuid import uuid4

from .factories import AdapterFactory
from .interfaces import IIDEAdapter
from .models import Command, ExecutionResult
from .repositories import ManifestRepository, SkillSourceRepository
from .services import (
    ContextAssembler,
    GovernanceValidator,
    InMemoryAuditSink,
    RouterService,
    RuntimeExecutor,
    SkillRegistry,
    build_compatibility_composition,
)
from .errors import RuntimeContractError


MCP_PROTOCOL_VERSION = "2026-07-28"
MCP_PROTOCOL_VERSION_META_KEY = "io.modelcontextprotocol/protocolVersion"
MCP_CLIENT_INFO_META_KEY = "io.modelcontextprotocol/clientInfo"
MCP_CLIENT_CAPABILITIES_META_KEY = "io.modelcontextprotocol/clientCapabilities"
MCP_SERVER_INFO_META_KEY = "io.modelcontextprotocol/serverInfo"

JSONRPC_PARSE_ERROR = -32700
JSONRPC_INVALID_REQUEST = -32600
JSONRPC_METHOD_NOT_FOUND = -32601
JSONRPC_INVALID_PARAMS = -32602
JSONRPC_INTERNAL_ERROR = -32603
MCP_UNSUPPORTED_PROTOCOL_VERSION = -32022


class McpProtocolError(Exception):
    def __init__(self, code: int, message: str, data: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.code = int(code)
        self.message = str(message)
        self.data = dict(data or {})


class _ExactCommandAdapter(IIDEAdapter):
    """Transport-only adapter view that preserves the selected PRAP adapter identity."""

    def __init__(self, backing: IIDEAdapter, command_name: str) -> None:
        self._backing = backing
        self._command_name = str(command_name).strip()

    @property
    def adapter_name(self) -> str:
        return self._backing.adapter_name

    def provide_context(self, prompt: str, metadata: dict | None = None):
        return self._backing.provide_context(prompt, metadata)

    def expose_commands(self) -> tuple[str, ...]:
        return self._backing.expose_commands()

    def parse_command(self, prompt: str, metadata: dict | None = None) -> Command:
        return Command(
            name=self._command_name,
            raw_input=prompt,
            adapter_name=self.adapter_name,
            metadata=dict(metadata or {}),
        )


RuntimeFactory = Callable[[], tuple[RuntimeExecutor, IIDEAdapter]]


class McpToolTransport:
    """MCP 2026-07-28 stdio transport over Orchestra's existing trusted runtime."""

    def __init__(
        self,
        runtime_factory: RuntimeFactory,
        *,
        server_name: str = "orchestra",
        server_version: str,
        error_stream: TextIO | None = None,
    ) -> None:
        if not callable(runtime_factory):
            raise TypeError("runtime_factory must be callable")
        name = str(server_name).strip()
        version = str(server_version).strip()
        if not name or not version:
            raise ValueError("server_name and server_version must be non-empty")
        self._runtime_factory = runtime_factory
        self._server_name = name
        self._server_version = version
        self._error_stream = error_stream or sys.stderr

    @property
    def server_info(self) -> dict[str, str]:
        return {"name": self._server_name, "version": self._server_version}

    def _response_meta(self) -> dict[str, object]:
        return {MCP_SERVER_INFO_META_KEY: self.server_info}

    @staticmethod
    def _request_id(message: object) -> object:
        if isinstance(message, dict) and "id" in message:
            return message["id"]
        return None

    def _validate_request(self, message: object) -> tuple[object, str, dict[str, object]]:
        if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
            raise McpProtocolError(JSONRPC_INVALID_REQUEST, "Invalid Request")
        if "id" not in message:
            raise McpProtocolError(JSONRPC_INVALID_REQUEST, "MCP stdio transport accepts requests only")
        method = message.get("method")
        params = message.get("params", {})
        if not isinstance(method, str) or not method.strip():
            raise McpProtocolError(JSONRPC_INVALID_REQUEST, "Invalid Request")
        if not isinstance(params, dict):
            raise McpProtocolError(JSONRPC_INVALID_PARAMS, "Request params must be an object")
        self._validate_meta(params)
        return message["id"], method, params

    @staticmethod
    def _validate_optional_implementation(value: object, field_name: str) -> None:
        if value is None:
            return
        if not isinstance(value, dict):
            raise McpProtocolError(JSONRPC_INVALID_PARAMS, f"{field_name} must be an object")
        name = value.get("name")
        version = value.get("version")
        if not isinstance(name, str) or not name.strip() or not isinstance(version, str) or not version.strip():
            raise McpProtocolError(JSONRPC_INVALID_PARAMS, f"{field_name} must include non-empty name and version")

    def _validate_meta(self, params: dict[str, object]) -> None:
        meta = params.get("_meta")
        if not isinstance(meta, dict):
            raise McpProtocolError(JSONRPC_INVALID_PARAMS, "Request _meta is required")
        requested = meta.get(MCP_PROTOCOL_VERSION_META_KEY)
        if not isinstance(requested, str) or not requested.strip():
            raise McpProtocolError(JSONRPC_INVALID_PARAMS, "Request protocol version is required")
        if requested != MCP_PROTOCOL_VERSION:
            raise McpProtocolError(
                MCP_UNSUPPORTED_PROTOCOL_VERSION,
                "Unsupported protocol version",
                {"requested": requested, "supported": [MCP_PROTOCOL_VERSION]},
            )
        self._validate_optional_implementation(meta.get(MCP_CLIENT_INFO_META_KEY), "clientInfo")
        capabilities = meta.get(MCP_CLIENT_CAPABILITIES_META_KEY)
        if capabilities is not None and not isinstance(capabilities, dict):
            raise McpProtocolError(JSONRPC_INVALID_PARAMS, "clientCapabilities must be an object")

    def _project_tools(self, executor: RuntimeExecutor, adapter: IIDEAdapter) -> list[dict[str, object]]:
        available = set(adapter.expose_commands())
        projected: dict[str, str] = {}
        for binding in executor.composition.policy.bindings:
            if binding.command_name not in available:
                continue
            existing = projected.get(binding.command_name)
            if existing is not None and existing != binding.skill_slug:
                raise RuntimeError(f"ambiguous runtime binding for command '{binding.command_name}'")
            projected[binding.command_name] = binding.skill_slug

        return [
            {
                "name": command_name,
                "title": f"Orchestra: {command_name}",
                "description": (
                    f"Route the '{command_name}' Orchestra command through the existing trusted "
                    f"runtime binding for specialist '{projected[command_name]}'."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "Task input supplied to the selected Orchestra command.",
                        }
                    },
                    "required": ["prompt"],
                    "additionalProperties": False,
                },
            }
            for command_name in sorted(projected)
        ]

    def discover(self) -> dict[str, object]:
        return {
            "resultType": "complete",
            "supportedVersions": [MCP_PROTOCOL_VERSION],
            "capabilities": {"tools": {}},
            "instructions": (
                "Orchestra exposes existing governed runtime commands as MCP tools. "
                "MCP metadata and tool arguments do not grant runtime authority or governance approval."
            ),
            "ttlMs": 0,
            "cacheScope": "private",
            "_meta": self._response_meta(),
        }

    def list_tools(self) -> dict[str, object]:
        executor, adapter = self._runtime_factory()
        return {
            "resultType": "complete",
            "tools": self._project_tools(executor, adapter),
            "ttlMs": 0,
            "cacheScope": "private",
            "_meta": self._response_meta(),
        }

    @staticmethod
    def _parse_tool_call(params: dict[str, object], allowed_names: set[str]) -> tuple[str, str]:
        name = params.get("name")
        arguments = params.get("arguments")
        if not isinstance(name, str) or name not in allowed_names:
            raise McpProtocolError(JSONRPC_INVALID_PARAMS, "Unknown tool")
        if not isinstance(arguments, dict):
            raise McpProtocolError(JSONRPC_INVALID_PARAMS, "Tool arguments must be an object")
        if set(arguments) != {"prompt"}:
            raise McpProtocolError(JSONRPC_INVALID_PARAMS, "Tool arguments must contain only 'prompt'")
        prompt = arguments.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise McpProtocolError(JSONRPC_INVALID_PARAMS, "Tool argument 'prompt' must be a non-empty string")
        return name, prompt

    def _tool_result(self, result: ExecutionResult) -> dict[str, object]:
        return {
            "resultType": "complete",
            "content": [{"type": "text", "text": result.output}],
            "isError": not result.success,
            "_meta": self._response_meta(),
        }

    def call_tool(self, params: dict[str, object]) -> dict[str, object]:
        executor, adapter = self._runtime_factory()
        tools = self._project_tools(executor, adapter)
        name, prompt = self._parse_tool_call(params, {str(item["name"]) for item in tools})
        exact_adapter = _ExactCommandAdapter(adapter, name)
        try:
            result = executor.execute(
                exact_adapter,
                prompt,
                {
                    "orchestra.transport": "mcp",
                    "orchestra.mcp.tool": name,
                },
            )
        except RuntimeContractError as exc:
            return {
                "resultType": "complete",
                "content": [
                    {
                        "type": "text",
                        "text": f"Orchestra runtime rejected the request ({exc.reason_code}).",
                    }
                ],
                "isError": True,
                "_meta": self._response_meta(),
            }
        return self._tool_result(result)

    def handle_message(self, message: object) -> dict[str, object]:
        request_id = self._request_id(message)
        try:
            request_id, method, params = self._validate_request(message)
            if method == "server/discover":
                result = self.discover()
            elif method == "tools/list":
                cursor = params.get("cursor")
                if cursor not in {None, ""}:
                    raise McpProtocolError(JSONRPC_INVALID_PARAMS, "Pagination cursors are not supported")
                result = self.list_tools()
            elif method == "tools/call":
                result = self.call_tool(params)
            else:
                raise McpProtocolError(JSONRPC_METHOD_NOT_FOUND, "Method not found")
            return {"jsonrpc": "2.0", "id": request_id, "result": result}
        except McpProtocolError as exc:
            error: dict[str, object] = {"code": exc.code, "message": exc.message}
            if exc.data:
                error["data"] = exc.data
            return {"jsonrpc": "2.0", "id": request_id, "error": error}

    def handle_line(self, line: str) -> dict[str, object]:
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            return {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": JSONRPC_PARSE_ERROR, "message": "Parse error"},
            }
        return self.handle_message(message)

    def serve_stdio(
        self,
        input_stream: TextIO | None = None,
        output_stream: TextIO | None = None,
    ) -> int:
        source = input_stream or sys.stdin
        sink = output_stream or sys.stdout
        for raw_line in source:
            if not raw_line.strip():
                continue
            try:
                response = self.handle_line(raw_line)
            except Exception as exc:
                print(
                    f"ORCHESTRA_MCP_INTERNAL_ERROR={type(exc).__name__}",
                    file=self._error_stream,
                    flush=True,
                )
                response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": JSONRPC_INTERNAL_ERROR, "message": "Internal error"},
                }
            sink.write(json.dumps(response, separators=(",", ":"), ensure_ascii=False) + "\n")
            sink.flush()
        return 0


def build_mcp_runtime_factory(
    repo_root: Path | str,
    *,
    backing_adapter: str = "codex",
) -> RuntimeFactory:
    root = Path(repo_root).resolve()
    adapter_name = str(backing_adapter).strip().casefold()
    if not adapter_name:
        raise ValueError("backing_adapter must be non-empty")

    def factory() -> tuple[RuntimeExecutor, IIDEAdapter]:
        manifest_repository = ManifestRepository(root)
        skill_repository = SkillSourceRepository(root)
        skill_registry = SkillRegistry(manifest_repository, skill_repository)
        audit_sink = InMemoryAuditSink()
        composition = build_compatibility_composition(
            skill_registry,
            audit_sink,
            run_id=f"mcp-{uuid4().hex}",
        )
        executor = RuntimeExecutor(
            skill_registry,
            RouterService(skill_registry),
            GovernanceValidator(),
            ContextAssembler(manifest_repository),
            composition,
        )
        adapter = AdapterFactory.create(adapter_name, root)
        return executor, adapter

    return factory


def build_mcp_stdio_transport(
    repo_root: Path | str,
    *,
    backing_adapter: str = "codex",
    error_stream: TextIO | None = None,
) -> McpToolTransport:
    root = Path(repo_root).resolve()
    manifest = ManifestRepository(root).load_manifest()
    server_version = str(manifest.get("version", "")).strip()
    if not server_version:
        raise ValueError("plugin.json must declare a non-empty version")
    return McpToolTransport(
        build_mcp_runtime_factory(root, backing_adapter=backing_adapter),
        server_name="orchestra",
        server_version=server_version,
        error_stream=error_stream,
    )
