from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Skill:
    slug: str
    name: str
    description: str
    skill_path: Path
    role: str = ""
    activation_level: str = ""
    depends_on: str = ""
    commands: tuple[str, ...] = ()
    output_formats: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Command:
    name: str
    raw_input: str
    adapter_name: str
    arguments: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ContextPackage:
    adapter_name: str
    prompt: str
    project_root: Path
    available_commands: tuple[str, ...]
    manifest_version: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RouteDecision:
    command_name: str
    skill_slug: str
    governance_required: bool
    reason: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GovernanceRule:
    name: str
    description: str
    skill_slugs: tuple[str, ...] = ()
    command_names: tuple[str, ...] = ()
    validator_key: str = ""
    blocking: bool = True


@dataclass(frozen=True)
class ValidationResult:
    allowed: bool
    status: str
    reasons: tuple[str, ...] = ()
    evaluated_rules: tuple[str, ...] = ()


@dataclass(frozen=True)
class ExecutionResult:
    success: bool
    adapter_name: str
    command_name: str
    route: RouteDecision
    validation: ValidationResult
    output: str
    audit_entry_id: str
