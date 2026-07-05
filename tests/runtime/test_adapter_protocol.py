from pathlib import Path

import pytest

from orchestra_runtime.adapters import VSCodeAdapter
from orchestra_runtime.factories import AdapterFactory
from orchestra_runtime.protocol import (
    COMPATIBILITY_MATRIX,
    PRAP_V1,
    AdapterCapabilities,
    AdapterError,
    AdapterProtocol,
    ProtocolValidator,
)


def test_all_runtime_adapters_declare_prap_metadata():
    repo_root = Path(__file__).resolve().parents[2]

    for adapter in AdapterFactory.create_all(repo_root):
        errors = ProtocolValidator.validate_adapter(adapter)
        assert errors == []
        metadata = adapter.protocol_metadata().to_metadata()
        assert metadata["protocol_version"] == PRAP_V1
        assert metadata["runtime_adapter"] == adapter.adapter_name


def test_capability_validation_rejects_non_boolean_metadata():
    protocol = AdapterProtocol(
        adapter_id="broken",
        display_name="Broken",
        runtime_adapter="broken",
        host_type="ide",
        protocol_version=PRAP_V1,
        packaging_status="scaffold-only",
        marketplace_status="deferred",
        capabilities=AdapterCapabilities(
            supports_commands=True,
            supports_context=True,
            supports_file_handoff="yes",  # type: ignore[arg-type]
            supports_workspace=True,
            supports_audit_trace=True,
            supports_streaming=False,
            supports_governance=True,
        ),
    )

    errors = ProtocolValidator.validate_protocol(protocol)

    assert any("Capability metadata must be boolean" in error for error in errors)


def test_compatibility_matrix_covers_known_hosts_and_versions():
    adapter_ids = {record.adapter_id for record in COMPATIBILITY_MATRIX}

    assert {
        "codex",
        "claude-code",
        "antigravity",
        "cursor",
        "windsurf",
        "vscode",
        "vscodium",
        "jetbrains",
        "zed",
        "neovim",
        "future",
        "unknown",
    }.issubset(adapter_ids)

    for record in COMPATIBILITY_MATRIX:
        assert record.protocol_version == PRAP_V1


def test_vscodium_is_supported_via_vscode_runtime_adapter():
    repo_root = Path(__file__).resolve().parents[2]

    adapter = AdapterFactory.create("vscodium", repo_root)
    record = ProtocolValidator.ensure_supported("vscodium")

    assert isinstance(adapter, VSCodeAdapter)
    assert adapter.protocol_metadata().runtime_adapter == "vscode"
    assert record.runtime_adapter == "vscode"
    assert record.compatibility_status == "compatible"


def test_unknown_adapter_is_rejected():
    with pytest.raises(AdapterError):
        ProtocolValidator.ensure_supported("unknown")

    with pytest.raises(ValueError):
        AdapterFactory.create("totally-unknown", Path(__file__).resolve().parents[2])
