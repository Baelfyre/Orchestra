from scripts import check_readme_impact as gate


def test_runtime_change_requires_machine_index_and_detailed_documentation() -> None:
    result = gate.evaluate_changed_paths(["orchestra_runtime/runtime.py"])
    assert result["passed"] is False
    assert result["readme_updated"] is False
    assert result["machine_impacts"] == ["orchestra_runtime/runtime.py"]
    assert result["detail_impacts"] == ["orchestra_runtime/runtime.py"]
    assert set(result["missing"]) == {"README.json", "detailed-documentation"}


def test_runtime_change_passes_without_root_readme_when_affected_docs_are_updated() -> None:
    result = gate.evaluate_changed_paths(
        [
            "orchestra_runtime/runtime.py",
            "README.json",
            "docs/architecture/README.md",
        ]
    )
    assert result["passed"] is True
    assert result["readme_updated"] is False
    assert result["machine_index_updated"] is True
    assert result["detailed_docs_updated"] is True


def test_test_and_validation_evidence_only_changes_do_not_require_documentation() -> None:
    result = gate.evaluate_changed_paths(
        [
            "tests/runtime/test_example.py",
            "docs/validation/EXAMPLE_EVIDENCE.md",
            "CHANGELOG.md",
        ]
    )
    assert result["passed"] is True
    assert result["public_impacts"] == []
    assert result["machine_impacts"] == []
    assert result["detail_impacts"] == []


def test_package_and_public_release_surfaces_require_root_and_machine_entrypoints() -> None:
    paths = [
        "plugin.json",
        ".claude-plugin/plugin.json",
        "docs/releases/v1.6.0-example.md",
    ]
    result = gate.evaluate_changed_paths(paths)
    assert result["passed"] is False
    assert "plugin.json" in result["public_impacts"]
    assert ".claude-plugin/plugin.json" in result["public_impacts"]
    assert "docs/releases/v1.6.0-example.md" in result["public_impacts"]
    assert "README.md" in result["missing"]
    assert "README.json" in result["missing"]


def test_governance_ci_and_specialist_changes_require_machine_parity_and_domain_docs() -> None:
    paths = [
        ".github/workflows/governance-check.yml",
        "scripts/check_readme_impact.py",
        "skills/the-governor/SKILL.md",
    ]
    result = gate.evaluate_changed_paths(paths)
    assert result["passed"] is False
    assert result["machine_impacts"] == sorted(paths)
    assert result["detail_impacts"] == ["skills/the-governor/SKILL.md"]
    assert set(result["missing"]) == {"README.json", "detailed-documentation"}
