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


def test_artificer_governance_validator_is_registered():
    script = "scripts/validate_artificer_governance_records.py"
    assert_equal("required governance validator", script in gc.REQUIRED_VALIDATION_SCRIPTS, True)
    assert_equal("strict governance validator", script in gc.STRICT_VALIDATOR_SCRIPTS, True)


def test_artificer_audit_renderer_is_registered_read_only():
    script = "scripts/render_artificer_audit_report.py"
    assert_equal("required audit renderer", script in gc.REQUIRED_VALIDATION_SCRIPTS, True)
    assert_equal("renderer is not a strict validator", script in gc.STRICT_VALIDATOR_SCRIPTS, False)


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


def test_startup_state_claim_check():
    with tempfile.TemporaryDirectory(prefix="governance-startup-test-") as temp_dir:
        repo_root = Path(temp_dir)

        def write_test_files(project_state_content, session_handoff_content, context_content=None, plugin_json_content=None):
            if project_state_content is not None:
                (repo_root / "PROJECT_STATE.md").write_text(project_state_content, encoding="utf-8")
            else:
                if (repo_root / "PROJECT_STATE.md").is_file():
                    (repo_root / "PROJECT_STATE.md").unlink()
            if session_handoff_content is not None:
                (repo_root / "SESSION_HANDOFF.md").write_text(session_handoff_content, encoding="utf-8")
            else:
                if (repo_root / "SESSION_HANDOFF.md").is_file():
                    (repo_root / "SESSION_HANDOFF.md").unlink()
            if context_content is not None:
                (repo_root / "PROJECT_CONTEXT.md").write_text(context_content, encoding="utf-8")
            else:
                if (repo_root / "PROJECT_CONTEXT.md").is_file():
                    (repo_root / "PROJECT_CONTEXT.md").unlink()
            if plugin_json_content is not None:
                (repo_root / "plugin.json").write_text(plugin_json_content, encoding="utf-8")
            else:
                if (repo_root / "plugin.json").is_file():
                    (repo_root / "plugin.json").unlink()

        original_get_remote = gc.get_remote_default_branch
        original_get_current = gc.get_current_git_branch
        original_get_plugin_version = gc.get_plugin_version

        mock_remote_default = "main"
        mock_current_branch = "fix/example-feature"

        gc.get_remote_default_branch = lambda r: mock_remote_default
        gc.get_current_git_branch = lambda r: mock_current_branch

        # 1. Canonical branch matches base branch (main) -> PASS
        write_test_files(
            "Canonical Branch: main\nBase Branch: main\n",
            "Canonical Branch: main\nBase Branch: main\n"
        )
        counters = {"warnings": 0, "errors": 0}
        gc.run_startup_state_claim_check(str(repo_root), counters, strict_mode=True)
        assert_equal("canonical matches base - pass", counters["errors"], 0)

        # 2. Canonical branch mismatch with base branch -> FAIL
        write_test_files(
            "Canonical Branch: main\nBase Branch: dev\n",
            "Canonical Branch: main\nBase Branch: main\n"
        )
        counters = {"warnings": 0, "errors": 0}
        gc.run_startup_state_claim_check(str(repo_root), counters, strict_mode=True)
        assert_equal("canonical mismatch base - fail", counters["errors"] > 0, True)

        # 3. Missing canonical branch -> FAIL
        write_test_files(
            "Base Branch: main\n",
            "Canonical Branch: main\nBase Branch: main\n"
        )
        counters = {"warnings": 0, "errors": 0}
        gc.run_startup_state_claim_check(str(repo_root), counters, strict_mode=True)
        assert_equal("missing canonical - fail", counters["errors"] > 0, True)

        # 4. Duplicate canonical branch claims -> FAIL
        write_test_files(
            "Canonical Branch: main\nCanonical Branch: main\nBase Branch: main\n",
            "Canonical Branch: main\nBase Branch: main\n"
        )
        counters = {"warnings": 0, "errors": 0}
        gc.run_startup_state_claim_check(str(repo_root), counters, strict_mode=True)
        assert_equal("duplicate canonical - fail", counters["errors"] > 0, True)

        # 5. Rejection of legacy Current Branch -> FAIL
        write_test_files(
            "Canonical Branch: main\nBase Branch: main\nCurrent Branch: fix/some-feature\n",
            "Canonical Branch: main\nBase Branch: main\n"
        )
        counters = {"warnings": 0, "errors": 0}
        gc.run_startup_state_claim_check(str(repo_root), counters, strict_mode=True)
        assert_equal("rejection of legacy Current Branch - fail", counters["errors"] > 0, True)

        # 6. Remote-default mismatch -> FAIL
        mock_remote_default = "master"
        write_test_files(
            "Canonical Branch: main\nBase Branch: main\n",
            "Canonical Branch: main\nBase Branch: main\n"
        )
        counters = {"warnings": 0, "errors": 0}
        gc.run_startup_state_claim_check(str(repo_root), counters, strict_mode=True)
        assert_equal("remote-default mismatch - fail", counters["errors"] > 0, True)

        mock_remote_default = "main"

        # 7. Version checks remain unchanged -> PASS and FAIL scenarios
        plugin_json = '{"version": "1.1.2"}'
        write_test_files(
            "Canonical Branch: main\nBase Branch: main\n",
            "Canonical Branch: main\nBase Branch: main\n",
            context_content="## Current Stage\nv1.1.2 - Release\n",
            plugin_json_content=plugin_json
        )
        counters = {"warnings": 0, "errors": 0}
        gc.run_startup_state_claim_check(str(repo_root), counters, strict_mode=True)
        assert_equal("version matches - pass", counters["errors"], 0)

        write_test_files(
            "Canonical Branch: main\nBase Branch: main\n",
            "Canonical Branch: main\nBase Branch: main\n",
            context_content="## Current Stage\nv1.1.1 - Release\n",
            plugin_json_content=plugin_json
        )
        counters = {"warnings": 0, "errors": 0}
        gc.run_startup_state_claim_check(str(repo_root), counters, strict_mode=True)
        assert_equal("version mismatch - fail", counters["errors"] > 0, True)

        gc.get_remote_default_branch = original_get_remote
        gc.get_current_git_branch = original_get_current
        gc.get_plugin_version = original_get_plugin_version


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
    test_artificer_governance_validator_is_registered()
    test_artificer_audit_renderer_is_registered_read_only()
    test_repo_memory_path_check()
    test_startup_state_claim_check()
    print("Governance check helper tests passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
