#!/usr/bin/env python3
"""Fail closed when Orchestra changes omit the documentation surfaces they affect.

The historical gate required README.md for nearly every significant change. That
made the root landing page accumulate implementation detail. This contract keeps
README.md stable and concise while requiring machine-index parity and detailed
documentation when the changed surface needs them.
"""
from __future__ import annotations

import fnmatch
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable


README_PATH = "README.md"
MACHINE_INDEX_PATH = "README.json"

# Changes that materially alter the public package/release/install identity must
# keep the concise landing page current.
PUBLIC_README_PATTERNS = (
    ".agents/plugins/marketplace.json",
    ".claude-plugin/**",
    ".codex-plugin/**",
    "assets/readme/**",
    "docs/releases/**",
    "docs/setup/INSTALLATION.md",
    "plugin.json",
)

# Machine-facing discovery must track changes to executable, routed, governed,
# integrated, or machine-contract surfaces. README.json is an index, not a copy.
MACHINE_INDEX_PATTERNS = (
    ".agents/plugins/marketplace.json",
    ".claude-plugin/**",
    ".codex-plugin/**",
    ".github/workflows/**",
    "adapters/**",
    "commands/**",
    "machine/**",
    "orchestra_runtime/**",
    "scripts/**",
    "skills/**",
    "templates/**",
    "AGENTS.md",
    "PROJECT_CONTEXT.md",
    "PROJECT_STATE.md",
    "ROUTING_MAP.md",
    "SKILL_INDEX.md",
    "plugin.json",
)

# Domain behavior should not become discoverable only through code. A changed
# implementation/contract surface must be accompanied by at least one detailed
# human documentation surface. This intentionally does not force README.md.
DETAIL_SOURCE_PATTERNS = (
    "adapters/**",
    "commands/**",
    "machine/developer-portal/**",
    "machine/governance/**",
    "machine/hosts/**",
    "machine/protocol/**",
    "machine/routing/**",
    "orchestra_runtime/**",
    "skills/**",
)

DETAIL_DOCUMENTATION_PATTERNS = (
    "docs/**",
    "AGENTS.md",
    "ROUTING_MAP.md",
    "SKILL_INDEX.md",
)

# Evidence-only/test-only changes remain outside documentation-impact forcing.
NON_SIGNIFICANT_PATTERNS = (
    "README.md",
    "README.json",
    "CHANGELOG.md",
    "DECISION_LOG.md",
    "SESSION_HANDOFF.md",
    "artifacts/**",
    "docs/validation/**",
    "tests/**",
)


def normalize_paths(paths: Iterable[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for raw in paths:
        path = str(raw).strip().replace("\\", "/")
        if path and path not in seen:
            seen.add(path)
            normalized.append(path)
    return normalized


def _matches(path: str, patterns: Iterable[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def _impact_paths(changed: list[str], patterns: Iterable[str]) -> list[str]:
    return sorted(
        path
        for path in changed
        if not _matches(path, NON_SIGNIFICANT_PATTERNS) and _matches(path, patterns)
    )


def evaluate_changed_paths(paths: Iterable[str]) -> dict[str, object]:
    changed = normalize_paths(paths)
    public_impacts = _impact_paths(changed, PUBLIC_README_PATTERNS)
    machine_impacts = _impact_paths(changed, MACHINE_INDEX_PATTERNS)
    detail_impacts = _impact_paths(changed, DETAIL_SOURCE_PATTERNS)

    readme_updated = README_PATH in changed
    machine_index_updated = MACHINE_INDEX_PATH in changed
    detailed_docs_updated = any(_matches(path, DETAIL_DOCUMENTATION_PATTERNS) for path in changed)

    missing: list[str] = []
    if public_impacts and not readme_updated:
        missing.append(README_PATH)
    if machine_impacts and not machine_index_updated:
        missing.append(MACHINE_INDEX_PATH)
    if detail_impacts and not detailed_docs_updated:
        missing.append("detailed-documentation")

    return {
        "passed": not missing,
        "changed": changed,
        "public_impacts": public_impacts,
        "machine_impacts": machine_impacts,
        "detail_impacts": detail_impacts,
        "readme_updated": readme_updated,
        "machine_index_updated": machine_index_updated,
        "detailed_docs_updated": detailed_docs_updated,
        "missing": missing,
    }


def _git(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )


def _commit_exists(repo_root: Path, revision: str) -> bool:
    if not revision:
        return False
    return _git(repo_root, "cat-file", "-e", f"{revision}^{{commit}}").returncode == 0


def _ensure_commit(repo_root: Path, revision: str, label: str) -> None:
    if _commit_exists(repo_root, revision):
        return
    if os.environ.get("GITHUB_ACTIONS") == "true":
        fetch = _git(repo_root, "fetch", "--no-tags", "--depth=1", "origin", revision)
        if fetch.returncode == 0 and _commit_exists(repo_root, revision):
            return
    raise RuntimeError(f"Verified {label} commit is unavailable: {revision or '<missing>'}")


def _load_event() -> tuple[str, dict[str, object]]:
    event_name = os.environ.get("GITHUB_EVENT_NAME", "").strip()
    event_path = os.environ.get("GITHUB_EVENT_PATH", "").strip()
    if not event_path or not Path(event_path).is_file():
        return event_name, {}
    return event_name, json.loads(Path(event_path).read_text(encoding="utf-8"))


def resolve_change_range(repo_root: Path) -> tuple[str, str, str] | None:
    """Return (label, base, head) for PR/push events, or None for manual runs."""
    event_name, event = _load_event()

    if event_name in {"pull_request", "pull_request_target"}:
        pull_request = event.get("pull_request")
        if not isinstance(pull_request, dict):
            raise RuntimeError("Pull-request event payload is missing pull_request data")
        base_obj = pull_request.get("base")
        if not isinstance(base_obj, dict):
            raise RuntimeError("Pull-request event payload is missing base data")
        base = str(base_obj.get("sha", "")).strip()
        head = os.environ.get("GITHUB_SHA", "").strip() or "HEAD"
        _ensure_commit(repo_root, base, "pull-request base")
        _ensure_commit(repo_root, head, "pull-request tested head")
        return "pull-request-base..tested-head", base, head

    if event_name == "push":
        base = str(event.get("before", "")).strip()
        head = str(event.get("after", "")).strip() or os.environ.get("GITHUB_SHA", "").strip()
        if base and set(base) == {"0"}:
            base = ""
        if not base:
            raise RuntimeError("Push event has no usable before commit; documentation impact cannot be verified")
        _ensure_commit(repo_root, base, "push-before")
        _ensure_commit(repo_root, head, "push-after")
        return "push-before..push-after", base, head

    return None


def changed_paths_for_range(repo_root: Path, base: str, head: str) -> list[str]:
    result = _git(repo_root, "diff", "--name-only", base, head)
    if result.returncode != 0:
        raise RuntimeError(
            "Could not enumerate changed paths for documentation impact validation: "
            + (result.stderr.strip() or "git diff failed")
        )
    return normalize_paths(result.stdout.splitlines())


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    try:
        change_range = resolve_change_range(repo_root)
        if change_range is None:
            print("README_IMPACT_GATE=SKIP event=workflow_dispatch reason=no_revision_transition")
            return 0

        label, base, head = change_range
        result = evaluate_changed_paths(changed_paths_for_range(repo_root, base, head))

        if result["passed"]:
            print(
                "README_IMPACT_GATE=PASS "
                f"comparison={label} public={len(result['public_impacts'])} "
                f"machine={len(result['machine_impacts'])} detail={len(result['detail_impacts'])} "
                f"readme_updated={str(result['readme_updated']).lower()} "
                f"machine_index_updated={str(result['machine_index_updated']).lower()} "
                f"detailed_docs_updated={str(result['detailed_docs_updated']).lower()}"
            )
            return 0

        print(
            "README_IMPACT_GATE=FAIL "
            f"comparison={label} missing={','.join(result['missing'])}"
        )
        if result["public_impacts"]:
            print("PUBLIC_IMPACT_PATHS=" + ",".join(result["public_impacts"]))
        if result["machine_impacts"]:
            print("MACHINE_IMPACT_PATHS=" + ",".join(result["machine_impacts"]))
        if result["detail_impacts"]:
            print("DETAIL_IMPACT_PATHS=" + ",".join(result["detail_impacts"]))
        print(
            "REMEDIATION=Update only the affected documentation surfaces: README.md for public identity/headline changes, "
            "README.json for machine discovery parity, and detailed documentation for changed domain behavior."
        )
        return 1
    except (OSError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"README_IMPACT_GATE=FAIL error={exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
