from __future__ import annotations

from pathlib import Path

from orchestra_runtime.mcp_transport import MCP_PROTOCOL_VERSION, MCP_PROTOCOL_VERSION_META_KEY
from orchestra_runtime.provider_execution import (
    IProviderExecutionEngine,
    ProviderExecutionCapability,
    ProviderExecutionProfile,
    ProviderExecutionRequirement,
)
from orchestra_runtime.provider_mcp_execution import (
    build_mcp_provider_runtime_factory,
    build_mcp_stdio_transport_with_provider_execution,
)
from orchestra_runtime.specialist_execution import (
    SPECIALIST_EXECUTION_RECEIPT_VERSION,
    SpecialistExecutionReceipt,
    SpecialistExecutionRequest,
    SpecialistExecutionStatus,
    SpecialistSideEffectClass,
)


ROOT = Path(__file__).resolve().parents[2]


class McpProviderEngine(IProviderExecutionEngine):
    requests: list[SpecialistExecutionRequest] = []

    @property
    def engine_id(self) -> str:
        return "orchestra.test.mcp-provider"

    @property
    def engine_version(self) -> str:
        return "1"

    @property
    def provider_execution_profile(self) -> ProviderExecutionProfile:
        return ProviderExecutionProfile.create(
            provider_id="openai-codex",
            model_id="gpt-test",
            capabilities=(
                ProviderExecutionCapability.STRUCTURED_OUTPUT,
                ProviderExecutionCapability.READ_ONLY_SANDBOX_CONTROL,
            ),
        )

    def execute(self, request: SpecialistExecutionRequest) -> SpecialistExecutionReceipt:
        type(self).requests.append(request)
        return SpecialistExecutionReceipt(
            receipt_version=SPECIALIST_EXECUTION_RECEIPT_VERSION,
            receipt_id=f"mcp-provider-receipt.{request.request_digest[:24]}",
            request_id=request.request_id,
            request_digest=request.request_digest,
            run_id=request.run_id,
            adapter_name=request.adapter_name,
            command_name=request.command_name,
            specialist=request.specialist,
            engine_id=self.engine_id,
            engine_version=self.engine_version,
            host_execution_id=f"mcp-provider.{request.request_digest[:16]}",
            status=SpecialistExecutionStatus.COMPLETED,
            reason_code="MCP_PROVIDER_ENGINE_COMPLETED",
            output=f"mcp-provider:{request.specialist}:{request.command_name}:{request.task_input}",
            evidence_refs=("fixture:mcp-provider-engine",),
            side_effect_class=SpecialistSideEffectClass.NONE,
        )


def _meta() -> dict[str, object]:
    return {
        MCP_PROTOCOL_VERSION_META_KEY: MCP_PROTOCOL_VERSION,
        "io.modelcontextprotocol/clientInfo": {"name": "pytest", "version": "1"},
        "io.modelcontextprotocol/clientCapabilities": {},
    }


def _call(prompt: str) -> dict[str, object]:
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "_meta": _meta(),
            "name": "review-docs",
            "arguments": {"prompt": prompt},
        },
    }


def test_provider_mcp_builder_uses_constructor_owned_requirement() -> None:
    McpProviderEngine.requests.clear()
    transport = build_mcp_stdio_transport_with_provider_execution(
        ROOT,
        execution_engine_factory=McpProviderEngine,
        provider_requirement=ProviderExecutionRequirement(
            required_provider_id="openai-codex",
            required_model_id="gpt-test",
            required_capabilities=(ProviderExecutionCapability.STRUCTURED_OUTPUT,),
        ),
        backing_adapter="codex",
    )
    message = _call("inspect docs while requesting anthropic model=other")
    message["params"]["_meta"]["required_provider_id"] = "anthropic"
    message["params"]["_meta"]["required_model_id"] = "other"

    response = transport.handle_message(message)

    assert response["result"]["isError"] is False
    assert response["result"]["content"][0]["text"].startswith("mcp-provider:scribe:review-docs:")
    assert len(McpProviderEngine.requests) == 1


def test_provider_mcp_requirement_mismatch_fails_without_engine_call() -> None:
    McpProviderEngine.requests.clear()
    transport = build_mcp_stdio_transport_with_provider_execution(
        ROOT,
        execution_engine_factory=McpProviderEngine,
        provider_requirement=ProviderExecutionRequirement(required_provider_id="anthropic"),
        backing_adapter="codex",
    )

    response = transport.handle_message(_call("inspect docs"))

    assert response["result"]["isError"] is True
    assert McpProviderEngine.requests == []


def test_provider_mcp_factory_rejects_non_provider_engine() -> None:
    class NotProviderEngine:
        pass

    factory = build_mcp_provider_runtime_factory(
        ROOT,
        execution_engine_factory=NotProviderEngine,  # type: ignore[arg-type]
    )
    try:
        factory()
    except TypeError as exc:
        assert "IProviderExecutionEngine" in str(exc)
    else:
        raise AssertionError("provider MCP factory must fail closed on a non-provider engine")


def test_provider_mcp_factory_rejects_empty_backing_adapter() -> None:
    try:
        build_mcp_provider_runtime_factory(
            ROOT,
            execution_engine_factory=McpProviderEngine,
            backing_adapter="   ",
        )
    except ValueError as exc:
        assert "backing_adapter" in str(exc)
    else:
        raise AssertionError("provider MCP factory must reject an empty backing adapter")


def test_provider_mcp_factory_rejects_non_callable_engine_factory() -> None:
    try:
        build_mcp_provider_runtime_factory(
            ROOT,
            execution_engine_factory=object(),  # type: ignore[arg-type]
        )
    except TypeError as exc:
        assert "execution_engine_factory" in str(exc)
    else:
        raise AssertionError("provider MCP factory must reject a non-callable engine factory")


def test_provider_mcp_factory_rejects_invalid_requirement_type() -> None:
    try:
        build_mcp_provider_runtime_factory(
            ROOT,
            execution_engine_factory=McpProviderEngine,
            provider_requirement=object(),  # type: ignore[arg-type]
        )
    except TypeError as exc:
        assert "provider_requirement" in str(exc)
    else:
        raise AssertionError("provider MCP factory must reject an invalid provider requirement")


def test_provider_mcp_stdio_rejects_empty_plugin_version(tmp_path: Path) -> None:
    (tmp_path / "plugin.json").write_text('{"version": ""}', encoding="utf-8")
    try:
        build_mcp_stdio_transport_with_provider_execution(
            tmp_path,
            execution_engine_factory=McpProviderEngine,
        )
    except ValueError as exc:
        assert "non-empty version" in str(exc)
    else:
        raise AssertionError("provider MCP stdio transport must require a plugin version")
