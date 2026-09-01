#!/usr/bin/env python3
"""Validate Orchestra runtime placement and dependency boundaries.

The validator intentionally grandfathers the explicitly enumerated legacy flat
runtime modules while failing closed on new unbounded top-level modules. New
code placed under canonical architectural roots is checked for dependency
inversion, persistence-object placement, resource placement, and compatibility
facade integrity.
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY = REPO_ROOT / "machine" / "architecture" / "runtime-boundaries.v1.json"
FACADE_MARKER = "ARCHITECTURE_COMPATIBILITY_FACADE"


def _starts_with_module(module: str, prefix: str) -> bool:
    return module == prefix or module.startswith(prefix + ".")


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def load_policy(policy_path: Path) -> dict:
    data = json.loads(policy_path.read_text(encoding="utf-8"))
    required = {
        "schema_version",
        "runtime_root",
        "canonical_roots",
        "legacy_package_roots",
        "legacy_top_level_modules",
        "layers",
        "placement",
        "compatibility_facades",
        "rules",
    }
    missing = sorted(required.difference(data))
    if missing:
        raise ValueError(f"architecture policy missing required keys: {', '.join(missing)}")
    if data["schema_version"] != "orchestra.runtime-architecture-boundaries.v1":
        raise ValueError(f"unsupported architecture policy schema: {data['schema_version']!r}")
    return data


def _module_parts(path: Path, runtime_root: Path) -> list[str]:
    relative = path.relative_to(runtime_root).with_suffix("")
    parts = [runtime_root.name, *relative.parts]
    if parts[-1] == "__init__":
        parts.pop()
    return parts


def _resolve_from_import(path: Path, runtime_root: Path, node: ast.ImportFrom) -> str:
    if node.level == 0:
        return node.module or ""

    module_parts = _module_parts(path, runtime_root)
    package_parts = module_parts if path.name == "__init__.py" else module_parts[:-1]
    ascend = node.level - 1
    if ascend > len(package_parts):
        return node.module or ""
    base = package_parts[: len(package_parts) - ascend]
    if node.module:
        base.extend(node.module.split("."))
    return ".".join(base)


def imported_modules(path: Path, runtime_root: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = _resolve_from_import(path, runtime_root, node)
            if module:
                imports.append(module)
    return tuple(imports)


def _iter_python(root: Path) -> Iterable[Path]:
    if not root.exists():
        return ()
    return sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)


def validate_top_level_placement(runtime_root: Path, policy: dict) -> list[str]:
    violations: list[str] = []
    allowed_dirs = set(policy["canonical_roots"]) | set(policy["legacy_package_roots"])
    allowed_modules = set(policy["legacy_top_level_modules"])

    for child in sorted(runtime_root.iterdir()):
        if child.name == "__pycache__":
            continue
        if child.is_dir() and child.name not in allowed_dirs:
            violations.append(
                f"PLACEMENT_UNBOUNDED_ROOT: {child.relative_to(runtime_root.parent)} is not an approved runtime root"
            )
        elif child.is_file() and child.suffix == ".py" and child.name not in allowed_modules:
            violations.append(
                f"PLACEMENT_NEW_FLAT_MODULE: {child.relative_to(runtime_root.parent)} must be placed in a canonical layer"
            )
    return violations


def validate_internal_boundary(runtime_root: Path) -> list[str]:
    violations: list[str] = []
    for path in _iter_python(runtime_root):
        for module in imported_modules(path, runtime_root):
            if _starts_with_module(module, "internal"):
                violations.append(
                    f"INTERNAL_RUNTIME_DEPENDENCY: {path.relative_to(runtime_root.parent)} imports {module}"
                )
    return violations


def validate_layer_dependencies(runtime_root: Path, policy: dict) -> list[str]:
    violations: list[str] = []
    for layer, rules in policy["layers"].items():
        layer_root = runtime_root / layer
        for path in _iter_python(layer_root):
            modules = imported_modules(path, runtime_root)
            for module in modules:
                for prefix in rules.get("forbidden_import_prefixes", []):
                    if _starts_with_module(module, prefix):
                        violations.append(
                            f"DEPENDENCY_DIRECTION: {path.relative_to(runtime_root.parent)} imports forbidden {module}"
                        )
                for prefix in rules.get("forbidden_stdlib_prefixes", []):
                    if _starts_with_module(module, prefix):
                        violations.append(
                            f"DOMAIN_EXTERNAL_IO: {path.relative_to(runtime_root.parent)} imports forbidden {module}"
                        )
    return violations


def validate_facades(repo_root: Path, runtime_root: Path, policy: dict) -> list[str]:
    violations: list[str] = []
    for relative_name, target_prefix in policy["compatibility_facades"].items():
        path = repo_root / relative_name
        if not path.is_file():
            violations.append(f"FACADE_MISSING: {relative_name}")
            continue
        text = path.read_text(encoding="utf-8")
        if FACADE_MARKER not in text:
            violations.append(f"FACADE_MARKER_MISSING: {relative_name}")
        tree = ast.parse(text, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
                violations.append(f"FACADE_BEHAVIOR_DEFINED: {relative_name} defines executable behavior")
                break
        for module in imported_modules(path, runtime_root):
            if module == "__future__":
                continue
            if not _starts_with_module(module, target_prefix):
                violations.append(
                    f"FACADE_WRONG_TARGET: {relative_name} imports {module}; expected {target_prefix}"
                )
    return violations


def validate_special_object_placement(repo_root: Path, runtime_root: Path, policy: dict) -> list[str]:
    violations: list[str] = []
    placement = policy["placement"]
    dto_root = repo_root / placement["dto_root"]
    dpo_root = repo_root / placement["dpo_root"]
    repository_port_root = repo_root / placement["repository_port_root"]
    repository_impl_root = repo_root / placement["repository_implementation_root"]

    canonical_paths: list[Path] = []
    for root_name in policy["canonical_roots"]:
        canonical_paths.extend(_iter_python(runtime_root / root_name))

    for path in sorted(set(canonical_paths)):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        lower_name = path.name.lower()
        if lower_name.endswith("_dto.py") and not _is_relative_to(path, dto_root):
            violations.append(f"DTO_WRONG_LAYER: {path.relative_to(repo_root)}")
        if lower_name.endswith("_dpo.py") and not _is_relative_to(path, dpo_root):
            violations.append(f"DPO_WRONG_LAYER: {path.relative_to(repo_root)}")

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            if node.name.endswith("DTO") and not _is_relative_to(path, dto_root):
                violations.append(f"DTO_WRONG_LAYER: {path.relative_to(repo_root)}::{node.name}")
            if node.name.endswith("DPO") and not _is_relative_to(path, dpo_root):
                violations.append(f"DPO_WRONG_LAYER: {path.relative_to(repo_root)}::{node.name}")
            if node.name.endswith("Repository") and not (
                _is_relative_to(path, repository_port_root) or _is_relative_to(path, repository_impl_root)
            ):
                violations.append(f"REPOSITORY_WRONG_LAYER: {path.relative_to(repo_root)}::{node.name}")
    return violations


def validate_runtime_resources(repo_root: Path, runtime_root: Path, policy: dict) -> list[str]:
    violations: list[str] = []
    resources_root = repo_root / policy["placement"]["runtime_resources_root"]
    for root_name in policy["canonical_roots"]:
        root = runtime_root / root_name
        if not root.exists():
            continue
        for path in sorted(p for p in root.rglob("*") if p.is_file()):
            if path.suffix in {".py", ".pyi"}:
                continue
            if not _is_relative_to(path, resources_root):
                violations.append(f"RUNTIME_RESOURCE_WRONG_LAYER: {path.relative_to(repo_root)}")
    return violations


def validate(repo_root: Path = REPO_ROOT, policy_path: Path | None = None) -> list[str]:
    repo_root = repo_root.resolve()
    policy_path = (policy_path or (repo_root / "machine" / "architecture" / "runtime-boundaries.v1.json")).resolve()
    policy = load_policy(policy_path)
    runtime_root = repo_root / policy["runtime_root"]
    if not runtime_root.is_dir():
        return [f"RUNTIME_ROOT_MISSING: {runtime_root}"]

    violations: list[str] = []
    violations.extend(validate_top_level_placement(runtime_root, policy))
    violations.extend(validate_internal_boundary(runtime_root))
    violations.extend(validate_layer_dependencies(runtime_root, policy))
    violations.extend(validate_facades(repo_root, runtime_root, policy))
    violations.extend(validate_special_object_placement(repo_root, runtime_root, policy))
    violations.extend(validate_runtime_resources(repo_root, runtime_root, policy))
    return sorted(set(violations))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--policy", type=Path, default=None)
    args = parser.parse_args()

    violations = validate(args.repo_root, args.policy)
    if violations:
        print("ARCHITECTURE_BOUNDARY_VALIDATION=FAIL")
        for violation in violations:
            print(f"- {violation}")
        return 1

    print("ARCHITECTURE_BOUNDARY_VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
