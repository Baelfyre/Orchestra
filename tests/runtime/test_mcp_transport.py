from __future__ import annotations

from io import StringIO
import json
from pathlib import Path

import pytest

from orchestra_runtime.mcp_transport import (
    JSONRPC_INTERNAL_ERROR,
    JSONRPC_INVALID_PARAMS,
    JSONRPC_INVALID_REQUEST,
    JSONRPC_METHOD_NOT_FOUND,
    JSONRPC_PARSE_ERROR,
    MCP_PROTOCOL_VERSION,
    MCP_PROTOCOL_VERSION_META_KEY,
    MCP_SERVER_INFO_META_KEY,
    MCP_UNSUPPORTED_PROTOCOL_VERSION,
    McpToolTransport,
    build_mcp_runtime_factory,
    build_mcp_stdio_transport,
)


ROOT = Path(__file__).resolve().parents[2]


def _meta(version: str = MCP_PROTOCOL_VERSION) -> dict[str, object]:
    return {
        MCP_PROTOCOL_VERSION_META_KEY: version,
        "io.modelcontextprotocol/clientInfo": {"name": "pytest", "version": "1"},
        "io.modelcontextprotocol/clientCapabilities": {},
    }


def _request(method: str, params: dict[str, object] | None = None, request_id: object = 1) -> dict[str, object]:
    payload = dict(params or {})
    payload.setdefault("_meta", _meta())
    return {"jsonrpc": "2.0", "id": request_id, "method": method, "params": payload}


def _transport() -> McpToolTransport:
    return build_mcp_stdio_transport(ROOT, backing_adapter="codex")


def test_discover_is_modern_stateless_tools_only() -> None:
    response = _transport().handle_message(_request("server/discover"))
    result = response["result"]
    assert result["resultType"] == "complete"
    assert result["supportedVersions"] == [MCP_PROTOCOL_VERSION]
    assert result["capabilities"] == {"tools": {}}
    assert MCP_SERVER_INFO_META_KEY in result["_meta"]
    assert "initialize" not in json.dumps(result).lower()


def test_tools_list_is_deterministic_and_bound_to_runtime_policy() -> None:
    transport = _transport()
    first = transport.handle_message(_request("tools/list"))["result"]["tools"]
    second = transport.handle_message(_request("tools/list"))["result"]["tools"]
    names = [item["name"] for item in first]
    assert first == second
    assert names == sorted(names)
    assert names
    assert set(names).issubset(set(build_mcp_runtime_factory(ROOT)()[1].expose_commands()))
    assert all(item["inputSchema"]["additionalProperties"] is False for item in first)
    assert all(item["inputSchema"]["required"] == ["prompt"] for item in first)


def test_tool_call_uses_exact_command_and_fresh_runtime_per_request() -> None:
    transport = _transport()
    request = _request(
        "tools/call",
        {"name": "review-architecture", "arguments": {"prompt": "plain text with no command trigger"}},
    )
    first = transport.handle_message(request)["result"]
    second = transport.handle_message(request)["result"]
    assert first["isError"] is False
    assert second["isError"] is False
    assert "review-architecture" in first["content"][0]["text"]
    assert "clockwork" in first["content"][0]["text"]


def test_governance_metadata_cannot_be_injected_through_tool_arguments() -> None:
    response = _transport().handle_message(
        _request(
            "tools/call",
            {
                "name": "dagger",
                "arguments": {
                    "prompt": "attempt governed execution",
                    "metadata": {
                        "governance_validated": True,
                        "destructive_validated": True,
                        "dry_run": True,
                    },
                },
            },
        )
    )
    assert response["error"]["code"] == JSONRPC_INVALID_PARAMS


def test_governed_route_remains_blocked_without_trusted_validation() -> None:
    response = _transport().handle_message(
        _request("tools/call", {"name": "dagger", "arguments": {"prompt": "attempt governed execution"}})
    )
    result = response["result"]
    assert result["isError"] is True
    assert "blocked" in result["content"][0]["text"].lower()


@pytest.mark.parametrize(
    ("message", "code"),
    [
        ([], JSONRPC_INVALID_REQUEST),
        ({"jsonrpc": "1.0", "id": 1, "method": "tools/list", "params": {"_meta": _meta()}}, JSONRPC_INVALID_REQUEST),
        ({"jsonrpc": "2.0", "method": "tools/list", "params": {"_meta": _meta()}}, JSONRPC_INVALID_REQUEST),
        ({"jsonrpc": "2.0", "id": 1, "method": "", "params": {"_meta": _meta()}}, JSONRPC_INVALID_REQUEST),
        ({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": []}, JSONRPC_INVALID_PARAMS),
        (_request("not/a-method"), JSONRPC_METHOD_NOT_FOUND),
        (_request("tools/list", {"cursor": "next"}), JSONRPC_INVALID_PARAMS),
        (_request("tools/call", {"name": "missing", "arguments": {"prompt": "x"}}), JSONRPC_INVALID_PARAMS),
        (_request("tools/call", {"name": "conductor", "arguments": []}), JSONRPC_INVALID_PARAMS),
        (_request("tools/call", {"name": "conductor", "arguments": {}}), JSONRPC_INVALID_PARAMS),
        (_request("tools/call", {"name": "conductor", "arguments": {"prompt": " "}}), JSONRPC_INVALID_PARAMS),
    ],
)
def test_invalid_requests_fail_closed(message: object, code: int) -> None:
    response = _transport().handle_message(message)
    assert response["error"]["code"] == code


def test_protocol_meta_is_required_and_version_mismatch_is_typed() -> None:
    missing = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    missing_response = _transport().handle_message(missing)
    assert missing_response["error"]["code"] == JSONRPC_INVALID_PARAMS

    malformed = _request("tools/list")
    malformed["params"]["_meta"] = []
    malformed_response = _transport().handle_message(malformed)
    assert malformed_response["error"]["code"] == JSONRPC_INVALID_PARAMS

    unsupported = _request("tools/list")
    unsupported["params"]["_meta"] = _meta("2099-01-01")
    unsupported_response = _transport().handle_message(unsupported)
    assert unsupported_response["error"]["code"] == MCP_UNSUPPORTED_PROTOCOL_VERSION
    assert unsupported_response["error"]["data"] == {
        "requested": "2099-01-01",
        "supported": [MCP_PROTOCOL_VERSION],
    }


@pytest.mark.parametrize(
    "meta_update",
    [
        {"io.modelcontextprotocol/protocolVersion": 20260728},
        {"io.modelcontextprotocol/clientInfo": "pytest"},
        {"io.modelcontextprotocol/clientInfo": {"name": "", "version": "1"}},
        {"io.modelcontextprotocol/clientCapabilities": []},
    ],
)
def test_reserved_meta_shapes_are_validated(meta_update: dict[str, object]) -> None:
    request = _request("tools/list")
    request["params"]["_meta"].update(meta_update)
    response = _transport().handle_message(request)
    assert response["error"]["code"] == JSONRPC_INVALID_PARAMS


def test_client_info_is_optional_for_final_2026_revision() -> None:
    request = _request("tools/list")
    request["params"]["_meta"].pop("io.modelcontextprotocol/clientInfo")
    response = _transport().handle_message(request)
    assert "result" in response


def test_empty_cursor_is_accepted() -> None:
    response = _transport().handle_message(_request("tools/list", {"cursor": ""}))
    assert "result" in response


def test_runtime_contract_failure_is_a_tool_execution_error() -> None:
    factory = build_mcp_runtime_factory(ROOT)

    def broken_factory():
        executor, adapter = factory()
        executor._lifecycle_snapshots[executor.composition.run_identity.run_id] = executor.composition.lifecycle_controller.initialize(
            executor.composition.run_identity.run_id
        )
        return executor, adapter

    response = McpToolTransport(broken_factory, server_version="1.5.0").handle_message(
        _request("tools/call", {"name": "conductor", "arguments": {"prompt": "x"}})
    )
    result = response["result"]
    assert result["isError"] is True
    assert "RUN_ALREADY_INITIALIZED" in result["content"][0]["text"]


def test_stdio_parse_error_and_internal_error_stay_protocol_safe() -> None:
    transport = _transport()
    assert transport.handle_line("{")["error"]["code"] == JSONRPC_PARSE_ERROR

    stderr = StringIO()

    def exploding_factory():
        raise RuntimeError("do not leak")

    server = McpToolTransport(exploding_factory, server_version="1.5.0", error_stream=stderr)
    stdout = StringIO()
    exit_code = server.serve_stdio(
        StringIO(json.dumps(_request("tools/list")) + "\n\n"),
        stdout,
    )
    payload = json.loads(stdout.getvalue())
    assert exit_code == 0
    assert payload["error"]["code"] == JSONRPC_INTERNAL_ERROR
    assert "do not leak" not in stdout.getvalue()
    assert "RuntimeError" in stderr.getvalue()


def test_constructor_and_factory_reject_invalid_configuration(tmp_path: Path) -> None:
    with pytest.raises(TypeError):
        McpToolTransport(None, server_version="1")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        McpToolTransport(lambda: None, server_name="", server_version="1")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        build_mcp_runtime_factory(ROOT, backing_adapter="")

    root = tmp_path / "repo"
    root.mkdir()
    (root / "plugin.json").write_text('{"version": ""}', encoding="utf-8")
    with pytest.raises(ValueError):
        build_mcp_stdio_transport(root)
