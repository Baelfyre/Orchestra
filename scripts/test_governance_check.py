import subprocess
import sys
import tempfile
from pathlib import Path

import governance_check as gc


def assert_equal(name, actual, expected):
    if actual != expected:
        raise AssertionError(f"{name}: expected {expected!r}, got {actual!r}")


def test_tracked_repo_files_only():
    with tempfile.TemporaryDirectory(prefix="governance-check-test-") as temp_dir:
        repo_root = Path(temp_dir)
        subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True, text=True)
        subprocess.run(["git", "config", "user.name", "Codex Test"], cwd=repo_root, check=True, capture_output=True, text=True)
        subprocess.run(["git", "config", "user.email", "codex@example.com"], cwd=repo_root, check=True, capture_output=True, text=True)

        tracked_file = repo_root / "README.md"
        tracked_file.write_text("tracked\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=repo_root, check=True, capture_output=True, text=True)

        artifact_dir = repo_root / "artifacts"
        artifact_dir.mkdir()
        (artifact_dir / "governance_report.txt").write_text("untracked\n", encoding="utf-8")

        tracked_paths = gc.get_tracked_repo_files(str(repo_root))
        assert_equal("tracked file present", "README.md" in tracked_paths, True)
        assert_equal("untracked artifact omitted", "artifacts/governance_report.txt" in tracked_paths, False)


def test_repo_memory_path_check():
    with tempfile.TemporaryDirectory(prefix="governance-memory-test-") as temp_dir:
        repo_root = Path(temp_dir)
        (repo_root / "scripts").mkdir()
        (repo_root / "scripts" / "existing.py").write_text("pass\n", encoding="utf-8")
        (repo_root / "SESSION_HANDOFF.md").write_text(
            "- Existing: `scripts/existing.py`\n- Missing: `scripts/missing.py`\n",
            encoding="utf-8",
        )

        counters = {"warnings": 0, "errors": 0}
        gc.run_repo_memory_path_check(str(repo_root), counters)
        assert_equal("missing memory path error", counters["errors"], 1)


def main():
    assert_equal("forbidden artifacts", gc.is_forbidden_repo_path("artifacts/governance_report.txt"), True)
    assert_equal("forbidden runtime folder", gc.is_forbidden_repo_path(".agents/skills/dagger/SKILL.md"), True)
    assert_equal("allowed source file", gc.is_forbidden_repo_path("skills/arbiter/SKILL.md"), False)
    assert_equal(
        "missing changelog issue",
        gc.get_changelog_issue(["scripts/governance_check.py"], False),
        "Significant changes were detected without a matching CHANGELOG.md update.",
    )
    assert_equal("present changelog issue", gc.get_changelog_issue(["scripts/governance_check.py"], True), None)
    assert_equal("advisory exit", gc.get_exit_code(False, 3), 0)
    assert_equal("strict exit", gc.get_exit_code(True, 1), 1)
    assert_equal("repo path detection", gc.is_repo_relative_memory_path("scripts/governance_check.py"), True)
    assert_equal("external path ignored", gc.is_repo_relative_memory_path("C:/conductor/scripts/governance_check.py"), False)
    test_tracked_repo_files_only()
    test_repo_memory_path_check()
    print("Governance check helper tests passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
