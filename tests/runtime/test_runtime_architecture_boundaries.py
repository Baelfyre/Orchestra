from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "orchestra_runtime"
CONTRACT_PATH = ROOT / "machine" / "governance" / "runtime-architecture-boundaries.v1.json"


def _contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _python_files(root: Path):
    yield from sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def _matches_prefix(import_name: str, prefix: str) -> bool:
    return import_name == prefix or import_name.startswith(prefix + ".")


def test_architecture_contract_is_parseable_and_versioned():
    contract = _contract()
    assert contract["schema_version"] == "1.0"
    assert contract["contract"] == "orchestra-runtime-architecture-boundaries"
    assert contract["migration"]["new_flat_python_modules_allowed"] is False


def test_no_new_flat_runtime_python_modules_outside_migration_allowlist():
    contract = _contract()
    allowed = set(contract["migration"]["legacy_flat_python_modules"])
    actual = {path.name for path in RUNTIME.glob("*.py")}
    unexpected = sorted(actual - allowed)
    assert not unexpected, (
        "New flat orchestra_runtime modules are prohibited. Place new code in its bounded "
        f"architecture package. Unexpected files: {unexpected}"
    )


def test_layer_dependency_direction():
    contract = _contract()
    failures: list[str] = []
    for layer, rules in contract["dependency_rules"].items():
        layer_root = RUNTIME / layer
        if not layer_root.exists():
            continue
        forbidden = rules["must_not_import"]
        for path in _python_files(layer_root):
            for imported in _imports(path):
                for prefix in forbidden:
                    if _matches_prefix(imported, prefix):
                        failures.append(
                            f"{path.relative_to(ROOT)} imports forbidden dependency {imported!r}"
                        )
    assert not failures, "Architecture dependency violations:\n" + "\n".join(failures)


def test_runtime_never_imports_internal():
    failures: list[str] = []
    for path in _python_files(RUNTIME):
        for imported in _imports(path):
            if _matches_prefix(imported, "internal"):
                failures.append(f"{path.relative_to(ROOT)} imports {imported!r}")
    assert not failures, "Production runtime must not import internal/:\n" + "\n".join(failures)


def test_dto_and_dpo_filename_placement():
    failures: list[str] = []
    for path in _python_files(RUNTIME):
        lowered = path.name.lower()
        relative = path.relative_to(RUNTIME).as_posix()
        if "dto" in lowered and not relative.startswith("application/dto/"):
            failures.append(f"DTO-intent file is outside application/dto: {relative}")
        if "dpo" in lowered and not relative.startswith("infrastructure/persistence/dpo/"):
            failures.append(f"DPO-intent file is outside infrastructure/persistence/dpo: {relative}")
    assert not failures, "DTO/DPO placement violations:\n" + "\n".join(failures)
