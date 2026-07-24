"""Deterministic, read-only Git evidence identity for Orchestra Phase 2.

This module never stages, restores, cleans, commits, pushes, or otherwise mutates
repository state. It emits paths and cryptographic identities only; file content
is never embedded in an evidence packet.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence

CANONICALIZATION_VERSION = "orchestra-evidence-v1"
HASH_ALGORITHM = "sha256"
IDENTITY_FIELDS = (
    "canonicalization_version",
    "hash_algorithm",
    "repository_identity",
    "branch",
    "approved_base_sha",
    "current_commit_sha",
    "git_object_format",
    "tracked_patch_hash",
    "staged_patch_hash",
    "untracked_file_manifest",
    "untracked_manifest_hash",
    "added_blob_hashes",
    "added_blob_hashes_hash",
    "artifact_lifecycle_records",
    "relevant_artifact_lifecycle_hash",
    "working_tree_fingerprint",
)


class EvidenceIdentityError(RuntimeError):
    """Raised when repository identity cannot be represented deterministically."""


def _run_git(repo_root: Path, args: Sequence[str], *, check: bool = True) -> bytes:
    command = ["git", "-C", str(repo_root), *args]
    completed = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and completed.returncode != 0:
        stderr = completed.stderr.decode("utf-8", errors="replace").strip()
        raise EvidenceIdentityError(
            f"Git command failed ({completed.returncode}): {' '.join(command)}"
            + (f"\n{stderr}" if stderr else "")
        )
    return completed.stdout


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize identity-bearing JSON using the Phase 2 canonical rules."""
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise EvidenceIdentityError(f"Value is not canonical JSON: {exc}") from exc
    return encoded.encode("utf-8")


def canonical_hash(value: Any) -> str:
    return _sha256_bytes(canonical_json_bytes(value))


def normalize_repo_path(raw_path: str) -> str:
    """Return a safe repository-relative POSIX path."""
    if not isinstance(raw_path, str) or not raw_path:
        raise EvidenceIdentityError("Repository path must be a non-empty string.")
    if "\x00" in raw_path:
        raise EvidenceIdentityError("Repository path contains a NUL byte.")
    normalized = raw_path.replace("\\", "/")
    candidate = PurePosixPath(normalized)
    if candidate.is_absolute() or any(part in {"", ".", ".."} for part in candidate.parts):
        raise EvidenceIdentityError(f"Unsafe repository-relative path: {raw_path!r}")
    return candidate.as_posix()


def _nul_paths(payload: bytes) -> list[str]:
    paths: list[str] = []
    for item in payload.split(b"\x00"):
        if not item:
            continue
        paths.append(normalize_repo_path(item.decode("utf-8", errors="surrogateescape")))
    return sorted(set(paths))


def _git_text(repo_root: Path, args: Sequence[str]) -> str:
    return _run_git(repo_root, args).decode("utf-8", errors="strict").strip()


def _ensure_repository(repo_root: Path) -> Path:
    resolved = repo_root.resolve()
    top = _git_text(resolved, ["rev-parse", "--show-toplevel"])
    top_path = Path(top).resolve()
    if top_path != resolved:
        resolved = top_path
    return resolved


def _repository_identity(repo_root: Path) -> str:
    remote = _run_git(repo_root, ["remote", "get-url", "origin"], check=False)
    if remote:
        return remote.decode("utf-8", errors="replace").strip()
    return repo_root.as_posix()


def _branch(repo_root: Path) -> str:
    branch = _run_git(repo_root, ["symbolic-ref", "--quiet", "--short", "HEAD"], check=False)
    if branch:
        return branch.decode("utf-8", errors="strict").strip()
    return "DETACHED"


def _object_format(repo_root: Path) -> str:
    value = _run_git(repo_root, ["rev-parse", "--show-object-format"], check=False)
    text = value.decode("utf-8", errors="replace").strip()
    return text or "sha1"


def _verify_commit(repo_root: Path, revision: str, label: str) -> str:
    if not revision or not isinstance(revision, str):
        raise EvidenceIdentityError(f"{label} must be a Git revision string.")
    return _git_text(repo_root, ["rev-parse", "--verify", f"{revision}^{{commit}}"])


def _patch_hash(repo_root: Path, approved_base_sha: str, *, staged: bool) -> str:
    args = [
        "diff",
        "--binary",
        "--full-index",
        "--no-ext-diff",
        "--no-color",
        "--no-renames",
        "--src-prefix=a/",
        "--dst-prefix=b/",
    ]
    if staged:
        args.extend(["--cached", "HEAD", "--"])
    else:
        args.extend([approved_base_sha, "--"])
    return _sha256_bytes(_run_git(repo_root, args))


def _file_kind(path: Path) -> str:
    if path.is_symlink():
        return "symlink"
    if path.is_file():
        return "regular"
    raise EvidenceIdentityError(f"Identity path is not a regular file or symlink: {path}")


def _byte_length(path: Path, kind: str) -> int:
    if kind == "symlink":
        return len(os.readlink(path).encode("utf-8", errors="surrogateescape"))
    return path.stat().st_size


def _working_blob_oid(repo_root: Path, relative_path: str) -> str:
    output = _git_text(
        repo_root,
        ["hash-object", f"--path={relative_path}", "--", relative_path],
    )
    if not output:
        raise EvidenceIdentityError(f"Git did not return a blob identity for {relative_path}")
    return output


def _index_blob_oid(repo_root: Path, relative_path: str) -> str | None:
    output = _run_git(repo_root, ["ls-files", "--stage", "-z", "--", relative_path], check=False)
    if not output:
        return None
    first = output.split(b"\x00", 1)[0].decode("utf-8", errors="surrogateescape")
    metadata, _, path_text = first.partition("\t")
    if normalize_repo_path(path_text) != relative_path:
        return None
    fields = metadata.split()
    if len(fields) < 3:
        raise EvidenceIdentityError(f"Malformed index identity for {relative_path}")
    return fields[1]


def _untracked_manifest(repo_root: Path, object_format: str) -> list[dict[str, Any]]:
    paths = _nul_paths(_run_git(repo_root, ["ls-files", "--others", "--exclude-standard", "-z"]))
    manifest: list[dict[str, Any]] = []
    for relative_path in paths:
        absolute = repo_root / Path(relative_path)
        kind = _file_kind(absolute)
        manifest.append(
            {
                "path": relative_path,
                "file_kind": kind,
                "git_object_format": object_format,
                "blob_oid": _working_blob_oid(repo_root, relative_path),
                "byte_length": _byte_length(absolute, kind),
            }
        )
    return manifest


def _added_paths(repo_root: Path, approved_base_sha: str) -> list[str]:
    committed = _nul_paths(
        _run_git(
            repo_root,
            ["diff", "--name-only", "--diff-filter=A", "-z", approved_base_sha, "HEAD", "--"],
        )
    )
    staged = _nul_paths(
        _run_git(
            repo_root,
            ["diff", "--cached", "--name-only", "--diff-filter=A", "-z", "HEAD", "--"],
        )
    )
    return sorted(set(committed) | set(staged))


def _added_blob_hashes(
    repo_root: Path,
    approved_base_sha: str,
    object_format: str,
) -> list[dict[str, str]]:
    identities: list[dict[str, str]] = []
    for relative_path in _added_paths(repo_root, approved_base_sha):
        oid = _index_blob_oid(repo_root, relative_path)
        if oid is None:
            absolute = repo_root / Path(relative_path)
            if not absolute.exists() and not absolute.is_symlink():
                raise EvidenceIdentityError(f"Added path has no index or working identity: {relative_path}")
            oid = _working_blob_oid(repo_root, relative_path)
        identities.append(
            {
                "path": relative_path,
                "git_object_format": object_format,
                "blob_oid": oid,
            }
        )
    return identities


def normalize_artifact_records(records: Iterable[Mapping[str, Any]] | None) -> list[dict[str, Any]]:
    if records is None:
        return []
    normalized: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, Mapping):
            raise EvidenceIdentityError("Artifact lifecycle records must be JSON objects.")
        copied = dict(record)
        if "path" in copied and copied["path"] is not None:
            copied["path"] = normalize_repo_path(str(copied["path"]))
        normalized.append(copied)
    return sorted(
        normalized,
        key=lambda item: (
            str(item.get("path", "")),
            str(item.get("artifact_id", "")),
            canonical_json_bytes(item),
        ),
    )


def collect_evidence_identity(
    repo_root: Path | str,
    approved_base_sha: str,
    artifact_lifecycle_records: Iterable[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Collect a deterministic identity snapshot without modifying repository state."""
    root = _ensure_repository(Path(repo_root))
    approved_base = _verify_commit(root, approved_base_sha, "approved_base_sha")
    current_commit = _verify_commit(root, "HEAD", "HEAD")
    object_format = _object_format(root)
    untracked = _untracked_manifest(root, object_format)
    added = _added_blob_hashes(root, approved_base, object_format)
    artifacts = normalize_artifact_records(artifact_lifecycle_records)

    identity: dict[str, Any] = {
        "canonicalization_version": CANONICALIZATION_VERSION,
        "hash_algorithm": HASH_ALGORITHM,
        "repository_identity": _repository_identity(root),
        "branch": _branch(root),
        "approved_base_sha": approved_base,
        "current_commit_sha": current_commit,
        "git_object_format": object_format,
        "tracked_patch_hash": _patch_hash(root, approved_base, staged=False),
        "staged_patch_hash": _patch_hash(root, approved_base, staged=True),
        "untracked_file_manifest": untracked,
        "untracked_manifest_hash": canonical_hash(untracked),
        "added_blob_hashes": added,
        "added_blob_hashes_hash": canonical_hash(added),
        "artifact_lifecycle_records": artifacts,
        "relevant_artifact_lifecycle_hash": canonical_hash(artifacts),
    }
    fingerprint_input = {
        key: identity[key]
        for key in (
            "repository_identity",
            "branch",
            "approved_base_sha",
            "current_commit_sha",
            "tracked_patch_hash",
            "staged_patch_hash",
            "untracked_manifest_hash",
            "added_blob_hashes_hash",
            "relevant_artifact_lifecycle_hash",
        )
    }
    identity["working_tree_fingerprint"] = canonical_hash(fingerprint_input)
    return identity


def validate_identity_document(expected: Mapping[str, Any], current: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if expected.get("canonicalization_version") != CANONICALIZATION_VERSION:
        errors.append(
            "unsupported canonicalization_version: "
            f"{expected.get('canonicalization_version')!r}"
        )
    if expected.get("hash_algorithm") != HASH_ALGORITHM:
        errors.append(f"unsupported hash_algorithm: {expected.get('hash_algorithm')!r}")

    for field in IDENTITY_FIELDS:
        if field not in expected:
            errors.append(f"missing identity field: {field}")
            continue
        if field not in current:
            errors.append(f"collector omitted identity field: {field}")
            continue
        if expected[field] != current[field]:
            errors.append(f"identity mismatch: {field}")
    return errors


def validate_evidence_file(
    repo_root: Path | str,
    approved_base_sha: str,
    evidence_path: Path | str,
) -> list[str]:
    evidence = json.loads(Path(evidence_path).read_text(encoding="utf-8"))
    if not isinstance(evidence, Mapping):
        return ["evidence document must be a JSON object"]
    artifacts = evidence.get("artifact_lifecycle_records", [])
    current = collect_evidence_identity(repo_root, approved_base_sha, artifacts)
    return validate_identity_document(evidence, current)


def _load_artifacts(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise EvidenceIdentityError("Artifact JSON must contain a top-level list.")
    return value


def _write_json(value: Any, output: Path | None) -> None:
    rendered = json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if output is None:
        sys.stdout.write(rendered)
        return
    output.write_text(rendered, encoding="utf-8", newline="\n")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect or validate Orchestra evidence identity.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    collect = subparsers.add_parser("collect", help="Collect current read-only repository identity.")
    collect.add_argument("--repo-root", type=Path, default=Path.cwd())
    collect.add_argument("--approved-base-sha", required=True)
    collect.add_argument("--artifact-records", type=Path)
    collect.add_argument("--output", type=Path)

    validate = subparsers.add_parser("validate", help="Validate an evidence JSON file.")
    validate.add_argument("--repo-root", type=Path, default=Path.cwd())
    validate.add_argument("--approved-base-sha", required=True)
    validate.add_argument("--evidence-json", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "collect":
            artifacts = _load_artifacts(args.artifact_records)
            identity = collect_evidence_identity(args.repo_root, args.approved_base_sha, artifacts)
            _write_json(identity, args.output)
            return 0

        errors = validate_evidence_file(
            args.repo_root,
            args.approved_base_sha,
            args.evidence_json,
        )
        if errors:
            for error in errors:
                print(f"[FAIL] {error}")
            return 1
        print("[PASS] Evidence identity matches the current repository state.")
        return 0
    except (EvidenceIdentityError, OSError, json.JSONDecodeError) as exc:
        print(f"[FAIL] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
