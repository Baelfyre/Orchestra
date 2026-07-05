from __future__ import annotations

from .interfaces import IIDEAdapter
from .models import Command, ContextPackage
from .repositories import ManifestRepository


class BaseAdapter(IIDEAdapter):
    adapter_name = "base"
    default_command = "conductor"
    trigger_map: tuple[tuple[str, str], ...] = ()

    def __init__(self, manifest_repository: ManifestRepository):
        self._manifest_repository = manifest_repository

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
