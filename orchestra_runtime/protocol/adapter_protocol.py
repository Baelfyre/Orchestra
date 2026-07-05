from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


PRAP_V1 = "PRAP v1"
SUPPORTED_PROTOCOL_VERSIONS = (PRAP_V1,)
REQUIRED_METADATA_FIELDS = (
    "adapter_id",
    "display_name",
    "runtime_adapter",
    "host_type",
    "protocol_version",
    "supports_commands",
    "supports_context",
    "supports_file_handoff",
    "supports_workspace",
    "supports_audit_trace",
    "supports_streaming",
    "supports_governance",
    "packaging_status",
    "marketplace_status",
)


@dataclass(frozen=True)
class AdapterCapabilities:
    supports_commands: bool
    supports_context: bool
    supports_file_handoff: bool
    supports_workspace: bool
    supports_audit_trace: bool
    supports_streaming: bool
    supports_governance: bool

    def to_metadata(self) -> dict[str, bool]:
        return {
            "supports_commands": self.supports_commands,
            "supports_context": self.supports_context,
            "supports_file_handoff": self.supports_file_handoff,
            "supports_workspace": self.supports_workspace,
            "supports_audit_trace": self.supports_audit_trace,
            "supports_streaming": self.supports_streaming,
            "supports_governance": self.supports_governance,
        }


@dataclass(frozen=True)
class AdapterProtocol:
    adapter_id: str
    display_name: str
    runtime_adapter: str
    host_type: str
    protocol_version: str
    packaging_status: str
    marketplace_status: str
    capabilities: AdapterCapabilities
    aliases: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_metadata(self) -> dict[str, Any]:
        payload = {
            "adapter_id": self.adapter_id,
            "display_name": self.display_name,
            "runtime_adapter": self.runtime_adapter,
            "host_type": self.host_type,
            "protocol_version": self.protocol_version,
            "packaging_status": self.packaging_status,
            "marketplace_status": self.marketplace_status,
            **self.capabilities.to_metadata(),
        }
        if self.aliases:
            payload["aliases"] = self.aliases
        if self.metadata:
            payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True)
class AdapterContext:
    adapter_id: str
    host_type: str
    protocol_version: str
    workspace_root: Path | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AdapterResponse:
    adapter_id: str
    protocol_version: str
    success: bool
    payload: dict[str, Any] = field(default_factory=dict)
    errors: tuple[str, ...] = ()


class AdapterError(ValueError):
    pass


@dataclass(frozen=True)
class AdapterCompatibilityRecord:
    adapter_id: str
    display_name: str
    runtime_adapter: str
    host_type: str
    protocol_version: str
    packaging_status: str
    marketplace_status: str
    compatibility_status: str
    notes: str = ""


COMPATIBILITY_MATRIX: tuple[AdapterCompatibilityRecord, ...] = (
    AdapterCompatibilityRecord(
        adapter_id="codex",
        display_name="Codex",
        runtime_adapter="codex",
        host_type="ai-assistant",
        protocol_version=PRAP_V1,
        packaging_status="marketplace",
        marketplace_status="available",
        compatibility_status="supported",
        notes="Primary Marketplace-backed adapter.",
    ),
    AdapterCompatibilityRecord(
        adapter_id="claude-code",
        display_name="Claude Code",
        runtime_adapter="claude-code",
        host_type="ai-assistant",
        protocol_version=PRAP_V1,
        packaging_status="marketplace",
        marketplace_status="available",
        compatibility_status="supported",
        notes="Plugin metadata remains separate from runtime logic.",
    ),
    AdapterCompatibilityRecord(
        adapter_id="antigravity",
        display_name="Antigravity",
        runtime_adapter="antigravity",
        host_type="ai-assistant",
        protocol_version=PRAP_V1,
        packaging_status="plugin",
        marketplace_status="available",
        compatibility_status="supported",
        notes="Plugin install remains host-native.",
    ),
    AdapterCompatibilityRecord(
        adapter_id="cursor",
        display_name="Cursor",
        runtime_adapter="cursor",
        host_type="ide",
        protocol_version=PRAP_V1,
        packaging_status="scaffold-only",
        marketplace_status="deferred",
        compatibility_status="supported",
        notes="Packaging scaffold points to shared runtime adapter.",
    ),
    AdapterCompatibilityRecord(
        adapter_id="windsurf",
        display_name="Windsurf",
        runtime_adapter="windsurf",
        host_type="ide",
        protocol_version=PRAP_V1,
        packaging_status="scaffold-only",
        marketplace_status="deferred",
        compatibility_status="supported",
        notes="Packaging scaffold points to shared runtime adapter.",
    ),
    AdapterCompatibilityRecord(
        adapter_id="vscode",
        display_name="VS Code",
        runtime_adapter="vscode",
        host_type="ide",
        protocol_version=PRAP_V1,
        packaging_status="scaffold-only",
        marketplace_status="deferred",
        compatibility_status="supported",
        notes="Canonical adapter for VS Code-family packaging.",
    ),
    AdapterCompatibilityRecord(
        adapter_id="vscodium",
        display_name="VSCodium",
        runtime_adapter="vscode",
        host_type="ide",
        protocol_version=PRAP_V1,
        packaging_status="shared-vscode-scaffold",
        marketplace_status="deferred",
        compatibility_status="compatible",
        notes="Uses the VS Code runtime adapter and packaging metadata.",
    ),
    AdapterCompatibilityRecord(
        adapter_id="jetbrains",
        display_name="JetBrains",
        runtime_adapter="jetbrains",
        host_type="ide",
        protocol_version=PRAP_V1,
        packaging_status="scaffold-only",
        marketplace_status="deferred",
        compatibility_status="supported",
        notes="Plugin scaffold only. Marketplace publication remains deferred.",
    ),
    AdapterCompatibilityRecord(
        adapter_id="zed",
        display_name="Zed",
        runtime_adapter="zed",
        host_type="editor",
        protocol_version=PRAP_V1,
        packaging_status="scaffold-only",
        marketplace_status="deferred",
        compatibility_status="supported",
        notes="Scaffold metadata references the shared runtime adapter.",
    ),
    AdapterCompatibilityRecord(
        adapter_id="neovim",
        display_name="Neovim",
        runtime_adapter="neovim",
        host_type="editor",
        protocol_version=PRAP_V1,
        packaging_status="scaffold-only",
        marketplace_status="deferred",
        compatibility_status="supported",
        notes="Scaffold metadata references the shared runtime adapter.",
    ),
    AdapterCompatibilityRecord(
        adapter_id="future",
        display_name="Future Adapter",
        runtime_adapter="future",
        host_type="unknown",
        protocol_version=PRAP_V1,
        packaging_status="external",
        marketplace_status="n/a",
        compatibility_status="reserved",
        notes="Third-party integrations should target PRAP metadata and validation rules.",
    ),
    AdapterCompatibilityRecord(
        adapter_id="unknown",
        display_name="Unknown Adapter",
        runtime_adapter="unknown",
        host_type="unknown",
        protocol_version=PRAP_V1,
        packaging_status="unregistered",
        marketplace_status="n/a",
        compatibility_status="rejected",
        notes="Unknown adapters are rejected until they declare PRAP-compatible metadata.",
    ),
)


class ProtocolValidator:
    @classmethod
    def validate_protocol(cls, protocol: AdapterProtocol) -> list[str]:
        errors: list[str] = []
        metadata = protocol.to_metadata()
        for field_name in REQUIRED_METADATA_FIELDS:
            value = metadata.get(field_name)
            if value in (None, ""):
                errors.append(f"Missing protocol metadata field: {field_name}")

        if protocol.protocol_version not in SUPPORTED_PROTOCOL_VERSIONS:
            errors.append(f"Unsupported protocol version: {protocol.protocol_version}")

        capability_values = protocol.capabilities.to_metadata()
        missing_capabilities = [
            field_name
            for field_name, value in capability_values.items()
            if not isinstance(value, bool)
        ]
        if missing_capabilities:
            errors.append(
                "Capability metadata must be boolean for: " + ", ".join(sorted(missing_capabilities))
            )

        if protocol.runtime_adapter != protocol.runtime_adapter.lower():
            errors.append("runtime_adapter must be lowercase.")

        if protocol.adapter_id != protocol.adapter_id.lower():
            errors.append("adapter_id must be lowercase.")

        return errors

    @classmethod
    def validate_adapter(cls, adapter: Any) -> list[str]:
        protocol_getter = getattr(adapter, "protocol_metadata", None)
        if not callable(protocol_getter):
            return ["Adapter does not implement protocol_metadata()."]
        return cls.validate_protocol(protocol_getter())

    @classmethod
    def validate_packaging_manifest(cls, adapter_name: str, orchestra_block: dict[str, Any], repo_root: Path) -> list[str]:
        errors: list[str] = []
        try:
            from orchestra_runtime.factories import AdapterFactory
        except ImportError:
            return ["Unable to import AdapterFactory for packaging validation."]

        try:
            adapter = AdapterFactory.create(adapter_name, repo_root)
        except ValueError as exc:
            return [f"AdapterFactory cannot build '{adapter_name}': {exc}"]

        protocol = adapter.protocol_metadata()
        errors.extend(cls.validate_protocol(protocol))

        runtime_adapter = orchestra_block.get("runtime_adapter")
        if runtime_adapter != protocol.runtime_adapter:
            errors.append(
                f"Packaging runtime_adapter mismatch for {adapter_name}: "
                f"{runtime_adapter} != {protocol.runtime_adapter}"
            )

        host = orchestra_block.get("host")
        if host != protocol.runtime_adapter:
            errors.append(f"Packaging host mismatch for {adapter_name}: {host} != {protocol.runtime_adapter}")

        return errors

    @classmethod
    def compatibility_for(cls, adapter_name: str) -> AdapterCompatibilityRecord:
        normalized = adapter_name.lower()
        for record in COMPATIBILITY_MATRIX:
            if record.adapter_id == normalized:
                return record
        raise AdapterError(f"Unknown adapter: {adapter_name}")

    @classmethod
    def ensure_supported(cls, adapter_name: str) -> AdapterCompatibilityRecord:
        record = cls.compatibility_for(adapter_name)
        if record.compatibility_status == "rejected":
            raise AdapterError(f"Adapter '{adapter_name}' is not PRAP-compatible.")
        return record
