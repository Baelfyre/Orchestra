from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .domain.orchestration.execution_efficiency import validate_execution_budget

EXECUTION_BUDGET_PATH = Path("machine/governance/execution-budget.v1.json")


def repository_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_execution_budget_contract(root: Path | str | None = None) -> dict[str, Any]:
    repo_root = repository_root() if root is None else Path(root)
    path = repo_root / EXECUTION_BUDGET_PATH
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"execution budget contract missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"execution budget contract is invalid JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"execution budget contract must be a JSON object: {path}")
    validate_execution_budget(value)
    return value


def execution_budget_errors(root: Path | str | None = None) -> tuple[str, ...]:
    try:
        load_execution_budget_contract(root)
    except (ValueError, OSError) as exc:
        return (f"EXECUTION_BUDGET_CONTRACT_INVALID:{exc}",)
    return ()


__all__ = [
    "EXECUTION_BUDGET_PATH",
    "execution_budget_errors",
    "load_execution_budget_contract",
]
