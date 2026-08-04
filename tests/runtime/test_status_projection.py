"""Comprehensive unit, validation, and authority-boundary tests for OrchestraStatusProjection."""

import datetime
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from orchestra_runtime import (
    STATUS_PROJECTION_VERSION,
    ContractStatus,
    DiagnosticsStatus,
    GitStatus,
    OrchestraStatusProjection,
    ProjectStatus,
    StatusDiagnostic,
    ValidationStatus,
    build_status_projection,
    collect_contract_status,
    collect_git_status,
    collect_project_status,
    reconcile_validation_status,
    render_status_projection,
    serialize_status_projection,
    serialize_status_projection_to_str,
)
from orchestra_runtime.status import _parse_porcelain_v1_z, main, redact_url_credentials


class EvidenceStub:
    def __init__(
        self,
        revision=None,
        governance_check=None,
        preflight_sync=None,
        runtime_test_count=None,
        runtime_coverage=None,
    ):
        self.revision = revision
        self.governance_check = governance_check
        self.preflight_sync = preflight_sync
        self.runtime_test_count = runtime_test_count
        self.runtime_coverage = runtime_coverage


class TestStatusProjectionModel(unittest.TestCase):
    def test_immutability(self):
        git_st = GitStatus(is_git_repo=True, current_branch="main", head_sha="a1b2c3d4e5f6")
        with self.assertRaises(Exception):
            git_st.current_branch = "other"  # type: ignore

        proj = OrchestraStatusProjection(
            projection_version=STATUS_PROJECTION_VERSION,
            timestamp="2026-08-05T00:00:00Z",
            git=git_st,
            project=ProjectStatus(current_release="v1.1.2"),
            contracts=ContractStatus(),
            validation=ValidationStatus(),
            diagnostics=DiagnosticsStatus(),
        )
        with self.assertRaises(Exception):
            proj.timestamp = "2026-08-06T00:00:00Z"  # type: ignore

    def test_deterministic_serialization(self):
        def runner(args, cwd):
            cmd = list(args)
            if cmd == ["git", "rev-parse", "--is-inside-work-tree"]:
                return subprocess.CompletedProcess(args, 0, "true\n", "")
            if cmd == ["git", "rev-parse", "HEAD"]:
                return subprocess.CompletedProcess(args, 0, "e55658da698e7b8871dd7851c62b9e22d860fb2f\n", "")
            if cmd == ["git", "symbolic-ref", "--quiet", "--short", "HEAD"]:
                return subprocess.CompletedProcess(args, 0, "main\n", "")
            if cmd == ["git", "rev-parse", "--git-common-dir"]:
                return subprocess.CompletedProcess(args, 0, ".git\n", "")
            if cmd == ["git", "rev-parse", "--git-dir"]:
                return subprocess.CompletedProcess(args, 0, ".git\n", "")
            if cmd == ["git", "rev-parse", "--is-shallow-repository"]:
                return subprocess.CompletedProcess(args, 0, "false\n", "")
            if cmd == ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"]:
                return subprocess.CompletedProcess(args, 0, b"", "")
            if cmd == ["git", "remote"]:
                return subprocess.CompletedProcess(args, 0, "origin\n", "")
            if cmd == ["git", "rev-parse", "--verify", "origin/main"]:
                return subprocess.CompletedProcess(args, 0, "e55658da698e7b8871dd7851c62b9e22d860fb2f\n", "")
            if cmd == ["git", "rev-list", "--left-right", "--count", "HEAD...origin/main"]:
                return subprocess.CompletedProcess(args, 0, "0\t0\n", "")
            return subprocess.CompletedProcess(args, 1, "", "")

        proj = build_status_projection(
            Path("."),
            now=datetime.datetime(2026, 8, 5, 12, 0, 0, tzinfo=datetime.timezone.utc),
            command_runner=runner,
        )
        s1 = serialize_status_projection_to_str(proj)
        s2 = serialize_status_projection_to_str(proj)
        self.assertEqual(s1, s2)
        data = json.loads(s1)
        self.assertEqual(data["projection_version"], STATUS_PROJECTION_VERSION)
        self.assertEqual(data["timestamp"], "2026-08-05T12:00:00Z")


class TestF002ModelValidation(unittest.TestCase):
    def test_status_diagnostic_validation(self):
        diag = StatusDiagnostic(severity="WARNING", message="test warning", field_path="git.head_sha")
        self.assertEqual(diag.severity, "WARNING")
        with self.assertRaises(ValueError):
            StatusDiagnostic(severity="INVALID", message="test")
        with self.assertRaises(ValueError):
            StatusDiagnostic(severity="WARNING", message="")

    def test_git_status_post_init_validation(self):
        with self.assertRaises(TypeError):
            GitStatus(is_git_repo="not_bool")  # type: ignore
        with self.assertRaises(TypeError):
            GitStatus(is_git_repo=True, staged_count=True)  # type: ignore
        with self.assertRaises(TypeError):
            GitStatus(is_git_repo=True, staged_count="str_count")  # type: ignore
        with self.assertRaises(ValueError):
            GitStatus(is_git_repo=True, staged_count=-1)
        with self.assertRaises(ValueError):
            GitStatus(is_git_repo=True, head_sha="not_a_sha!")
        with self.assertRaises(ValueError):
            GitStatus(is_git_repo=True, selected_remote="upstream", remote_names=("origin",))
        with self.assertRaises(ValueError):
            GitStatus(is_git_repo=True, selected_main_ref="origin/main", selected_remote=None)
        with self.assertRaises(ValueError):
            GitStatus(
                is_git_repo=True,
                is_clean=True,
                staged_count=1,
                modified_count=0,
                untracked_count=0,
            )

    def test_project_status_validation(self):
        with self.assertRaises(ValueError):
            ProjectStatus(current_release="")
        with self.assertRaises(TypeError):
            ProjectStatus(current_release=123)  # type: ignore
        with self.assertRaises(TypeError):
            ProjectStatus(policy_integrated="not_bool")  # type: ignore

    def test_validation_status_validation(self):
        with self.assertRaises(ValueError):
            ValidationStatus(runtime_coverage="invalid_cov")
        with self.assertRaises(ValueError):
            ValidationStatus(runtime_coverage="105%")
        with self.assertRaises(ValueError):
            ValidationStatus(runtime_coverage="-5%")
        v_ok = ValidationStatus(runtime_coverage="93.72%")
        self.assertEqual(v_ok.runtime_coverage, "93.72%")

    def test_orchestra_status_projection_validation(self):
        git_st = GitStatus(is_git_repo=True)
        proj_st = ProjectStatus()
        cont_st = ContractStatus()
        val_st = ValidationStatus()
        diag_st = DiagnosticsStatus()

        with self.assertRaises(ValueError):
            OrchestraStatusProjection(
                projection_version="99.0",
                timestamp="2026-08-05T00:00:00Z",
                git=git_st,
                project=proj_st,
                contracts=cont_st,
                validation=val_st,
                diagnostics=diag_st,
            )
        with self.assertRaises(ValueError):
            OrchestraStatusProjection(
                projection_version=STATUS_PROJECTION_VERSION,
                timestamp="naive_timestamp_no_tz",
                git=git_st,
                project=proj_st,
                contracts=cont_st,
                validation=val_st,
                diagnostics=diag_st,
            )
        with self.assertRaises(TypeError):
            OrchestraStatusProjection(
                projection_version=STATUS_PROJECTION_VERSION,
                timestamp="2026-08-05T00:00:00Z",
                git="not_a_git_status",  # type: ignore
                project=proj_st,
                contracts=cont_st,
                validation=val_st,
                diagnostics=diag_st,
            )
        with self.assertRaises(TypeError):
            OrchestraStatusProjection(
                projection_version=STATUS_PROJECTION_VERSION,
                timestamp="2026-08-05T00:00:00Z",
                git=git_st,
                project="not_project",  # type: ignore
                contracts=cont_st,
                validation=val_st,
                diagnostics=diag_st,
            )
        with self.assertRaises(TypeError):
            OrchestraStatusProjection(
                projection_version=STATUS_PROJECTION_VERSION,
                timestamp="2026-08-05T00:00:00Z",
                git=git_st,
                project=proj_st,
                contracts="not_contract",  # type: ignore
                validation=val_st,
                diagnostics=diag_st,
            )
        with self.assertRaises(TypeError):
            OrchestraStatusProjection(
                projection_version=STATUS_PROJECTION_VERSION,
                timestamp="2026-08-05T00:00:00Z",
                git=git_st,
                project=proj_st,
                contracts=cont_st,
                validation="not_val",  # type: ignore
                diagnostics=diag_st,
            )
        with self.assertRaises(TypeError):
            OrchestraStatusProjection(
                projection_version=STATUS_PROJECTION_VERSION,
                timestamp="2026-08-05T00:00:00Z",
                git=git_st,
                project=proj_st,
                contracts=cont_st,
                validation=val_st,
                diagnostics="not_diag",  # type: ignore
            )
        with self.assertRaises(TypeError):
            DiagnosticsStatus(unknown_fields="not_a_seq")  # type: ignore
        with self.assertRaises(ValueError):
            DiagnosticsStatus(unknown_fields=("",))

    def test_build_status_projection_naive_now_rejected(self):
        with self.assertRaises(ValueError):
            build_status_projection(
                Path("."),
                now=datetime.datetime(2026, 8, 5, 12, 0, 0),  # naive
            )


class TestF003PorcelainZParsing(unittest.TestCase):
    def test_parse_porcelain_z_ordinary(self):
        raw = b" M file1.txt\x00?? file2.txt\x00A  file3.txt\x00"
        staged, modified, untracked, is_clean = _parse_porcelain_v1_z(raw)
        self.assertFalse(is_clean)
        self.assertEqual(staged, 1)
        self.assertEqual(modified, 1)
        self.assertEqual(untracked, 1)

    def test_parse_porcelain_z_rename_and_spaces(self):
        raw = b"R  old name.txt\x00new name.txt\x00?? path with spaces.py\x00"
        staged, modified, untracked, is_clean = _parse_porcelain_v1_z(raw)
        self.assertFalse(is_clean)
        self.assertEqual(staged, 1)
        self.assertEqual(untracked, 1)

    def test_parse_porcelain_z_clean(self):
        staged, modified, untracked, is_clean = _parse_porcelain_v1_z(b"")
        self.assertTrue(is_clean)
        self.assertEqual(staged, 0)
        self.assertEqual(modified, 0)
        self.assertEqual(untracked, 0)


class TestRedactionAndPrivacy(unittest.TestCase):
    def test_credential_redaction(self):
        raw = "Origin URL: https://token123:secret456@github.com/Baelfyre/Orchestra.git"
        redacted = redact_url_credentials(raw)
        self.assertNotIn("token123", redacted)
        self.assertNotIn("secret456", redacted)
        self.assertIn("https://***:***@github.com", redacted)


class TestGitCollectorScenarios(unittest.TestCase):
    def test_not_a_git_repo(self):
        def runner(args, cwd):
            return subprocess.CompletedProcess(args, 128, "", "fatal: not a git repository\n")

        status, unknowns, warnings = collect_git_status(Path("."), command_runner=runner)
        self.assertFalse(status.is_git_repo)
        self.assertIn("git.current_branch", unknowns)

    def test_git_unavailable(self):
        def runner(args, cwd):
            raise FileNotFoundError("git not found")

        status, unknowns, warnings = collect_git_status(Path("."), command_runner=runner)
        self.assertFalse(status.is_git_repo)
        self.assertTrue(any("Git executable unavailable" in w for w in warnings))

    def test_git_timeout(self):
        def runner(args, cwd):
            raise subprocess.TimeoutExpired(args, 10)

        status, unknowns, warnings = collect_git_status(Path("."), command_runner=runner)
        self.assertFalse(status.is_git_repo)
        self.assertTrue(any("timed out" in w for w in warnings))

    def test_unborn_branch(self):
        def runner(args, cwd):
            cmd = list(args)
            if cmd == ["git", "rev-parse", "--is-inside-work-tree"]:
                return subprocess.CompletedProcess(args, 0, "true\n", "")
            if cmd == ["git", "rev-parse", "HEAD"]:
                return subprocess.CompletedProcess(args, 128, "", "fatal: ambiguous argument 'HEAD'\n")
            if cmd == ["git", "rev-parse", "--git-common-dir"]:
                return subprocess.CompletedProcess(args, 0, ".git\n", "")
            if cmd == ["git", "rev-parse", "--git-dir"]:
                return subprocess.CompletedProcess(args, 0, ".git\n", "")
            if cmd == ["git", "rev-parse", "--is-shallow-repository"]:
                return subprocess.CompletedProcess(args, 0, "false\n", "")
            if cmd == ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"]:
                return subprocess.CompletedProcess(args, 0, "", "")
            if cmd == ["git", "remote"]:
                return subprocess.CompletedProcess(args, 0, "", "")
            return subprocess.CompletedProcess(args, 1, "", "")

        status, unknowns, warnings = collect_git_status(Path("."), command_runner=runner)
        self.assertTrue(status.is_git_repo)
        self.assertEqual(status.current_branch, "unborn")
        self.assertIsNone(status.head_sha)
        self.assertIn("git.head_sha", unknowns)

    def test_detached_head(self):
        def runner(args, cwd):
            cmd = list(args)
            if cmd == ["git", "rev-parse", "--is-inside-work-tree"]:
                return subprocess.CompletedProcess(args, 0, "true\n", "")
            if cmd == ["git", "rev-parse", "HEAD"]:
                return subprocess.CompletedProcess(args, 0, "a1b2c3d4e5f67890\n", "")
            if cmd == ["git", "symbolic-ref", "--quiet", "--short", "HEAD"]:
                return subprocess.CompletedProcess(args, 1, "", "")
            if cmd == ["git", "rev-parse", "--git-common-dir"]:
                return subprocess.CompletedProcess(args, 0, ".git\n", "")
            if cmd == ["git", "rev-parse", "--git-dir"]:
                return subprocess.CompletedProcess(args, 0, ".git\n", "")
            if cmd == ["git", "rev-parse", "--is-shallow-repository"]:
                return subprocess.CompletedProcess(args, 0, "false\n", "")
            if cmd == ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"]:
                return subprocess.CompletedProcess(args, 0, "", "")
            if cmd == ["git", "remote"]:
                return subprocess.CompletedProcess(args, 0, "", "")
            return subprocess.CompletedProcess(args, 1, "", "")

        status, unknowns, warnings = collect_git_status(Path("."), command_runner=runner)
        self.assertTrue(status.is_git_repo)
        self.assertEqual(status.current_branch, "(HEAD detached at a1b2c3d)")
        self.assertEqual(status.head_sha, "a1b2c3d4e5f67890")

    def test_multiple_remotes_fallback(self):
        def runner(args, cwd):
            cmd = list(args)
            if cmd == ["git", "rev-parse", "--is-inside-work-tree"]:
                return subprocess.CompletedProcess(args, 0, "true\n", "")
            if cmd == ["git", "rev-parse", "HEAD"]:
                return subprocess.CompletedProcess(args, 0, "a1b2c3d4e5f67890\n", "")
            if cmd == ["git", "symbolic-ref", "--quiet", "--short", "HEAD"]:
                return subprocess.CompletedProcess(args, 0, "main\n", "")
            if cmd == ["git", "rev-parse", "--git-common-dir"]:
                return subprocess.CompletedProcess(args, 0, ".git\n", "")
            if cmd == ["git", "rev-parse", "--git-dir"]:
                return subprocess.CompletedProcess(args, 0, ".git\n", "")
            if cmd == ["git", "rev-parse", "--is-shallow-repository"]:
                return subprocess.CompletedProcess(args, 0, "false\n", "")
            if cmd == ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"]:
                return subprocess.CompletedProcess(args, 0, b" M file.py\x00?? new.txt\x00", "")
            if cmd == ["git", "remote"]:
                return subprocess.CompletedProcess(args, 0, "upstream\nbackup\n", "")
            if cmd == ["git", "rev-parse", "--verify", "backup/main"]:
                return subprocess.CompletedProcess(args, 0, "f1e2d3c4b5a67890\n", "")
            if cmd == ["git", "rev-list", "--left-right", "--count", "HEAD...backup/main"]:
                return subprocess.CompletedProcess(args, 0, "2\t1\n", "")
            return subprocess.CompletedProcess(args, 1, "", "")

        status, unknowns, warnings = collect_git_status(Path("."), command_runner=runner)
        self.assertEqual(status.selected_remote, "backup")
        self.assertEqual(status.selected_main_sha, "f1e2d3c4b5a67890")
        self.assertEqual(status.ahead_count, 2)
        self.assertEqual(status.behind_count, 1)
        self.assertEqual(status.modified_count, 1)
        self.assertEqual(status.untracked_count, 1)
        self.assertFalse(status.is_clean)

    def test_secondary_worktree_detection(self):
        def runner(args, cwd):
            cmd = list(args)
            if cmd == ["git", "rev-parse", "--is-inside-work-tree"]:
                return subprocess.CompletedProcess(args, 0, "true\n", "")
            if cmd == ["git", "rev-parse", "HEAD"]:
                return subprocess.CompletedProcess(args, 0, "a1b2c3d4e5f67890\n", "")
            if cmd == ["git", "symbolic-ref", "--quiet", "--short", "HEAD"]:
                return subprocess.CompletedProcess(args, 0, "feature-branch\n", "")
            if cmd == ["git", "rev-parse", "--git-common-dir"]:
                return subprocess.CompletedProcess(args, 0, "C:/repo/.git\n", "")
            if cmd == ["git", "rev-parse", "--git-dir"]:
                return subprocess.CompletedProcess(args, 0, "C:/repo/.git/worktrees/wt1\n", "")
            if cmd == ["git", "rev-parse", "--is-shallow-repository"]:
                return subprocess.CompletedProcess(args, 0, "false\n", "")
            if cmd == ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"]:
                return subprocess.CompletedProcess(args, 0, b"", "")
            if cmd == ["git", "remote"]:
                return subprocess.CompletedProcess(args, 0, "", "")
            return subprocess.CompletedProcess(args, 1, "", "")

        status, unknowns, warnings = collect_git_status(Path("."), command_runner=runner)
        self.assertTrue(status.is_worktree)
        self.assertEqual(status.worktree_path_redacted, "[worktree: feature-branch]")


class TestProjectAndContractCollector(unittest.TestCase):
    def test_collect_project_status_with_temp_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            state_file = tmp_path / "PROJECT_STATE.md"
            state_file.write_text(
                "- **Current Public Release:** `v1.1.2`\n"
                "- **Next Active Software Task:** Candidate Phase 3B\n",
                encoding="utf-8",
            )
            context_file = tmp_path / "PROJECT_CONTEXT.md"
            context_file.write_text("DELEGATED_EXECUTION_POLICY.md included", encoding="utf-8")

            st, unk, conf = collect_project_status(tmp_path)
            self.assertEqual(st.current_release, "v1.1.2")
            self.assertEqual(st.active_phase, "Candidate Phase 3B")
            self.assertTrue(st.policy_integrated)
            self.assertEqual(len(conf), 0)

    def test_collect_contract_status_with_temp_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            doc_dir = tmp_path / "docs" / "project"
            doc_dir.mkdir(parents=True)
            c_file = doc_dir / "SPEC_KITTY_DERIVED_CONTRACT_OWNERSHIP.md"
            c_file.write_text(
                "| **OrchestraRuntimeEnvelope** | path | owner | consumer | val | cont | `DESIGN_SPECIFIED` | `IMPLEMENTED_MERGED` |\n"
                "| **OrchestraStatusProjection** | path | owner | consumer | val | cont | `DESIGN_ACCEPTED_MERGED` | `NOT_IMPLEMENTED` |\n",
                encoding="utf-8",
            )

            st, unk = collect_contract_status(tmp_path)
            self.assertIn("IMPLEMENTED_MERGED", st.runtime_envelope or "")
            self.assertIn("DESIGN_ACCEPTED_MERGED", st.status_projection or "")


class TestValidationEvidenceReconciliation(unittest.TestCase):
    def test_matching_evidence(self):
        ev = EvidenceStub(
            revision="a1b2c3d4e5f67890",
            governance_check="PASS",
            preflight_sync="PASS",
            runtime_test_count=390,
            runtime_coverage="93.72%",
        )
        st, unk, warn = reconcile_validation_status("a1b2c3d4e5f67890", ev)
        self.assertTrue(st.revision_match)
        self.assertEqual(st.governance_check, "PASS")
        self.assertEqual(len(warn), 0)

    def test_mismatched_evidence(self):
        ev = EvidenceStub(
            revision="f1e2d3c4b5a67890",
            governance_check="PASS",
        )
        st, unk, warn = reconcile_validation_status("a1b2c3d4e5f67890", ev)
        self.assertFalse(st.revision_match)
        self.assertTrue(any("does not match" in w for w in warn))


class TestCLISurfaceAndRendering(unittest.TestCase):
    def test_render_status_projection_all_sections(self):
        proj = OrchestraStatusProjection(
            projection_version=STATUS_PROJECTION_VERSION,
            timestamp="2026-08-05T00:00:00Z",
            git=GitStatus(is_git_repo=True, current_branch="main", head_sha="a1b2c3d4e5f67890", is_clean=True),
            project=ProjectStatus(current_release="v1.1.2"),
            contracts=ContractStatus(),
            validation=ValidationStatus(),
            diagnostics=DiagnosticsStatus(
                unknown_fields=("git.selected_remote",),
                conflicts=("Conflict 1",),
                warnings=("Warning 1",),
            ),
        )
        rendered = render_status_projection(proj)
        self.assertIn("--- Git Status ---", rendered)
        self.assertIn("--- Unknown Fields ---", rendered)
        self.assertIn("--- Conflicts ---", rendered)
        self.assertIn("--- Warnings ---", rendered)

    def test_main_cli_modes_and_errors(self):
        self.assertEqual(main(["--repo", ".", "--quiet"]), 0)
        self.assertEqual(main(["--repo", "non_existent_path_123456", "--quiet"]), 1)
        self.assertEqual(main(["--repo", "non_existent_path_123456"]), 1)

    def test_main_cli_json_and_human(self):
        self.assertEqual(main(["--repo", ".", "--json"]), 0)
        self.assertEqual(main(["--repo", "."]), 0)

    def test_script_wrapper_invocable(self):
        res = subprocess.run(
            [sys.executable, "scripts/orchestra_status.py", "--repo", ".", "--json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["projection_version"], STATUS_PROJECTION_VERSION)


class TestAuthorityBoundary(unittest.TestCase):
    def test_read_only_guarantee(self):
        repo_path = Path(".")
        state_file = repo_path / "PROJECT_STATE.md"
        before_mtime = state_file.stat().st_mtime if state_file.exists() else None

        res = main(["--repo", ".", "--json"])
        self.assertEqual(res, 0)

        after_mtime = state_file.stat().st_mtime if state_file.exists() else None
        self.assertEqual(before_mtime, after_mtime)


if __name__ == "__main__":
    unittest.main()
