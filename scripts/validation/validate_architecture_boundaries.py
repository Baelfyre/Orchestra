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
    enforcement = payload.get("enforcement")
    if not isinstance(enforcement, dict):
        raise ValueError("runtime architecture policy is missing enforcement")
    if enforcement.get("fail_closed_on_unknown_runtime_package_root") is not True:
        raise ValueError("runtime architecture policy must fail closed on unknown package roots")
    if enforcement.get("fail_closed_on_unplaced_runtime_file") is not True:
        raise ValueError("runtime architecture policy must fail closed on unplaced runtime files")
    return payload


def _python_files(root: Path) -> Iterable[Path]:
    if root.exists():
        yield from sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)


def _module_package(path: Path, runtime_root: Path) -> list[str]:
    relative = path.relative_to(runtime_root)
    parts = [runtime_root.name, *relative.parts[:-1]]
    return parts


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
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open":
            return True
    return False


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
    imported_targets: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            continue
        if isinstance(node, ast.ImportFrom):
            if node.level:
                package_parts = path.with_suffix("").parts
                keep = max(1, len(package_parts) - (node.level - 1))
                base = list(package_parts[:keep])
                if node.module:
                    base.extend(node.module.split("."))
                imported_targets.add(".".join(base[-len(target_module.split(".")) :]))
            elif node.module:
                imported_targets.add(node.module)
            continue
        if isinstance(node, ast.Import):
            imported_targets.update(alias.name for alias in node.names)
            continue
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        violations.append(f"compatibility facade contains executable/behavioral node {type(node).__name__}: {path.as_posix()}")
    text = path.read_text(encoding="utf-8")
    dotted_tail = ".".join(target_module.split(".")[1:])
    if target_module not in imported_targets and dotted_tail not in text:
        violations.append(f"compatibility facade does not import canonical target {target_module}: {path.as_posix()}")
    return violations


def validate_repository(root: Path, policy_path: Path = POLICY_PATH) -> list[str]:
    root = root.resolve()
    policy = _load_policy(root, policy_path)
    runtime_root = root / str(policy["runtime_root"])
    if not runtime_root.is_dir():
        return [f"runtime root is missing: {runtime_root.relative_to(root).as_posix()}"]

    violations: list[str] = []
    migration = policy["migration"]
    legacy_flat = set(migration["legacy_flat_modules"])
    legacy_packages = set(migration["legacy_package_roots"])
    canonical_packages = set(policy["canonical_package_roots"])

    actual_flat = {path.name for path in runtime_root.glob("*.py")}
    unexpected_flat = sorted(actual_flat - legacy_flat)
    for filename in unexpected_flat:
        violations.append(f"new flat runtime module is prohibited: {runtime_root.name}/{filename}")

    actual_package_roots = {
        path.name
        for path in runtime_root.iterdir()
        if path.is_dir() and path.name != "__pycache__" and any(_python_files(path))
    }
    for package_root in sorted(actual_package_roots - canonical_packages - legacy_packages):
        violations.append(f"unknown runtime package root is prohibited: {runtime_root.name}/{package_root}/")

    layer_rules = policy["layer_rules"]
    for layer, rules in layer_rules.items():
        layer_root = runtime_root / layer
        if not layer_root.exists():
            continue
        forbidden = tuple(rules.get("forbidden_import_prefixes", ()))
        forbidden_io = tuple(rules.get("forbidden_io_import_prefixes", ()))
        for path in _python_files(layer_root):
            relative = path.relative_to(root).as_posix()
            for imported in _imports(path, runtime_root):
                for prefix in forbidden:
                    if _matches_prefix(imported, prefix):
                        violations.append(f"{relative} imports forbidden dependency {imported!r}")
                for prefix in forbidden_io:
                    if _matches_prefix(imported, prefix):
                        violations.append(f"{relative} imports forbidden domain I/O dependency {imported!r}")
            if rules.get("forbid_builtin_open") is True and _uses_builtin_open(path):
                violations.append(f"{relative} calls builtin open(); filesystem I/O belongs in infrastructure")

    for path in _python_files(runtime_root):
        relative_runtime = path.relative_to(runtime_root).as_posix()
        imports = _imports(path, runtime_root)
        if any(_matches_prefix(imported, "internal") for imported in imports):
            violations.append(f"production runtime imports repository internal/: {relative_runtime}")

        if _intent_token(path, "dto") and not relative_runtime.startswith(policy["placement"]["dto_prefix"]):
            violations.append(f"DTO-intent file is outside application/dto/: {relative_runtime}")
        if _intent_token(path, "dpo") and not relative_runtime.startswith(policy["placement"]["dpo_prefix"]):
            violations.append(f"DPO-intent file is outside infrastructure/persistence/dpo/: {relative_runtime}")
        if _repository_intent(path):
            allowed = tuple(policy["placement"]["repository_allowed_prefixes"])
            if not relative_runtime.startswith(allowed):
                if path.name != "repositories.py":
                    violations.append(f"repository-intent file is outside repository port/implementation zones: {relative_runtime}")

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
