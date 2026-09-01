from __future__ import annotations

import copy
import json
from pathlib import Path

import jsonschema

from scripts.validation.validate_architecture_boundaries import POLICY_PATH, validate_repository


ROOT = Path(__file__).resolve().parents[2]


def _policy() -> dict:
    return json.loads((ROOT / POLICY_PATH).read_text(encoding="utf-8"))


def _write(path: Path, text: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    policy = copy.deepcopy(_policy())
    policy["migration"]["legacy_flat_modules"] = ["__init__.py", "errors.py", "evidence.py"]
    policy["migration"]["legacy_package_files"] = {"adaptive": ["__init__.py"]}
    policy_path = Path("policy.json")
    _write(tmp_path / policy_path, json.dumps(policy))

    runtime = tmp_path / "orchestra_runtime"
    _write(runtime / "__init__.py")
    _write(runtime / "adaptive/__init__.py")
    _write(runtime / "shared/__init__.py")
    _write(runtime / "shared/errors.py", "class RuntimeContractError(Exception):\n    pass\n")
    _write(
        runtime / "errors.py",
        '"""Compatibility facade."""\nfrom .shared.errors import RuntimeContractError\n__all__ = ["RuntimeContractError"]\n',
    )
    for layer in ("domain", "application", "infrastructure", "bootstrap", "resources"):
        _write(runtime / layer / "__init__.py")
    return tmp_path, policy_path


def _violations(tmp_path: Path) -> list[str]:
    root, policy_path = _fixture(tmp_path)
    return validate_repository(root, policy_path)


def test_runtime_architecture_policy_matches_schema():
    policy = _policy()
    schema = json.loads(
        (ROOT / "machine/schemas/runtime-architecture-boundaries.v1.schema.json").read_text(encoding="utf-8")
    )
    jsonschema.validate(policy, schema)


def test_runtime_architecture_policy_validator_passes_repository():
    assert validate_repository(ROOT) == []


def test_runtime_architecture_policy_is_fail_closed_and_authority_bounded():
    policy = _policy()
    assert policy["migration"]["new_flat_runtime_modules_prohibited"] is True
    assert policy["enforcement"]["fail_closed_on_unknown_runtime_package_root"] is True
    assert policy["enforcement"]["fail_closed_on_unplaced_runtime_file"] is True
    assert policy["enforcement"]["freeze_legacy_package_file_inventories"] is True
    assert policy["enforcement"]["forbid_migrated_layers_from_importing_flat_legacy_runtime"] is True
    assert policy["authority"]["validation_does_not_grant_authority"] is True
    assert policy["authority"]["release_authorized"] is False
    assert policy["authority"]["architecture_owner"] == "clockwork"
    assert policy["authority"]["implementation_owner"] == "ponytail"


def test_runtime_architecture_policy_uses_entrypoints_not_legacy_interfaces_package():
    policy = _policy()
    assert "entrypoints" in policy["canonical_package_roots"]
    assert "interfaces" not in policy["canonical_package_roots"]
    assert "interfaces.py" in policy["migration"]["legacy_flat_modules"]


def test_validator_rejects_new_flat_runtime_module(tmp_path: Path):
    root, policy_path = _fixture(tmp_path)
    _write(root / "orchestra_runtime/rogue.py", "VALUE = 1\n")
    violations = validate_repository(root, policy_path)
    assert any("new flat runtime module is prohibited" in item for item in violations)


def test_validator_freezes_files_inside_legacy_packages(tmp_path: Path):
    root, policy_path = _fixture(tmp_path)
    _write(root / "orchestra_runtime/adaptive/new_debt.py", "VALUE = 1\n")
    violations = validate_repository(root, policy_path)
    assert any("new file inside frozen legacy package is prohibited" in item for item in violations)


def test_validator_rejects_unknown_canonical_subzone_and_direct_file(tmp_path: Path):
    root, policy_path = _fixture(tmp_path)
    _write(root / "orchestra_runtime/domain/rogue.py", "VALUE = 1\n")
    _write(root / "orchestra_runtime/domain/mystery/value.py", "VALUE = 1\n")
    violations = validate_repository(root, policy_path)
    assert any("unplaced direct file in canonical layer" in item for item in violations)
    assert any("unknown subzone in canonical layer domain" in item for item in violations)


def test_validator_rejects_flat_legacy_import_from_migrated_domain(tmp_path: Path):
    root, policy_path = _fixture(tmp_path)
    _write(root / "orchestra_runtime/domain/context/__init__.py")
    _write(root / "orchestra_runtime/domain/context/state.py", "from orchestra_runtime.evidence import receipt_digest\n")
    violations = validate_repository(root, policy_path)
    assert any("migrated layers may not depend on flat legacy runtime" in item for item in violations)


def test_validator_rejects_domain_io_import_and_builtin_open(tmp_path: Path):
    root, policy_path = _fixture(tmp_path)
    _write(root / "orchestra_runtime/domain/context/__init__.py")
    _write(
        root / "orchestra_runtime/domain/context/state.py",
        "from pathlib import Path\n\ndef load():\n    with open('state.json') as handle:\n        return handle.read()\n",
    )
    violations = validate_repository(root, policy_path)
    assert any("forbidden domain I/O dependency 'pathlib'" in item for item in violations)
    assert any("calls builtin open()" in item for item in violations)


def test_validator_rejects_misplaced_dto_dpo_and_repository_files(tmp_path: Path):
    root, policy_path = _fixture(tmp_path)
    _write(root / "orchestra_runtime/application/use_cases/order_dto.py", "VALUE = 1\n")
    _write(root / "orchestra_runtime/infrastructure/providers/order_dpo.py", "VALUE = 1\n")
    _write(root / "orchestra_runtime/infrastructure/providers/user_repository.py", "VALUE = 1\n")
    violations = validate_repository(root, policy_path)
    assert any("DTO-intent file is outside application/dto/" in item for item in violations)
    assert any("DPO-intent file is outside infrastructure/persistence/dpo/" in item for item in violations)
    assert any("repository-intent file is outside repository port/implementation zones" in item for item in violations)


def test_validator_rejects_methods_package_outside_bounded_domain_context(tmp_path: Path):
    root, policy_path = _fixture(tmp_path)
    _write(root / "orchestra_runtime/application/use_cases/methods/score.py", "VALUE = 1\n")
    violations = validate_repository(root, policy_path)
    assert any("methods package is outside domain/<bounded-context>/methods/" in item for item in violations)


def test_validator_rejects_behavior_inside_compatibility_facade(tmp_path: Path):
    root, policy_path = _fixture(tmp_path)
    facade = root / "orchestra_runtime/errors.py"
    facade.write_text(
        facade.read_text(encoding="utf-8") + "\ndef make_error():\n    return RuntimeContractError()\n",
        encoding="utf-8",
    )
    violations = validate_repository(root, policy_path)
    assert any("compatibility facade contains executable/behavioral node FunctionDef" in item for item in violations)
