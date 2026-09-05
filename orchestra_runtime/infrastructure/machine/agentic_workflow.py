from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from ...domain.adaptive import (
    PATTERN_ORDER,
    REQUIRED_COMPOSITION_INVARIANT_IDS,
    parse_authority_view,
)

AUTHORITY_VIEW_PATH = Path("machine/specialists/authority-view.v1.json")
PATTERNS_PATH = Path("machine/workflows/patterns.v1.json")
INVARIANTS_PATH = Path("machine/workflows/composition-invariants.v1.json")
SCHEMA_PATHS = (
    Path("machine/schemas/task-profile.v1.schema.json"),
    Path("machine/schemas/critic-contract.v1.schema.json"),
    Path("machine/schemas/specialist-authority-view.v1.schema.json"),
    Path("machine/schemas/agentic-workflow-profile.v1.schema.json"),
)


def repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"agentic workflow contract missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"agentic workflow contract is invalid JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"agentic workflow contract must be a JSON object: {path}")
    return value


def _git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    # Reconstruct canonical tracked text bytes instead of binding authority
    # identity to platform-specific Windows CRLF checkout materialization.
    canonical = data.replace(b"\\r\\n", b"\\n")
    header = f"blob {len(canonical)}\\0".encode("utf-8")
    return hashlib.sha1(header + canonical).hexdigest()


def load_agentic_workflow_authority_view(root: Path | str | None = None) -> dict[str, Any]:
    repo_root = repository_root() if root is None else Path(root)
    value = _load_json(repo_root / AUTHORITY_VIEW_PATH)
    authorities = parse_authority_view(value)
    for authority in authorities.values():
        source_path = repo_root / authority.source_path
        if _git_blob_sha(source_path) != authority.source_blob_sha:
            raise ValueError(f"authority view source binding is stale: {authority.slug}")
    return value


def load_agentic_pattern_contract(root: Path | str | None = None) -> dict[str, Any]:
    repo_root = repository_root() if root is None else Path(root)
    value = _load_json(repo_root / PATTERNS_PATH)
    if value.get("schema_version") != "orchestra.agentic-patterns.v1":
        raise ValueError("unsupported agentic pattern contract schema")
    if value.get("owner") != "conductor":
        raise ValueError("agentic pattern contract owner must be conductor")
    raw_patterns = value.get("patterns")
    if not isinstance(raw_patterns, list):
        raise TypeError("agentic pattern contract patterns must be a list")
    names = tuple(item.get("name") for item in raw_patterns if isinstance(item, Mapping))
    if names != PATTERN_ORDER:
        raise ValueError("agentic pattern order or set changed")
    if value.get("topology_change_requires_human_approval") is not False:
        raise ValueError("workflow topology change must not require a human gate inside granted authority")
    return value


def load_agentic_composition_invariants(root: Path | str | None = None) -> dict[str, Any]:
    repo_root = repository_root() if root is None else Path(root)
    value = _load_json(repo_root / INVARIANTS_PATH)
    if value.get("schema_version") != "orchestra.agentic-composition-invariants.v1":
        raise ValueError("unsupported agentic composition invariant schema")
    if value.get("owner") != "conductor":
        raise ValueError("agentic composition invariants owner must be conductor")
    raw = value.get("invariants")
    if not isinstance(raw, list):
        raise TypeError("agentic composition invariants must be a list")
    ids = tuple(item.get("id") for item in raw if isinstance(item, Mapping))
    if ids != REQUIRED_COMPOSITION_INVARIANT_IDS:
        raise ValueError("agentic composition invariant set changed")
    if any(item.get("hard") is not True for item in raw if isinstance(item, Mapping)):
        raise ValueError("all agentic composition invariants must be hard")
    if value.get("authority_expansion") is not False:
        raise ValueError("agentic composition contract cannot expand authority")
    if value.get("topology_change_requires_human_approval") is not False:
        raise ValueError("topology change human-gate semantics changed")
    return value


def load_agentic_workflow_contracts(root: Path | str | None = None) -> dict[str, Any]:
    repo_root = repository_root() if root is None else Path(root)
    for schema_path in SCHEMA_PATHS:
        _load_json(repo_root / schema_path)
    return {
        "authority_view": load_agentic_workflow_authority_view(repo_root),
        "patterns": load_agentic_pattern_contract(repo_root),
        "composition_invariants": load_agentic_composition_invariants(repo_root),
    }


def agentic_workflow_errors(root: Path | str | None = None) -> tuple[str, ...]:
    try:
        load_agentic_workflow_contracts(root)
    except (ValueError, TypeError, OSError) as exc:
        return (f"AGENTIC_WORKFLOW_CONTRACT_INVALID:{exc}",)
    return ()


__all__ = [
    "AUTHORITY_VIEW_PATH",
    "INVARIANTS_PATH",
    "PATTERNS_PATH",
    "SCHEMA_PATHS",
    "agentic_workflow_errors",
    "load_agentic_composition_invariants",
    "load_agentic_pattern_contract",
    "load_agentic_workflow_authority_view",
    "load_agentic_workflow_contracts",
]
