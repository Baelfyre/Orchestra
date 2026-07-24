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
FIXTURES_PATH = ROOT / "tests/behavior/evidence-identity-fixtures.json"

spec = importlib.util.spec_from_file_location("evidence_identity", MODULE_PATH)
identity = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = identity
spec.loader.exec_module(identity)


def run(repo, *args, input_bytes=None):
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"git {' '.join(args)} failed: "
            + result.stderr.decode("utf-8", errors="replace")
        )
    return result.stdout


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
    baseline = run(path, "rev-parse", "HEAD").decode().strip()
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
        committed_blob = run(repo, "rev-parse", "HEAD:tracked.txt").decode().strip()
        (repo / "tracked.txt").write_bytes(b"alpha\r\n")
        filtered_blob = run(
            repo,
            "hash-object",
            "--path=tracked.txt",
            "--",
            "tracked.txt",
        ).decode().strip()
        assert filtered_blob == committed_blob
        snapshot = identity.collect_evidence_identity(repo, baseline)
        assert snapshot["tracked_patch_hash"] == identity._sha256_bytes(b"")
    finally:
        cleanup_repo(repo)


def test_artifact_records_are_path_normalized_and_deterministic():
    repo, baseline = make_repo()
    try:
        records = [
            {"artifact_id": "b", "path": "test-results\\b.json", "state_before": "ABSENT"},
            {"artifact_id": "a", "path": "coverage/a.json", "state_before": "PRESENT_IGNORED"},
        ]
        first = identity.collect_evidence_identity(repo, baseline, records)
        second = identity.collect_evidence_identity(repo, baseline, list(reversed(records)))
        assert first["artifact_lifecycle_records"] == second["artifact_lifecycle_records"]
        assert first["relevant_artifact_lifecycle_hash"] == second["relevant_artifact_lifecycle_hash"]
    finally:
        cleanup_repo(repo)


def main():
    test_static_canonicalization_fixture()
    test_clean_identity_is_self_consistent()
    test_tracked_staged_untracked_and_added_identity_changes()
    test_untracked_manifest_supports_binary_empty_and_unicode_paths()
    test_omitted_untracked_file_and_wrong_metadata_fail_validation()
    test_clean_filter_blob_identity_normalizes_crlf()
    test_artifact_records_are_path_normalized_and_deterministic()
    print("Evidence identity tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
