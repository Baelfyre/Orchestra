# @codebase_provenance_JEO
# @codebase_rights_JEO

import pytest

from scripts.validation.classify_adaptive_assurance_scope import (
    APPLICABLE,
    NOT_APPLICABLE,
    classify_paths,
)


RELEASE_PACKAGING_PATHS = [
    ".claude-plugin/marketplace.json",
    ".claude-plugin/plugin.json",
    ".codex-plugin/plugin.json",
    "CHANGELOG.md",
    "PROJECT_CONTEXT.md",
    "PROJECT_STATE.md",
    "README.json",
    "README.md",
    "adapters/cursor/package.json",
    "adapters/jetbrains/package.json",
    "adapters/jetbrains/plugin.xml",
    "adapters/neovim/package.json",
    "adapters/vscode/package.json",
    "adapters/windsurf/package.json",
    "adapters/zed/package.json",
    "docs/reference/releases/README.md",
    "docs/releases/v1.11.0-adaptive-assurance-governance-release-candidate.md",
    "docs/validation/V1_11_0_RELEASE_READINESS_EVIDENCE.md",
    "machine/hosts/update-contract.v1.json",
    "plugin.json",
    "tests/runtime/test_host_updates.py",
    "tests/runtime/test_release_version_surfaces.py",
]


@pytest.mark.parametrize("gate", ["prai", "aq5", "aq7"])
def test_exact_release_packaging_scope_is_not_applicable_to_historical_exact_gates(gate: str) -> None:
    assert classify_paths(RELEASE_PACKAGING_PATHS, gate) == NOT_APPLICABLE


@pytest.mark.parametrize(
    "extra_path",
    [
        "orchestra_runtime/domain/adaptive/prai.py",
        "machine/governance/covenant.v1.json",
        "orchestra_runtime/infrastructure/providers/provider.py",
        "orchestra_runtime/infrastructure/telemetry/exporter.py",
        ".github/workflows/deploy.yml",
        "unexpected.txt",
    ],
)
@pytest.mark.parametrize("gate", ["prai", "aq5", "aq7"])
def test_release_packaging_mixed_with_semantic_or_unknown_change_fails_closed(
    gate: str,
    extra_path: str,
) -> None:
    assert classify_paths([*RELEASE_PACKAGING_PATHS, extra_path], gate) == APPLICABLE


@pytest.mark.parametrize("gate", ["prai", "aq5", "aq7"])
def test_partial_release_packaging_scope_fails_closed(gate: str) -> None:
    partial = RELEASE_PACKAGING_PATHS.copy()
    partial.remove("tests/runtime/test_release_version_surfaces.py")
    assert classify_paths(partial, gate) == APPLICABLE


@pytest.mark.parametrize("gate", ["prai", "aq5", "aq7"])
def test_release_packaging_version_identity_mismatch_fails_closed(gate: str) -> None:
    mismatched = [
        "docs/releases/v1.11.0-adaptive-assurance-governance-release-candidate.md"
        if path.startswith("docs/releases/")
        else "docs/validation/V1_12_0_RELEASE_READINESS_EVIDENCE.md"
        if path.startswith("docs/validation/V1_11_0_")
        else path
        for path in RELEASE_PACKAGING_PATHS
    ]
    assert classify_paths(mismatched, gate) == APPLICABLE


def test_release_packaging_duplicate_path_is_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate changed path"):
        classify_paths([*RELEASE_PACKAGING_PATHS, "plugin.json"], "prai")


def test_release_packaging_unsafe_path_is_rejected() -> None:
    with pytest.raises(ValueError, match="unsafe changed path"):
        classify_paths([*RELEASE_PACKAGING_PATHS, "../plugin.json"], "prai")
