#!/usr/bin/env python3
"""Fail closed when significant Orchestra changes omit README.md.

The gate is intentionally deterministic. It classifies repository paths whose
changes materially affect Orchestra's user-facing capabilities, governance,
routing, installation, host integrations, release/version contract, or CI
policy. Any such change must update README.md in the same revision.
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

SIGNIFICANT_CHANGE_PATTERNS = (
    ".agents/plugins/marketplace.json",
    ".claude-plugin/**",
    ".codex-plugin/**",
    ".github/workflows/**",
    "adapters/**",
    "commands/**",
    "orchestra_runtime/**",
    "scripts/**",
    "skills/**",
    "templates/**",
    "docs/governance/**",
    "docs/project/**",
    "docs/releases/**",
    "docs/routing/**",
    "docs/setup/**",
    "AGENTS.md",
    "PROJECT_CONTEXT.md",
    "PROJECT_STATE.md",
    "ROUTING_MAP.md",
    "SKILL_INDEX.md",
    "plugin.json",
)

# These paths are evidence, tests, or documentation maintenance that should not
# force meaningless README churn when changed by themselves.
NON_SIGNIFICANT_PATTERNS = (
    "README.md",
    "CHANGELOG.md",
    "DECISION_LOG.md",
    "SESSION_HANDOFF.md",
    "assets/**",
    "docs/validation/**",
    "docs/artificer/**",
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


def is_significant_change(path: str) -> bool:
    path = path.strip().replace("\\", "/")
    if not path or _matches(path, NON_SIGNIFICANT_PATTERNS):
        return False
    return _matches(path, SIGNIFICANT_CHANGE_PATTERNS)


def evaluate_changed_paths(paths: Iterable[str]) -> dict[str, object]:
    changed = normalize_paths(paths)
    significant = sorted(path for path in changed if is_significant_change(path))
    readme_updated = README_PATH in changed
    passed = not significant or readme_updated
    return {
        "passed": passed,
        "changed": changed,
        "significant": significant,
        "readme_updated": readme_updated,
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
        # GITHUB_SHA is the tested merge revision for pull_request workflows.
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
            raise RuntimeError("Push event has no usable before commit; README impact cannot be verified")
        _ensure_commit(repo_root, base, "push-before")
        _ensure_commit(repo_root, head, "push-after")
        return "push-before..push-after", base, head

    # workflow_dispatch has no trustworthy change range. The gate remains
    # enforced on pull_request and push, where a revision transition exists.
    return None


def changed_paths_for_range(repo_root: Path, base: str, head: str) -> list[str]:
    result = _git(repo_root, "diff", "--name-only", base, head)
    if result.returncode != 0:
        raise RuntimeError(
            "Could not enumerate changed paths for README impact validation: "
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
        significant = result["significant"]
        if result["passed"]:
            print(
                "README_IMPACT_GATE=PASS "
                f"comparison={label} significant={len(significant)} "
                f"readme_updated={str(result['readme_updated']).lower()}"
            )
            if significant:
                print("SIGNIFICANT_PATHS=" + ",".join(significant))
            return 0

        print(
            "README_IMPACT_GATE=FAIL "
            f"comparison={label} significant={len(significant)} readme_updated=false"
        )
        print("SIGNIFICANT_PATHS=" + ",".join(significant))
        print(
            "REMEDIATION=Update README.md in the same change so public documentation "
            "reflects the significant Orchestra capability/governance change."
        )
        return 1
    except (OSError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"README_IMPACT_GATE=FAIL error={exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
