from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "orchestra_runtime"

LEGACY_FLAT_MODULES = {
    "__init__.py",
    "adapters.py",
    "authority.py",
    "capabilities.py",
    "communication_budget.py",
    "compliance_protocol.py",
    "context_state.py",
    "coordination.py",
    "correlation.py",
    "delegation.py",
    "errors.py",
    "evidence.py",
    "factories.py",
    "governance_kernel.py",
    "host_protocol.py",
    "host_updates.py",
    "interfaces.py",
    "lifecycle.py",
    "machine_contracts.py",
    "mcp_specialist_execution.py",
    "mcp_transport.py",
    "models.py",
    "preexecution.py",
    "presentation.py",
    "provider_execution.py",
    "provider_mcp_execution.py",
    "provider_qualification.py",
    "registry_adaptive.py",
    "registry_o7.py",
    "remediation_circuit.py",
    "repositories.py",
    "retrospective.py",
    "serialization.py",
    "services.py",
    "shadow_conformance.py",
    "specialist_execution.py",
    "status.py",
    "test_evidence.py",
    "unified_testing.py",
    "workflow_contracts.py",
    "worktree.py",
}

FORBIDDEN_IMPORT_PREFIXES = {
    "domain": (
        "orchestra_runtime.application",
        "orchestra_runtime.infrastructure",
        "orchestra_runtime.interfaces",
        "internal",
    ),
    "application": (
        "orchestra_runtime.infrastructure",
        "orchestra_runtime.interfaces",
        "internal",
    ),
    "infrastructure": ("orchestra_runtime.interfaces", "internal"),
    "interfaces": ("internal",),
}


def _python_files(root: Path):
    if root.exists():
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


def test_no_new_flat_runtime_python_modules_outside_migration_allowlist():
    actual = {path.name for path in RUNTIME.glob("*.py")}
    unexpected = sorted(actual - LEGACY_FLAT_MODULES)
    assert not unexpected, (
        "New flat orchestra_runtime modules are prohibited. Place new code in its bounded "
        f"architecture package. Unexpected files: {unexpected}"
    )


def test_layer_dependency_direction_for_migrated_packages():
    failures: list[str] = []
    for layer, forbidden in FORBIDDEN_IMPORT_PREFIXES.items():
        layer_root = RUNTIME / layer
        for path in _python_files(layer_root):
            for imported in _imports(path):
                for prefix in forbidden:
                    if _matches_prefix(imported, prefix):
                        failures.append(
                            f"{path.relative_to(ROOT)} imports forbidden dependency {imported!r}"
                        )
    assert not failures, "Architecture dependency violations:\n" + "\n".join(failures)


def test_runtime_never_imports_repository_internal_package():
    failures: list[str] = []
    for path in _python_files(RUNTIME):
        for imported in _imports(path):
            if _matches_prefix(imported, "internal"):
                failures.append(f"{path.relative_to(ROOT)} imports {imported!r}")
    assert not failures, "Production runtime must not import internal/:\n" + "\n".join(failures)


def test_dto_and_dpo_filename_placement_after_migration_begins():
    failures: list[str] = []
    for path in _python_files(RUNTIME):
        lowered = path.name.lower()
        relative = path.relative_to(RUNTIME).as_posix()
        if "dto" in lowered and not relative.startswith("application/dto/"):
            failures.append(f"DTO-intent file is outside application/dto: {relative}")
        if "dpo" in lowered and not relative.startswith("infrastructure/persistence/dpo/"):
            failures.append(f"DPO-intent file is outside infrastructure/persistence/dpo: {relative}")
    assert not failures, "DTO/DPO placement violations:\n" + "\n".join(failures)


def test_ar2_foundation_packages_and_error_facade_are_compatible():
    required = [
        "domain",
        "application",
        "application/use_cases",
        "application/services",
        "application/dto",
        "application/ports",
        "infrastructure",
        "infrastructure/persistence",
        "infrastructure/persistence/repositories",
        "infrastructure/persistence/dpo",
        "infrastructure/persistence/mappers",
        "infrastructure/persistence/stores",
        "infrastructure/persistence/serialization",
        "bootstrap",
        "resources",
        "shared",
    ]
    missing = [path for path in required if not (RUNTIME / path / "__init__.py").is_file()]
    assert not missing, f"Missing AR-2 package boundaries: {missing}"

    from orchestra_runtime import errors as legacy_errors
    from orchestra_runtime.shared import errors as shared_errors

    names = [
        "RuntimeContractError",
        "InvalidAuthorityConfigurationError",
        "AuthorityDeniedError",
        "InvalidCapabilityConfigurationError",
        "CapabilityCollisionError",
        "CapabilityDeniedError",
        "DelegationRejectedError",
        "DelegationDepthViolationError",
        "InvalidLifecycleTransitionError",
        "InvalidLifecycleSignalError",
        "ConflictingTerminalSignalError",
        "RuntimeInitializationError",
        "RuntimeBindingError",
        "RuntimeAuditError",
        "InvalidCoordinationContractError",
        "InvalidCoordinationTransitionError",
        "InvalidCoordinationSignalError",
        "CoordinationReadinessError",
        "ConflictingCoordinationSignalError",
    ]
    mismatched = [name for name in names if getattr(legacy_errors, name) is not getattr(shared_errors, name)]
    assert not mismatched, f"Legacy error facade changed class identity: {mismatched}"
