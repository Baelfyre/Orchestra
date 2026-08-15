from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .repositories import ManifestRepository, SkillSourceRepository

SPECIALIST_REGISTRY_SCHEMA_VERSION = "orchestra.specialist-registry.v1"
ROUTING_CONTRACT_SCHEMA_VERSION = "orchestra.routing-contract.v1"
GOVERNANCE_POLICY_SCHEMA_VERSION = "orchestra.governance-policy.v1"

_MACHINE_ROOT = Path("machine")
_SPECIALIST_REGISTRY = _MACHINE_ROOT / "specialists" / "registry.v1.json"
_ROUTING_CONTRACT = _MACHINE_ROOT / "routing" / "routes.v1.json"
_GOVERNANCE_POLICY = _MACHINE_ROOT / "governance" / "policy.v1.json"

FRONTMATTER_FIELDS = (
    "name",
    "description",
    "slug",
    "role",
    "primary_use",
    "avoid_when",
    "activation_level",
    "depends_on",
    "output_formats",
)


def repository_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _root(root: Path | str | None) -> Path:
    return repository_root() if root is None else Path(root)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"machine contract missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"machine contract is invalid JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"machine contract must be a JSON object: {path}")
    return value


def _frontmatter_list(value: str, *, none_is_empty: bool = False) -> list[str]:
    cleaned = str(value or "").strip()
    if none_is_empty and cleaned.lower() == "none":
        return []
    if cleaned.startswith("[") and cleaned.endswith("]"):
        cleaned = cleaned[1:-1]
    return [item.strip() for item in cleaned.split(",") if item.strip()]


def compile_specialist_registry(root: Path | str | None = None) -> dict[str, Any]:
    repo_root = _root(root)
    manifest = ManifestRepository(repo_root).load_manifest()
    source_repo = SkillSourceRepository(repo_root)
    specialists: list[dict[str, Any]] = []

    for manifest_skill in manifest.get("skills", []):
        slug = str(manifest_skill.get("slug", "")).strip()
        skill_path = str(manifest_skill.get("skill_path", "")).strip()
        if not slug or not skill_path:
            raise ValueError("plugin manifest contains a specialist without slug/skill_path")
        frontmatter = source_repo.parse_frontmatter(repo_root / skill_path)
        missing = [field for field in FRONTMATTER_FIELDS if field not in frontmatter]
        if missing:
            raise ValueError(f"{slug}: missing specialist frontmatter fields: {missing}")
        if frontmatter["slug"] != slug:
            raise ValueError(
                f"{slug}: frontmatter slug {frontmatter['slug']!r} does not match plugin manifest"
            )
        specialists.append(
            {
                "primary_use": frontmatter["primary_use"],
                "slug": slug,
                "description": frontmatter["description"],
                "avoid_when": frontmatter["avoid_when"],
                "skill_path": skill_path,
                "role": frontmatter["role"],
                "name": frontmatter["name"],
                "activation_level": frontmatter["activation_level"],
                "depends_on": _frontmatter_list(frontmatter["depends_on"], none_is_empty=True),
                "icon_path": str(manifest_skill.get("icon_path", "")).strip(),
                "output_formats": _frontmatter_list(frontmatter["output_formats"]),
            }
        )

    return {
        "schema_version": SPECIALIST_REGISTRY_SCHEMA_VERSION,
        "source_of_truth": "skills/*/SKILL.md#frontmatter",
        "generation_policy": "deterministic_frontmatter_compilation",
        "specialists": specialists,
    }


def load_specialist_registry(root: Path | str | None = None) -> dict[str, Any]:
    repo_root = _root(root)
    registry = _load_json(repo_root / _SPECIALIST_REGISTRY)
    if registry.get("schema_version") != SPECIALIST_REGISTRY_SCHEMA_VERSION:
        raise ValueError("unsupported specialist registry schema_version")
    return registry


def load_routing_contract(root: Path | str | None = None) -> dict[str, Any]:
    repo_root = _root(root)
    contract = _load_json(repo_root / _ROUTING_CONTRACT)
    if contract.get("schema_version") != ROUTING_CONTRACT_SCHEMA_VERSION:
        raise ValueError("unsupported routing contract schema_version")
    return contract


def load_governance_policy(root: Path | str | None = None) -> dict[str, Any]:
    repo_root = _root(root)
    policy = _load_json(repo_root / _GOVERNANCE_POLICY)
    if policy.get("schema_version") != GOVERNANCE_POLICY_SCHEMA_VERSION:
        raise ValueError("unsupported governance policy schema_version")
    return policy


def valid_specialist_ids(root: Path | str | None = None) -> frozenset[str]:
    registry = load_specialist_registry(root)
    values = [str(item.get("slug", "")).strip() for item in registry.get("specialists", [])]
    if not values or any(not value for value in values):
        raise ValueError("specialist registry contains an empty or missing slug")
    if len(values) != len(set(values)):
        raise ValueError("specialist registry contains duplicate slugs")
    return frozenset(values)


def machine_contract_errors(root: Path | str | None = None) -> tuple[str, ...]:
    repo_root = _root(root)
    errors: list[str] = []

    try:
        registry = load_specialist_registry(repo_root)
        compiled = compile_specialist_registry(repo_root)
        if registry != compiled:
            errors.append("SPECIALIST_REGISTRY_DRIFT")
    except (ValueError, OSError) as exc:
        return (f"SPECIALIST_REGISTRY_INVALID:{exc}",)

    specialist_ids = {item["slug"] for item in registry["specialists"]}
    manifest_ids = {
        str(item.get("slug", "")).strip()
        for item in ManifestRepository(repo_root).load_manifest().get("skills", [])
    }
    if specialist_ids != manifest_ids:
        errors.append("SPECIALIST_PLUGIN_SET_MISMATCH")

    try:
        routing = load_routing_contract(repo_root)
        for route in routing.get("direct_routes", []):
            target = route.get("target")
            via = route.get("via")
            if target not in specialist_ids:
                errors.append(f"ROUTE_UNKNOWN_SPECIALIST:{route.get('route_id')}:{target}")
            if via is not None and via not in specialist_ids:
                errors.append(f"ROUTE_UNKNOWN_VIA:{route.get('route_id')}:{via}")
            if target == "dagger" and route.get("explicit_authority_required") is not True:
                errors.append(f"DAGGER_ROUTE_MISSING_EXPLICIT_AUTHORITY:{route.get('route_id')}")

        for route in routing.get("ordered_sequences", []):
            for node in route.get("sequence", []):
                if node not in specialist_ids and node not in route.get("symbolic_nodes", []):
                    errors.append(f"SEQUENCE_UNKNOWN_SPECIALIST:{route.get('route_id')}:{node}")
        for alias, target in routing.get("legacy_aliases", {}).items():
            if target not in specialist_ids:
                errors.append(f"ALIAS_UNKNOWN_SPECIALIST:{alias}:{target}")
        if routing.get("ambiguity_fallback") not in specialist_ids:
            errors.append("AMBIGUITY_FALLBACK_UNKNOWN")
    except (ValueError, OSError) as exc:
        errors.append(f"ROUTING_CONTRACT_INVALID:{exc}")

    try:
        policy = load_governance_policy(repo_root)
        if set(policy.get("role_ownership", {})) - specialist_ids:
            errors.append("GOVERNANCE_OWNERSHIP_UNKNOWN_SPECIALIST")
        if set(policy.get("specialist_controls", {})) - specialist_ids:
            errors.append("GOVERNANCE_CONTROL_UNKNOWN_SPECIALIST")
        expected_precedence = [
            "STOP",
            "ESCALATE_HUMAN",
            "WAIT_FOR_CAPACITY",
            "WAIT_FOR_EVIDENCE",
            "AUTO_REMEDIATE_AND_REVALIDATE",
            "AUTO_CONTINUE",
        ]
        if policy.get("transition_precedence") != expected_precedence:
            errors.append("GOVERNANCE_PRECEDENCE_DRIFT")
        remediation = policy.get("default_remediation", {})
        if remediation.get("maximum_remediation_attempts_per_unit") != 3:
            errors.append("REMEDIATION_ATTEMPT_DEFAULT_DRIFT")
        if remediation.get("maximum_identical_failure_repetitions") != 2:
            errors.append("IDENTICAL_FAILURE_DEFAULT_DRIFT")
    except (ValueError, OSError) as exc:
        errors.append(f"GOVERNANCE_POLICY_INVALID:{exc}")

    return tuple(errors)


def assert_machine_contracts(root: Path | str | None = None) -> None:
    errors = machine_contract_errors(root)
    if errors:
        raise ValueError("machine contract validation failed: " + "; ".join(errors))
