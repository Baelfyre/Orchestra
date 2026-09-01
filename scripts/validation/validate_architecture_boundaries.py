from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import re
from typing import Any, Iterable


POLICY_PATH = Path("machine/governance/runtime-architecture-boundaries.v1.json")
EXPECTED_SCHEMA_VERSION = "orchestra.runtime-architecture-boundaries.v1"


def _matches_prefix(import_name: str, prefix: str) -> bool:
    return import_name == prefix or import_name.startswith(prefix + ".")


def _load_policy(root: Path, policy_path: Path = POLICY_PATH) -> dict[str, Any]:
    payload = json.loads((root / policy_path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != EXPECTED_SCHEMA_VERSION:
        raise ValueError("unsupported runtime architecture boundary policy schema")
    if payload.get("policy_role") != "machine_runtime_architecture_policy":
        raise ValueError("unexpected runtime architecture boundary policy role")
    if payload.get("runtime_root") != "orchestra_runtime":
        raise ValueError("runtime architecture policy must target orchestra_runtime")
    migration = payload.get("migration")
    if not isinstance(migration, dict) or migration.get("new_flat_runtime_modules_prohibited") is not True:
        raise ValueError("runtime architecture policy must fail closed on new flat modules")
    if not isinstance(migration.get("legacy_package_files"), dict):
        raise ValueError("runtime architecture policy must freeze legacy package file inventories")
    enforcement = payload.get("enforcement")
    if not isinstance(enforcement, dict):
        raise ValueError("runtime architecture policy is missing enforcement")
    required_true = (
        "fail_closed_on_unknown_runtime_package_root",
        "fail_closed_on_unplaced_runtime_file",
        "freeze_legacy_package_file_inventories",
        "forbid_migrated_layers_from_importing_flat_legacy_runtime",
    )
    for key in required_true:
        if enforcement.get(key) is not True:
            raise ValueError(f"runtime architecture policy must set {key}=true")
    return payload


def _python_files(root: Path) -> Iterable[Path]:
    if root.exists():
        yield from sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)


def _module_package(path: Path, runtime_root: Path) -> list[str]:
    relative = path.relative_to(runtime_root)
    return [runtime_root.name, *relative.parts[:-1]]


def _imports(path: Path, runtime_root: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    package = _module_package(path, runtime_root)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                keep = max(1, len(package) - (node.level - 1))
                base = package[:keep]
                if node.module:
                    base.extend(node.module.split("."))
                names.add(".".join(base))
            elif node.module:
                names.add(node.module)
    return names


def _uses_builtin_open(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open"
        for node in ast.walk(tree)
    )


def _intent_token(path: Path, token: str) -> bool:
    pieces = [part for part in re.split(r"[^a-z0-9]+", path.stem.casefold()) if part]
    return token in pieces


def _repository_intent(path: Path) -> bool:
    stem = path.stem.casefold()
    return stem in {"repository", "repositories"} or stem.endswith("_repository") or stem.endswith("_repositories")


def _module_to_path(runtime_root: Path, module_name: str) -> Path:
    parts = module_name.split(".")
    if not parts or parts[0] != runtime_root.name:
        raise ValueError(f"compatibility facade module is outside runtime root: {module_name}")
    return runtime_root.parent.joinpath(*parts).with_suffix(".py")


def _validate_facade(path: Path, target_module: str) -> list[str]:
    if not path.is_file():
        return [f"compatibility facade is missing: {path.as_posix()}"]
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    violations: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            continue
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        if isinstance(node, ast.Assign):
            names = [target.id for target in node.targets if isinstance(target, ast.Name)]
            if names == ["__all__"]:
                continue
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "__all__":
            continue
        violations.append(
            f"compatibility facade contains executable/behavioral node {type(node).__name__}: {path.as_posix()}"
        )
    target_tail = ".".join(target_module.split(".")[1:])
    if target_module not in _imports(path, path.parents[len(target_module.split('.')) - 1]) and target_tail not in path.read_text(encoding="utf-8"):
        violations.append(
            f"compatibility facade does not import canonical target {target_module}: {path.as_posix()}"
        )
    return violations


def _legacy_runtime_prefixes(runtime_name: str, migration: dict[str, Any]) -> tuple[str, ...]:
    prefixes = [
        f"{runtime_name}.{name[:-3]}"
        for name in migration["legacy_flat_modules"]
        if name.endswith(".py") and name != "__init__.py"
    ]
    prefixes.extend(f"{runtime_name}.{name}" for name in migration["legacy_package_files"])
    return tuple(sorted(prefixes))


def validate_repository(root: Path, policy_path: Path = POLICY_PATH) -> list[str]:
    root = root.resolve()
    policy = _load_policy(root, policy_path)
    runtime_root = root / str(policy["runtime_root"])
    if not runtime_root.is_dir():
        return [f"runtime root is missing: {runtime_root.relative_to(root).as_posix()}"]

    violations: list[str] = []
    migration = policy["migration"]
    legacy_flat = set(migration["legacy_flat_modules"])
    legacy_package_files = migration["legacy_package_files"]
    legacy_packages = set(legacy_package_files)
    canonical_packages = set(policy["canonical_package_roots"])
    legacy_runtime_prefixes = _legacy_runtime_prefixes(runtime_root.name, migration)

    actual_flat = {path.name for path in runtime_root.glob("*.py")}
    for filename in sorted(actual_flat - legacy_flat):
        violations.append(f"new flat runtime module is prohibited: {runtime_root.name}/{filename}")

    actual_package_roots = {
        path.name
        for path in runtime_root.iterdir()
        if path.is_dir() and path.name != "__pycache__" and any(_python_files(path))
    }
    for package_root in sorted(actual_package_roots - canonical_packages - legacy_packages):
        violations.append(f"unknown runtime package root is prohibited: {runtime_root.name}/{package_root}/")

    for package_root, allowed_files in legacy_package_files.items():
        package_path = runtime_root / package_root
        actual = {
            path.relative_to(package_path).as_posix()
            for path in _python_files(package_path)
        }
        for relative in sorted(actual - set(allowed_files)):
            violations.append(
                f"new file inside frozen legacy package is prohibited: {runtime_root.name}/{package_root}/{relative}"
            )

    placement = policy["placement"]
    layer_subzones = placement["layer_subzones"]
    allowed_direct_files = placement["allowed_direct_files"]
    for layer in canonical_packages:
        layer_root = runtime_root / layer
        if not layer_root.exists():
            continue
        direct_allowed = set(allowed_direct_files.get(layer, ()))
        for direct_file in sorted(layer_root.glob("*.py")):
            if direct_file.name not in direct_allowed:
                violations.append(
                    f"unplaced direct file in canonical layer: {direct_file.relative_to(runtime_root).as_posix()}"
                )
        if layer in layer_subzones:
            allowed_subzones = set(layer_subzones[layer])
            for child in sorted(path for path in layer_root.iterdir() if path.is_dir() and path.name != "__pycache__"):
                if any(_python_files(child)) and child.name not in allowed_subzones:
                    violations.append(
                        f"unknown subzone in canonical layer {layer}: {child.relative_to(runtime_root).as_posix()}/"
                    )

    layer_rules = policy["layer_rules"]
    for layer, rules in layer_rules.items():
        layer_root = runtime_root / layer
        if not layer_root.exists():
            continue
        allowed_runtime = tuple(rules.get("allowed_runtime_import_prefixes", ()))
        forbidden = tuple(rules.get("forbidden_import_prefixes", ()))
        forbidden_io = tuple(rules.get("forbidden_io_import_prefixes", ()))
        allow_legacy = rules.get("allow_legacy_runtime_imports") is True
        for path in _python_files(layer_root):
            relative = path.relative_to(root).as_posix()
            for imported in _imports(path, runtime_root):
                for prefix in forbidden:
                    if _matches_prefix(imported, prefix):
                        violations.append(f"{relative} imports forbidden dependency {imported!r}")
                for prefix in forbidden_io:
                    if _matches_prefix(imported, prefix):
                        violations.append(f"{relative} imports forbidden domain I/O dependency {imported!r}")
                if _matches_prefix(imported, runtime_root.name):
                    if any(_matches_prefix(imported, prefix) for prefix in allowed_runtime):
                        continue
                    if allow_legacy and any(_matches_prefix(imported, prefix) for prefix in legacy_runtime_prefixes):
                        continue
                    violations.append(
                        f"{relative} imports non-inward runtime dependency {imported!r}; migrated layers may not depend on flat legacy runtime"
                    )
            if rules.get("forbid_builtin_open") is True and _uses_builtin_open(path):
                violations.append(f"{relative} calls builtin open(); filesystem I/O belongs in infrastructure")

    for path in _python_files(runtime_root):
        relative_runtime = path.relative_to(runtime_root).as_posix()
        imports = _imports(path, runtime_root)
        if any(_matches_prefix(imported, "internal") for imported in imports):
            violations.append(f"production runtime imports repository internal/: {relative_runtime}")

        if _intent_token(path, "dto") and not relative_runtime.startswith(placement["dto_prefix"]):
            violations.append(f"DTO-intent file is outside application/dto/: {relative_runtime}")
        if _intent_token(path, "dpo") and not relative_runtime.startswith(placement["dpo_prefix"]):
            violations.append(f"DPO-intent file is outside infrastructure/persistence/dpo/: {relative_runtime}")
        if _repository_intent(path):
            allowed = tuple(placement["repository_allowed_prefixes"])
            if not relative_runtime.startswith(allowed) and path.name != "repositories.py":
                violations.append(
                    f"repository-intent file is outside repository port/implementation zones: {relative_runtime}"
                )
        if "methods" in path.relative_to(runtime_root).parts:
            parts = path.relative_to(runtime_root).parts
            valid_methods = len(parts) >= 4 and parts[0] == "domain" and parts[2] == "methods"
            if not valid_methods:
                violations.append(
                    f"methods package is outside domain/<bounded-context>/methods/: {relative_runtime}"
                )

    for facade_module, target_module in migration["compatibility_facades"].items():
        facade_path = _module_to_path(runtime_root, facade_module)
        violations.extend(_validate_facade(facade_path, target_module))

    return sorted(dict.fromkeys(violations))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Orchestra runtime architectural boundaries.")
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--policy", type=Path, default=POLICY_PATH)
    args = parser.parse_args()

    violations = validate_repository(args.repository_root, args.policy)
    if violations:
        print("RUNTIME_ARCHITECTURE_BOUNDARIES=FAIL")
        for violation in violations:
            print(f"- {violation}")
        return 1
    print("RUNTIME_ARCHITECTURE_BOUNDARIES=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
