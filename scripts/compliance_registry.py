from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlparse

CANONICAL_REPOSITORY = "Baelfyre/Orchestra-Compliance-Registry"
LATEST_RELEASE_API = f"https://api.github.com/repos/{CANONICAL_REPOSITORY}/releases/latest"
DEFAULT_ASSET_NAME = "orchestra-compliance-registry.zip"
SUPPORTED_RELEASE_SCHEMA = 1
ACTIVE_SCHEMA = 1
VERSION_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,127}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SOURCE_STATES = {
    "VERIFIED_CURRENT",
    "CURRENT_WITH_PENDING_CHANGE",
    "NOT_EFFECTIVE_YET",
    "SUPERSEDED",
    "REPEALED",
    "SOURCE_UNAVAILABLE",
    "SOURCE_MOVED",
    "APPLICABILITY_UNRESOLVED",
    "HUMAN_INTERPRETATION_REQUIRED",
    "REVIEW_OVERDUE",
}
STALE_SOURCE_STATES = {"SOURCE_UNAVAILABLE", "SOURCE_MOVED", "REVIEW_OVERDUE"}


class RegistryError(RuntimeError):
    pass


@dataclass(frozen=True)
class VerifiedBundle:
    root: Path
    manifest: dict[str, Any]
    manifest_sha256: str


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _cache_root(value: str | None = None) -> Path:
    if value:
        return Path(value).expanduser().resolve()
    env = os.environ.get("ORCHESTRA_COMPLIANCE_HOME")
    if env:
        return Path(env).expanduser().resolve()
    return (Path.home() / ".orchestra" / "compliance").resolve()


def _json_load(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise RegistryError(f"missing file: {path}") from None
    except json.JSONDecodeError as exc:
        raise RegistryError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise RegistryError(f"expected JSON object in {path}")
    return data


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_version_token(value: Any) -> str:
    if not isinstance(value, str) or VERSION_TOKEN_RE.fullmatch(value) is None:
        raise RegistryError("registry_version must be a safe version token")
    return value


def _validate_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        raise RegistryError(f"invalid SHA-256 for {label}")
    return value


def _safe_child(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative:
        raise RegistryError("manifest file path must be a non-empty string")
    pure = PurePosixPath(relative)
    if pure.is_absolute() or ".." in pure.parts:
        raise RegistryError(f"unsafe manifest path: {relative}")
    candidate = (root / Path(*pure.parts)).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise RegistryError(f"manifest path escapes bundle root: {relative}") from exc
    return candidate


def _validate_release_manifest(manifest: dict[str, Any], *, expected_tag: str | None = None) -> None:
    if manifest.get("schema_version") != SUPPORTED_RELEASE_SCHEMA:
        raise RegistryError("unsupported release manifest schema_version")
    if manifest.get("canonical_repository") != CANONICAL_REPOSITORY:
        raise RegistryError("release canonical_repository mismatch")
    if manifest.get("status") != "TRUSTED_RELEASE":
        raise RegistryError("registry bundle is not a TRUSTED_RELEASE")
    _validate_version_token(manifest.get("registry_version"))
    sequence = manifest.get("release_sequence")
    if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence <= 0:
        raise RegistryError("trusted release requires positive release_sequence")
    release_tag = manifest.get("release_tag")
    if not isinstance(release_tag, str) or not release_tag:
        raise RegistryError("release_tag is required")
    if expected_tag is not None and release_tag != expected_tag:
        raise RegistryError("GitHub release tag does not match bundle release_tag")
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise RegistryError("release manifest files map must be non-empty")
    for relative, expected in files.items():
        if not isinstance(relative, str) or not relative or relative == "release-manifest.json":
            raise RegistryError(f"invalid release manifest file path: {relative!r}")
        pure = PurePosixPath(relative)
        if pure.is_absolute() or ".." in pure.parts:
            raise RegistryError(f"unsafe manifest path: {relative}")
        _validate_sha256(expected, relative)


def verify_bundle(root: Path, *, expected_tag: str | None = None) -> VerifiedBundle:
    root = root.resolve()
    manifest_path = root / "release-manifest.json"
    manifest = _json_load(manifest_path)
    _validate_release_manifest(manifest, expected_tag=expected_tag)
    expected_files = set(manifest["files"])
    for relative, expected in manifest["files"].items():
        path = _safe_child(root, relative)
        if not path.is_file():
            raise RegistryError(f"release bundle missing hashed file: {relative}")
        actual = _sha256(path)
        if actual != expected:
            raise RegistryError(f"release bundle hash mismatch: {relative}")
    actual_files = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.resolve() != manifest_path.resolve()
    }
    if actual_files != expected_files:
        unlisted = sorted(actual_files - expected_files)
        missing = sorted(expected_files - actual_files)
        details: list[str] = []
        if unlisted:
            details.append(f"unlisted files={unlisted}")
        if missing:
            details.append(f"missing files={missing}")
        raise RegistryError("release bundle file inventory mismatch: " + "; ".join(details))
    return VerifiedBundle(root=root, manifest=manifest, manifest_sha256=_sha256(manifest_path))


def _safe_extract(zip_path: Path, destination: Path) -> None:
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.infolist():
            name = member.filename
            pure = PurePosixPath(name)
            if pure.is_absolute() or ".." in pure.parts:
                raise RegistryError(f"unsafe ZIP path: {name}")
            unix_mode = (member.external_attr >> 16) & 0o170000
            if unix_mode == 0o120000:
                raise RegistryError(f"symbolic links are not allowed in registry bundles: {name}")
            _safe_child(destination, name)
        archive.extractall(destination)


def _active_record(cache_root: Path) -> dict[str, Any] | None:
    path = cache_root / "active.json"
    if not path.is_file():
        return None
    data = _json_load(path)
    if data.get("schema_version") != ACTIVE_SCHEMA:
        raise RegistryError("unsupported active registry state schema")
    if data.get("canonical_repository") != CANONICAL_REPOSITORY:
        raise RegistryError("active registry canonical_repository mismatch")
    _validate_version_token(data.get("registry_version"))
    sequence = data.get("release_sequence")
    if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence <= 0:
        raise RegistryError("active registry release_sequence is invalid")
    _validate_sha256(data.get("manifest_sha256"), "active registry manifest")
    release_tag = data.get("release_tag")
    if not isinstance(release_tag, str) or not release_tag:
        raise RegistryError("active registry release_tag is missing")
    relative = data.get("path")
    if not isinstance(relative, str):
        raise RegistryError("active registry state missing path")
    _safe_child(cache_root, relative)
    return data


def _active_bundle(cache_root: Path) -> VerifiedBundle:
    active = _active_record(cache_root)
    if active is None:
        raise RegistryError("NO_REGISTRY")
    bundle_root = _safe_child(cache_root, active["path"])
    verified = verify_bundle(bundle_root, expected_tag=active["release_tag"])
    if verified.manifest_sha256 != active.get("manifest_sha256"):
        raise RegistryError("active registry manifest identity mismatch")
    if verified.manifest.get("registry_version") != active.get("registry_version"):
        raise RegistryError("active registry version mismatch")
    if verified.manifest.get("release_sequence") != active.get("release_sequence"):
        raise RegistryError("active registry release_sequence mismatch")
    return verified


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp, path)


def install_bundle(bundle_zip: Path, cache_root: Path, *, expected_tag: str | None = None, allow_rollback: bool = False) -> dict[str, Any]:
    cache_root.mkdir(parents=True, exist_ok=True)
    candidate_parent = cache_root / "candidate"
    candidate_parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="registry-", dir=candidate_parent) as temp_dir:
        candidate = Path(temp_dir)
        _safe_extract(bundle_zip, candidate)
        verified = verify_bundle(candidate, expected_tag=expected_tag)
        version = _validate_version_token(verified.manifest["registry_version"])
        sequence = verified.manifest["release_sequence"]
        release_tag = verified.manifest["release_tag"]
        active = _active_record(cache_root)
        if active is not None:
            current_sequence = active["release_sequence"]
            if sequence < current_sequence and not allow_rollback:
                raise RegistryError(f"rollback rejected: candidate sequence {sequence} < active sequence {current_sequence}")
            if sequence == current_sequence and active["manifest_sha256"] != verified.manifest_sha256:
                raise RegistryError(f"release sequence collision at {sequence}")
        install_root = _safe_child(cache_root, f"registry/{version}")
        if install_root.exists():
            existing = verify_bundle(install_root, expected_tag=release_tag)
            if existing.manifest_sha256 != verified.manifest_sha256:
                raise RegistryError(f"version collision for {version}")
        else:
            install_root.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(candidate, install_root)
            verify_bundle(install_root, expected_tag=release_tag)
        active_payload = {
            "schema_version": ACTIVE_SCHEMA,
            "canonical_repository": CANONICAL_REPOSITORY,
            "registry_version": version,
            "release_sequence": sequence,
            "release_tag": release_tag,
            "manifest_sha256": verified.manifest_sha256,
            "path": str(Path("registry") / version).replace("\\", "/"),
            "installed_at": _now_iso(),
        }
        _write_json_atomic(cache_root / "active.json", active_payload)
        return active_payload


def _fetch_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "Orchestra-Compliance-Registry-Client"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RegistryError(f"network request failed: {exc}") from exc
    if not isinstance(data, dict):
        raise RegistryError("unexpected GitHub API response")
    return data


def _latest_release() -> dict[str, Any]:
    release = _fetch_json(LATEST_RELEASE_API)
    if release.get("draft"):
        raise RegistryError("latest registry release is a draft")
    if release.get("prerelease"):
        raise RegistryError("latest registry release is a prerelease")
    if not isinstance(release.get("tag_name"), str):
        raise RegistryError("latest registry release has no tag_name")
    return release


def sync(cache_root: Path, *, asset_name: str = DEFAULT_ASSET_NAME) -> dict[str, Any]:
    release = _latest_release()
    assets = release.get("assets")
    if not isinstance(assets, list):
        raise RegistryError("latest registry release has no assets")
    selected = next((item for item in assets if isinstance(item, dict) and item.get("name") == asset_name), None)
    if selected is None:
        raise RegistryError(f"latest registry release is missing required asset: {asset_name}")
    url = selected.get("browser_download_url")
    if not isinstance(url, str):
        raise RegistryError("registry release asset has no download URL")
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc not in {"github.com", "objects.githubusercontent.com"}:
        raise RegistryError("registry release asset URL is outside the trusted GitHub distribution boundary")
    cache_root.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix="orchestra-registry-", suffix=".zip", delete=False, dir=cache_root) as temp:
        temp_path = Path(temp.name)
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "Orchestra-Compliance-Registry-Client"})
        try:
            with urllib.request.urlopen(request, timeout=60) as response, temp_path.open("wb") as out:
                shutil.copyfileobj(response, out)
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RegistryError(f"registry asset download failed: {exc}") from exc
        return install_bundle(temp_path, cache_root, expected_tag=release["tag_name"])
    finally:
        temp_path.unlink(missing_ok=True)


def freshness_summary(bundle: VerifiedBundle) -> dict[str, Any]:
    due_path = bundle.root / "registry" / "review-due.json"
    status_path = bundle.root / "registry" / "source-status.json"
    due_entries = _json_load(due_path).get("entries", []) if due_path.is_file() else []
    status_entries = _json_load(status_path).get("entries", []) if status_path.is_file() else []
    if not isinstance(due_entries, list) or not isinstance(status_entries, list):
        raise RegistryError("registry freshness stores must contain entry lists")
    today = date.today()
    overdue: list[str] = []
    for entry in due_entries:
        if not isinstance(entry, dict):
            raise RegistryError("review-due entry must be an object")
        value = entry.get("next_review_due")
        source_id = entry.get("source_id")
        if not isinstance(value, str) or not isinstance(source_id, str) or not source_id:
            raise RegistryError("review-due entry is malformed")
        try:
            if date.fromisoformat(value) < today:
                overdue.append(source_id)
        except ValueError as exc:
            raise RegistryError(f"invalid next_review_due for {source_id}: {value}") from exc
    source_states: dict[str, str] = {}
    attention: list[str] = []
    stale: list[str] = []
    for entry in status_entries:
        if not isinstance(entry, dict):
            raise RegistryError("source-status entry must be an object")
        source_id = entry.get("source_id")
        source_state = entry.get("status")
        if not isinstance(source_id, str) or not source_id or source_state not in SOURCE_STATES:
            raise RegistryError("source-status entry is malformed")
        source_states[source_id] = source_state
        if source_state != "VERIFIED_CURRENT":
            attention.append(source_id)
        if source_state in STALE_SOURCE_STATES:
            stale.append(source_id)
    stale_ids = sorted(set(overdue) | set(stale))
    attention_ids = sorted(set(attention) - set(stale_ids))
    if stale_ids:
        state = "STALE"
    elif attention_ids:
        state = "REVIEW_REQUIRED"
    else:
        state = "CURRENT" if status_entries else "NO_TRACKED_SOURCES"
    return {
        "state": state,
        "overdue_source_ids": sorted(set(overdue)),
        "stale_source_ids": stale_ids,
        "attention_source_ids": attention_ids,
        "source_states": source_states,
        "tracked_source_count": len(status_entries),
    }


def status(cache_root: Path) -> dict[str, Any]:
    try:
        active = _active_record(cache_root)
        if active is None:
            return {"registry_status": "NO_REGISTRY", "canonical_repository": CANONICAL_REPOSITORY}
        verified = _active_bundle(cache_root)
        fresh = freshness_summary(verified)
        return {"registry_status": "VERIFIED", "canonical_repository": CANONICAL_REPOSITORY, "registry_version": verified.manifest["registry_version"], "release_sequence": verified.manifest["release_sequence"], "release_tag": verified.manifest["release_tag"], "manifest_sha256": verified.manifest_sha256, "freshness": fresh}
    except RegistryError as exc:
        return {"registry_status": "INTEGRITY_FAILED", "canonical_repository": CANONICAL_REPOSITORY, "error": str(exc)}


def query(cache_root: Path, *, jurisdiction: str | None = None, provider: str | None = None, domain: str | None = None, source_id: str | None = None, obligation_id: str | None = None) -> dict[str, Any]:
    bundle = _active_bundle(cache_root)
    sources = _json_load(bundle.root / "registry" / "sources.json").get("sources", [])
    obligations = _json_load(bundle.root / "registry" / "obligations.json").get("obligations", [])
    if not isinstance(sources, list) or not isinstance(obligations, list):
        raise RegistryError("registry source or obligation store is malformed")

    def source_match(item: Any) -> bool:
        return isinstance(item, dict) and (not source_id or item.get("source_id") == source_id) and (not jurisdiction or jurisdiction in item.get("jurisdiction_ids", [])) and (not domain or domain in item.get("domains", []))

    def obligation_match(item: Any) -> bool:
        return isinstance(item, dict) and (not obligation_id or item.get("obligation_id") == obligation_id) and (not jurisdiction or jurisdiction in item.get("jurisdiction_ids", [])) and (not provider or provider in item.get("provider_ids", [])) and (not domain or domain in item.get("domains", []))

    return {"registry_version": bundle.manifest["registry_version"], "release_sequence": bundle.manifest["release_sequence"], "sources": [item for item in sources if source_match(item)], "obligations": [item for item in obligations if obligation_match(item)]}


def pin(cache_root: Path, project_root: Path, jurisdictions: list[str], providers: list[str]) -> dict[str, Any]:
    bundle = _active_bundle(cache_root)
    jurisdiction_store = _json_load(bundle.root / "registry" / "jurisdictions.json").get("jurisdictions", [])
    provider_store = _json_load(bundle.root / "registry" / "providers.json").get("providers", [])
    if not isinstance(jurisdiction_store, list) or not isinstance(provider_store, list):
        raise RegistryError("registry taxonomy stores are malformed")
    known_jurisdictions = {item.get("jurisdiction_id") for item in jurisdiction_store if isinstance(item, dict)}
    known_providers = {item.get("provider_id") for item in provider_store if isinstance(item, dict)}
    unknown_jurisdictions = sorted(set(jurisdictions) - known_jurisdictions)
    unknown_providers = sorted(set(providers) - known_providers)
    if unknown_jurisdictions:
        raise RegistryError(f"unknown jurisdiction IDs: {unknown_jurisdictions}")
    if unknown_providers:
        raise RegistryError(f"unknown provider IDs: {unknown_providers}")
    lock = {
        "schema_version": 1,
        "canonical_repository": CANONICAL_REPOSITORY,
        "registry_version": bundle.manifest["registry_version"],
        "release_sequence": bundle.manifest["release_sequence"],
        "release_tag": bundle.manifest["release_tag"],
        "manifest_sha256": bundle.manifest_sha256,
        "jurisdictions": sorted(set(jurisdictions)),
        "providers": sorted(set(providers)),
    }
    path = project_root.resolve() / ".orchestra" / "compliance.lock.json"
    _write_json_atomic(path, lock)
    return {"lockfile": str(path), **lock}


def update_check(cache_root: Path) -> dict[str, Any]:
    release = _latest_release()
    active = _active_record(cache_root)
    active_tag = active.get("release_tag") if active else None
    return {
        "canonical_repository": CANONICAL_REPOSITORY,
        "latest_tag": release["tag_name"],
        "active_tag": active_tag,
        "active_version": active.get("registry_version") if active else None,
        "update_available": active is None or active_tag != release["tag_name"],
    }


def _emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verified local client for the Orchestra Compliance Registry.")
    parser.add_argument("--cache-root", help="Override compliance cache root. Defaults to ORCHESTRA_COMPLIANCE_HOME or ~/.orchestra/compliance.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    sub.add_parser("verify")
    sync_parser = sub.add_parser("sync")
    sync_parser.add_argument("--asset-name", default=DEFAULT_ASSET_NAME)
    install_parser = sub.add_parser("install")
    install_parser.add_argument("bundle")
    install_parser.add_argument("--expected-tag")
    install_parser.add_argument("--allow-rollback", action="store_true")
    query_parser = sub.add_parser("query")
    query_parser.add_argument("--jurisdiction")
    query_parser.add_argument("--provider")
    query_parser.add_argument("--domain")
    query_parser.add_argument("--source-id")
    query_parser.add_argument("--obligation-id")
    pin_parser = sub.add_parser("pin")
    pin_parser.add_argument("--project-root", default=".")
    pin_parser.add_argument("--jurisdiction", action="append", default=[])
    pin_parser.add_argument("--provider", action="append", default=[])
    sub.add_parser("update-check")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    cache_root = _cache_root(args.cache_root)
    try:
        if args.command == "status":
            _emit(status(cache_root))
        elif args.command == "verify":
            bundle = _active_bundle(cache_root)
            _emit({"registry_status": "VERIFIED", "registry_version": bundle.manifest["registry_version"], "release_sequence": bundle.manifest["release_sequence"], "release_tag": bundle.manifest["release_tag"], "manifest_sha256": bundle.manifest_sha256, "freshness": freshness_summary(bundle)})
        elif args.command == "sync":
            _emit(sync(cache_root, asset_name=args.asset_name))
        elif args.command == "install":
            _emit(install_bundle(Path(args.bundle).resolve(), cache_root, expected_tag=args.expected_tag, allow_rollback=args.allow_rollback))
        elif args.command == "query":
            _emit(query(cache_root, jurisdiction=args.jurisdiction, provider=args.provider, domain=args.domain, source_id=args.source_id, obligation_id=args.obligation_id))
        elif args.command == "pin":
            _emit(pin(cache_root, Path(args.project_root), args.jurisdiction, args.provider))
        elif args.command == "update-check":
            _emit(update_check(cache_root))
        else:
            raise RegistryError(f"unsupported command: {args.command}")
        return 0
    except RegistryError as exc:
        _emit({"registry_status": "ERROR", "error": str(exc)})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
