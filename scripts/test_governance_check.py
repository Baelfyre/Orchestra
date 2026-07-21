import os
import subprocess
import sys
import tempfile
from pathlib import Path

import governance_check as gc

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.codex import validate_codex_export


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


def test_artificer_pattern_catalog_validator_is_registered():
    script = "scripts/validate_artificer_pattern_catalog.py"
    assert_equal("required catalog validator", script in gc.REQUIRED_VALIDATION_SCRIPTS, True)
    assert_equal("strict catalog validator", script in gc.STRICT_VALIDATOR_SCRIPTS, True)


def test_issue_171_validators_are_registered():
    for script in (
        "scripts/validate_prompt_load_budget.py",
        "scripts/validate_governance_protocol_consistency.py",
        "scripts/validate_routing_contract.py",
    ):
        assert_equal(f"required {script}", script in gc.REQUIRED_VALIDATION_SCRIPTS, True)
        assert_equal(f"strict {script}", script in gc.STRICT_VALIDATOR_SCRIPTS, True)


def test_codex_parity_normalizes_only_approved_reference_depths():
    normalize = validate_codex_export.normalize_body_for_parity
    source = "See `../../docs/routing/EXECUTION_MODES_POLICY.md`.\n"
    exported = "See `../../../../docs/routing/EXECUTION_MODES_POLICY.md`.\n"
    assert_equal("approved reference depth", normalize(source), normalize(exported))

    negative_cases = {
        "changed prose": (source, "Read `../../../../docs/routing/EXECUTION_MODES_POLICY.md`.\n"),
        "changed filename": (source, "See `../../../../docs/routing/MINIMAL_PROMPT_FORMAT.md`.\n"),
        "changed code example": (
            "```text\n../../docs/routing/EXECUTION_MODES_POLICY.md\n```\n",
            "```text\n../../../../docs/routing/EXECUTION_MODES_POLICY.md\n```\n",
        ),
        "unrelated relative path": ("See `../../notes/example.md`.\n", "See `../../../../notes/example.md`.\n"),
    }
    for name, (left, right) in negative_cases.items():
        assert_equal(name, normalize(left) != normalize(right), True)


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


def test_active_branch_memory_path_exception():
    with tempfile.TemporaryDirectory(prefix="governance-active-branch-test-") as temp_dir:
        repo_root = Path(temp_dir)
        (repo_root / "docs" / "governance").mkdir(parents=True)
        (repo_root / "docs" / "governance" / "GOVERNANCE_LAYER.md").write_text("# Layer\n", encoding="utf-8")

        memory_content = (
            "- Active branch: `docs/delegated-autonomous-governance-phase-a`\n"
            "- Similar branch: `docs/delegated-autonomous-governance-phase-b`\n"
            "- Nonexistent path: `docs/governance/DOES_NOT_EXIST.md`\n"
            "- Existing path: `docs/governance/GOVERNANCE_LAYER.md`\n"
        )
        (repo_root / "SESSION_HANDOFF.md").write_text(memory_content, encoding="utf-8")

        original_get_current = gc.get_current_git_branch
        gc.get_current_git_branch = lambda r: "docs/delegated-autonomous-governance-phase-a"

        try:
            counters = {"warnings": 0, "errors": 0}
            gc.run_repo_memory_path_check(str(repo_root), counters)
            assert_equal("active branch exception errors count (expects 2 errors for phase-b and DOES_NOT_EXIST)", counters["errors"], 2)
        finally:
            gc.get_current_git_branch = original_get_current


def test_known_git_branches_detached_head_and_ci():
    with tempfile.TemporaryDirectory(prefix="governance-detached-test-") as temp_dir:
        repo_root = Path(temp_dir)
        (repo_root / "docs" / "governance").mkdir(parents=True)
        (repo_root / "docs" / "governance" / "GOVERNANCE_LAYER.md").write_text("# Layer\n", encoding="utf-8")

        gc.run_git(str(repo_root), "init")
        gc.run_git(str(repo_root), "config", "user.name", "Test")
        gc.run_git(str(repo_root), "config", "user.email", "test@example.com")

        (repo_root / "README.md").write_text("# Test\n", encoding="utf-8")
        gc.run_git(str(repo_root), "add", ".")
        gc.run_git(str(repo_root), "commit", "-m", "initial")

        branch_name = "docs/delegated-autonomous-governance-phase-a"
        gc.run_git(str(repo_root), "update-ref", f"refs/remotes/origin/{branch_name}", "HEAD")
        gc.run_git(str(repo_root), "checkout", "--detach", "HEAD")

        current_branch = gc.get_current_git_branch(str(repo_root))
        assert_equal("detached HEAD git branch --show-current is empty", current_branch, None)

        known = gc.get_known_git_branches(str(repo_root))
        assert_equal("remote tracking branch discovered in detached HEAD", branch_name in known, True)
        assert_equal("remote prefixed branch discovered in detached HEAD", f"origin/{branch_name}" in known, True)

        memory_content = (
            f"- Active branch: `{branch_name}`\n"
            f"- Remote branch: `origin/{branch_name}`\n"
            "- Similar branch: `docs/delegated-autonomous-governance-phase-b`\n"
            "- Nonexistent path: `docs/governance/DOES_NOT_EXIST.md`\n"
            "- Existing path: `docs/governance/GOVERNANCE_LAYER.md`\n"
            "- Random missing path: `docs/random-missing-value`\n"
        )
        (repo_root / "SESSION_HANDOFF.md").write_text(memory_content, encoding="utf-8")

        counters = {"warnings": 0, "errors": 0}
        gc.run_repo_memory_path_check(str(repo_root), counters)
        assert_equal("detached HEAD memory check errors count (phase-b, DOES_NOT_EXIST, random-missing-value = 3)", counters["errors"], 3)

        old_gh_head = os.environ.get("GITHUB_HEAD_REF")
        try:
            os.environ["GITHUB_HEAD_REF"] = "docs/ci-feature-branch"
            known_ci = gc.get_known_git_branches(str(repo_root))
            assert_equal("GITHUB_HEAD_REF recognized in known branches", "docs/ci-feature-branch" in known_ci, True)
        finally:
            if old_gh_head is None:
                os.environ.pop("GITHUB_HEAD_REF", None)
            else:
                os.environ["GITHUB_HEAD_REF"] = old_gh_head

        original_run_git = gc.run_git
        def mock_run_git(root, *args):
            if args and args[0] == "for-each-ref":
                class DummyResult:
                    returncode = 1
                    stdout = ""
                return DummyResult()
            return original_run_git(root, *args)

        gc.run_git = mock_run_git
        try:
            known_fallback = gc.get_known_git_branches(str(repo_root))
            assert_equal("graceful fallback on for-each-ref failure does not crash", isinstance(known_fallback, set), True)
        finally:
            gc.run_git = original_run_git


def test_isolated_github_head_ref_and_ref_name_rejection():
    with tempfile.TemporaryDirectory(prefix="governance-gh-head-test-") as temp_dir:
        repo_root = Path(temp_dir)
        gc.run_git(str(repo_root), "init")
        gc.run_git(str(repo_root), "config", "user.name", "Test")
        gc.run_git(str(repo_root), "config", "user.email", "test@example.com")
        (repo_root / "README.md").write_text("# Test\n", encoding="utf-8")
        gc.run_git(str(repo_root), "add", ".")
        gc.run_git(str(repo_root), "commit", "-m", "initial")
        gc.run_git(str(repo_root), "checkout", "--detach", "HEAD")

        feature_branch = "docs/delegated-autonomous-governance-phase-a"

        old_gh_head = os.environ.get("GITHUB_HEAD_REF")
        old_gh_ref = os.environ.get("GITHUB_REF_NAME")

        try:
            os.environ.pop("GITHUB_HEAD_REF", None)
            os.environ.pop("GITHUB_REF_NAME", None)

            initial_known = gc.get_known_git_branches(str(repo_root))
            assert_equal("feature branch absent from clean git refs", feature_branch in initial_known, False)

            os.environ["GITHUB_HEAD_REF"] = feature_branch
            os.environ["GITHUB_REF_NAME"] = "189/merge"

            known = gc.get_known_git_branches(str(repo_root))
            assert_equal("GITHUB_HEAD_REF accepted independently without git refs", feature_branch in known, True)
            assert_equal("GITHUB_REF_NAME 189/merge is not in known branches", "189/merge" in known, False)

            (repo_root / "SESSION_HANDOFF.md").write_text(f"- Active branch: `{feature_branch}`\n", encoding="utf-8")
            counters = {"warnings": 0, "errors": 0}
            gc.run_repo_memory_path_check(str(repo_root), counters)
            assert_equal("isolated GITHUB_HEAD_REF accepted in memory check", counters["errors"], 0)
        finally:
            if old_gh_head is None:
                os.environ.pop("GITHUB_HEAD_REF", None)
            else:
                os.environ["GITHUB_HEAD_REF"] = old_gh_head
            if old_gh_ref is None:
                os.environ.pop("GITHUB_REF_NAME", None)
            else:
                os.environ["GITHUB_REF_NAME"] = old_gh_ref


def test_git_enumeration_failure_fail_closed():
    with tempfile.TemporaryDirectory(prefix="governance-enum-fail-test-") as temp_dir:
        repo_root = Path(temp_dir)
        (repo_root / "docs" / "governance").mkdir(parents=True)
        (repo_root / "docs" / "governance" / "GOVERNANCE_LAYER.md").write_text("# Layer\n", encoding="utf-8")

        gc.run_git(str(repo_root), "init")
        gc.run_git(str(repo_root), "config", "user.name", "Test")
        gc.run_git(str(repo_root), "config", "user.email", "test@example.com")
        (repo_root / "README.md").write_text("# Test\n", encoding="utf-8")
        gc.run_git(str(repo_root), "add", ".")
        gc.run_git(str(repo_root), "commit", "-m", "initial")
        gc.run_git(str(repo_root), "checkout", "--detach", "HEAD")

        feature_branch = "docs/delegated-autonomous-governance-phase-a"
        old_gh_head = os.environ.get("GITHUB_HEAD_REF")
        original_run_git = gc.run_git

        def mock_run_git(root, *args):
            if args and args[0] == "for-each-ref":
                class DummyResult:
                    returncode = 1
                    stdout = ""
                return DummyResult()
            return original_run_git(root, *args)

        gc.run_git = mock_run_git
        try:
            os.environ["GITHUB_HEAD_REF"] = feature_branch
            memory_content = (
                f"- Active branch: `{feature_branch}`\n"
                "- Unknown branch: `docs/delegated-autonomous-governance-phase-b`\n"
                "- Nonexistent path: `docs/governance/DOES_NOT_EXIST.md`\n"
                "- Existing path: `docs/governance/GOVERNANCE_LAYER.md`\n"
            )
            (repo_root / "SESSION_HANDOFF.md").write_text(memory_content, encoding="utf-8")

            counters = {"warnings": 0, "errors": 0}
            gc.run_repo_memory_path_check(str(repo_root), counters)
            assert_equal("enumeration failure fail-closed errors count (expects 2 for phase-b and DOES_NOT_EXIST)", counters["errors"], 2)
        finally:
            gc.run_git = original_run_git
            if old_gh_head is None:
                os.environ.pop("GITHUB_HEAD_REF", None)
            else:
                os.environ["GITHUB_HEAD_REF"] = old_gh_head


def test_wildcard_glob_handling_regression():
    assert_equal("glob docs/* excluded", gc.is_repo_relative_memory_path("docs/*"), False)
    assert_equal("glob scripts/*.py excluded", gc.is_repo_relative_memory_path("scripts/*.py"), False)
    assert_equal("glob tests/behavior/test_?.py excluded", gc.is_repo_relative_memory_path("tests/behavior/test_?.py"), False)

    assert_equal("ordinary missing path included", gc.is_repo_relative_memory_path("docs/random-missing-value"), True)
    assert_equal("ordinary missing file included", gc.is_repo_relative_memory_path("docs/governance/DOES_NOT_EXIST.md"), True)


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
    test_artificer_pattern_catalog_validator_is_registered()
    test_issue_171_validators_are_registered()
    test_codex_parity_normalizes_only_approved_reference_depths()
    test_repo_memory_path_check()
    test_active_branch_memory_path_exception()
    test_known_git_branches_detached_head_and_ci()
    test_isolated_github_head_ref_and_ref_name_rejection()
    test_git_enumeration_failure_fail_closed()
    test_wildcard_glob_handling_regression()
    test_startup_state_claim_check()
    print("Governance check helper tests passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
