from pathlib import Path

import pytest

from orchestra_runtime.factories import AdapterFactory
from orchestra_runtime.repositories import ManifestRepository, SkillSourceRepository
from orchestra_runtime.services import (
    ContextAssembler,
    GovernanceValidator,
    InMemoryAuditSink,
    RouterService,
    RuntimeExecutor,
    SkillRegistry,
    build_compatibility_composition,
)


def build_executor(repo_root: Path) -> RuntimeExecutor:
    manifest_repository = ManifestRepository(repo_root)
    skill_repository = SkillSourceRepository(repo_root)
    skill_registry = SkillRegistry(manifest_repository, skill_repository)
    composition = build_compatibility_composition(
        skill_registry,
        InMemoryAuditSink(),
        run_id="adapter-contract-compatibility",
    )
    return RuntimeExecutor(
        skill_registry,
        RouterService(skill_registry),
        GovernanceValidator(),
        ContextAssembler(manifest_repository),
        composition,
    )


@pytest.mark.parametrize(
    ("adapter_name", "prompt"),
    (
        ("codex", "@Orchestra review-docs"),
        ("antigravity", "/ponytail /conductor review docs"),
        ("claude-code", "Use Conductor for this task"),
        ("cursor", "@Orchestra review docs"),
        ("windsurf", "/conductor review docs"),
        ("vscode", "orchestra: review docs"),
        ("jetbrains", "Use Conductor to review docs"),
        ("zed", "@Orchestra review docs"),
        ("neovim", ":Orchestra review docs"),
    ),
)
def test_adapter_contracts(adapter_name: str, prompt: str):
    repo_root = Path(__file__).resolve().parents[2]
    executor = build_executor(repo_root)
    adapter = AdapterFactory.create(adapter_name, repo_root)

    context = adapter.provide_context(prompt)
    result = executor.execute(adapter, prompt)

    assert context.adapter_name == adapter_name
    assert context.available_commands
    assert "conductor" in context.available_commands
    assert result.adapter_name == adapter_name
    assert result.audit_entry_id
    assert result.output
    assert result.lifecycle_state == "COMPLETED"


@pytest.mark.parametrize(
    ("adapter_name", "prompt", "expected_command", "expected_adapter_name"),
    (
        ("cursor", "@Orchestra review docs", "conductor", "cursor"),
        ("windsurf", "/conductor review docs", "conductor", "windsurf"),
        ("vscode", "orchestra: review docs", "conductor", "vscode"),
        ("vscodium", "orchestra: review docs", "conductor", "vscode"),
        ("jetbrains", "Use Conductor to review docs", "conductor", "jetbrains"),
        ("zed", "@Orchestra review docs", "conductor", "zed"),
        ("neovim", ":Orchestra review docs", "conductor", "neovim"),
    ),
)
def test_new_adapter_command_translation(
    adapter_name: str,
    prompt: str,
    expected_command: str,
    expected_adapter_name: str,
):
    repo_root = Path(__file__).resolve().parents[2]
    adapter = AdapterFactory.create(adapter_name, repo_root)

    command = adapter.parse_command(prompt)

    assert command.adapter_name == expected_adapter_name
    assert command.name == expected_command


def test_parse_command_falls_back_to_default_command_for_unmatched_prompt():
    repo_root = Path(__file__).resolve().parents[2]
    adapter = AdapterFactory.create("codex", repo_root)

    command = adapter.parse_command("plain freeform request", metadata={"source": "test"})

    assert command.adapter_name == "codex"
    assert command.name == adapter.default_command
    assert command.metadata == {"source": "test"}


def test_context_assembler_preserves_adapter_provided_context_metadata():
    from orchestra_runtime.adapters import BaseAdapter
    from orchestra_runtime.models import ContextPackage

    class TestAdapter(BaseAdapter):
        def provide_context(self, prompt: str, metadata: dict | None = None) -> ContextPackage:
            context = super().provide_context(prompt, metadata)
            context.metadata["custom_flag"] = "present"
            return context

    repo_root = Path(__file__).resolve().parents[2]
    repository = ManifestRepository(repo_root)
    assembler = ContextAssembler(repository)
    adapter = TestAdapter(repository)

    context = assembler.assemble(adapter, "test prompt", {"caller_flag": "present"})

    assert context.metadata.get("custom_flag") == "present"
    assert context.metadata.get("caller_flag") == "present"
    assert "governance_validated" in context.metadata
    assert "destructive_validated" in context.metadata
    assert "dry_run" in context.metadata


@pytest.mark.parametrize("adapter_name", ("codex", "antigravity"))
def test_supported_adapters_envelope_integration(adapter_name: str):
    from orchestra_runtime.models import EnvelopeMessageType, OrchestraRuntimeEnvelope
    from orchestra_runtime.serialization import serialize_runtime_envelope

    repo_root = Path(__file__).resolve().parents[2]
    adapter = AdapterFactory.create(adapter_name, repo_root)

    # 1. Existing default output remains unchanged
    cmd = adapter.parse_command("review docs")
    assert cmd.name in ("conductor", "review-docs")

    # 2. Envelope formatting equals core serializer output
    env_res = OrchestraRuntimeEnvelope(
        schema_version="1.0.0",
        message_type=EnvelopeMessageType.EXECUTION_RESULT,
        timestamp="2026-08-03T08:00:00Z",
        run_id="run-adapter-1",
        specialist=adapter_name,
        operation="op_test",
        status="COMPLETED",
        reason_code="RC_OK",
        summary="Test summary",
    )
    formatted_bytes = adapter.format_envelope(env_res)
    assert formatted_bytes == serialize_runtime_envelope(env_res)

    # 3. Envelope parsing recovers identical typed object
    parsed_env = adapter.parse_envelope(formatted_bytes)
    assert parsed_env == env_res

    # 4. Absent correlation_id omitted, present correlation_id preserved
    from orchestra_runtime import generate_correlation_id
    valid_cid = generate_correlation_id()
    env_corr = OrchestraRuntimeEnvelope(
        schema_version="1.0.0",
        message_type=EnvelopeMessageType.TRANSITION_DECISION,
        timestamp="2026-08-03T08:00:00Z",
        run_id="run-adapter-2",
        specialist=adapter_name,
        operation="transition",
        disposition="AUTO_CONTINUE",
        reason_code="GOV_PASS",
        correlation_id=valid_cid,
    )
    corr_bytes = adapter.format_envelope(env_corr)
    parsed_corr = adapter.parse_envelope(corr_bytes)
    assert parsed_corr.correlation_id == valid_cid

    # 5. Invalid JSON / invalid envelope raises ValueError without fallback
    with pytest.raises(ValueError):
        adapter.parse_envelope(b"{invalid_json")


@pytest.mark.parametrize(
    "scaffold_adapter_name",
    ("claude-code", "cursor", "windsurf", "vscode", "jetbrains", "zed", "neovim"),
)
def test_scaffold_adapters_do_not_expose_envelope_capabilities(scaffold_adapter_name: str):
    from orchestra_runtime.adapters import RuntimeEnvelopeAdapterMixin

    repo_root = Path(__file__).resolve().parents[2]
    adapter = AdapterFactory.create(scaffold_adapter_name, repo_root)

    assert not isinstance(adapter, RuntimeEnvelopeAdapterMixin)
    assert not hasattr(adapter, "format_envelope")
    assert not hasattr(adapter, "parse_envelope")


@pytest.mark.parametrize(
    ("adapter_name", "expected_supported", "expected_mode"),
    (
        ("codex", True, "OPTIONAL"),
        ("antigravity", True, "OPTIONAL"),
        ("claude-code", False, "NONE"),
        ("cursor", False, "NONE"),
        ("windsurf", False, "NONE"),
        ("vscode", False, "NONE"),
        ("jetbrains", False, "NONE"),
        ("zed", False, "NONE"),
        ("neovim", False, "NONE"),
    ),
)
def test_adapter_worktree_capabilities(
    adapter_name: str, expected_supported: bool, expected_mode: str
):
    from orchestra_runtime.protocol import ProtocolValidator

    repo_root = Path(__file__).resolve().parents[2]
    adapter = AdapterFactory.create(adapter_name, repo_root)
    protocol = adapter.protocol_metadata()

    assert protocol.capabilities.worktree_supported == expected_supported
    assert protocol.capabilities.worktree_isolation_mode == expected_mode

    errors = ProtocolValidator.validate_protocol(protocol)
    assert not errors, f"Protocol validation failed: {errors}"
