#!/usr/bin/env python3
"""Regression tests for scripts/check_readme_impact.py."""
from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "check_readme_impact.py"
spec = importlib.util.spec_from_file_location("check_readme_impact", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def evaluate(*paths: str) -> dict[str, object]:
    return module.evaluate_changed_paths(paths)


def assert_pass(*paths: str) -> None:
    result = evaluate(*paths)
    assert result["passed"], result


def assert_fail(expected_missing: set[str], *paths: str) -> None:
    result = evaluate(*paths)
    assert not result["passed"], result
    assert set(result["missing"]) == expected_missing, result


def main() -> int:
    # Runtime behavior no longer forces root README churn, but it must update the
    # machine discovery index and a detailed human documentation surface.
    assert_fail(
        {"README.json", "detailed-documentation"},
        "orchestra_runtime/executor.py",
    )
    assert_fail(
        {"detailed-documentation"},
        "orchestra_runtime/executor.py",
        "README.json",
    )
    assert_pass(
        "orchestra_runtime/executor.py",
        "README.json",
        "docs/architecture/README.md",
    )

    # Public package identity remains visible on the root landing page and in
    # the AI-facing repository index.
    assert_fail(
        {"README.md", "README.json"},
        "plugin.json",
    )
    assert_pass(
        "plugin.json",
        "README.md",
        "README.json",
    )

    # Machine-schema/index evolution needs machine parity but not meaningless
    # README prose or a domain guide when no domain behavior changed.
    assert_fail(
        {"README.json"},
        "machine/schemas/example.schema.json",
    )
    assert_pass(
        "machine/schemas/example.schema.json",
        "README.json",
    )

    # Evidence-only and test-only maintenance does not force documentation.
    assert_pass("docs/validation/example.md")
    assert_pass("tests/runtime/test_example.py")

    # A routed/host machine contract needs both machine discovery and detailed
    # documentation, but still does not force the concise root README.
    assert_fail(
        {"README.json", "detailed-documentation"},
        "machine/hosts/update-contract.v1.json",
    )
    assert_pass(
        "machine/hosts/update-contract.v1.json",
        "README.json",
        "docs/setup/HOST_UPDATES.md",
    )

    print("DOCUMENTATION_IMPACT_CONTRACT_TEST=PASS scenarios=10")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
