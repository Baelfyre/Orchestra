"""Comprehensive Unit Tests for OrchestraWorktreeContract Runtime Module.

Covers all required edge cases, serialization, path confinement, state transitions,
advisory non-destruction, explicit release, runner mocks, and adapter capability integration.
Includes targeted tests for F-IDENTITY-001, F-PATH-CASE-001, F-NESTED-001, and F-TOCTOU-001 security revisions.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from orchestra_runtime import (
    AUTHORIZED_PARENT_DIRS,
    WORKTREE_CONTRACT_VERSION,
    OrchestraWorktreeContract,
    WorktreeCleanupPolicy,
    WorktreeDiagnostic,
    WorktreeIsolationStatus,
    WorktreeOperationResult,
    WorktreeReasonCode,
    WorktreeValidationResult,
    derive_worktree_creation_identity,
    deserialize_worktree_contract,
    initialize_worktree,
    inspect_worktree,
    plan_worktree_release,
    release_worktree,
    resolve_authorized_worktree_path,
    serialize_worktree_contract,
    serialize_worktree_contract_to_str,
    validate_worktree_contract,
    validate_worktree_path,
    verify_worktree_base_sha,
)
from orchestra_runtime.worktree import (
    _check_git_repo,
    _default_command_runner,
    transition_worktree_status,
    normalize_git_remote_identity,
    derive_repository_identity,
    derive_path_collision_key,
    find_nested_git_boundary,
    _check_submodule_boundary,
    _require_transition,
)


class TestWorktreeContractValidation(unittest.TestCase):
    def setUp(self):
        self.valid_contract = OrchestraWorktreeContract(
            unit_id="unit-123",
            worktree_path=".tmp/spec-kitty-test",
            worktree_branch="feature/test-branch",
            approved_base_sha="a" * 40,
            isolation_status=WorktreeIsolationStatus.INITIALIZED,
            correlation_id="corr-456",
            is_clean_at_start=True,
            cleanup_policy=WorktreeCleanupPolicy.EXPLICIT_HOST_ACTION_ONLY,
        )

    def test_valid_contract(self):
        res = validate_worktree_contract(self.valid_contract)
        self.assertTrue(res.valid)
        self.assertEqual(len(res.diagnostics), 0)

    def test_invalid_contract_type(self):
        res = validate_worktree_contract("not-a-contract")  # type: ignore
        self.assertFalse(res.valid)
        self.assertEqual(res.diagnostics[0].code, WorktreeReasonCode.INVALID_CONTRACT)

    def test_version_rejection(self):
        c = OrchestraWorktreeContract(
            unit_id="unit-123",
            worktree_path=".tmp/test",
            worktree_branch="feature/test",
            approved_base_sha="a" * 40,
            isolation_status=WorktreeIsolationStatus.INITIALIZED,
            contract_version="9.9",
        )
        res = validate_worktree_contract(c)
        self.assertFalse(res.valid)
        self.assertEqual(res.diagnostics[0].code, WorktreeReasonCode.INVALID_CONTRACT)

    def test_unit_id_validation(self):
        invalid_ids = ["", "invalid id space", "invalid/slash"]
        for uid in invalid_ids:
            c = OrchestraWorktreeContract(
                unit_id=uid,
                worktree_path=".tmp/test",
                worktree_branch="feature/test",
                approved_base_sha="a" * 40,
                isolation_status=WorktreeIsolationStatus.INITIALIZED,
            )
            res = validate_worktree_contract(c)
            self.assertFalse(res.valid)
            self.assertEqual(res.diagnostics[0].code, WorktreeReasonCode.INVALID_UNIT_ID)

    def test_correlation_id_validation(self):
        c = OrchestraWorktreeContract(
            unit_id="unit-123",
            worktree_path=".tmp/test",
            worktree_branch="feature/test",
            approved_base_sha="a" * 40,
            isolation_status=WorktreeIsolationStatus.INITIALIZED,
            correlation_id="invalid correlation space!",
        )
        res = validate_worktree_contract(c)
        self.assertFalse(res.valid)
        self.assertEqual(res.diagnostics[0].code, WorktreeReasonCode.INVALID_CORRELATION_ID)

    def test_sha_validation(self):
        self.assertTrue(verify_worktree_base_sha("a" * 40))
        self.assertTrue(verify_worktree_base_sha("1234567890abcdef1234567890abcdef12345678"))
        self.assertFalse(verify_worktree_base_sha("short-sha"))
        self.assertFalse(verify_worktree_base_sha("G" * 40))
        self.assertFalse(verify_worktree_base_sha(""))

        c = OrchestraWorktreeContract(
            unit_id="unit-123",
            worktree_path=".tmp/test",
            worktree_branch="feature/test",
            approved_base_sha="invalid-sha",
            isolation_status=WorktreeIsolationStatus.INITIALIZED,
        )
        res = validate_worktree_contract(c)
        self.assertFalse(res.valid)
        self.assertEqual(res.diagnostics[0].code, WorktreeReasonCode.INVALID_BASE_SHA)

    def test_branch_validation(self):
        c = OrchestraWorktreeContract(
            unit_id="unit-123",
            worktree_path=".tmp/test",
            worktree_branch="invalid branch spaces",
            approved_base_sha="a" * 40,
            isolation_status=WorktreeIsolationStatus.INITIALIZED,
        )
        res = validate_worktree_contract(c)
        self.assertFalse(res.valid)
        self.assertEqual(res.diagnostics[0].code, WorktreeReasonCode.INVALID_BRANCH)

    def test_invalid_status_and_policy_types(self):
        c = OrchestraWorktreeContract(
            unit_id="unit-123",
            worktree_path=".tmp/test",
            worktree_branch="feature/test",
            approved_base_sha="a" * 40,
            isolation_status="INVALID_STATUS",  # type: ignore
            cleanup_policy="INVALID_POLICY",  # type: ignore
            is_clean_at_start="not-a-bool",  # type: ignore
        )
        res = validate_worktree_contract(c)
        self.assertFalse(res.valid)
        codes = [d.code for d in res.diagnostics]
        self.assertIn(WorktreeReasonCode.INVALID_CONTRACT, codes)

    def test_validate_contract_with_repo_root_path_error(self):
        c = OrchestraWorktreeContract(
            unit_id="unit-123",
            worktree_path="src/unauthorized-path",
            worktree_branch="feature/test",
            approved_base_sha="a" * 40,
            isolation_status=WorktreeIsolationStatus.INITIALIZED,
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            res = validate_worktree_contract(c, repo_root=temp_dir)
            self.assertFalse(res.valid)
            self.assertEqual(res.diagnostics[0].code, WorktreeReasonCode.PATH_OUTSIDE_AUTHORIZED_PARENT)


class TestPathConfinement(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_root = Path(self.temp_dir.name).resolve()
        self.repo_root = self.temp_root / "repo"
        self.repo_root.mkdir()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_authorized_parents(self):
        for pdir in AUTHORIZED_PARENT_DIRS:
            target, code = resolve_authorized_worktree_path(f"{pdir}/test-sub", self.repo_root)
            self.assertIsNone(code)
            self.assertIsNotNone(target)
            norm_path, pcode = validate_worktree_path(f"{pdir}/test-sub", self.repo_root)
            self.assertIsNone(pcode)
            self.assertEqual(norm_path, f"{pdir}/test-sub")

    def test_tmp_symlink_escape_rejected(self):
        outside = self.temp_root / "outside-tmp"
        outside.mkdir()
        link = self.repo_root / ".tmp"
        os.symlink(outside, link, target_is_directory=True)

        target, code = resolve_authorized_worktree_path(".tmp/child", self.repo_root)

        self.assertIsNone(target)
        self.assertEqual(code, WorktreeReasonCode.PATH_OUTSIDE_AUTHORIZED_PARENT)

    def test_orchestra_worktrees_symlink_escape_rejected(self):
        outside = self.temp_root / "outside-orchestra"
        outside.mkdir()
        orchestra_dir = self.repo_root / ".orchestra"
        orchestra_dir.mkdir()
        os.symlink(outside, orchestra_dir / "worktrees", target_is_directory=True)

        target, code = resolve_authorized_worktree_path(
            ".orchestra/worktrees/child", self.repo_root
        )

        self.assertIsNone(target)
        self.assertEqual(code, WorktreeReasonCode.PATH_OUTSIDE_AUTHORIZED_PARENT)

    def test_windows_tmp_junction_escape_rejected(self):
        if os.name != "nt":
            return

        outside = self.temp_root / "outside-junction"
        outside.mkdir()
        junction = self.repo_root / ".tmp"
        created = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(junction), str(outside)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(created.returncode, 0, msg=created.stderr or created.stdout)
        try:
            target, code = resolve_authorized_worktree_path(".tmp/child", self.repo_root)
            self.assertIsNone(target)
            self.assertEqual(code, WorktreeReasonCode.PATH_OUTSIDE_AUTHORIZED_PARENT)
        finally:
            junction.rmdir()

    def test_empty_path_rejection(self):
        target, code = resolve_authorized_worktree_path("  ", self.repo_root)
        self.assertEqual(code, WorktreeReasonCode.INVALID_PATH)

    def test_unauthorized_parent_rejection(self):
        target, code = resolve_authorized_worktree_path("src/worktree-1", self.repo_root)
        self.assertEqual(code, WorktreeReasonCode.PATH_OUTSIDE_AUTHORIZED_PARENT)

    def test_path_traversal_rejection(self):
        target, code = resolve_authorized_worktree_path(".tmp/../outside", self.repo_root)
        self.assertEqual(code, WorktreeReasonCode.PATH_TRAVERSAL_REJECTED)

    def test_absolute_path_rejection(self):
        target, code = resolve_authorized_worktree_path("C:\\Windows\\System32", self.repo_root)
        self.assertEqual(code, WorktreeReasonCode.ABSOLUTE_PATH_REJECTED)

        target, code = resolve_authorized_worktree_path("/usr/local/bin", self.repo_root)
        self.assertEqual(code, WorktreeReasonCode.ABSOLUTE_PATH_REJECTED)

    def test_unc_path_rejection(self):
        target, code = resolve_authorized_worktree_path("\\\\server\\share\\path", self.repo_root)
        self.assertEqual(code, WorktreeReasonCode.UNC_PATH_REJECTED)

    def test_python_compatibility_fallback(self):
        target_path = self.repo_root / ".tmp" / "sub"
        with patch.object(Path, "is_relative_to", side_effect=AttributeError):
            res, code = resolve_authorized_worktree_path(".tmp/sub", self.repo_root)
            self.assertIsNone(code)
            self.assertEqual(res, target_path)


class TestSerialization(unittest.TestCase):
    def setUp(self):
        self.contract = OrchestraWorktreeContract(
            unit_id="unit-abc",
            worktree_path=".tmp/spec-kitty-ser",
            worktree_branch="feature/ser-test",
            approved_base_sha="b" * 40,
            isolation_status=WorktreeIsolationStatus.ACTIVE,
            correlation_id="corr-789",
            is_clean_at_start=True,
            cleanup_policy=WorktreeCleanupPolicy.EXPLICIT_HOST_ACTION_ONLY,
            creation_identity="hash123",
        )

    def test_deterministic_serialization(self):
        d1 = serialize_worktree_contract(self.contract)
        s1 = serialize_worktree_contract_to_str(self.contract)
        s2 = serialize_worktree_contract_to_str(self.contract)
        self.assertEqual(s1, s2)
        self.assertNotIn("C:", s1)
        self.assertNotIn("D:", s1)
        self.assertNotIn("\\\\", s1)

    def test_roundtrip_deserialization(self):
        s1 = serialize_worktree_contract_to_str(self.contract)
        deserialized = deserialize_worktree_contract(s1)
        self.assertEqual(deserialized.unit_id, self.contract.unit_id)
        self.assertEqual(deserialized.worktree_path, self.contract.worktree_path)
        self.assertEqual(deserialized.approved_base_sha, self.contract.approved_base_sha)
        self.assertEqual(deserialized.isolation_status, self.contract.isolation_status)
        self.assertEqual(deserialized.cleanup_policy, self.contract.cleanup_policy)

    def test_deserialization_invalid_payload_types(self):
        with self.assertRaises(ValueError):
            deserialize_worktree_contract(12345)  # type: ignore
        with self.assertRaises(ValueError):
            deserialize_worktree_contract("invalid json string {")
        with self.assertRaises(ValueError):
            deserialize_worktree_contract(json.dumps(["list", "not", "dict"]))

    def test_deserialization_missing_required_keys(self):
        d1 = {"contract_version": "1.0", "unit_id": "u1"}
        with self.assertRaises(ValueError):
            deserialize_worktree_contract(d1)

    def test_unknown_fields_rejection(self):
        d1 = serialize_worktree_contract(self.contract)
        d1["extra_unknown_field"] = "malicious"
        with self.assertRaises(ValueError):
            deserialize_worktree_contract(d1)

    def test_deserialization_version_rejection(self):
        d1 = serialize_worktree_contract(self.contract)
        d1["contract_version"] = "99.0"
        with self.assertRaises(ValueError):
            deserialize_worktree_contract(d1)

    def test_deserialization_invalid_enums_and_types(self):
        d1 = serialize_worktree_contract(self.contract)
        d1["isolation_status"] = "INVALID_STATUS"
        with self.assertRaises(ValueError):
            deserialize_worktree_contract(d1)

        d2 = serialize_worktree_contract(self.contract)
        d2["cleanup_policy"] = "INVALID_POLICY"
        with self.assertRaises(ValueError):
            deserialize_worktree_contract(d2)

        d3 = serialize_worktree_contract(self.contract)
        d3["is_clean_at_start"] = "not-a-bool"
        with self.assertRaises(ValueError):
            deserialize_worktree_contract(d3)


class TestStateTransitions(unittest.TestCase):
    def test_valid_transitions(self):
        self.assertTrue(
            transition_worktree_status(
                WorktreeIsolationStatus.INITIALIZED, WorktreeIsolationStatus.ACTIVE
            )
        )
        self.assertTrue(
            transition_worktree_status(
                WorktreeIsolationStatus.ACTIVE, WorktreeIsolationStatus.RELEASED
            )
        )
        self.assertTrue(
            transition_worktree_status(
                WorktreeIsolationStatus.ACTIVE, WorktreeIsolationStatus.FAILED_CLEANUP
            )
        )
        self.assertTrue(
            transition_worktree_status(
                WorktreeIsolationStatus.FAILED_CLEANUP, WorktreeIsolationStatus.RELEASED
            )
        )

    def test_invalid_transitions(self):
        self.assertFalse(
            transition_worktree_status(
                WorktreeIsolationStatus.RELEASED, WorktreeIsolationStatus.ACTIVE
            )
        )
        self.assertFalse(
            transition_worktree_status(
                WorktreeIsolationStatus.STALE_ORPHANED, WorktreeIsolationStatus.RELEASED
            )
        )
        self.assertFalse(
            transition_worktree_status(
                WorktreeIsolationStatus.ACTIVE, WorktreeIsolationStatus.INITIALIZED
            )
        )

    def test_transition_enforcement_helper(self):
        c = OrchestraWorktreeContract(
            unit_id="unit-1",
            worktree_path=".tmp/w1",
            worktree_branch="br1",
            approved_base_sha="a"*40,
            isolation_status=WorktreeIsolationStatus.RELEASED,
        )
        res = _require_transition(c.isolation_status, WorktreeIsolationStatus.ACTIVE, c)
        self.assertIsNotNone(res)
        self.assertFalse(res.success)
        self.assertEqual(res.diagnostics[0].code, WorktreeReasonCode.INVALID_STATE_TRANSITION)


class TestCommandRunnerAndMocks(unittest.TestCase):
    def test_default_command_runner(self):
        code, stdout, stderr = _default_command_runner(["python", "-c", "print('hello')"], os.getcwd())
        self.assertEqual(code, 0)
        self.assertIn("hello", stdout)

        code_fnf, _, stderr_fnf = _default_command_runner(["nonexistent_executable_12345"], os.getcwd())
        self.assertEqual(code_fnf, 127)
        self.assertIn("not found", stderr_fnf)

    @patch("subprocess.run")
    def test_command_runner_exceptions(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(["git"], 15.0)
        code, _, stderr = _default_command_runner(["git"], os.getcwd())
        self.assertEqual(code, 124)
        self.assertIn("timed out", stderr)

        mock_run.side_effect = RuntimeError("generic error")
        code, _, stderr = _default_command_runner(["git"], os.getcwd())
        self.assertEqual(code, 1)
        self.assertIn("generic error", stderr)


class TestRepositoryIdentityAndRemoteNormalization(unittest.TestCase):
    def test_normalize_git_remote_identity(self):
        test_cases = [
            ("https://user:token@github.com/Owner/Repo.git", "github.com/Owner/Repo"),
            ("ssh://git@github.com/Owner/Repo.git", "github.com/Owner/Repo"),
            ("git@github.com:Owner/Repo.git", "github.com/Owner/Repo"),
            ("https://github.com/Owner/Repo", "github.com/Owner/Repo"),
            ("https://GITHUB.com/Owner/Repo.git", "github.com/Owner/Repo"),
            ("git@gitlab.com:group/subgroup/project.git", "gitlab.com/group/subgroup/project"),
            ("", None),
            ("invalid_url", None),
        ]
        for url, expected in test_cases:
            self.assertEqual(normalize_git_remote_identity(url), expected, msg=f"Failed URL: {url}")

    def test_derive_repository_identity_success_origin(self):
        def mock_runner(args, cwd):
            if args == ["git", "remote"]:
                return 0, "origin\nupstream\n", ""
            if args == ["git", "remote", "get-url", "origin"]:
                return 0, "https://github.com/Baelfyre/Orchestra.git\n", ""
            return 1, "", "unknown command"

        digest, err = derive_repository_identity(os.getcwd(), mock_runner)
        self.assertIsNone(err)
        self.assertIsNotNone(digest)
        expected_digest = hashlib.sha256(b"remote:github.com/Baelfyre/Orchestra").hexdigest()
        self.assertEqual(digest, expected_digest)

    def test_derive_repository_identity_success_non_origin(self):
        def mock_runner(args, cwd):
            if args == ["git", "remote"]:
                return 0, "backup\n", ""
            if args == ["git", "remote", "get-url", "backup"]:
                return 0, "git@gitlab.com:Baelfyre/Orchestra.git\n", ""
            return 1, "", "unknown command"

        digest, err = derive_repository_identity(os.getcwd(), mock_runner)
        self.assertIsNone(err)
        expected_digest = hashlib.sha256(b"remote:gitlab.com/Baelfyre/Orchestra").hexdigest()
        self.assertEqual(digest, expected_digest)

    def test_derive_repository_identity_fallback_roots(self):
        def mock_runner(args, cwd):
            if args == ["git", "remote"]:
                return 1, "", "error"
            if args == ["git", "rev-list", "--max-parents=0", "--all"]:
                return 0, "commit2\ncommit1\n", ""
            return 1, "", "unknown command"

        digest, err = derive_repository_identity(os.getcwd(), mock_runner)
        self.assertIsNone(err)
        expected_digest = hashlib.sha256(b"roots:commit1|commit2").hexdigest()
        self.assertEqual(digest, expected_digest)

    def test_derive_repository_identity_unavailable(self):
        def mock_runner(args, cwd):
            return 1, "", "error"

        digest, err = derive_repository_identity(os.getcwd(), mock_runner)
        self.assertEqual(err, WorktreeReasonCode.REPOSITORY_IDENTITY_UNAVAILABLE)
        self.assertIsNone(digest)


class TestPathCollisionPlatformAwareness(unittest.TestCase):
    def test_derive_path_collision_key(self):
        # win32: case-insensitive
        self.assertEqual(
            derive_path_collision_key("Path/To\\WT", "win32"),
            "path/to/wt"
        )
        # darwin: case-insensitive
        self.assertEqual(
            derive_path_collision_key("Path/To/WT", "darwin"),
            "path/to/wt"
        )
        # linux: case-sensitive but normalized separators
        self.assertEqual(
            derive_path_collision_key("Path/To\\WT", "linux"),
            "Path/To/WT"
        )
        # Unicode casefold: Straße casefolded to strasse
        self.assertEqual(
            derive_path_collision_key("Straße", "win32"),
            "strasse"
        )
        self.assertEqual(
            derive_path_collision_key("Straße", "darwin"),
            "strasse"
        )


class TestRecursiveNestedRepositoryAndSubmodules(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.target_path = Path(self.temp_dir.name).resolve()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_no_nested_repository(self):
        # Just create some folders/files
        (self.target_path / "src").mkdir()
        (self.target_path / "src" / "main.py").write_text("print(1)")
        found, rel = find_nested_git_boundary(self.target_path)
        self.assertFalse(found)
        self.assertIsNone(rel)

    def test_nested_git_directory_at_root(self):
        # Root .git is a directory (bare conflict or initialization)
        (self.target_path / ".git").mkdir()
        found, rel = find_nested_git_boundary(self.target_path)
        # Treated as nested boundary since it's a dir, not a file
        self.assertTrue(found)

    def test_nested_git_linked_worktree_file_at_root_ignored(self):
        # Root .git is a file (correct linked worktree status)
        (self.target_path / ".git").write_text("gitdir: /some/path")
        found, rel = find_nested_git_boundary(self.target_path)
        self.assertFalse(found)

    def test_nested_git_directory_deep(self):
        (self.target_path / "vendor" / "nested").mkdir(parents=True)
        (self.target_path / "vendor" / "nested" / ".git").mkdir()
        found, rel = find_nested_git_boundary(self.target_path)
        self.assertTrue(found)
        self.assertEqual(rel, str(Path("vendor/nested/.git")))

    def test_nested_git_file_deep(self):
        (self.target_path / "vendor" / "nested").mkdir(parents=True)
        (self.target_path / "vendor" / "nested" / ".git").write_text("gitdir: ...")
        found, rel = find_nested_git_boundary(self.target_path)
        self.assertTrue(found)
        self.assertEqual(rel, str(Path("vendor/nested/.git")))

    def test_symlink_directories_not_followed(self):
        ext_git = self.target_path.parent / "ext_git_dir"
        ext_git.mkdir(exist_ok=True)
        (ext_git / ".git").mkdir(exist_ok=True)

        (self.target_path / "subdir").mkdir()
        # Create symlink pointing outside target_path
        link_target = self.target_path / "subdir" / "linked_dir"
        try:
            os.symlink(str(ext_git), str(link_target), target_is_directory=True)
        except OSError:
            # Skip if OS permissions restrict symlinks
            return

        found, rel = find_nested_git_boundary(self.target_path)
        self.assertFalse(found)

    def test_submodule_boundary_status_positive(self):
        def runner(args, cwd):
            if "submodule" in args and "status" in args:
                return 0, " -submodule_path hash (v1.0)\n", ""
            return 1, "", "error"
        self.assertTrue(_check_submodule_boundary(self.target_path, runner))

    def test_submodule_boundary_status_negative_with_gitmodules(self):
        def runner(args, cwd):
            return 0, "", ""
        (self.target_path / ".gitmodules").write_text("[submodule]\n")
        self.assertTrue(_check_submodule_boundary(self.target_path, runner))

    def test_submodule_boundary_none(self):
        def runner(args, cwd):
            return 0, "", ""
        self.assertFalse(_check_submodule_boundary(self.target_path, runner))


class TestWorktreeOperationsWithGitMock(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_dir = Path(self.temp_dir.name).resolve()
        # Initialize a temporary Git repository
        subprocess.run(["git", "init", "-b", "main"], cwd=self.repo_dir, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=self.repo_dir, check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=self.repo_dir, check=True)

        test_file = self.repo_dir / "README.md"
        test_file.write_text("# Test Repo\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=self.repo_dir, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.repo_dir, check=True)

        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=self.repo_dir, capture_output=True, text=True, check=True
        )
        self.base_sha = proc.stdout.strip().lower()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_check_git_repo(self):
        with tempfile.TemporaryDirectory() as no_git_dir:
            err = _check_git_repo(Path(no_git_dir), _default_command_runner)
            self.assertIsNotNone(err)
            self.assertEqual(err.code, WorktreeReasonCode.NOT_A_GIT_REPO)

        def failing_runner(args, cwd):
            return 1, "", "not a git repo"

        err2 = _check_git_repo(self.repo_dir, failing_runner)
        self.assertIsNotNone(err2)
        self.assertEqual(err2.code, WorktreeReasonCode.NOT_A_GIT_REPO)

    def test_initialize_worktree_unauthorized(self):
        contract = OrchestraWorktreeContract(
            unit_id="unit-001",
            worktree_path=".tmp/wt-unauth",
            worktree_branch="feature/wt-unauth",
            approved_base_sha=self.base_sha,
            isolation_status=WorktreeIsolationStatus.INITIALIZED,
        )
        res = initialize_worktree(contract, self.repo_dir, authorize_creation=False)
        self.assertFalse(res.success)
        self.assertEqual(res.diagnostics[0].code, WorktreeReasonCode.WORKTREE_UNSUPPORTED)

    def test_initialize_worktree_path_already_exists(self):
        wt_path = self.repo_dir / ".tmp" / "wt-exists"
        wt_path.mkdir(parents=True, exist_ok=True)

        contract = OrchestraWorktreeContract(
            unit_id="unit-exists",
            worktree_path=".tmp/wt-exists",
            worktree_branch="feature/wt-exists",
            approved_base_sha=self.base_sha,
            isolation_status=WorktreeIsolationStatus.INITIALIZED,
        )
        res = initialize_worktree(contract, self.repo_dir, authorize_creation=True)
        self.assertFalse(res.success)
        self.assertEqual(res.diagnostics[0].code, WorktreeReasonCode.PATH_ALREADY_EXISTS)

    def test_initialize_worktree_invalid_base_sha_in_git(self):
        contract = OrchestraWorktreeContract(
            unit_id="unit-badsha",
            worktree_path=".tmp/wt-badsha",
            worktree_branch="feature/wt-badsha",
            approved_base_sha="f" * 40,
            isolation_status=WorktreeIsolationStatus.INITIALIZED,
        )
        res = initialize_worktree(contract, self.repo_dir, authorize_creation=True)
        self.assertFalse(res.success)
        self.assertEqual(res.diagnostics[0].code, WorktreeReasonCode.BASE_SHA_MISMATCH)

    def test_inspect_worktree_status_failure_fails_closed(self):
        contract = OrchestraWorktreeContract(
            unit_id="unit-status-inspect",
            worktree_path=".tmp/wt-status-inspect",
            worktree_branch="feature/wt-status-inspect",
            approved_base_sha=self.base_sha,
            isolation_status=WorktreeIsolationStatus.INITIALIZED,
        )
        active_contract = initialize_worktree(
            contract, self.repo_dir, authorize_creation=True
        ).contract

        def status_failure_runner(args, cwd):
            if args == ["git", "status", "--porcelain=v1"]:
                return 1, "", "sensitive output must not be copied"
            return _default_command_runner(args, cwd)

        result = inspect_worktree(active_contract, self.repo_dir, status_failure_runner)

        self.assertFalse(result.success)
        self.assertEqual(
            result.diagnostics[0].code,
            WorktreeReasonCode.WORKTREE_STATUS_CHECK_FAILED,
        )
        self.assertNotIn("sensitive output", result.diagnostics[0].message)
        release_worktree(active_contract, self.repo_dir, authorize_cleanup=True)

    def test_release_worktree_status_failure_never_removes(self):
        contract = OrchestraWorktreeContract(
            unit_id="unit-status-release",
            worktree_path=".tmp/wt-status-release",
            worktree_branch="feature/wt-status-release",
            approved_base_sha=self.base_sha,
            isolation_status=WorktreeIsolationStatus.INITIALIZED,
        )
        active_contract = initialize_worktree(
            contract, self.repo_dir, authorize_creation=True
        ).contract
        target = self.repo_dir / ".tmp" / "wt-status-release"
        remove_called = False

        def status_failure_runner(args, cwd):
            nonlocal remove_called
            if args == ["git", "status", "--porcelain=v1"]:
                return 1, "", "status failed"
            if args[:3] == ["git", "worktree", "remove"]:
                remove_called = True
            return _default_command_runner(args, cwd)

        result = release_worktree(
            active_contract,
            self.repo_dir,
            authorize_cleanup=True,
            runner=status_failure_runner,
        )

        self.assertFalse(result.success)
        self.assertEqual(result.contract.isolation_status, WorktreeIsolationStatus.FAILED_CLEANUP)
        self.assertEqual(
            result.diagnostics[0].code,
            WorktreeReasonCode.WORKTREE_STATUS_CHECK_FAILED,
        )
        self.assertFalse(remove_called)
        self.assertTrue(target.exists())
        self.assertEqual(
            subprocess.run(
                ["git", "show-ref", "--verify", "--quiet", "refs/heads/feature/wt-status-release"],
                cwd=self.repo_dir,
            ).returncode,
            0,
        )
        release_worktree(active_contract, self.repo_dir, authorize_cleanup=True)

    def test_initialize_inspect_release_lifecycle(self):
        contract = OrchestraWorktreeContract(
            unit_id="unit-lifecycle",
            worktree_path=".tmp/wt-lifecycle",
            worktree_branch="feature/wt-lifecycle",
            approved_base_sha=self.base_sha,
            isolation_status=WorktreeIsolationStatus.INITIALIZED,
            cleanup_policy=WorktreeCleanupPolicy.EXPLICIT_HOST_ACTION_ONLY,
        )

        # 1. Initialize
        init_res = initialize_worktree(contract, self.repo_dir, authorize_creation=True)
        self.assertTrue(init_res.success, msg=f"Init failed: {init_res.diagnostics}")
        active_contract = init_res.contract
        self.assertIsNotNone(active_contract)
        self.assertEqual(active_contract.isolation_status, WorktreeIsolationStatus.ACTIVE)
        self.assertIsNotNone(active_contract.creation_identity)

        # Verify filesystem directory was created
        wt_path = self.repo_dir / ".tmp" / "wt-lifecycle"
        self.assertTrue(wt_path.exists())

        # 2. Inspect
        insp_res = inspect_worktree(active_contract, self.repo_dir)
        self.assertTrue(insp_res.success, msg=f"Inspect failed: {insp_res.diagnostics}")

        # 3. Advisory release plan
        advisory_contract = OrchestraWorktreeContract(
            unit_id=active_contract.unit_id,
            worktree_path=active_contract.worktree_path,
            worktree_branch=active_contract.worktree_branch,
            approved_base_sha=active_contract.approved_base_sha,
            isolation_status=active_contract.isolation_status,
            cleanup_policy=WorktreeCleanupPolicy.ADVISORY_SAFE_SUBSET,
            creation_identity=active_contract.creation_identity,
        )
        plan_res = plan_worktree_release(advisory_contract, self.repo_dir)
        self.assertTrue(plan_res.success)
        self.assertTrue(wt_path.exists())  # Proves non-destructive

        # Advisory release attempt fails closed
        rel_adv_res = release_worktree(advisory_contract, self.repo_dir, authorize_cleanup=True)
        self.assertFalse(rel_adv_res.success)
        self.assertEqual(rel_adv_res.diagnostics[0].code, WorktreeReasonCode.ADVISORY_POLICY_NON_DESTRUCTIVE)
        self.assertTrue(wt_path.exists())

        # 4. Explicit release without authority fails closed
        rel_unauth_res = release_worktree(active_contract, self.repo_dir, authorize_cleanup=False)
        self.assertFalse(rel_unauth_res.success)
        self.assertEqual(rel_unauth_res.diagnostics[0].code, WorktreeReasonCode.CLEANUP_AUTHORITY_REQUIRED)
        self.assertTrue(wt_path.exists())

        # 5. Explicit authorized release succeeds
        rel_res = release_worktree(active_contract, self.repo_dir, authorize_cleanup=True)
        self.assertTrue(rel_res.success, msg=f"Release failed: {rel_res.diagnostics}")
        self.assertEqual(rel_res.contract.isolation_status, WorktreeIsolationStatus.RELEASED)

        # Verify worktree path was removed
        self.assertFalse(wt_path.exists())

        # Verify branch is still preserved in git
        proc = subprocess.run(
            ["git", "branch", "--list", "feature/wt-lifecycle"],
            cwd=self.repo_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("feature/wt-lifecycle", proc.stdout)

    def test_creation_identity_mismatch_release_block(self):
        contract = OrchestraWorktreeContract(
            unit_id="unit-tamper",
            worktree_path=".tmp/wt-tamper",
            worktree_branch="feature/wt-tamper",
            approved_base_sha=self.base_sha,
            isolation_status=WorktreeIsolationStatus.INITIALIZED,
        )
        init_res = initialize_worktree(contract, self.repo_dir, authorize_creation=True)
        self.assertTrue(init_res.success)

        # Release without creation_identity fails
        no_id_contract = OrchestraWorktreeContract(
            unit_id=init_res.contract.unit_id,
            worktree_path=init_res.contract.worktree_path,
            worktree_branch=init_res.contract.worktree_branch,
            approved_base_sha=init_res.contract.approved_base_sha,
            isolation_status=init_res.contract.isolation_status,
            creation_identity=None,
        )
        rel_noid = release_worktree(no_id_contract, self.repo_dir, authorize_cleanup=True)
        self.assertFalse(rel_noid.success)
        self.assertEqual(rel_noid.diagnostics[0].code, WorktreeReasonCode.WORKTREE_IDENTITY_MISMATCH)

        # Release with forged identity fails
        tampered_contract = OrchestraWorktreeContract(
            unit_id=init_res.contract.unit_id,
            worktree_path=init_res.contract.worktree_path,
            worktree_branch=init_res.contract.worktree_branch,
            approved_base_sha=init_res.contract.approved_base_sha,
            isolation_status=init_res.contract.isolation_status,
            creation_identity="forged_identity_hash",
        )

        rel_res = release_worktree(tampered_contract, self.repo_dir, authorize_cleanup=True)
        self.assertFalse(rel_res.success)
        self.assertEqual(rel_res.diagnostics[0].code, WorktreeReasonCode.WORKTREE_IDENTITY_MISMATCH)

        # Clean up properly with authentic contract
        release_worktree(init_res.contract, self.repo_dir, authorize_cleanup=True)

    def test_dirty_worktree_inspection_warning(self):
        contract = OrchestraWorktreeContract(
            unit_id="unit-dirty",
            worktree_path=".tmp/wt-dirty",
            worktree_branch="feature/wt-dirty",
            approved_base_sha=self.base_sha,
            isolation_status=WorktreeIsolationStatus.INITIALIZED,
        )
        init_res = initialize_worktree(contract, self.repo_dir, authorize_creation=True)
        self.assertTrue(init_res.success)

        wt_path = self.repo_dir / ".tmp" / "wt-dirty"
        (wt_path / "dirty_file.txt").write_text("uncommitted change", encoding="utf-8")

        insp_res = inspect_worktree(init_res.contract, self.repo_dir)
        self.assertFalse(insp_res.success)
        self.assertEqual(insp_res.diagnostics[0].code, WorktreeReasonCode.WORKTREE_DIRTY)

        # Release fails when dirty
        rel_res = release_worktree(init_res.contract, self.repo_dir, authorize_cleanup=True)
        self.assertFalse(rel_res.success)
        self.assertEqual(rel_res.diagnostics[0].code, WorktreeReasonCode.WORKTREE_DIRTY)

        # Clean up file manually to release test dir
        (wt_path / "dirty_file.txt").unlink()
        release_worktree(init_res.contract, self.repo_dir, authorize_cleanup=True)

    def test_nested_repository_detection(self):
        contract = OrchestraWorktreeContract(
            unit_id="unit-nested",
            worktree_path=".tmp/wt-nested",
            worktree_branch="feature/wt-nested",
            approved_base_sha=self.base_sha,
            isolation_status=WorktreeIsolationStatus.INITIALIZED,
        )
        init_res = initialize_worktree(contract, self.repo_dir, authorize_creation=True)
        self.assertTrue(init_res.success)

        wt_path = self.repo_dir / ".tmp" / "wt-nested"
        sub_repo = wt_path / "sub_repo"
        (sub_repo / ".git").mkdir(parents=True, exist_ok=True)
        (wt_path / ".gitmodules").write_text("[submodule]\n", encoding="utf-8")

        insp_res = inspect_worktree(init_res.contract, self.repo_dir)
        self.assertFalse(insp_res.success)
        codes = [d.code for d in insp_res.diagnostics]
        self.assertIn(WorktreeReasonCode.NESTED_REPOSITORY_DETECTED, codes)
        self.assertIn(WorktreeReasonCode.SUBMODULE_BOUNDARY_DETECTED, codes)

        (wt_path / ".gitmodules").unlink()
        (sub_repo / ".git").rmdir()
        sub_repo.rmdir()
        release_worktree(init_res.contract, self.repo_dir, authorize_cleanup=True)


class TestReleaseTwoPhaseVerificationAndRaces(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_dir = Path(self.temp_dir.name).resolve()
        subprocess.run(["git", "init", "-b", "main"], cwd=self.repo_dir, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=self.repo_dir, check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=self.repo_dir, check=True)
        (self.repo_dir / "README.md").write_text("# Test\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=self.repo_dir, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.repo_dir, check=True)
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=self.repo_dir, capture_output=True, text=True, check=True
        )
        self.base_sha = proc.stdout.strip().lower()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_release_race_dirty_mutation(self):
        contract = OrchestraWorktreeContract(
            unit_id="unit-race1",
            worktree_path=".tmp/wt-race1",
            worktree_branch="feature/wt-race1",
            approved_base_sha=self.base_sha,
            isolation_status=WorktreeIsolationStatus.INITIALIZED,
        )
        init_res = initialize_worktree(contract, self.repo_dir, authorize_creation=True)
        self.assertTrue(init_res.success)
        active_contract = init_res.contract

        # Intercept runner to write a dirty file in phase 2 (during second inspect)
        inspect_count = 0
        wt_path = self.repo_dir / ".tmp" / "wt-race1"

        def race_runner(args, cwd):
            nonlocal inspect_count
            # First inspect calls git status, then second inspect calls git status.
            # We insert the dirty file right before the second git status status check.
            if args == ["git", "status", "--porcelain=v1"] and str(cwd) == str(wt_path):
                inspect_count += 1
                if inspect_count == 2:
                    (wt_path / "race_file.txt").write_text("dirty mutation")
            return _default_command_runner(args, cwd)

        # Release worktree should fail with release race because fingerprint changed
        res = release_worktree(active_contract, self.repo_dir, authorize_cleanup=True, runner=race_runner)
        self.assertFalse(res.success)
        self.assertEqual(res.diagnostics[0].code, WorktreeReasonCode.WORKTREE_RELEASE_RACE)
        self.assertEqual(res.contract.isolation_status, WorktreeIsolationStatus.FAILED_CLEANUP)
        self.assertTrue(wt_path.exists())

        # Clean up
        (wt_path / "race_file.txt").unlink()
        release_worktree(active_contract, self.repo_dir, authorize_cleanup=True)

    def test_release_race_lock_mutation(self):
        contract = OrchestraWorktreeContract(
            unit_id="unit-race2",
            worktree_path=".tmp/wt-race2",
            worktree_branch="feature/wt-race2",
            approved_base_sha=self.base_sha,
            isolation_status=WorktreeIsolationStatus.INITIALIZED,
        )
        init_res = initialize_worktree(contract, self.repo_dir, authorize_creation=True)
        self.assertTrue(init_res.success)
        active_contract = init_res.contract
        wt_path = self.repo_dir / ".tmp" / "wt-race2"

        inspect_count = 0

        def race_runner(args, cwd):
            nonlocal inspect_count
            if args == ["git", "worktree", "list", "--porcelain"]:
                inspect_count += 1
                if inspect_count == 2:
                    # Return locked output in second inspect
                    return 0, f"worktree {wt_path}\nHEAD {self.base_sha}\nbranch refs/heads/feature/wt-race2\nlocked\n\n", ""
            return _default_command_runner(args, cwd)

        res = release_worktree(active_contract, self.repo_dir, authorize_cleanup=True, runner=race_runner)
        self.assertFalse(res.success)
        self.assertEqual(res.diagnostics[0].code, WorktreeReasonCode.WORKTREE_RELEASE_RACE)
        self.assertTrue(wt_path.exists())

        # Clean up
        release_worktree(active_contract, self.repo_dir, authorize_cleanup=True)

    def test_branch_verification_command_failure_blocks_released(self):
        contract = OrchestraWorktreeContract(
            unit_id="unit-branch-check-failure",
            worktree_path=".tmp/wt-branch-check-failure",
            worktree_branch="feature/wt-branch-check-failure",
            approved_base_sha=self.base_sha,
            isolation_status=WorktreeIsolationStatus.INITIALIZED,
        )
        active_contract = initialize_worktree(
            contract, self.repo_dir, authorize_creation=True
        ).contract

        def branch_check_failure_runner(args, cwd):
            if args[:4] == ["git", "show-ref", "--verify", "--quiet"]:
                return 1, "", "verification unavailable"
            return _default_command_runner(args, cwd)

        result = release_worktree(
            active_contract,
            self.repo_dir,
            authorize_cleanup=True,
            runner=branch_check_failure_runner,
        )

        self.assertFalse(result.success)
        self.assertEqual(result.contract.isolation_status, WorktreeIsolationStatus.FAILED_CLEANUP)
        self.assertEqual(result.diagnostics[0].code, WorktreeReasonCode.WORKTREE_REMOVE_FAILED)

    def test_missing_branch_ref_blocks_released(self):
        contract = OrchestraWorktreeContract(
            unit_id="unit-branch-missing",
            worktree_path=".tmp/wt-branch-missing",
            worktree_branch="feature/wt-branch-missing",
            approved_base_sha=self.base_sha,
            isolation_status=WorktreeIsolationStatus.INITIALIZED,
        )
        active_contract = initialize_worktree(
            contract, self.repo_dir, authorize_creation=True
        ).contract

        def branch_removal_runner(args, cwd):
            result = _default_command_runner(args, cwd)
            if args[:3] == ["git", "worktree", "remove"] and result[0] == 0:
                _default_command_runner(
                    ["git", "branch", "-D", contract.worktree_branch], self.repo_dir
                )
            return result

        result = release_worktree(
            active_contract,
            self.repo_dir,
            authorize_cleanup=True,
            runner=branch_removal_runner,
        )

        self.assertFalse(result.success)
        self.assertEqual(result.contract.isolation_status, WorktreeIsolationStatus.FAILED_CLEANUP)
        self.assertEqual(result.diagnostics[0].code, WorktreeReasonCode.WORKTREE_REMOVE_FAILED)

    def test_unrelated_worktree_removal_evidence_blocks_released(self):
        target_contract = OrchestraWorktreeContract(
            unit_id="unit-target-registration",
            worktree_path=".tmp/wt-target-registration",
            worktree_branch="feature/wt-target-registration",
            approved_base_sha=self.base_sha,
            isolation_status=WorktreeIsolationStatus.INITIALIZED,
        )
        other_contract = OrchestraWorktreeContract(
            unit_id="unit-other-registration",
            worktree_path=".tmp/wt-other-registration",
            worktree_branch="feature/wt-other-registration",
            approved_base_sha=self.base_sha,
            isolation_status=WorktreeIsolationStatus.INITIALIZED,
        )
        target_active = initialize_worktree(
            target_contract, self.repo_dir, authorize_creation=True
        ).contract
        other_active = initialize_worktree(
            other_contract, self.repo_dir, authorize_creation=True
        ).contract
        other_path = self.repo_dir / ".tmp" / "wt-other-registration"
        list_count = 0

        def omit_other_after_removal_runner(args, cwd):
            nonlocal list_count
            result = _default_command_runner(args, cwd)
            if args == ["git", "worktree", "list", "--porcelain"]:
                list_count += 1
                if list_count == 4:
                    blocks = result[1].strip().split("\n\n")
                    filtered = [
                        block
                        for block in blocks
                        if "branch refs/heads/feature/wt-other-registration" not in block
                    ]
                    return result[0], "\n\n".join(filtered) + "\n\n", result[2]
            return result

        result = release_worktree(
            target_active,
            self.repo_dir,
            authorize_cleanup=True,
            runner=omit_other_after_removal_runner,
        )

        self.assertFalse(result.success)
        self.assertEqual(result.contract.isolation_status, WorktreeIsolationStatus.FAILED_CLEANUP)
        self.assertEqual(result.diagnostics[0].code, WorktreeReasonCode.WORKTREE_REMOVE_FAILED)
        self.assertTrue(other_path.exists())
        release_worktree(other_active, self.repo_dir, authorize_cleanup=True)

    def test_unrelated_worktree_head_and_branch_drift_blocks_released(self):
        target_contract = OrchestraWorktreeContract(
            unit_id="unit-target-drift",
            worktree_path=".tmp/wt-target-drift",
            worktree_branch="feature/wt-target-drift",
            approved_base_sha=self.base_sha,
            isolation_status=WorktreeIsolationStatus.INITIALIZED,
        )
        other_contract = OrchestraWorktreeContract(
            unit_id="unit-other-drift",
            worktree_path=".tmp/wt-other-drift",
            worktree_branch="feature/wt-other-drift",
            approved_base_sha=self.base_sha,
            isolation_status=WorktreeIsolationStatus.INITIALIZED,
        )
        target_active = initialize_worktree(
            target_contract, self.repo_dir, authorize_creation=True
        ).contract
        other_active = initialize_worktree(
            other_contract, self.repo_dir, authorize_creation=True
        ).contract
        other_path = self.repo_dir / ".tmp" / "wt-other-drift"
        list_count = 0

        def drift_other_after_removal_runner(args, cwd):
            nonlocal list_count
            result = _default_command_runner(args, cwd)
            if args == ["git", "worktree", "list", "--porcelain"]:
                list_count += 1
                if list_count == 4:
                    blocks = result[1].strip().split("\n\n")
                    changed = []
                    for block in blocks:
                        if "branch refs/heads/feature/wt-other-drift" in block:
                            block = block.replace(
                                f"HEAD {self.base_sha}", f"HEAD {'0' * 40}"
                            ).replace(
                                "branch refs/heads/feature/wt-other-drift",
                                "branch refs/heads/feature/wt-other-drift-observed",
                            )
                        changed.append(block)
                    return result[0], "\n\n".join(changed) + "\n\n", result[2]
            return result

        result = release_worktree(
            target_active,
            self.repo_dir,
            authorize_cleanup=True,
            runner=drift_other_after_removal_runner,
        )

        self.assertFalse(result.success)
        self.assertEqual(result.contract.isolation_status, WorktreeIsolationStatus.FAILED_CLEANUP)
        self.assertEqual(result.diagnostics[0].code, WorktreeReasonCode.WORKTREE_REMOVE_FAILED)
        self.assertTrue(other_path.exists())
        release_worktree(other_active, self.repo_dir, authorize_cleanup=True)


class TestCoverageEdgeCases(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_dir = Path(self.temp_dir.name).resolve()
        subprocess.run(["git", "init", "-b", "main"], cwd=self.repo_dir, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=self.repo_dir, check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=self.repo_dir, check=True)
        (self.repo_dir / "README.md").write_text("# Test\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=self.repo_dir, check=True)
        subprocess.run(["git", "commit", "-m", "Initial"], cwd=self.repo_dir, check=True)
        proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo_dir, capture_output=True, text=True, check=True)
        self.base_sha = proc.stdout.strip().lower()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_inspect_worktree_errors(self):
        # Invalid contract
        c_inv = OrchestraWorktreeContract(
            unit_id="",
            worktree_path=".tmp/sub",
            worktree_branch="main",
            approved_base_sha=self.base_sha,
            isolation_status=WorktreeIsolationStatus.INITIALIZED,
        )
        res_inv = inspect_worktree(c_inv, self.repo_dir)
        self.assertFalse(res_inv.success)

        # Not a git repo
        with tempfile.TemporaryDirectory() as no_git:
            c_valid = OrchestraWorktreeContract(
                unit_id="u1",
                worktree_path=".tmp/sub",
                worktree_branch="main",
                approved_base_sha=self.base_sha,
                isolation_status=WorktreeIsolationStatus.INITIALIZED,
            )
            res_nogit = inspect_worktree(c_valid, no_git)
            self.assertFalse(res_nogit.success)

        # Path confinement failure
        c_badpath = OrchestraWorktreeContract(
            unit_id="u1",
            worktree_path="src/unauth",
            worktree_branch="main",
            approved_base_sha=self.base_sha,
            isolation_status=WorktreeIsolationStatus.INITIALIZED,
        )
        res_badpath = inspect_worktree(c_badpath, self.repo_dir)
        self.assertFalse(res_badpath.success)

        # git worktree list error
        def list_fails_runner(args, cwd):
            if "worktree" in args and "list" in args:
                return 1, "", "worktree list error"
            return _default_command_runner(args, cwd)

        res_listerr = inspect_worktree(c_valid, self.repo_dir, runner=list_fails_runner)
        self.assertFalse(res_listerr.success)

    def test_inspect_worktree_mismatches_and_locked(self):
        c_valid = OrchestraWorktreeContract(
            unit_id="u1",
            worktree_path=".tmp/sub",
            worktree_branch="feature/sub",
            approved_base_sha=self.base_sha,
            isolation_status=WorktreeIsolationStatus.INITIALIZED,
        )
        wt_target = (self.repo_dir / ".tmp" / "sub").resolve()

        def mock_wt_list_runner(args, cwd):
            if "worktree" in args and "list" in args:
                output = f"worktree {wt_target}\nHEAD {'0'*40}\nbranch refs/heads/feature/other\nlocked Locked for maintenance\n\n"
                return 0, output, ""
            return _default_command_runner(args, cwd)

        res = inspect_worktree(c_valid, self.repo_dir, runner=mock_wt_list_runner)
        self.assertFalse(res.success)
        codes = [d.code for d in res.diagnostics]
        self.assertIn(WorktreeReasonCode.BASE_SHA_MISMATCH, codes)
        self.assertIn(WorktreeReasonCode.INVALID_BRANCH, codes)
        self.assertIn(WorktreeReasonCode.WORKTREE_LOCKED, codes)

    def test_initialize_worktree_errors(self):
        c_inv = OrchestraWorktreeContract(
            unit_id="",
            worktree_path=".tmp/sub",
            worktree_branch="main",
            approved_base_sha=self.base_sha,
            isolation_status=WorktreeIsolationStatus.INITIALIZED,
        )
        res1 = initialize_worktree(c_inv, self.repo_dir, authorize_creation=True)
        self.assertFalse(res1.success)

        with tempfile.TemporaryDirectory() as no_git:
            c_valid = OrchestraWorktreeContract(
                unit_id="u1",
                worktree_path=".tmp/sub",
                worktree_branch="feature/init-err",
                approved_base_sha=self.base_sha,
                isolation_status=WorktreeIsolationStatus.INITIALIZED,
            )
            res2 = initialize_worktree(c_valid, no_git, authorize_creation=True)
            self.assertFalse(res2.success)

        c_badpath = OrchestraWorktreeContract(
            unit_id="u1",
            worktree_path="src/unauth",
            worktree_branch="main",
            approved_base_sha=self.base_sha,
            isolation_status=WorktreeIsolationStatus.INITIALIZED,
        )
        res3 = initialize_worktree(c_badpath, self.repo_dir, authorize_creation=True)
        self.assertFalse(res3.success)

        # Post-creation inspection fails -> STALE_ORPHANED
        def post_insp_fails_runner(args, cwd):
            if "status" in args:
                return 0, " M dirty_file.py", ""
            return _default_command_runner(args, cwd)

        res4 = initialize_worktree(c_valid, self.repo_dir, authorize_creation=True, runner=post_insp_fails_runner)
        self.assertFalse(res4.success)
        self.assertEqual(res4.contract.isolation_status, WorktreeIsolationStatus.STALE_ORPHANED)
        wt_target = self.repo_dir / ".tmp" / "sub"
        if wt_target.exists():
            release_worktree(c_valid, self.repo_dir, authorize_cleanup=True)

    def test_plan_and_release_error_branches(self):
        c_inv = OrchestraWorktreeContract(
            unit_id="",
            worktree_path=".tmp/sub",
            worktree_branch="main",
            approved_base_sha=self.base_sha,
            isolation_status=WorktreeIsolationStatus.INITIALIZED,
        )
        res_p1 = plan_worktree_release(c_inv, self.repo_dir)
        self.assertFalse(res_p1.success)

        res_r1 = release_worktree(c_inv, self.repo_dir, authorize_cleanup=True)
        self.assertFalse(res_r1.success)

        c_valid = OrchestraWorktreeContract(
            unit_id="u1",
            worktree_path=".tmp/sub",
            worktree_branch="main",
            approved_base_sha=self.base_sha,
            isolation_status=WorktreeIsolationStatus.ACTIVE,
            creation_identity="fake-identity",
        )
        res_p2 = plan_worktree_release(c_valid, self.repo_dir)
        self.assertFalse(res_p2.success)

        res_r2 = release_worktree(c_valid, self.repo_dir, authorize_cleanup=True)
        self.assertFalse(res_r2.success)

    def test_creation_race_detection_initialize(self):
        c = OrchestraWorktreeContract(
            unit_id="u1",
            worktree_path=".tmp/sub-race",
            worktree_branch="feature/sub-race",
            approved_base_sha=self.base_sha,
            isolation_status=WorktreeIsolationStatus.INITIALIZED,
        )
        # Mock Path.exists to return False on the first call, and True on the second call only for the target path
        orig_exists = Path.exists
        call_count = 0
        def mock_exists(self_path):
            nonlocal call_count
            if ".tmp/sub-race" in str(self_path).replace("\\", "/"):
                call_count += 1
                return False if call_count == 1 else True
            return orig_exists(self_path)

        with patch.object(Path, "exists", mock_exists):
            res = initialize_worktree(c, self.repo_dir, authorize_creation=True)
            self.assertFalse(res.success)
            self.assertEqual(res.diagnostics[0].code, WorktreeReasonCode.WORKTREE_CREATION_RACE)

    def test_additional_coverage_branches(self):
        # 1. verify_worktree_base_sha with non-string
        self.assertFalse(verify_worktree_base_sha(12345))

        # 2. normalize_git_remote_identity with empty path
        self.assertIsNone(normalize_git_remote_identity("git@github.com:.git"))
        self.assertIsNone(normalize_git_remote_identity(""))

        # 3. derive_worktree_creation_identity with repo_root=None
        c = OrchestraWorktreeContract(
            unit_id="u1",
            worktree_path=".tmp/sub",
            worktree_branch="feature/sub",
            approved_base_sha=self.base_sha,
            isolation_status=WorktreeIsolationStatus.INITIALIZED,
        )
        res_id = derive_worktree_creation_identity(c, repo_root=None)
        self.assertTrue(isinstance(res_id, str))

        # 4. derive_repository_identity failure fallback during contract creation identity derivation
        res_id2 = derive_worktree_creation_identity(c, repo_root="nonexistent_dir_random_123")
        self.assertTrue(isinstance(res_id2, str))

        # 4b. derive_repository_identity remote failed / invalid branch coverage
        from orchestra_runtime.worktree import derive_repository_identity
        # A: git remote get-url fails (code2 != 0)
        def remote_fail_runner(args, cwd):
            if "remote" in args:
                if "get-url" in args:
                    return 1, "", "error"
                return 0, "origin", ""
            return _default_command_runner(args, cwd)
        dig_a, err_a = derive_repository_identity(self.repo_dir, runner=remote_fail_runner)
        self.assertIsNotNone(dig_a)

        # B: git remote get-url returns empty/invalid (canonical is None)
        def remote_invalid_runner(args, cwd):
            if "remote" in args:
                if "get-url" in args:
                    return 0, "http://invalid-url-no-path", ""
                return 0, "origin", ""
            return _default_command_runner(args, cwd)
        dig_b, err_b = derive_repository_identity(self.repo_dir, runner=remote_invalid_runner)
        self.assertIsNotNone(dig_b)

        # 5. is_relative_to fallback for Python < 3.9
        with patch.object(Path, "is_relative_to", side_effect=AttributeError):
            res_path, res_err = resolve_authorized_worktree_path(".tmp/sub", self.repo_dir)
            self.assertIsNotNone(res_path)
            self.assertIsNone(res_err)

            # Check invalid path check in resolving path too
            res_val, res_val_err = validate_worktree_path(".tmp/sub", self.repo_dir)
            self.assertEqual(res_val, ".tmp/sub")
            self.assertIsNone(res_val_err)

            # Cover 478->468 (target_path == authorized_parent under AttributeError fallback)
            res_path2, res_err2 = resolve_authorized_worktree_path(".tmp", self.repo_dir)
            self.assertIsNone(res_path2)
            self.assertEqual(res_err2, WorktreeReasonCode.PATH_OUTSIDE_AUTHORIZED_PARENT)

        # 6. _parse_worktree_list error and locked/trailing branches
        from orchestra_runtime.worktree import _parse_worktree_list
        res_parse1 = _parse_worktree_list("HEAD 12345\n\n")
        self.assertEqual(len(res_parse1), 0)

        res_parse2 = _parse_worktree_list("worktree /path\nlocked reason for lock\n\n")
        self.assertEqual(res_parse2[os.path.normcase("/path")]["locked"], "reason for lock")

        res_parse3 = _parse_worktree_list("worktree /path\nHEAD 12345")
        self.assertEqual(res_parse3[os.path.normcase("/path")]["head"], "12345")

        res_parse4 = _parse_worktree_list("worktree /path\nsomething_else\n\n")
        self.assertEqual(res_parse4[os.path.normcase("/path")]["worktree"], "/path")

        # 7. initialize_worktree absolute / invalid path resolution failure
        c_inv_path = OrchestraWorktreeContract(
            unit_id="u1",
            worktree_path="/absolute/path",
            worktree_branch="feature/sub",
            approved_base_sha=self.base_sha,
            isolation_status=WorktreeIsolationStatus.INITIALIZED,
        )
        res_init = initialize_worktree(c_inv_path, self.repo_dir, authorize_creation=True)
        self.assertFalse(res_init.success)

        # 8. initialize_worktree invalid status transition (e.g. from ACTIVE instead of INITIALIZED)
        c_active = OrchestraWorktreeContract(
            unit_id="u1",
            worktree_path=".tmp/sub",
            worktree_branch="feature/sub",
            approved_base_sha=self.base_sha,
            isolation_status=WorktreeIsolationStatus.ACTIVE,
        )
        res_init = initialize_worktree(c_active, self.repo_dir, authorize_creation=True)
        self.assertFalse(res_init.success)

        # 9. initialize_worktree transition INITIALIZED -> STALE_ORPHANED failure (when inspect fails after creation)
        def mock_require_transition(current, target, contract_arg):
            if target == WorktreeIsolationStatus.STALE_ORPHANED:
                return WorktreeOperationResult(
                    success=False,
                    contract=contract_arg,
                    diagnostics=(WorktreeDiagnostic(code=WorktreeReasonCode.INVALID_STATE_TRANSITION, message="invalid"),)
                )
            return _require_transition(current, target, contract_arg)

        def inspect_fail_runner(args, cwd):
            if "status" in args:
                # Returns dirty status -> post-creation inspect fails
                return 0, " M dirty.txt", ""
            return _default_command_runner(args, cwd)

        # Run initialize_worktree where inspect fails and transition to STALE_ORPHANED fails
        c_init = OrchestraWorktreeContract(
            unit_id="u_stale_fail",
            worktree_path=".tmp/sub_stale_fail",
            worktree_branch="feature/sub_stale_fail",
            approved_base_sha=self.base_sha,
            isolation_status=WorktreeIsolationStatus.INITIALIZED,
        )
        with patch("orchestra_runtime.worktree._require_transition", side_effect=mock_require_transition):
            res_init2 = initialize_worktree(c_init, self.repo_dir, authorize_creation=True, runner=inspect_fail_runner)
            self.assertFalse(res_init2.success)
            self.assertEqual(res_init2.diagnostics[0].code, WorktreeReasonCode.INVALID_STATE_TRANSITION)

        # 10. plan_worktree_release inspect_worktree failure
        c_bad_sha = OrchestraWorktreeContract(
            unit_id="u1",
            worktree_path=".tmp/sub",
            worktree_branch="feature/sub",
            approved_base_sha="invalidsha",
            isolation_status=WorktreeIsolationStatus.ACTIVE,
            creation_identity="fake",
        )
        res_plan = plan_worktree_release(c_bad_sha, self.repo_dir)
        self.assertFalse(res_plan.success)

        # 11. plan_worktree_release creation identity mismatch check
        c_mismatch = OrchestraWorktreeContract(
            unit_id="u1",
            worktree_path=".tmp/sub",
            worktree_branch="feature/sub",
            approved_base_sha=self.base_sha,
            isolation_status=WorktreeIsolationStatus.ACTIVE,
            creation_identity="wrong-identity",
        )
        res_plan = plan_worktree_release(c_mismatch, self.repo_dir)
        self.assertFalse(res_plan.success)

        # 12. release_worktree check list error during first inspection
        c_release = OrchestraWorktreeContract(
            unit_id="u1",
            worktree_path=".tmp/sub",
            worktree_branch="feature/sub",
            approved_base_sha=self.base_sha,
            isolation_status=WorktreeIsolationStatus.ACTIVE,
            creation_identity="fake-identity",
        )
        def list_err_runner(args, cwd):
            if "list" in args:
                return 1, "", "error"
            return _default_command_runner(args, cwd)

        with patch("orchestra_runtime.worktree.derive_worktree_creation_identity", return_value="fake-identity"):
            res_rel = release_worktree(c_release, self.repo_dir, authorize_cleanup=True, runner=list_err_runner)
            self.assertFalse(res_rel.success)

        # 13. release_worktree repository identity derivation failure
        with patch("orchestra_runtime.worktree.derive_repository_identity", return_value=(None, WorktreeReasonCode.REPOSITORY_IDENTITY_UNAVAILABLE)):
            res_rel = release_worktree(c_release, self.repo_dir, authorize_cleanup=True)
            self.assertFalse(res_rel.success)

        # 14. release_worktree path resolution failure
        c_release_abs = OrchestraWorktreeContract(
            unit_id="u1",
            worktree_path="/absolute/path",
            worktree_branch="feature/sub",
            approved_base_sha=self.base_sha,
            isolation_status=WorktreeIsolationStatus.ACTIVE,
            creation_identity="fake-identity",
        )
        with patch("orchestra_runtime.worktree.derive_worktree_creation_identity", return_value="fake-identity"):
            res_rel = release_worktree(c_release_abs, self.repo_dir, authorize_cleanup=True)
            self.assertFalse(res_rel.success)

        # 15. release_worktree check diags2 check inside release
        from orchestra_runtime.worktree import ReleasePreconditionFingerprint
        fp_fake = ReleasePreconditionFingerprint(
            repo_identity="repo", registered_path_key="path", head_sha="sha", branch_ref="branch",
            is_clean=True, is_locked=False, nested_repo_found=False, submodule_found=False, creation_identity="fake-identity"
        )
        with patch("orchestra_runtime.worktree.derive_worktree_creation_identity", return_value="fake-identity"), \
             patch("orchestra_runtime.worktree._inspect_for_release", side_effect=[(fp_fake, ()), (fp_fake, (WorktreeDiagnostic(code=WorktreeReasonCode.WORKTREE_DIRTY, message="dirty"),))]):
            res_rel = release_worktree(c_release, self.repo_dir, authorize_cleanup=True)
            self.assertFalse(res_rel.success)

        # 16. release_worktree git worktree remove command fails
        def remove_fail_runner(args, cwd):
            if "remove" in args:
                return 1, "", "error"
            return _default_command_runner(args, cwd)

        target_p = (self.repo_dir / ".tmp" / "sub").resolve()
        target_p.mkdir(parents=True, exist_ok=True)
        wt_info = {"worktree": str(target_p), "head": self.base_sha, "branch": "refs/heads/feature/sub"}
        with patch("orchestra_runtime.worktree._get_worktree_list", return_value=({os.path.normcase(str(target_p)): wt_info}, None)), \
             patch("orchestra_runtime.worktree.derive_worktree_creation_identity", return_value="fake-identity"):
            res_rel = release_worktree(c_release, self.repo_dir, authorize_cleanup=True, runner=remove_fail_runner)
            self.assertFalse(res_rel.success)

        # 17. release_worktree post-release list check failed
        target_p.mkdir(parents=True, exist_ok=True)
        list_call_count = 0
        def post_list_fail_runner(args, cwd):
            if "remove" in args:
                return 0, "", ""
            if "list" in args:
                nonlocal list_call_count
                list_call_count += 1
                if list_call_count > 2:
                    return 1, "", "error"
            return _default_command_runner(args, cwd)

        with patch("orchestra_runtime.worktree.derive_worktree_creation_identity", return_value="fake-identity"), \
             patch("orchestra_runtime.worktree._get_worktree_list", side_effect=[({os.path.normcase(str(target_p)): wt_info}, None), ({os.path.normcase(str(target_p)): wt_info}, None), (None, WorktreeDiagnostic(code=WorktreeReasonCode.NOT_A_GIT_REPO, message="error"))]):
            res_rel = release_worktree(c_release, self.repo_dir, authorize_cleanup=True, runner=post_list_fail_runner)
            self.assertFalse(res_rel.success)
            self.assertEqual(res_rel.diagnostics[0].code, WorktreeReasonCode.WORKTREE_REMOVE_FAILED)

        # 18. release_worktree post-release worktree still registered check
        target_p.mkdir(parents=True, exist_ok=True)
        with patch("orchestra_runtime.worktree.derive_worktree_creation_identity", return_value="fake-identity"), \
             patch("orchestra_runtime.worktree._get_worktree_list", return_value=({os.path.normcase(str(target_p)): wt_info}, None)):
            res_rel = release_worktree(c_release, self.repo_dir, authorize_cleanup=True)
            self.assertFalse(res_rel.success)
            self.assertEqual(res_rel.diagnostics[0].code, WorktreeReasonCode.WORKTREE_REMOVE_FAILED)

        # 19. release_worktree transition failure (ACTIVE -> RELEASED fails)
        target_p.mkdir(parents=True, exist_ok=True)
        def mock_require_transition_released(current, target, contract_arg):
            if target == WorktreeIsolationStatus.RELEASED:
                return WorktreeOperationResult(
                    success=False,
                    contract=contract_arg,
                    diagnostics=(WorktreeDiagnostic(code=WorktreeReasonCode.INVALID_STATE_TRANSITION, message="invalid"),)
                )
            return _require_transition(current, target, contract_arg)

        def success_runner(args, cwd):
            if "remove" in args:
                return 0, "", ""
            if "status" in args:
                return 0, "", ""
            if args[:4] == ["git", "show-ref", "--verify", "--quiet"]:
                return 0, "", ""
            return _default_command_runner(args, cwd)

        with patch("orchestra_runtime.worktree._require_transition", side_effect=mock_require_transition_released), \
             patch("orchestra_runtime.worktree.derive_worktree_creation_identity", return_value="fake-identity"), \
             patch("orchestra_runtime.worktree._get_worktree_list", side_effect=[({os.path.normcase(str(target_p)): wt_info}, None), ({os.path.normcase(str(target_p)): wt_info}, None), ({os.path.normcase(str(target_p)): wt_info}, None), ({}, None)]):
            res_rel = release_worktree(c_release, self.repo_dir, authorize_cleanup=True, runner=success_runner)
            self.assertFalse(res_rel.success)
            self.assertEqual(res_rel.diagnostics[0].code, WorktreeReasonCode.INVALID_STATE_TRANSITION)

        # 20. Cover 752->753 (inspect_worktree invalid path)
        c_invalid_path = OrchestraWorktreeContract(
            unit_id="u_invalid_path",
            worktree_path="/absolute/path",
            worktree_branch="feature/sub",
            approved_base_sha=self.base_sha,
            isolation_status=WorktreeIsolationStatus.ACTIVE,
        )
        res_inspect = inspect_worktree(c_invalid_path, self.repo_dir)
        self.assertFalse(res_inspect.success)

        # 21. Cover 787->818 (target_path exists but is not registered in git worktrees)
        c_unregistered = OrchestraWorktreeContract(
            unit_id="u_unregistered",
            worktree_path=".tmp/unregistered",
            worktree_branch="feature/unregistered",
            approved_base_sha=self.base_sha,
            isolation_status=WorktreeIsolationStatus.ACTIVE,
        )
        unreg_p = (self.repo_dir / ".tmp" / "unregistered").resolve()
        unreg_p.mkdir(parents=True, exist_ok=True)
        res_unreg = inspect_worktree(c_unregistered, self.repo_dir)
        self.assertFalse(res_unreg.success)
        self.assertEqual(res_unreg.diagnostics[0].code, WorktreeReasonCode.WORKTREE_DIRTY)
        unreg_p.rmdir()

        # 22. Cover 871->872 (release_worktree target not in registered worktrees list)
        c_not_reg = OrchestraWorktreeContract(
            unit_id="u_not_reg",
            worktree_path=".tmp/not_reg",
            worktree_branch="feature/not_reg",
            approved_base_sha=self.base_sha,
            isolation_status=WorktreeIsolationStatus.ACTIVE,
            creation_identity="fake-identity",
        )
        not_reg_p = (self.repo_dir / ".tmp" / "not_reg").resolve()
        not_reg_p.mkdir(parents=True, exist_ok=True)
        with patch("orchestra_runtime.worktree.derive_worktree_creation_identity", return_value="fake-identity"), \
             patch("orchestra_runtime.worktree._get_worktree_list", return_value=({}, None)):
            res_not_reg = release_worktree(c_not_reg, self.repo_dir, authorize_cleanup=True)
            self.assertFalse(res_not_reg.success)
            self.assertEqual(res_not_reg.diagnostics[0].code, WorktreeReasonCode.WORKTREE_NOT_REGISTERED)
        not_reg_p.rmdir()

        # 23. Cover 884->885 and 894->895 (release_worktree head/branch mismatch in inspection)
        c_mismatch2 = OrchestraWorktreeContract(
            unit_id="u_mismatch2",
            worktree_path=".tmp/mismatch2",
            worktree_branch="feature/mismatch2",
            approved_base_sha=self.base_sha,
            isolation_status=WorktreeIsolationStatus.ACTIVE,
            creation_identity="fake-identity",
        )
        mismatch2_p = (self.repo_dir / ".tmp" / "mismatch2").resolve()
        mismatch2_p.mkdir(parents=True, exist_ok=True)
        wt_mismatch_info = {"worktree": str(mismatch2_p), "head": "mismatched_sha", "branch": "refs/heads/wrong_branch"}
        with patch("orchestra_runtime.worktree.derive_worktree_creation_identity", return_value="fake-identity"), \
             patch("orchestra_runtime.worktree._get_worktree_list", return_value=({os.path.normcase(str(mismatch2_p)): wt_mismatch_info}, None)):
            res_mismatch2 = release_worktree(c_mismatch2, self.repo_dir, authorize_cleanup=True)
            self.assertFalse(res_mismatch2.success)
            codes = [d.code for d in res_mismatch2.diagnostics]
            self.assertIn(WorktreeReasonCode.BASE_SHA_MISMATCH, codes)
            self.assertIn(WorktreeReasonCode.INVALID_BRANCH, codes)
        mismatch2_p.rmdir()

        # 24. Cover 917->948 and 1333->1334 (target_path does not exist but is registered in list)
        c_no_exist = OrchestraWorktreeContract(
            unit_id="u_no_exist",
            worktree_path=".tmp/no_exist_on_disk",
            worktree_branch="feature/no_exist_on_disk",
            approved_base_sha=self.base_sha,
            isolation_status=WorktreeIsolationStatus.ACTIVE,
            creation_identity="fake-identity",
        )
        no_exist_p = (self.repo_dir / ".tmp" / "no_exist_on_disk").resolve()
        wt_no_exist_info = {"worktree": str(no_exist_p), "head": self.base_sha, "branch": f"refs/heads/{c_no_exist.worktree_branch}"}
        with patch("orchestra_runtime.worktree.derive_worktree_creation_identity", return_value="fake-identity"), \
             patch("orchestra_runtime.worktree._get_worktree_list", return_value=({os.path.normcase(str(no_exist_p)): wt_no_exist_info}, None)):
            res_no_exist = release_worktree(c_no_exist, self.repo_dir, authorize_cleanup=True)
            self.assertFalse(res_no_exist.success)
            self.assertEqual(res_no_exist.diagnostics[0].code, WorktreeReasonCode.WORKTREE_NOT_REGISTERED)

        # 25. Cover 920->921 and 930->931 (nested and submodule boundaries detected in _inspect_for_release)
        c_boundary = OrchestraWorktreeContract(
            unit_id="u_boundary",
            worktree_path=".tmp/boundary",
            worktree_branch="feature/boundary",
            approved_base_sha=self.base_sha,
            isolation_status=WorktreeIsolationStatus.ACTIVE,
            creation_identity="fake-identity",
        )
        boundary_p = (self.repo_dir / ".tmp" / "boundary").resolve()
        boundary_p.mkdir(parents=True, exist_ok=True)
        wt_boundary_info = {"worktree": str(boundary_p), "head": self.base_sha, "branch": f"refs/heads/{c_boundary.worktree_branch}"}
        with patch("orchestra_runtime.worktree.derive_worktree_creation_identity", return_value="fake-identity"), \
             patch("orchestra_runtime.worktree._get_worktree_list", return_value=({os.path.normcase(str(boundary_p)): wt_boundary_info}, None)), \
             patch("orchestra_runtime.worktree.find_nested_git_boundary", return_value=(True, "evidence")), \
             patch("orchestra_runtime.worktree._check_submodule_boundary", return_value=True):
            res_boundary = release_worktree(c_boundary, self.repo_dir, authorize_cleanup=True)
            self.assertFalse(res_boundary.success)
            codes = [d.code for d in res_boundary.diagnostics]
            self.assertIn(WorktreeReasonCode.NESTED_REPOSITORY_DETECTED, codes)
            self.assertIn(WorktreeReasonCode.SUBMODULE_BOUNDARY_DETECTED, codes)
        boundary_p.rmdir()

        # 26. Cover 990->991 (resolve_authorized_worktree_path fails in initialize_worktree)
        with patch("orchestra_runtime.worktree.resolve_authorized_worktree_path", return_value=(None, WorktreeReasonCode.PATH_OUTSIDE_AUTHORIZED_PARENT)):
            res_init3 = initialize_worktree(c, self.repo_dir, authorize_creation=True)
            self.assertFalse(res_init3.success)

        # 27. Cover 1050->1051 (git worktree add fails in initialize_worktree)
        c_add_fail = OrchestraWorktreeContract(
            unit_id="u_add_fail",
            worktree_path=".tmp/sub_add_fail",
            worktree_branch="feature/sub_add_fail",
            approved_base_sha=self.base_sha,
            isolation_status=WorktreeIsolationStatus.INITIALIZED,
        )
        def add_fail_runner(args, cwd):
            if "add" in args:
                return 1, "", "error"
            return _default_command_runner(args, cwd)
        res_init4 = initialize_worktree(c_add_fail, self.repo_dir, authorize_creation=True, runner=add_fail_runner)
        self.assertFalse(res_init4.success)
        self.assertEqual(res_init4.diagnostics[0].code, WorktreeReasonCode.WORKTREE_ADD_FAILED)

        # 28. Cover 1130->1131 (inspect_worktree fails in plan_worktree_release)
        with patch("orchestra_runtime.worktree.inspect_worktree", return_value=WorktreeOperationResult(success=False, contract=c, diagnostics=(WorktreeDiagnostic(code=WorktreeReasonCode.BASE_SHA_MISMATCH, message="mismatch"),))):
            res_plan_fail = plan_worktree_release(c, self.repo_dir)
            self.assertFalse(res_plan_fail.success)

        # 29. Cover 1143->1153 (plan_worktree_release with creation_identity=None)
        c_no_id = OrchestraWorktreeContract(
            unit_id="u_no_id",
            worktree_path=".tmp/sub",
            worktree_branch="feature/sub",
            approved_base_sha=self.base_sha,
            isolation_status=WorktreeIsolationStatus.ACTIVE,
            creation_identity=None,
        )
        with patch("orchestra_runtime.worktree.inspect_worktree", return_value=WorktreeOperationResult(success=True, contract=c_no_id, diagnostics=())):
            res_plan_no_id = plan_worktree_release(c_no_id, self.repo_dir)
            self.assertTrue(res_plan_no_id.success)

        # 30. Cover 1245->1246 (resolve_authorized_worktree_path fails in release_worktree)
        with patch("orchestra_runtime.worktree.resolve_authorized_worktree_path", return_value=(None, WorktreeReasonCode.PATH_OUTSIDE_AUTHORIZED_PARENT)):
            res_rel_fail = release_worktree(c, self.repo_dir, authorize_cleanup=True)
            self.assertFalse(res_rel_fail.success)

        # 31. Cover 1470->1472 and 1472->1474 (serialize_worktree_contract with None correlation_id and creation_identity)
        from orchestra_runtime.worktree import serialize_worktree_contract
        c_none_fields = OrchestraWorktreeContract(
            unit_id="u_none_fields",
            worktree_path=".tmp/sub",
            worktree_branch="feature/sub",
            approved_base_sha=self.base_sha,
            isolation_status=WorktreeIsolationStatus.ACTIVE,
            correlation_id=None,
            creation_identity=None,
        )
        payload = serialize_worktree_contract(c_none_fields)
        self.assertNotIn("correlation_id", payload)
        self.assertNotIn("creation_identity", payload)

        # Clean up target_p directory
        if target_p.exists():
            target_p.rmdir()


if __name__ == "__main__":
    unittest.main()
