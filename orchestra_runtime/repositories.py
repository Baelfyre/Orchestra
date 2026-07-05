from __future__ import annotations

import json
import re
from pathlib import Path


FRONTMATTER_PATTERN = re.compile(r"(?s)^---\r?\n(.*?)\r?\n---")


class ManifestRepository:
    def __init__(self, repo_root: Path | str):
        self.repo_root = Path(repo_root)

    @property
    def manifest_path(self) -> Path:
        return self.repo_root / "plugin.json"

    @property
    def aliases_path(self) -> Path:
        return self.repo_root / "aliases.json"

    def load_manifest(self) -> dict:
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def load_aliases(self) -> dict[str, str]:
        if not self.aliases_path.is_file():
            return {}
        return json.loads(self.aliases_path.read_text(encoding="utf-8"))

    def load_commands(self) -> tuple[str, ...]:
        manifest = self.load_manifest()
        return tuple(manifest.get("commands", []))


class SkillSourceRepository:
    def __init__(self, repo_root: Path | str):
        self.repo_root = Path(repo_root)

    @property
    def skills_root(self) -> Path:
        return self.repo_root / "skills"

    @staticmethod
    def parse_frontmatter(path: Path | str) -> dict[str, str]:
        file_path = Path(path)
        content = file_path.read_text(encoding="utf-8")
        match = FRONTMATTER_PATTERN.search(content)
        if not match:
            raise ValueError(f"Frontmatter not found in file: {file_path}")
        fields: dict[str, str] = {}
        for line in match.group(1).splitlines():
            frontmatter_match = re.match(r"^([^:]+):\s*(.*)$", line)
            if frontmatter_match:
                fields[frontmatter_match.group(1).strip()] = frontmatter_match.group(2).strip()
        return fields

    def get_skill_path(self, slug: str) -> Path:
        return self.skills_root / slug / "SKILL.md"
