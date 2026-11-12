"""Separate frozen UIX-9 V1 records from candidate-only static V2 evidence."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from functools import lru_cache
import hashlib
import json
from pathlib import Path, PurePosixPath
import platform
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from typing import Any

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
FROZEN_HISTORICAL_V1 = "FROZEN_HISTORICAL_V1"
CANDIDATE_STATIC_V2 = "CANDIDATE_STATIC_V2"
FROZEN_MANIFEST_SHA = "9f49a29827513199ae16ea29b8e75bfbb90ca38d"
FROZEN_SOURCE_SHA = "bf6f14316fa8814eeac91440c4a7d70be0d04b9e"
FROZEN_GUIDANCE_DIGEST = "f989ac579875fbcd349f812fa6e241ba5c8505f9f940abcb5e0e30006f1606ab"
MANIFEST = "machine/ui/uix9-live-guidance-manifest.v1.json"
IDENTITY = "machine/ui/uix9b-live-proof-v2-identity.json"
EVALUATOR = "scripts/uix9_live_metric_evaluator_v2.py"
VALIDATOR = "scripts/uix9_live_proof_runner.py"
MODULE = "scripts/uix9_static_evidence_v2.py"
SCHEMA = "machine/schemas/uix9-candidate-static-evidence.v2.schema.json"
ALGORITHM = "sha256(sorted(path<TAB>sha256<TAB>role<TAB>revision_identity> joined by LF).v1"
VERSION = "uix9-candidate-static-evidence-v2.0.0"
EVALUATOR_VERSION = "uix9b-live-metric-evaluator-v2.0.0"
SHA40 = re.compile(r"^[0-9a-f]{40}$")


class EvidenceError(ValueError):
    pass


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _text(data: bytes, label: str) -> str:
    try:
        return data.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    except UnicodeError as exc:
        raise EvidenceError(f"invalid UTF-8: {label}") from exc


def _parts(relative: str) -> tuple[str, ...]:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise EvidenceError(f"invalid relative path: {relative!r}")
    path = PurePosixPath(relative)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise EvidenceError(f"path traversal or absolute path: {relative!r}")
    return path.parts


def _repo_file(root: Path, relative: str) -> Path:
    root = root.resolve(strict=True)
    candidate = root
    for part in _parts(relative):
        candidate = candidate / part
        if candidate.is_symlink():
            raise EvidenceError(f"symlink input rejected: {relative}")
    try:
        path = candidate.resolve(strict=True)
    except OSError as exc:
        raise EvidenceError(f"missing evidence file: {relative}") from exc
    if not path.is_relative_to(root) or not path.is_file():
        raise EvidenceError(f"invalid evidence file: {relative}")
    return path


def _git(root: Path, *args: str) -> bytes:
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, check=False)
    if result.returncode:
        raise EvidenceError(result.stderr.decode("utf-8", "replace").strip() or "git evidence read failed")
    return result.stdout


@lru_cache(maxsize=256)
def _blob(root: Path, revision: str, relative: str) -> bytes:
    if revision not in {FROZEN_MANIFEST_SHA, FROZEN_SOURCE_SHA} or not SHA40.fullmatch(revision):
        raise EvidenceError("unrecognized frozen revision")
    path = "/".join(_parts(relative))
    tree = _git(root, "ls-tree", revision, "--", path).strip().split(b"\t", 1)
    if len(tree) != 2 or tree[1].decode("utf-8") != path:
        raise EvidenceError(f"missing frozen Git path: {path}")
    mode, kind, _ = tree[0].decode("ascii").split()
    if kind != "blob" or mode not in {"100644", "100755"}:
        raise EvidenceError(f"non-regular frozen Git path: {path}")
    return _git(root, "show", f"{revision}:{path}")


def _git_json(root: Path, revision: str, relative: str) -> tuple[dict[str, Any], bytes]:
    raw = _blob(root, revision, relative)
    try:
        value = json.loads(_text(raw, relative))
    except (json.JSONDecodeError, EvidenceError) as exc:
        raise EvidenceError(f"malformed frozen JSON: {relative}") from exc
    if not isinstance(value, dict):
        raise EvidenceError(f"frozen JSON must be an object: {relative}")
    return value, raw


def _records_digest(records: list[dict[str, str]]) -> str:
    payload = "\n".join(
        f"{item['path']}\t{item['sha256']}\t{item['role']}\t{item['revision_identity']}"
        for item in sorted(records, key=lambda row: row["path"])
    )
    return _sha(payload.encode("utf-8"))

def _frozen_context(root: Path) -> dict[str, Any]:
    manifest, manifest_raw = _git_json(root, FROZEN_MANIFEST_SHA, MANIFEST)
    identity, _ = _git_json(root, FROZEN_MANIFEST_SHA, IDENTITY)
    if manifest.get("canonical_sha") != FROZEN_SOURCE_SHA or manifest.get("guidance_digest") != FROZEN_GUIDANCE_DIGEST:
        raise EvidenceError("frozen V1 manifest identity changed")
    if identity.get("canonical_sha") != FROZEN_SOURCE_SHA or identity.get("uix_guidance_digest") != FROZEN_GUIDANCE_DIGEST:
        raise EvidenceError("frozen V1 proof identity changed")
    materials = []
    for item in manifest.get("materials", []):
        if not isinstance(item, dict):
            raise EvidenceError("malformed frozen material")
        path = item.get("path")
        raw = _blob(root, FROZEN_SOURCE_SHA, path)
        content = _text(raw, path)
        digest = _sha(content.encode("utf-8"))
        if digest != item.get("canonical_blob_digest"):
            raise EvidenceError(f"frozen material digest mismatch: {path}")
        materials.append({"path": path, "role": item.get("role"), "revision_identity": item.get("revision_identity"), "sha256": digest, "content": content})
    actual = _records_digest(materials)
    if not materials or actual != FROZEN_GUIDANCE_DIGEST:
        raise EvidenceError("frozen V1 guidance digest mismatch")
    return {"context": FROZEN_HISTORICAL_V1, "manifest_snapshot_sha": FROZEN_MANIFEST_SHA, "manifest_sha256": _sha(manifest_raw), "source_sha": FROZEN_SOURCE_SHA, "guidance_digest": actual, "materials": materials}


def _candidate_context(root: Path, manifest_path: str = MANIFEST) -> dict[str, Any]:
    path = _repo_file(root, manifest_path)
    raw = path.read_bytes()
    try:
        manifest = json.loads(_text(raw, manifest_path))
    except (json.JSONDecodeError, EvidenceError) as exc:
        raise EvidenceError("malformed candidate guidance manifest") from exc
    if not isinstance(manifest, dict) or not isinstance(manifest.get("materials"), list):
        raise EvidenceError("malformed candidate guidance manifest")
    materials, seen = [], set()
    for item in manifest["materials"]:
        if not isinstance(item, dict):
            raise EvidenceError("malformed candidate guidance material")
        relative = item.get("path")
        if relative in seen:
            raise EvidenceError(f"duplicate candidate material: {relative}")
        seen.add(relative)
        material_path = _repo_file(root, relative)
        content = _text(material_path.read_bytes(), relative)
        digest = _sha(content.encode("utf-8"))
        if digest != item.get("canonical_blob_digest"):
            raise EvidenceError(f"candidate material digest mismatch: {relative}")
        role, revision = item.get("role"), item.get("revision_identity")
        if not isinstance(role, str) or not role or not isinstance(revision, str) or not revision:
            raise EvidenceError(f"incomplete candidate material identity: {relative}")
        materials.append({"path": relative, "role": role, "revision_identity": revision, "sha256": digest, "content": content})
    actual = _records_digest(materials)
    if not materials or actual != manifest.get("guidance_digest"):
        raise EvidenceError("candidate guidance manifest digest mismatch")
    return {"context": CANDIDATE_STATIC_V2, "manifest_path": manifest_path, "manifest_sha256": _sha(raw), "source_sha": manifest.get("canonical_sha"), "guidance_digest": actual, "algorithm": ALGORITHM, "materials": materials}


def guidance_context(root: Path, context: str) -> dict[str, Any]:
    if context == FROZEN_HISTORICAL_V1:
        return _frozen_context(root)
    if context == CANDIDATE_STATIC_V2:
        return _candidate_context(root)
    raise EvidenceError(f"unsupported guidance context: {context}")


def frozen_source_digest(root: Path, role: str) -> str:
    context = _frozen_context(root)
    identity, _ = _git_json(root, FROZEN_MANIFEST_SHA, IDENTITY)
    if role == "evaluator":
        path, expected = identity.get("evaluator_source"), identity.get("evaluator_digest")
        if path != EVALUATOR:
            raise EvidenceError("frozen evaluator path changed")
    elif role == "validator":
        path, expected = VALIDATOR, identity.get("validator_digest")
    else:
        raise EvidenceError(f"unsupported frozen source role: {role}")
    actual = _sha(_text(_blob(root, FROZEN_MANIFEST_SHA, path), path).encode("utf-8"))
    if actual != expected:
        raise EvidenceError(f"frozen {role} source digest mismatch")
    return actual


def candidate_worktree_binding(root: Path) -> dict[str, Any]:
    root = root.resolve(strict=True)
    staged = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=root, check=False)
    if staged.returncode != 0:
        raise EvidenceError("candidate evidence requires an unstaged worktree")
    base = _git(root, "rev-parse", "HEAD").decode("ascii").strip()
    tree = _git(root, "rev-parse", "HEAD^{tree}").decode("ascii").strip()
    if not SHA40.fullmatch(base) or not SHA40.fullmatch(tree):
        raise EvidenceError("invalid candidate Git identity")
    rows = _git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all").split(b"\0")
    files = []
    for row in rows:
        if not row:
            continue
        status, relative = row[:2].decode("ascii"), row[3:].decode("utf-8")
        kind = "untracked" if status == "??" else "modified" if status == " M" else None
        if kind is None:
            raise EvidenceError(f"staged, deleted, renamed or conflicted path: {status} {relative}")
        path = _repo_file(root, relative)
        files.append({"path": relative, "status": kind, "sha256": _sha(path.read_bytes())})
    files.sort(key=lambda item: item["path"])
    if not files:
        raise EvidenceError("candidate has no changed files")
    binding = {"base_sha": base, "base_tree_sha": tree, "changed_files": files}
    fingerprint = _sha(json.dumps(binding, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    return {**binding, "content_fingerprint": fingerprint}


def _has_symlink_component(path: Path) -> bool:
    absolute = path.absolute()
    return any(part.is_symlink() for part in (absolute, *absolute.parents))


def _external_file(root: Path, path_text: str, digest: str) -> Path:
    path = Path(path_text)
    if not path.is_absolute() or _has_symlink_component(path):
        raise EvidenceError("test evidence must be absolute and not symlinked")
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise EvidenceError(f"missing test evidence: {path}") from exc
    if not resolved.is_file() or resolved.is_relative_to(root.resolve()) or _sha(resolved.read_bytes()) != digest:
        raise EvidenceError(f"external test evidence mismatch: {path}")
    return resolved


def _observed_run(root: Path, item: dict[str, Any]) -> dict[str, Any]:
    suite, command = item.get("suite_id"), item.get("command")
    log, junit = Path(item.get("log_path", "")), Path(item.get("junit_path", ""))
    if not isinstance(suite, str) or not suite or not isinstance(command, str) or not command:
        raise EvidenceError("test run requires suite_id and exact command")
    for path in (log, junit):
        if not path.is_absolute() or _has_symlink_component(path) or not path.is_file() or path.resolve().is_relative_to(root.resolve()):
            raise EvidenceError("test outputs must be regular files outside the repository")
    try:
        xml_root = ET.parse(junit).getroot()
    except (OSError, ET.ParseError) as exc:
        raise EvidenceError(f"invalid JUnit XML: {junit}") from exc
    cases = []
    for case in xml_root.iter("testcase"):
        failure = any(node.tag in {"failure", "error"} for node in case)
        skipped = any(node.tag == "skipped" for node in case)
        outcome = "FAILED" if failure else "SKIPPED" if skipped else "PASSED"
        cases.append({"case_id": f"{case.get('classname', '')}::{case.get('name', '')}", "outcome": outcome})
    if not cases:
        raise EvidenceError("JUnit contains no test cases")
    try:
        exit_code = int(item["exit_code"])
    except (KeyError, TypeError, ValueError) as exc:
        raise EvidenceError("test run requires observed exit_code") from exc
    counts = {name: sum(row["outcome"] == name for row in cases) for name in ("PASSED", "FAILED", "SKIPPED")}
    return {"suite_id": suite, "command": command, "exit_code": exit_code, "total": len(cases), "passed": counts["PASSED"], "failed": counts["FAILED"], "skipped": counts["SKIPPED"], "log": {"path": str(log.resolve()), "sha256": _sha(log.read_bytes())}, "junit": {"path": str(junit.resolve()), "sha256": _sha(junit.read_bytes())}, "cases": cases}

def build_candidate_evidence(root: Path, runs: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    root = root.resolve(strict=True)
    candidate = candidate_worktree_binding(root)
    guidance = guidance_context(root, CANDIDATE_STATIC_V2)
    frozen = guidance_context(root, FROZEN_HISTORICAL_V1)
    run_records = [_observed_run(root, item) for item in (runs or [])]
    uix9 = next((item for item in run_records if item["suite_id"] == "UIX9_STATIC_58"), None)
    pending = bool(run_records) and all(item["exit_code"] == 0 and item["failed"] == 0 for item in run_records)
    pending = pending and uix9 is not None and uix9["total"] == 58 and uix9["passed"] == 58 and uix9["skipped"] == 0
    evaluator = _repo_file(root, EVALUATOR)
    validator = _repo_file(root, MODULE)
    return {
        "schema_version": "uix9.candidate-static-evidence.v2",
        "context": CANDIDATE_STATIC_V2,
        "status": "STATIC_EVIDENCE_PENDING_REVIEW" if pending else "DRAFT_DIAGNOSTIC",
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "candidate": candidate,
        "guidance": {
            "manifest_path": guidance["manifest_path"], "manifest_sha256": guidance["manifest_sha256"],
            "source_sha": guidance["source_sha"], "guidance_digest": guidance["guidance_digest"], "algorithm": guidance["algorithm"],
            "materials": [{key: item[key] for key in ("path", "role", "revision_identity", "sha256")} for item in guidance["materials"]],
        },
        "frozen_predecessor": {
            "context": FROZEN_HISTORICAL_V1, "manifest_snapshot_sha": frozen["manifest_snapshot_sha"],
            "manifest_sha256": frozen["manifest_sha256"], "source_sha": frozen["source_sha"],
            "guidance_digest": frozen["guidance_digest"], "historical_approval_inherited": False,
        },
        "implementation": {
            "evaluator": {"path": EVALUATOR, "version": EVALUATOR_VERSION, "sha256": _sha(evaluator.read_bytes())},
            "validator": {"path": MODULE, "version": VERSION, "sha256": _sha(validator.read_bytes())},
            "frozen_evaluator_sha256": frozen_source_digest(root, "evaluator"),
            "frozen_validator_sha256": frozen_source_digest(root, "validator"),
        },
        "test_runs": run_records,
        "provenance": {
            "creator": "local-static-evidence-validator", "python": sys.version.split()[0], "platform": platform.platform(),
            "runtime_routing_requested_model": "gpt-6-luna", "runtime_routing_requested_effort": "max",
            "runtime_routing_observed": "NEEDS_VERIFICATION",
        },
        "authority": {
            "human_review": "PENDING", "live_uix9b_authorized": False,
            "governance_activation_authorized": False, "merge_authorized": False, "publication_authorized": False,
        },
    }


def validate_candidate_evidence(root: Path, record: dict[str, Any], schema_path: Path | None = None) -> None:
    root = root.resolve(strict=True)
    schema_path = schema_path or root / SCHEMA
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.Draft202012Validator(schema).validate(record)
    except (OSError, json.JSONDecodeError, jsonschema.exceptions.SchemaError, jsonschema.exceptions.ValidationError) as exc:
        raise EvidenceError(f"candidate evidence schema failure: {exc}") from exc
    current = candidate_worktree_binding(root)
    for key in ("base_sha", "base_tree_sha", "content_fingerprint", "changed_files"):
        if record["candidate"].get(key) != current[key]:
            raise EvidenceError(f"candidate binding changed: {key}")
    guidance = guidance_context(root, CANDIDATE_STATIC_V2)
    for key in ("manifest_path", "manifest_sha256", "source_sha", "guidance_digest", "algorithm"):
        if record["guidance"].get(key) != guidance.get(key):
            raise EvidenceError(f"candidate guidance changed: {key}")
    material_rows = [{key: item[key] for key in ("path", "role", "revision_identity", "sha256")} for item in guidance["materials"]]
    if record["guidance"].get("materials") != material_rows:
        raise EvidenceError("candidate material list changed")
    frozen = guidance_context(root, FROZEN_HISTORICAL_V1)
    predecessor = record["frozen_predecessor"]
    expected_predecessor = {
        "context": FROZEN_HISTORICAL_V1, "manifest_snapshot_sha": frozen["manifest_snapshot_sha"],
        "manifest_sha256": frozen["manifest_sha256"], "source_sha": frozen["source_sha"],
        "guidance_digest": frozen["guidance_digest"], "historical_approval_inherited": False,
    }
    if predecessor != expected_predecessor:
        raise EvidenceError("frozen predecessor binding or approval boundary changed")
    implementation = record["implementation"]
    expected_implementation = {
        "evaluator": {"path": EVALUATOR, "version": EVALUATOR_VERSION, "sha256": _sha(_repo_file(root, EVALUATOR).read_bytes())},
        "validator": {"path": MODULE, "version": VERSION, "sha256": _sha(_repo_file(root, MODULE).read_bytes())},
        "frozen_evaluator_sha256": frozen_source_digest(root, "evaluator"),
        "frozen_validator_sha256": frozen_source_digest(root, "validator"),
    }
    if implementation != expected_implementation:
        raise EvidenceError("candidate or frozen implementation identity changed")
    for run in record["test_runs"]:
        observed = _observed_run(root, {
            "suite_id": run["suite_id"], "command": run["command"], "exit_code": run["exit_code"],
            "log_path": run["log"]["path"], "junit_path": run["junit"]["path"],
        })
        if observed != run:
            raise EvidenceError(f"test log or result record changed: {run['suite_id']}")
    if record["status"] == "STATIC_EVIDENCE_PENDING_REVIEW":
        uix9 = next((item for item in record["test_runs"] if item["suite_id"] == "UIX9_STATIC_58"), None)
        if not record["test_runs"] or any(item["exit_code"] != 0 or item["failed"] for item in record["test_runs"]):
            raise EvidenceError("pending review requires all recorded tests to pass")
        if uix9 is None or uix9["total"] != 58 or uix9["passed"] != 58 or uix9["skipped"] != 0:
            raise EvidenceError("pending review requires all 58 UIX9 cases and zero skips")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--schema", type=Path, default=ROOT / SCHEMA)
    parser.add_argument("--runs", type=Path, required=True, help="JSON array of observed command, exit code, log and JUnit paths")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    output = args.output
    if not output.is_absolute() or output.is_symlink() or output.resolve().is_relative_to(root):
        raise EvidenceError("evidence output must be absolute and outside the repository")
    runs = json.loads(args.runs.read_text(encoding="utf-8"))
    if not isinstance(runs, list):
        raise EvidenceError("run manifest must be a JSON array")
    record = build_candidate_evidence(root, runs)
    validate_candidate_evidence(root, record, args.schema)
    output.write_text(json.dumps(record, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": record["status"], "content_fingerprint": record["candidate"]["content_fingerprint"], "output": str(output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())