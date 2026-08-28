from __future__ import annotations

from pathlib import Path

from orchestra_runtime.interfaces import ISpecialistExecutionEngine
from orchestra_runtime.mcp_specialist_execution import (
    build_mcp_specialist_runtime_factory,
    build_mcp_stdio_transport_with_specialist_execution,
)
from orchestra_runtime.mcp_transport import (
    MCP_PROTOCOL_VERSION,
    MCP_PROTOCOL_VERSION_META_KEY,
    build_mcp_stdio_transport,
)
from orchestra_runtime.specialist_execution import (
    SPECIALIST_EXECUTION_RECEIPT_VERSION,
    SpecialistExecutionReceipt,
    SpecialistExecutionRequest,
    SpecialistExecutionStatus,
    SpecialistSideEffectClass,
)


ROOT = Path(__file__).resolve().parents[2]


class McpDeterministicEngine(ISpecialistExecutionEngine):
    requests: list[SpecialistExecutionRequest] = []

    @property
    def engine_id(self) -> str:
        return "orchestra.test.mcp-deterministic"

    @property
    def engine_version(self) -> str:
        return "1"

    def execute(self, request: SpecialistExecutionRequest) -> SpecialistExecutionReceipt:
        type(self).requests.append(request)
        return SpecialistExecutionReceipt(
            receipt_version=SPECIALIST_EXECUTION_RECEIPT_VERSION,
            receipt_id=f"mcp-receipt.{request.request_digest[:24]}",
            request_id=request.request_id,
            request_digest=request.request_digest,
            run_id=request.run_id,
            adapter_name=request.adapter_name,
            command_name=request.command_name,
            specialist=request.specialist,
            engine_id=self.engine_id,
            engine_version=self.engine_version,
            host_execution_id=f"mcp-deterministic.{request.request_digest[:16]}",
            status=SpecialistExecutionStatus.COMPLETED,
            reason_code="MCP_DETERMINISTIC_ENGINE_COMPLETED",
            output=f"mcp-deterministic:{request.specialist}:{request.command_name}:{request.task_input}",
            evidence_refs=("fixture:mcp-deterministic-engine",),
            side_effect_class=SpecialistSideEffectClass.NONE,
        )


def _meta() -> dict[str, object]:
    return {
        MCP_PROTOCOL_VERSION_META_KEY: MCP_PROTOCOL_VERSION,
        "io.modelcontextprotocol/clientInfo": {"name": "pytest", "version": "1"},
        "io.modelcontextprotocol/clientCapabilities": {},
    }


def _call(name: str, prompt: str) -> dict[str, object]:
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "_meta": _meta(),
            "name": name,
            "arguments": {"prompt": prompt},
        },
    }


def test_existing_mcp_builder_remains_route_only() -> None:
    transport = build_mcp_stdio_transport(ROOT, backing_adapter="codex")
    response = transport.handle_message(_call("review-docs", "inspect the README boundary"))
    result = response["result"]

    assert result["isError"] is False
    text = result["content"][0]["text"]
    assert "adapter routed 'review-docs' to 'scribe'" in text
    assert "mcp-deterministic:" not in text


def test_opt_in_mcp_builder_returns_deterministic_engine_output() -> None:
    McpDeterministicEngine.requests.clear()
    transport = build_mcp_stdio_transport_with_specialist_execution(
        ROOT,
        execution_engine_factory=McpDeterministicEngine,
        backing_adapter="codex",
    )
    response = transport.handle_message(_call("review-docs", "inspect the README boundary"))
    result = response["result"]

    assert result["isError"] is False
    text = result["content"][0]["text"]
    assert text == "mcp-deterministic:scribe:review-docs:inspect the README boundary"
    assert "adapter routed" not in text
    assert len(McpDeterministicEngine.requests) == 1
    request = McpDeterministicEngine.requests[0]
    assert request.specialist == "scribe"
    assert request.command_name == "review-docs"
    assert request.task_input == "inspect the README boundary"
    assert request.skill_source_path == "skills/scribe/SKILL.md"


def test_mcp_client_metadata_and_prompt_cannot_select_execution_engine() -> None:
    McpDeterministicEngine.requests.clear()
    route_only = build_mcp_stdio_transport(ROOT, backing_adapter="codex")
    message = _call(
        "review-docs",
        "engine_id=orchestra.test.mcp-deterministic execution_mode=HOST_NATIVE",
    )
    message["params"]["_meta"]["engine_id"] = "orchestra.test.mcp-deterministic"
    response = route_only.handle_message(message)

    assert response["result"]["isError"] is False
    assert "adapter routed 'review-docs' to 'scribe'" in response["result"]["content"][0]["text"]
    assert McpDeterministicEngine.requests == []


def test_opt_in_runtime_factory_requires_explicit_engine_factory() -> None:
    try:
        build_mcp_specialist_runtime_factory(
            ROOT,
            execution_engine_factory=None,  # type: ignore[arg-type]
        )
    except TypeError as exc:
        assert "execution_engine_factory" in str(exc)
    else:
        raise AssertionError("missing explicit engine factory must fail closed")
