import copy
import gc
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts/evidence_identity.py"
VALIDATOR_PATH = ROOT / "scripts/validate_evidence_identity.py"
FIXTURES_PATH = ROOT / "tests/behavior/evidence-identity-fixtures.json"

spec = importlib.util.spec_from_file_location("evidence_identity", MODULE_PATH)
identity = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = identity
spec.loader.exec_module(identity)


def run(repo, *args, input_bytes=None, check=True):
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode != 0:
        raise AssertionError(
            f"git {' '.join(args)} failed: "
            + result.stderr.decode("utf-8", errors="replace")
        )
    return result


def _remove_readonly(func, path, exc_info):
    error = exc_info[1]
    if not isinstance(error, PermissionError):
        raise error
    mode = stat.S_IWRITE | stat.S_IREAD
    if os.path.isdir(path):
        mode |= stat.S_IEXEC
    os.chmod(path, mode)
    func(path)


def cleanup_repo(repo):
    if not repo.exists():
        return
    last_error = None
    for attempt in range(6):
        try:
            shutil.rmtree(repo, onerror=_remove_readonly)
            return
        except PermissionError as exc:
            last_error = exc
            gc.collect()
            time.sleep(0.1 * (attempt + 1))
    raise last_error


def make_repo():
    path = Path(tempfile.mkdtemp(prefix="orchestra-evidence-test-"))
    run(path, "init")
    run(path, "config", "user.email", "test@example.com")
    run(path, "config", "user.name", "Orchestra Test")
    run(path, "config", "core.autocrlf", "false")
    (path / ".gitattributes").write_text("*.txt text eol=lf\n", encoding="utf-8", newline="\n")
    (path / "tracked.txt").write_text("alpha\n", encoding="utf-8", newline="\n")
    run(path, "add", ".gitattributes", "tracked.txt")
    run(path, "commit", "-m", "baseline")
    baseline = run(path, "rev-parse", "HEAD").stdout.decode().strip()
    return path, baseline


def test_static_canonicalization_fixture():
    fixtures = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
    canonical = fixtures["canonical_hash_fixture"]
    assert identity.canonical_hash(canonical["value"]) == canonical["expected_sha256"]
    for case in fixtures["path_normalization"]:
        assert identity.normalize_repo_path(case["input"]) == case["expected"]
    for unsafe in fixtures["unsafe_paths"]:
        try:
            identity.normalize_repo_path(unsafe)
        except identity.EvidenceIdentityError:
            pass
        else:
            raise AssertionError(f"unsafe path accepted: {unsafe}")


def test_clean_identity_is_self_consistent():
    repo, baseline = make_repo()
    try:
        snapshot = identity.collect_evidence_identity(repo, baseline)
        assert snapshot["canonicalization_version"] == "orchestra-evidence-v1"
        assert snapshot["untracked_file_manifest"] == []
        assert snapshot["added_blob_hashes"] == []
        assert identity.validate_identity_document(snapshot, snapshot) == []
    finally:
        cleanup_repo(repo)


def test_tracked_staged_untracked_and_added_identity_changes():
    repo, baseline = make_repo()
    try:
        clean = identity.collect_evidence_identity(repo, baseline)
        (repo / "tracked.txt").write_text("alpha\nbeta\n", encoding="utf-8", newline="\n")
        tracked = identity.collect_evidence_identity(repo, baseline)
        assert tracked["tracked_patch_hash"] != clean["tracked_patch_hash"]
        assert tracked["staged_patch_hash"] == clean["staged_patch_hash"]

        run(repo, "add", "tracked.txt")
        staged = identity.collect_evidence_identity(repo, baseline)
        assert staged["staged_patch_hash"] != clean["staged_patch_hash"]

        (repo / "new-file.txt").write_text("new\n", encoding="utf-8", newline="\n")
        untracked = identity.collect_evidence_identity(repo, baseline)
        assert [item["path"] for item in untracked["untracked_file_manifest"]] == ["new-file.txt"]

        run(repo, "add", "new-file.txt")
        added = identity.collect_evidence_identity(repo, baseline)
        assert added["untracked_file_manifest"] == []
        assert [item["path"] for item in added["added_blob_hashes"]] == ["new-file.txt"]
    finally:
        cleanup_repo(repo)


def test_committed_descendant_changes_tracked_patch_hash():
    repo, baseline = make_repo()
    try:
        clean = identity.collect_evidence_identity(repo, baseline)
        (repo / "tracked.txt").write_text("alpha\ncommitted\n", encoding="utf-8", newline="\n")
        run(repo, "add", "tracked.txt")
        run(repo, "commit", "-m", "descendant")
        descendant = identity.collect_evidence_identity(repo, baseline)
        head_relative = identity.collect_evidence_identity(repo, "HEAD")
        assert descendant["tracked_patch_hash"] != clean["tracked_patch_hash"]
        assert head_relative["tracked_patch_hash"] == identity._sha256_bytes(b"")
    finally:
        cleanup_repo(repo)


def test_untracked_manifest_supports_binary_empty_and_unicode_paths():
    repo, baseline = make_repo()
    try:
        (repo / "empty.bin").write_bytes(b"")
        (repo / "binary.bin").write_bytes(bytes(range(256)))
        (repo / "unicodé.txt").write_text("content\n", encoding="utf-8")
        snapshot = identity.collect_evidence_identity(repo, baseline)
        paths = [item["path"] for item in snapshot["untracked_file_manifest"]]
        assert paths == sorted(["binary.bin", "empty.bin", "unicodé.txt"])
        sizes = {item["path"]: item["byte_length"] for item in snapshot["untracked_file_manifest"]}
        assert sizes["empty.bin"] == 0
        assert sizes["binary.bin"] == 256
    finally:
        cleanup_repo(repo)


def test_omitted_untracked_file_and_wrong_metadata_fail_validation():
    repo, baseline = make_repo()
    try:
        (repo / "untracked.txt").write_text("x\n", encoding="utf-8")
        snapshot = identity.collect_evidence_identity(repo, baseline)

        omitted = json.loads(json.dumps(snapshot))
        omitted["untracked_file_manifest"] = []
        errors = identity.validate_identity_document(omitted, snapshot)
        assert "identity mismatch: untracked_file_manifest" in errors

        wrong = json.loads(json.dumps(snapshot))
        wrong["branch"] = "wrong-branch"
        wrong["current_commit_sha"] = "0" * 40
        errors = identity.validate_identity_document(wrong, snapshot)
        assert "identity mismatch: branch" in errors
        assert "identity mismatch: current_commit_sha" in errors

        unknown = json.loads(json.dumps(snapshot))
        unknown["canonicalization_version"] = "future-version"
        errors = identity.validate_identity_document(unknown, snapshot)
        assert any("unsupported canonicalization_version" in item for item in errors)
    finally:
        cleanup_repo(repo)


def test_clean_filter_blob_identity_normalizes_crlf():
    repo, baseline = make_repo()
    try:
        committed_blob = run(repo, "rev-parse", "HEAD:tracked.txt").stdout.decode().strip()
        (repo / "tracked.txt").write_bytes(b"alpha\r\n")
        filtered_blob = run(
            repo,
            "hash-object",
            "--path=tracked.txt",
            "--",
            "tracked.txt",
        ).stdout.decode().strip()
        assert filtered_blob == committed_blob
        snapshot = identity.collect_evidence_identity(repo, baseline)
        assert snapshot["tracked_patch_hash"] == identity._sha256_bytes(b"")
    finally:
        cleanup_repo(repo)


def test_repository_identity_redacts_credentials_and_local_paths():
    repo, baseline = make_repo()
    try:
        run(repo, "remote", "add", "origin", "https://user:secret@example.com/owner/repo.git")
        snapshot = identity.collect_evidence_identity(repo, baseline)
        assert snapshot["repository_identity"] == "https://example.com/owner/repo.git"
        assert "user" not in snapshot["repository_identity"]
        assert "secret" not in snapshot["repository_identity"]

        run(repo, "remote", "remove", "origin")
        local = identity.collect_evidence_identity(repo, baseline)
        assert local["repository_identity"].startswith("local-repository-sha256:")
        assert str(repo) not in local["repository_identity"]
    finally:
        cleanup_repo(repo)


def test_unexpected_git_failures_fail_closed():
    repo, baseline = make_repo()
    original = identity.subprocess.run

    def forced_failure(command, **kwargs):
        if command[-2:] == ["rev-parse", "--show-object-format"]:
            return subprocess.CompletedProcess(
                command,
                128,
                stdout=b"",
                stderr=b"forced failure",
            )
        return original(command, **kwargs)

    try:
        identity.subprocess.run = forced_failure
        try:
            identity.collect_evidence_identity(repo, baseline)
        except identity.EvidenceIdentityError as exc:
            assert "forced failure" in str(exc)
        else:
            raise AssertionError("unexpected Git failure did not fail closed")
    finally:
        identity.subprocess.run = original
        cleanup_repo(repo)


def _artifact_record(repo, baseline, relative_path):
    current = run(repo, "rev-parse", "HEAD").stdout.decode().strip()
    artifact = repo / relative_path
    content_hash = identity._sha256_bytes(artifact.read_bytes())
    return {
        "artifact_id": "report",
        "collaboration_session_id": "session-1",
        "contract_packet_revision": 2,
        "producer_role": "overseer",
        "producing_command": "python generate_report.py",
        "path": relative_path,
        "artifact_type": "validation-report",
        "state_before": "ABSENT",
        "state_after": "PRESENT_UNTRACKED",
        "content_hash": content_hash,
        "inspection_required": True,
        "inspection_owner": "overseer",
        "inspection_completed": True,
        "retention_required": True,
        "cleanup_authority": None,
        "cleanup_condition": None,
        "cleanup_performed": False,
        "cleanup_evidence": None,
        "freshness_binding": {
            "baseline_sha": baseline,
            "current_commit_sha": current,
            "contract_hash": "c" * 64,
        },
    }


def test_artifact_records_require_independent_current_verification():
    repo, baseline = make_repo()
    try:
        (repo / "report.json").write_text('{"ok":true}\n', encoding="utf-8", newline="\n")
        record = _artifact_record(repo, baseline, "report.json")
        snapshot = identity.collect_evidence_identity(repo, baseline, [record])
        handle, evidence_name = tempfile.mkstemp(prefix="orchestra-evidence-", suffix=".json")
        os.close(handle)
        evidence_path = Path(evidence_name)
        evidence_path.write_text(json.dumps(snapshot), encoding="utf-8")

        errors = identity.validate_evidence_file(repo, baseline, evidence_path)
        assert any("cannot validate itself" in item for item in errors)

        assert identity.validate_evidence_file(repo, baseline, evidence_path, [record]) == []

        missing_hash = copy.deepcopy(record)
        missing_hash["content_hash"] = None
        try:
            identity.collect_evidence_identity(repo, baseline, [missing_hash])
        except identity.EvidenceIdentityError as exc:
            assert "content_hash" in str(exc)
        else:
            raise AssertionError("present artifact without content_hash was accepted")

        invalid_state = copy.deepcopy(record)
        invalid_state["state_after"] = "UNKNOWN"
        try:
            identity.collect_evidence_identity(repo, baseline, [invalid_state])
        except identity.EvidenceIdentityError as exc:
            assert "invalid state_after" in str(exc)
        else:
            raise AssertionError("invalid artifact state was accepted")

        (repo / "report.json").write_text('{"ok":false}\n', encoding="utf-8", newline="\n")
        try:
            identity.validate_evidence_file(repo, baseline, evidence_path, [record])
        except identity.EvidenceIdentityError as exc:
            assert "content_hash differs" in str(exc)
        else:
            raise AssertionError("stale artifact content was accepted")

        (repo / "report.json").unlink()
        try:
            identity.validate_evidence_file(repo, baseline, evidence_path, [record])
        except identity.EvidenceIdentityError as exc:
            assert "state_after" in str(exc)
        else:
            raise AssertionError("missing artifact was accepted")
    finally:
        if "evidence_path" in locals() and evidence_path.exists():
            evidence_path.unlink()
        cleanup_repo(repo)


def test_validator_requires_explicit_baseline():
    result = subprocess.run(
        [sys.executable, str(VALIDATOR_PATH), "--repo-root", str(ROOT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "--approved-base-sha" in result.stderr


def main():
    test_static_canonicalization_fixture()
    test_clean_identity_is_self_consistent()
    test_tracked_staged_untracked_and_added_identity_changes()
    test_committed_descendant_changes_tracked_patch_hash()
    test_untracked_manifest_supports_binary_empty_and_unicode_paths()
    test_omitted_untracked_file_and_wrong_metadata_fail_validation()
    test_clean_filter_blob_identity_normalizes_crlf()
    test_repository_identity_redacts_credentials_and_local_paths()
    test_unexpected_git_failures_fail_closed()
    test_artifact_records_require_independent_current_verification()
    test_validator_requires_explicit_baseline()
    print("Evidence identity tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
