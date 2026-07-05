from __future__ import annotations

from pathlib import Path

from .adapters import AntigravityAdapter, ClaudeCodeAdapter, CodexAdapter
from .models import Skill
from .repositories import ManifestRepository


class SkillFactory:
    @staticmethod
    def create(
        manifest_entry: dict,
        frontmatter: dict[str, str],
        skill_path: Path,
        commands: tuple[str, ...],
    ) -> Skill:
        output_formats = tuple(
            item.strip()
            for item in str(frontmatter.get("output_formats", "")).strip("[]").split(",")
            if item.strip()
        )
        metadata = {
            "icon_path": manifest_entry.get("icon_path", ""),
            "primary_use": frontmatter.get("primary_use", manifest_entry.get("primary_use", "")),
            "avoid_when": frontmatter.get("avoid_when", manifest_entry.get("avoid_when", "")),
        }
        return Skill(
            slug=manifest_entry.get("slug", ""),
            name=frontmatter.get("name", manifest_entry.get("name", "")),
            description=frontmatter.get("description", manifest_entry.get("description", "")),
            skill_path=skill_path,
            role=frontmatter.get("role", manifest_entry.get("role", "")),
            activation_level=frontmatter.get("activation_level", manifest_entry.get("activation_level", "")),
            depends_on=frontmatter.get("depends_on", manifest_entry.get("depends_on", "")),
            commands=commands,
            output_formats=output_formats,
            metadata=metadata,
        )


class AdapterFactory:
    @staticmethod
    def create(adapter_name: str, repo_root: Path | str):
        manifest_repository = ManifestRepository(repo_root)
        normalized = adapter_name.lower()
        if normalized == "codex":
            return CodexAdapter(manifest_repository)
        if normalized == "antigravity":
            return AntigravityAdapter(manifest_repository)
        if normalized in {"claude", "claude-code"}:
            return ClaudeCodeAdapter(manifest_repository)
        raise ValueError(f"Unsupported adapter: {adapter_name}")
