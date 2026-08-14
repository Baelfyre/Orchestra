from scripts import check_readme_impact as gate


def test_significant_runtime_change_requires_readme() -> None:
    result = gate.evaluate_changed_paths(["orchestra_runtime/runtime.py"])
    assert result["passed"] is False
    assert result["readme_updated"] is False
    assert result["significant"] == ["orchestra_runtime/runtime.py"]


def test_significant_change_passes_with_readme() -> None:
    result = gate.evaluate_changed_paths(
        ["docs/governance/GOVERNANCE_LAYER.md", "README.md"]
    )
    assert result["passed"] is True
    assert result["readme_updated"] is True
    assert result["significant"] == ["docs/governance/GOVERNANCE_LAYER.md"]


def test_test_and_validation_evidence_only_changes_do_not_require_readme() -> None:
    result = gate.evaluate_changed_paths(
        [
            "tests/runtime/test_example.py",
            "docs/validation/EXAMPLE_EVIDENCE.md",
            "CHANGELOG.md",
        ]
    )
    assert result["passed"] is True
    assert result["significant"] == []


def test_version_and_host_surfaces_are_significant() -> None:
    paths = [
        "plugin.json",
        ".claude-plugin/plugin.json",
        "adapters/vscode/package.json",
        "docs/releases/v1.4.0-governance-upgrade.md",
    ]
    result = gate.evaluate_changed_paths(paths)
    assert result["passed"] is False
    assert result["significant"] == sorted(paths)


def test_governance_and_ci_changes_are_significant() -> None:
    paths = [
        ".github/workflows/governance-check.yml",
        "scripts/check_readme_impact.py",
        "skills/the-governor/SKILL.md",
    ]
    result = gate.evaluate_changed_paths(paths)
    assert result["passed"] is False
    assert result["significant"] == sorted(paths)
