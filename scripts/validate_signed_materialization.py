#!/usr/bin/env python3
"""Validate a materialization pull request and emit non-authorizing machine evidence."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "machine" / "governance" / "policy.v1.json"
SCHEMA_VERSION = "orchestra.signed-materialization-evidence.v1"
DISPOSITION = "REVIEWED_UNSIGNED_SOURCE_READY_FOR_GITHUB_SQUASH_MATERIALIZATION"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
ALLOWED_ACTIONS = {"opened", "synchronize", "reopened"}


class MaterializationValidationError(ValueError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise MaterializationValidationError(f"expected JSON object: {path}")
    return value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise MaterializationValidationError(message)


def require_sha(value: Any, label: str) -> str:
    require(isinstance(value, str) and SHA_RE.fullmatch(value) is not None, f"{label} must be a full lowercase Git SHA")
    return value


def transport_policy(policy: dict[str, Any]) -> dict[str, Any]:
    transport = policy.get("repository_change_transport", {}).get("api_authored_unsigned_tree")
    require(isinstance(transport, dict), "missing api-authored unsigned-tree transport policy")
    required = {
        "mode": "TWO_PR_SIGNED_MATERIALIZATION",
        "materialization_pr_role": "REVIEW_AND_SIGNING_TRANSPORT",
        "source_pr_required": False,
        "source_head_signature_required": False,
        "materialization_pr_is_canonical_readiness": False,
        "materialization_pr_creates_project_state_authority": False,
        "materialization_pr_creates_release_authority": False,
        "materialization_pr_creates_bypass_authority": False,
        "materialized_commit_signature_required": True,
        "materialized_tree_must_equal_reviewed_source_tree": True,
        "materialized_parent_must_equal_verified_canonical_base": True,
        "materialization_validation_mode": "BOUNDED_MACHINE_EVIDENCE_ONLY",
        "materialization_required_workflow": "signed-materialization",
        "materialization_runs_full_validate": False,
        "materialization_runs_mutation_campaigns": False,
        "canonical_pr_base": "main",
        "canonical_pr_required": True,
        "canonical_pr_must_use_materialized_signed_head": True,
        "canonical_pr_revalidates_exact_signed_head": True,
        "canonical_required_checks_reusable_from_materialization": False,
        "canonical_full_validation_required": True,
        "canonical_mergeable_required": True,
        "canonical_mergeable_state_required": "clean",
        "canonical_merge_method": "squash",
        "canonical_bypass_used": False,
        "post_merge_independent_canonical_read_required": True,
        "workflow_optimization_disposition": "MATERIALIZATION_PR_BOUNDED_CHECKS_ONLY;FULL_MATRIX_MAIN_ONLY",
    }
    for key, expected in required.items():
        require(transport.get(key) == expected, f"transport policy {key} must equal {expected!r}")
    prefix = transport.get("materialization_branch_prefix")
    require(prefix == "materialize/", "materialization branch prefix must remain materialize/")
    require(
        transport.get("materialization_evidence_schema") == "machine/schemas/signed-materialization-evidence.schema.json",
        "materialization evidence schema path changed",
    )
    require(
        transport.get("materialization_evidence_artifact") == "signed-materialization-evidence",
        "materialization evidence artifact identity changed",
    )
    return transport


def build_evidence(
    *,
    event: dict[str, Any],
    policy: dict[str, Any],
    checked_head_sha: str,
    checked_head_tree: str,
    changed_paths: list[str],
) -> dict[str, Any]:
    transport = transport_policy(policy)
    require(event.get("action") in ALLOWED_ACTIONS, "unsupported pull-request action")
    pr = event.get("pull_request")
    require(isinstance(pr, dict), "pull_request payload missing")
    number = event.get("number")
    require(isinstance(number, int) and number > 0, "pull request number must be positive")
    base = pr.get("base")
    head = pr.get("head")
    require(isinstance(base, dict) and isinstance(head, dict), "pull request base/head payload missing")
    base_ref = base.get("ref")
    head_ref = head.get("ref")
    base_sha = require_sha(base.get("sha"), "pull_request.base.sha")
    head_sha = require_sha(head.get("sha"), "pull_request.head.sha")
    checked_sha = require_sha(checked_head_sha, "checked_head_sha")
    checked_tree = require_sha(checked_head_tree, "checked_head_tree")
    require(isinstance(base_ref, str) and base_ref.startswith(transport["materialization_branch_prefix"]), "materialization PR must target materialize/**")
    require(base_ref != transport["canonical_pr_base"], "materialization PR must not target canonical main")
    require(isinstance(head_ref, str) and head_ref, "pull request source ref missing")
    require(checked_sha == head_sha, "checked-out revision does not equal exact pull-request head")
    require(isinstance(changed_paths, list) and bool(changed_paths), "materialization PR must contain at least one changed path")
    normalized: list[str] = []
    for path in changed_paths:
        require(isinstance(path, str) and path and not path.startswith("/") and ".." not in Path(path).parts, "changed path must be normalized and repository-relative")
        normalized.append(path.replace("\\", "/"))
    require(len(normalized) == len(set(normalized)), "changed paths must be unique")
    return {
        "schema_version": SCHEMA_VERSION,
        "repository": event.get("repository", {}).get("full_name") or os.environ.get("GITHUB_REPOSITORY", ""),
        "event": {"name": "pull_request", "action": event["action"], "pull_request_number": number},
        "base": {"ref": base_ref, "sha": base_sha, "role": "ISOLATED_SIGNING_TARGET_NOT_CANONICAL"},
        "source": {"ref": head_ref, "sha": head_sha, "signature_requirement": "NOT_REQUIRED_PRE_MATERIALIZATION"},
        "reviewed_tree": checked_tree,
        "changed_paths": normalized,
        "authority": {"canonical_merge_readiness": False, "project_state_promotion": False, "release": False, "bypass": False},
        "disposition": DISPOSITION,
    }


def git_output(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="validate-signed-materialization")
    parser.add_argument("--event", default=os.environ.get("GITHUB_EVENT_PATH"))
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        require(bool(args.event), "GitHub pull-request event path is required")
        event = load_json(Path(args.event))
        policy = load_json(POLICY_PATH)
        head_sha = git_output("rev-parse", "HEAD")
        head_tree = git_output("rev-parse", "HEAD^{tree}")
        base_sha = require_sha(event.get("pull_request", {}).get("base", {}).get("sha"), "pull_request.base.sha")
        pr_head_sha = require_sha(event.get("pull_request", {}).get("head", {}).get("sha"), "pull_request.head.sha")
        changed_output = git_output("diff", "--name-only", f"{base_sha}...{pr_head_sha}")
        changed_paths = [line for line in changed_output.splitlines() if line.strip()]
        diff_check = subprocess.run(["git", "diff", "--check", f"{base_sha}...{pr_head_sha}"], cwd=ROOT, check=False)
        require(diff_check.returncode == 0, "git diff --check failed for materialization source tree")
        evidence = build_evidence(
            event=event,
            policy=policy,
            checked_head_sha=head_sha,
            checked_head_tree=head_tree,
            changed_paths=changed_paths,
        )
        require(evidence["repository"] == os.environ.get("GITHUB_REPOSITORY", evidence["repository"]), "repository identity mismatch")
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(evidence, indent=2, sort_keys=True))
        print("ORCHESTRA_SIGNED_MATERIALIZATION=READY_FOR_GITHUB_SQUASH")
        return 0
    except (MaterializationValidationError, FileNotFoundError, json.JSONDecodeError, subprocess.CalledProcessError) as exc:
        print(f"ORCHESTRA_SIGNED_MATERIALIZATION=FAIL: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
