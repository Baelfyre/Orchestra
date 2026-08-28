from __future__ import annotations

from pathlib import Path

from orchestra_runtime.mcp_transport import (
    MCP_PROTOCOL_VERSION,
    MCP_PROTOCOL_VERSION_META_KEY,
    build_mcp_stdio_transport,
)


ROOT = Path(__file__).resolve().parents[2]


def test_codex_2026_discovery_result_includes_required_cache_hints() -> None:
    transport = build_mcp_stdio_transport(ROOT, backing_adapter="codex")
    response = transport.handle_message(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "server/discover",
            "params": {
                "_meta": {
                    MCP_PROTOCOL_VERSION_META_KEY: MCP_PROTOCOL_VERSION,
                    "io.modelcontextprotocol/clientInfo": {
                        "name": "codex-compat-test",
                        "version": "0.150.1",
                    },
                    "io.modelcontextprotocol/clientCapabilities": {},
                }
            },
        }
    )

    result = response["result"]
    assert result["resultType"] == "complete"
    assert result["supportedVersions"] == [MCP_PROTOCOL_VERSION]
    assert result["capabilities"] == {"tools": {}}
    assert result["ttlMs"] == 0
    assert result["cacheScope"] == "private"
    assert result["_meta"]["io.modelcontextprotocol/serverInfo"]["name"] == "orchestra"
