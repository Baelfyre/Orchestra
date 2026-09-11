# @codebase_provenance_JEO
# @codebase_rights_JEO

import pytest

from scripts.validation.classify_adaptive_assurance_scope import (
    APPLICABLE,
    NOT_APPLICABLE,
    classify_paths,
)


POST_PUBLICATION_DOCS_PATHS = [
    "CHANGELOG.md",
    "PROJECT_CONTEXT.md",
    "PROJECT_STATE.md",
    "README.json",
    "README.md",
    "SESSION_HANDOFF.md",
    "docs/MATURITY.md",
    "docs/README.md",
    "docs/project/OOP_RUNTIME_ARCHITECTURE.md",
    "docs/project/ROADMAP.md",
    "docs/reference/README.md",
    "docs/reference/releases/README.md",
    "docs/reference/releases/v1.11.0.md",
    "docs/setup/COMPATIBILITY.md",
    "docs/setup/INSTALLATION.md",
    "tests/runtime/test_uai10_maturity_closeout.py",
]


@pytest.mark.parametrize("gate", ["prai", "aq5", "aq7"])
def test_exact_post_publication_docs_scope_is_not_applicable_to_historical_exact_gates(gate: str) -> None:
    assert classify_paths(POST_PUBLICATION_DOCS_PATHS, gate) == NOT_APPLICABLE


@pytest.mark.parametrize("gate", ["prai", "aq5", "aq7"])
def test_partial_post_publication_docs_scope_fails_closed(gate: str) -> None:
    partial = POST_PUBLICATION_DOCS_PATHS.copy()
    partial.remove("docs/reference/releases/v1.11.0.md")
    assert classify_paths(partial, gate) == APPLICABLE


@pytest.mark.parametrize(
    "extra_path",
    [
        "orchestra_runtime/application/services/example.py",
        "machine/governance/covenant.v1.json",
        "orchestra_runtime/infrastructure/providers/provider.py",
        "orchestra_runtime/infrastructure/telemetry/exporter.py",
        ".github/workflows/deploy.yml",
        "unexpected.txt",
    ],
)
@pytest.mark.parametrize("gate", ["prai", "aq5", "aq7"])
def test_post_publication_docs_mixed_with_semantic_or_unknown_change_fails_closed(
    gate: str,
    extra_path: str,
) -> None:
    assert classify_paths([*POST_PUBLICATION_DOCS_PATHS, extra_path], gate) == APPLICABLE


def test_post_publication_docs_duplicate_path_is_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate changed path"):
        classify_paths([*POST_PUBLICATION_DOCS_PATHS, "README.md"], "prai")


def test_post_publication_docs_unsafe_path_is_rejected() -> None:
    with pytest.raises(ValueError, match="unsafe changed path"):
        classify_paths([*POST_PUBLICATION_DOCS_PATHS, "../README.md"], "prai")
