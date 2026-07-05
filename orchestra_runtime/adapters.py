from __future__ import annotations

from .interfaces import IIDEAdapter
from .models import Command, ContextPackage
from .protocol import AdapterCapabilities, AdapterProtocol, PRAP_V1
from .repositories import ManifestRepository


class BaseAdapter(IIDEAdapter):
    adapter_name = "base"
    display_name = "Base Adapter"
    runtime_adapter_name = "base"
    host_type = "unknown"
    packaging_status = "internal"
    marketplace_status = "n/a"
    aliases: tuple[str, ...] = ()
    default_command = "conductor"
    trigger_map: tuple[tuple[str, str], ...] = ()
    capabilities = AdapterCapabilities(
        supports_commands=True,
        supports_context=True,
        supports_file_handoff=True,
        supports_workspace=True,
        supports_audit_trace=True,
        supports_streaming=False,
        supports_governance=True,
    )

    def __init__(self, manifest_repository: ManifestRepository):
        self._manifest_repository = manifest_repository

    def protocol_metadata(self) -> AdapterProtocol:
        return AdapterProtocol(
            adapter_id=self.adapter_name,
            display_name=self.display_name,
            runtime_adapter=self.runtime_adapter_name,
            host_type=self.host_type,
            protocol_version=PRAP_V1,
            packaging_status=self.packaging_status,
            marketplace_status=self.marketplace_status,
            capabilities=self.capabilities,
            aliases=self.aliases,
        )

    def provide_context(self, prompt: str, metadata: dict | None = None) -> ContextPackage:
        manifest = self._manifest_repository.load_manifest()
        return ContextPackage(
            adapter_name=self.adapter_name,
            prompt=prompt,
            project_root=self._manifest_repository.repo_root,
            available_commands=self.expose_commands(),
            manifest_version=str(manifest.get("version", "")),
            metadata=dict(metadata or {}),
        )

    def expose_commands(self) -> tuple[str, ...]:
        return self._manifest_repository.load_commands()

    def parse_command(self, prompt: str, metadata: dict | None = None) -> Command:
        lowered = prompt.lower()
        for trigger, command_name in self.trigger_map:
            if trigger.lower() in lowered:
                return Command(
                    name=command_name,
                    raw_input=prompt,
                    adapter_name=self.adapter_name,
                    metadata=dict(metadata or {}),
                )
        return Command(
            name=self.default_command,
            raw_input=prompt,
            adapter_name=self.adapter_name,
            metadata=dict(metadata or {}),
        )


class CodexAdapter(BaseAdapter):
    adapter_name = "codex"
    display_name = "Codex"
    runtime_adapter_name = "codex"
    host_type = "ai-assistant"
    packaging_status = "marketplace"
    marketplace_status = "available"
    trigger_map = (
        ("@orchestra", "conductor"),
        ("@conductor", "conductor"),
        ("review-architecture", "review-architecture"),
        ("review-ui", "review-ui"),
        ("review-db", "review-db"),
        ("review-docs", "review-docs"),
        ("diagram-check", "diagram-check"),
        ("qa-check", "qa-check"),
        ("security-check", "security-check"),
        ("resilience-check", "resilience-check"),
    )


class AntigravityAdapter(BaseAdapter):
    adapter_name = "antigravity"
    display_name = "Antigravity"
    runtime_adapter_name = "antigravity"
    host_type = "ai-assistant"
    packaging_status = "plugin"
    marketplace_status = "available"
    trigger_map = (
        ("/ponytail /conductor", "conductor"),
        ("/conductor", "conductor"),
        ("/review-architecture", "review-architecture"),
        ("/review-ui", "review-ui"),
        ("/review-db", "review-db"),
        ("/review-docs", "review-docs"),
        ("/diagram-check", "diagram-check"),
        ("/qa-check", "qa-check"),
        ("/security-check", "security-check"),
        ("/resilience-check", "resilience-check"),
    )


class ClaudeCodeAdapter(BaseAdapter):
    adapter_name = "claude-code"
    display_name = "Claude Code"
    runtime_adapter_name = "claude-code"
    host_type = "ai-assistant"
    packaging_status = "marketplace"
    marketplace_status = "available"
    aliases = ("claude",)
    trigger_map = (
        ("use conductor", "conductor"),
        ("conductor", "conductor"),
        ("review architecture", "review-architecture"),
        ("review ui", "review-ui"),
        ("review db", "review-db"),
        ("review docs", "review-docs"),
        ("diagram check", "diagram-check"),
        ("qa check", "qa-check"),
        ("security check", "security-check"),
        ("resilience check", "resilience-check"),
    )


class CursorAdapter(BaseAdapter):
    adapter_name = "cursor"
    display_name = "Cursor"
    runtime_adapter_name = "cursor"
    host_type = "ide"
    packaging_status = "scaffold-only"
    marketplace_status = "deferred"
    trigger_map = (
        ("@orchestra", "conductor"),
        ("use conductor", "conductor"),
        ("review architecture", "review-architecture"),
        ("review ui", "review-ui"),
        ("review db", "review-db"),
        ("review docs", "review-docs"),
        ("diagram check", "diagram-check"),
        ("qa check", "qa-check"),
        ("security check", "security-check"),
        ("resilience check", "resilience-check"),
    )


class WindsurfAdapter(BaseAdapter):
    adapter_name = "windsurf"
    display_name = "Windsurf"
    runtime_adapter_name = "windsurf"
    host_type = "ide"
    packaging_status = "scaffold-only"
    marketplace_status = "deferred"
    trigger_map = (
        ("@orchestra", "conductor"),
        ("use conductor", "conductor"),
        ("/conductor", "conductor"),
        ("review architecture", "review-architecture"),
        ("review ui", "review-ui"),
        ("review db", "review-db"),
        ("review docs", "review-docs"),
        ("diagram check", "diagram-check"),
        ("qa check", "qa-check"),
        ("security check", "security-check"),
        ("resilience check", "resilience-check"),
    )


class VSCodeAdapter(BaseAdapter):
    adapter_name = "vscode"
    display_name = "VS Code"
    runtime_adapter_name = "vscode"
    host_type = "ide"
    packaging_status = "scaffold-only"
    marketplace_status = "deferred"
    aliases = ("vs-code", "vs_code", "vscodium")
    trigger_map = (
        ("@orchestra", "conductor"),
        ("orchestra:", "conductor"),
        ("review architecture", "review-architecture"),
        ("review ui", "review-ui"),
        ("review db", "review-db"),
        ("review docs", "review-docs"),
        ("diagram check", "diagram-check"),
        ("qa check", "qa-check"),
        ("security check", "security-check"),
        ("resilience check", "resilience-check"),
    )


class JetBrainsAdapter(BaseAdapter):
    adapter_name = "jetbrains"
    display_name = "JetBrains"
    runtime_adapter_name = "jetbrains"
    host_type = "ide"
    packaging_status = "scaffold-only"
    marketplace_status = "deferred"
    aliases = ("intellij",)
    trigger_map = (
        ("@orchestra", "conductor"),
        ("use conductor", "conductor"),
        ("review architecture", "review-architecture"),
        ("review ui", "review-ui"),
        ("review db", "review-db"),
        ("review docs", "review-docs"),
        ("diagram check", "diagram-check"),
        ("qa check", "qa-check"),
        ("security check", "security-check"),
        ("resilience check", "resilience-check"),
    )


class ZedAdapter(BaseAdapter):
    adapter_name = "zed"
    display_name = "Zed"
    runtime_adapter_name = "zed"
    host_type = "editor"
    packaging_status = "scaffold-only"
    marketplace_status = "deferred"
    trigger_map = (
        ("@orchestra", "conductor"),
        ("use conductor", "conductor"),
        ("review architecture", "review-architecture"),
        ("review ui", "review-ui"),
        ("review db", "review-db"),
        ("review docs", "review-docs"),
        ("diagram check", "diagram-check"),
        ("qa check", "qa-check"),
        ("security check", "security-check"),
        ("resilience check", "resilience-check"),
    )


class NeovimAdapter(BaseAdapter):
    adapter_name = "neovim"
    display_name = "Neovim"
    runtime_adapter_name = "neovim"
    host_type = "editor"
    packaging_status = "scaffold-only"
    marketplace_status = "deferred"
    aliases = ("nvim",)
    trigger_map = (
        ("orchestra ", "conductor"),
        (":orchestra", "conductor"),
        ("review architecture", "review-architecture"),
        ("review ui", "review-ui"),
        ("review db", "review-db"),
        ("review docs", "review-docs"),
        ("diagram check", "diagram-check"),
        ("qa check", "qa-check"),
        ("security check", "security-check"),
        ("resilience check", "resilience-check"),
    )
