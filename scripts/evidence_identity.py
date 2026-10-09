"""Deterministic, read-only Git evidence identity for Orchestra Phase 2.

This module never stages, restores, cleans, commits, pushes, fetches, or otherwise
mutates repository state. It emits normalized paths and cryptographic identities
only; file content and credentials are never embedded in an evidence packet.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import urlsplit, urlunsplit

CANONICALIZATION_VERSION = "orchestra-evidence-v1"
HASH_ALGORITHM = "sha256"
GIT_HASH_RE = re.compile(r"^[0-9a-f]{40,64}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:(?:/|$)")
ARTIFACT_STATES = {
    "ABSENT",
    "PRESENT_TRACKED",
    "PRESENT_UNTRACKED",
    "PRESENT_IGNORED",
}
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


def _run_git_process(
    repo_root: Path,
    args: Sequence[str],
    *,
    check: bool = True,
    allowed_returncodes: Sequence[int] = (0,),
) -> subprocess.CompletedProcess[bytes]:
    command = ["git", "-C", str(repo_root), *args]
    completed = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and completed.returncode not in allowed_returncodes:
        stderr = completed.stderr.decode("utf-8", errors="replace").strip()
        raise EvidenceIdentityError(
            f"Git command failed ({completed.returncode}): {' '.join(command)}"
            + (f"\n{stderr}" if stderr else "")
        )
    return completed


def _run_git(repo_root: Path, args: Sequence[str]) -> bytes:
    return _run_git_process(repo_root, args).stdout


def _git_text(repo_root: Path, args: Sequence[str]) -> str:
    return _run_git(repo_root, args).decode("utf-8", errors="strict").strip()


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
    if normalized.startswith("/") or normalized.startswith("//"):
        raise EvidenceIdentityError(f"Absolute or UNC path is not allowed: {raw_path!r}")
    if WINDOWS_DRIVE_RE.match(normalized):
        raise EvidenceIdentityError(f"Windows drive-qualified path is not allowed: {raw_path!r}")
    if normalized.startswith("//?/") or normalized.startswith("//./"):
        raise EvidenceIdentityError(f"Windows device path is not allowed: {raw_path!r}")

    parts = normalized.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise EvidenceIdentityError(f"Unsafe repository-relative path: {raw_path!r}")
    return "/".join(parts)


def _nul_paths(payload: bytes) -> list[str]:
    paths: list[str] = []
    for item in payload.split(b"\x00"):
        if not item:
            continue
        paths.append(normalize_repo_path(item.decode("utf-8", errors="surrogateescape")))
    return sorted(set(paths))


def _ensure_repository(repo_root: Path) -> Path:
    resolved = repo_root.resolve()
    top = _git_text(resolved, ["rev-parse", "--show-toplevel"])
    return Path(top).resolve()


def _sanitize_remote_url(remote: str) -> str:
    value = remote.strip()
    if not value:
        raise EvidenceIdentityError("Origin remote URL is empty.")

    if "://" in value:
        parsed = urlsplit(value)
        scheme = parsed.scheme.lower()
        if scheme == "file":
            return f"file-sha256:{_sha256_bytes(value.encode('utf-8'))}"
        if not parsed.hostname:
            raise EvidenceIdentityError("Origin remote URL has no hostname.")
        host = parsed.hostname.lower()
        try:
            port = parsed.port
        except ValueError as exc:
            raise EvidenceIdentityError(f"Origin remote URL has an invalid port: {exc}") from exc
        if port is not None:
            host = f"{host}:{port}"
        return urlunsplit((scheme, host, parsed.path, "", ""))

    scp_like = re.fullmatch(r"(?:(?:[^@/\s]+)@)?([^:/\s]+):(.+)", value)
    if scp_like:
        host, path = scp_like.groups()
        return f"ssh://{host.lower()}/{path.lstrip('/')}"

    # Local-path remotes are represented by a non-reversible digest.
    return f"local-remote-sha256:{_sha256_bytes(value.encode('utf-8', errors='surrogateescape'))}"


def _repository_identity(repo_root: Path) -> str:
    remotes = set(_git_text(repo_root, ["remote"]).splitlines())
    if "origin" not in remotes:
        digest = _sha256_bytes(repo_root.as_posix().encode("utf-8", errors="surrogateescape"))
        return f"local-repository-sha256:{digest}"
    remote = _git_text(repo_root, ["remote", "get-url", "origin"])
    return _sanitize_remote_url(remote)


def _branch(repo_root: Path) -> str:
    completed = _run_git_process(
        repo_root,
        ["symbolic-ref", "--quiet", "--short", "HEAD"],
        check=False,
    )
    if completed.returncode == 0:
        return completed.stdout.decode("utf-8", errors="strict").strip()
    if completed.returncode == 1 and not completed.stdout:
        return "DETACHED"
    stderr = completed.stderr.decode("utf-8", errors="replace").strip()
    raise EvidenceIdentityError(
        f"Could not determine branch ({completed.returncode})"
        + (f": {stderr}" if stderr else "")
    )


def _object_format(repo_root: Path) -> str:
    value = _git_text(repo_root, ["rev-parse", "--show-object-format"])
    if value not in {"sha1", "sha256"}:
        raise EvidenceIdentityError(f"Unsupported Git object format: {value!r}")
    return value


def _verify_commit(repo_root: Path, revision: str, label: str) -> str:
    if not isinstance(revision, str) or not revision.strip():
        raise EvidenceIdentityError(f"{label} must be a Git revision string.")
    value = _git_text(repo_root, ["rev-parse", "--verify", f"{revision}^{{commit}}"])
    if not GIT_HASH_RE.fullmatch(value):
        raise EvidenceIdentityError(f"{label} did not resolve to a canonical Git object ID.")
    return value


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
    if not GIT_HASH_RE.fullmatch(output):
        raise EvidenceIdentityError(f"Git did not return a blob identity for {relative_path}")
    return output


def _index_blob_oid(repo_root: Path, relative_path: str) -> str | None:
    output = _run_git(repo_root, ["ls-files", "--stage", "-z", "--", relative_path])
    if not output:
        return None
    first = output.split(b"\x00", 1)[0].decode("utf-8", errors="surrogateescape")
    metadata, separator, path_text = first.partition("\t")
    if separator != "\t" or normalize_repo_path(path_text) != relative_path:
        raise EvidenceIdentityError(f"Malformed index identity for {relative_path}")
    fields = metadata.split()
    if len(fields) < 3 or not GIT_HASH_RE.fullmatch(fields[1]):
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


def _required_text(record: Mapping[str, Any], field: str, label: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise EvidenceIdentityError(f"artifact {label}: {field} must be a non-empty string")
    return value.strip()


def _required_bool(record: Mapping[str, Any], field: str, label: str) -> bool:
    value = record.get(field)
    if type(value) is not bool:
        raise EvidenceIdentityError(f"artifact {label}: {field} must be a JSON boolean")
    return value


def _artifact_state(repo_root: Path, relative_path: str) -> str:
    absolute = repo_root / Path(relative_path)
    exists = absolute.exists() or absolute.is_symlink()
    tracked_result = _run_git_process(
        repo_root,
        ["ls-files", "--error-unmatch", "--", relative_path],
        check=False,
    )
    if tracked_result.returncode not in {0, 1}:
        stderr = tracked_result.stderr.decode("utf-8", errors="replace").strip()
        raise EvidenceIdentityError(
            f"Could not determine tracked state for {relative_path}"
            + (f": {stderr}" if stderr else "")
        )
    if tracked_result.returncode == 0:
        return "PRESENT_TRACKED" if exists else "ABSENT"
    ignored_result = _run_git_process(
        repo_root,
        ["check-ignore", "-q", "--", relative_path],
        check=False,
    )
    if ignored_result.returncode not in {0, 1}:
        stderr = ignored_result.stderr.decode("utf-8", errors="replace").strip()
        raise EvidenceIdentityError(
            f"Could not determine ignore state for {relative_path}"
            + (f": {stderr}" if stderr else "")
        )
    if not exists:
        return "ABSENT"
    return "PRESENT_IGNORED" if ignored_result.returncode == 0 else "PRESENT_UNTRACKED"


def _artifact_content_hash(path: Path) -> str:
    kind = _file_kind(path)
    if kind == "symlink":
        payload = os.readlink(path).encode("utf-8", errors="surrogateescape")
    else:
        payload = path.read_bytes()
    return _sha256_bytes(payload)


def normalize_artifact_records(
    records: Iterable[Mapping[str, Any]] | None,
    *,
    repo_root: Path | None = None,
    approved_base_sha: str | None = None,
    current_commit_sha: str | None = None,
    verify_current: bool = False,
) -> list[dict[str, Any]]:
    if records is None:
        return []

    normalized: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            raise EvidenceIdentityError("Artifact lifecycle records must be JSON objects.")
        copied = dict(record)
        label = str(copied.get("artifact_id") or copied.get("path") or index)

        for field in (
            "artifact_id",
            "collaboration_session_id",
            "producer_role",
            "producing_command",
            "artifact_type",
        ):
            copied[field] = _required_text(copied, field, label)

        revision = copied.get("contract_packet_revision")
        if not isinstance(revision, (str, int)) or isinstance(revision, bool) or str(revision).strip() == "":
            raise EvidenceIdentityError(
                f"artifact {label}: contract_packet_revision must be a non-empty string or integer"
            )

        copied["path"] = normalize_repo_path(_required_text(copied, "path", label))
        for state_field in ("state_before", "state_after"):
            state = copied.get(state_field)
            if state not in ARTIFACT_STATES:
                raise EvidenceIdentityError(f"artifact {label}: invalid {state_field}")
        for bool_field in (
            "inspection_required",
            "inspection_completed",
            "retention_required",
            "cleanup_performed",
        ):
            copied[bool_field] = _required_bool(copied, bool_field, label)

        inspection_owner = copied.get("inspection_owner")
        if copied["inspection_required"] or copied["inspection_completed"]:
            if not isinstance(inspection_owner, str) or not inspection_owner.strip():
                raise EvidenceIdentityError(
                    f"artifact {label}: inspection_owner is required for inspected artifacts"
                )
        elif inspection_owner is not None and not isinstance(inspection_owner, str):
            raise EvidenceIdentityError(f"artifact {label}: inspection_owner must be a string or null")

        if copied["inspection_required"] and not copied["inspection_completed"]:
            raise EvidenceIdentityError(
                f"artifact {label}: required generated-artifact inspection is incomplete"
            )

        cleanup_authority = copied.get("cleanup_authority")
        cleanup_condition = copied.get("cleanup_condition")
        cleanup_evidence = copied.get("cleanup_evidence")
        if copied["cleanup_performed"]:
            for field, value in (
                ("cleanup_authority", cleanup_authority),
                ("cleanup_condition", cleanup_condition),
                ("cleanup_evidence", cleanup_evidence),
            ):
                if not isinstance(value, str) or not value.strip():
                    raise EvidenceIdentityError(
                        f"artifact {label}: {field} is required when cleanup_performed is true"
                    )
        if copied["retention_required"] and copied["cleanup_performed"]:
            raise EvidenceIdentityError(f"artifact {label}: retained evidence artifact was cleaned")
        if copied["state_before"] != "ABSENT" and copied["cleanup_performed"] and not cleanup_authority:
            raise EvidenceIdentityError(
                f"artifact {label}: pre-existing artifact cleanup lacks authority"
            )

        binding = copied.get("freshness_binding")
        if not isinstance(binding, Mapping):
            raise EvidenceIdentityError(f"artifact {label}: freshness_binding must be an object")
        binding_copy = dict(binding)
        for field in ("baseline_sha", "current_commit_sha", "contract_hash"):
            value = binding_copy.get(field)
            if not isinstance(value, str) or not value.strip():
                raise EvidenceIdentityError(
                    f"artifact {label}: freshness_binding.{field} must be non-empty"
                )
        copied["freshness_binding"] = binding_copy

        content_hash = copied.get("content_hash")
        if copied["state_after"] == "ABSENT":
            if content_hash not in {None, ""}:
                raise EvidenceIdentityError(
                    f"artifact {label}: absent artifact must not carry content_hash"
                )
            copied["content_hash"] = None
        else:
            if not isinstance(content_hash, str) or not SHA256_RE.fullmatch(content_hash):
                raise EvidenceIdentityError(
                    f"artifact {label}: present artifact requires a lowercase SHA-256 content_hash"
                )

        if verify_current:
            if repo_root is None or approved_base_sha is None or current_commit_sha is None:
                raise EvidenceIdentityError("Artifact verification requires repository freshness context.")
            actual_state = _artifact_state(repo_root, copied["path"])
            if actual_state != copied["state_after"]:
                raise EvidenceIdentityError(
                    f"artifact {label}: state_after is {copied['state_after']}, current state is {actual_state}"
                )
            if binding_copy["baseline_sha"] != approved_base_sha:
                raise EvidenceIdentityError(f"artifact {label}: baseline freshness binding differs")
            if binding_copy["current_commit_sha"] != current_commit_sha:
                raise EvidenceIdentityError(f"artifact {label}: commit freshness binding differs")
            if copied["state_after"] != "ABSENT":
                actual_hash = _artifact_content_hash(repo_root / Path(copied["path"]))
                if copied["content_hash"] != actual_hash:
                    raise EvidenceIdentityError(f"artifact {label}: content_hash differs from current artifact")

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
    artifacts = normalize_artifact_records(
        artifact_lifecycle_records,
        repo_root=root,
        approved_base_sha=approved_base,
        current_commit_sha=current_commit,
        verify_current=True,
    )

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
    artifact_lifecycle_records: Iterable[Mapping[str, Any]] | None = None,
) -> list[str]:
    evidence = json.loads(Path(evidence_path).read_text(encoding="utf-8"))
    if not isinstance(evidence, Mapping):
        return ["evidence document must be a JSON object"]

    evidence_artifacts = evidence.get("artifact_lifecycle_records", [])
    if evidence_artifacts and artifact_lifecycle_records is None:
        return [
            "independent artifact lifecycle records are required; "
            "artifact evidence cannot validate itself"
        ]

    authoritative_artifacts = artifact_lifecycle_records or []
    current = collect_evidence_identity(
        repo_root,
        approved_base_sha,
        authoritative_artifacts,
    )
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
    validate.add_argument("--artifact-records", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        artifacts = _load_artifacts(args.artifact_records)
        if args.command == "collect":
            identity = collect_evidence_identity(args.repo_root, args.approved_base_sha, artifacts)
            _write_json(identity, args.output)
            return 0

        errors = validate_evidence_file(
            args.repo_root,
            args.approved_base_sha,
            args.evidence_json,
            artifacts if args.artifact_records else None,
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
