#!/usr/bin/env python3
# @codebase_provenance_JEO
# @codebase_rights_JEO
"""Verify tree-attested promotion assurance for signed canonical promotions.

Ordinary source candidates return FULL_ASSURANCE. Recognized signed-promotion
lanes must prove the complete source -> signed carrier -> canonical chain or
fail closed. Evidence is non-authorizing and cannot bypass repository rules.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys
from typing import Any, Callable
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
MATERIALIZE_PREFIX = "materialize/"
CANONICAL_BRANCH = "main"
MODE_FULL = "FULL_ASSURANCE"
MODE_ATTESTED = "TREE_ATTESTED"
REQUIRED_SOURCE_CHECKS = (
    "governance-check",
    "validate",
    "runtime-tests",
    "native-windows-latest",
    "native-ubuntu-latest",
    "native-macos-latest",
    "Compatibility CodeQL (python)",
)
OPTIONAL_SECURITY_CHECKS = ("CodeQL",)
SUCCESSFUL_CONCLUSIONS = {"success", "neutral", "skipped"}
API_VERSION = "2022-11-28"


class PromotionAttestationError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PromotionAttestationError(message)


def require_sha(value: Any, label: str) -> str:
    require(isinstance(value, str) and SHA_RE.fullmatch(value) is not None, f"{label} must be a full lowercase Git SHA")
    return value


def load_json(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"expected JSON object: {path}")
    return value


def _api_get(path: str, *, repository: str, token: str) -> Any:
    url = f"https://api.github.com/repos/{repository}{path}"
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "orchestra-promotion-attestation",
        },
    )
    try:
        with urlopen(request, timeout=20) as response:
            return json.load(response)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise PromotionAttestationError(f"GitHub API read failed for {path}: {exc}") from exc


def github_getter(repository: str, token: str) -> Callable[[str], Any]:
    return lambda path: _api_get(path, repository=repository, token=token)


def _commit(get: Callable[[str], Any], sha: str) -> dict[str, Any]:
    value = get(f"/git/commits/{sha}")
    require(isinstance(value, dict), "commit response must be an object")
    return value


def _tree_sha(commit: dict[str, Any], label: str) -> str:
    tree = commit.get("tree")
    require(isinstance(tree, dict), f"{label} tree missing")
    return require_sha(tree.get("sha"), f"{label}.tree.sha")


def _signature_valid(commit: dict[str, Any], label: str) -> None:
    verification = commit.get("verification")
    require(isinstance(verification, dict), f"{label} signature verification missing")
    require(verification.get("verified") is True, f"{label} signature must be verified")
    require(verification.get("reason") == "valid", f"{label} signature reason must be valid")


def _pull_files(get: Callable[[str], Any], number: int) -> tuple[str, ...]:
    values = get(f"/pulls/{number}/files?per_page=100")
    require(isinstance(values, list), "pull files response must be a list")
    require(len(values) < 100, "pull file pagination beyond 100 is not supported by bounded attestation")
    paths = []
    for entry in values:
        require(isinstance(entry, dict), "pull file entry must be an object")
        filename = entry.get("filename")
        require(isinstance(filename, str) and filename, "pull file name missing")
        paths.append(filename)
    require(paths, "promotion source must contain at least one changed path")
    require(len(paths) == len(set(paths)), "pull file paths must be unique")
    return tuple(sorted(paths))


def _associated_pulls(get: Callable[[str], Any], sha: str) -> list[dict[str, Any]]:
    values = get(f"/commits/{sha}/pulls?per_page=100")
    require(isinstance(values, list), "associated pulls response must be a list")
    return [value for value in values if isinstance(value, dict)]


def _find_source_pr(get: Callable[[str], Any], source_sha: str, expected_base_sha: str) -> dict[str, Any]:
    matches: list[dict[str, Any]] = []
    for pr in _associated_pulls(get, source_sha):
        base = pr.get("base")
        head = pr.get("head")
        if not isinstance(base, dict) or not isinstance(head, dict):
            continue
        if (
            base.get("ref") == CANONICAL_BRANCH
            and base.get("sha") == expected_base_sha
            and head.get("sha") == source_sha
        ):
            matches.append(pr)
    require(len(matches) == 1, f"expected exactly one source PR on {CANONICAL_BRANCH}, found {len(matches)}")
    return matches[0]


def _find_materialization_pr(
    get: Callable[[str], Any],
    *,
    materialize_ref: str,
    carrier_sha: str,
    expected_base_sha: str,
) -> dict[str, Any]:
    encoded = quote(materialize_ref, safe="")
    values = get(f"/pulls?state=closed&base={encoded}&per_page=100&sort=updated&direction=desc")
    require(isinstance(values, list), "materialization pull list must be a list")
    matches: list[dict[str, Any]] = []
    for pr in values:
        if not isinstance(pr, dict):
            continue
        base = pr.get("base")
        if (
            pr.get("merged_at")
            and pr.get("merge_commit_sha") == carrier_sha
            and isinstance(base, dict)
            and base.get("ref") == materialize_ref
            and base.get("sha") == expected_base_sha
        ):
            matches.append(pr)
    require(len(matches) == 1, f"expected exactly one materialization PR for carrier, found {len(matches)}")
    return matches[0]


def _source_checks(get: Callable[[str], Any], source_sha: str) -> dict[str, Any]:
    value = get(f"/commits/{source_sha}/check-runs?per_page=100")
    require(isinstance(value, dict), "check-runs response must be an object")
    check_runs = value.get("check_runs")
    require(isinstance(check_runs, list), "check-runs list missing")
    require(len(check_runs) < 100, "source check-run pagination beyond 100 is not supported by bounded attestation")
    by_name: dict[str, list[dict[str, Any]]] = {}
    for run in check_runs:
        if not isinstance(run, dict):
            continue
        name = run.get("name")
        if isinstance(name, str):
            by_name.setdefault(name, []).append(run)

    for name in REQUIRED_SOURCE_CHECKS:
        candidates = by_name.get(name, [])
        require(candidates, f"required source check missing: {name}")
        require(
            any(run.get("status") == "completed" and run.get("conclusion") == "success" for run in candidates),
            f"required source check not successful: {name}",
        )

    for name in OPTIONAL_SECURITY_CHECKS:
        for run in by_name.get(name, []):
            require(
                run.get("status") == "completed" and run.get("conclusion") in SUCCESSFUL_CONCLUSIONS,
                f"present source security check not successful: {name}",
            )
    return {"required": list(REQUIRED_SOURCE_CHECKS), "observed_count": len(check_runs)}


def _source_workflow_runs(get: Callable[[str], Any], source_sha: str) -> dict[str, Any]:
    value = get(f"/actions/runs?head_sha={source_sha}&event=pull_request&per_page=100")
    require(isinstance(value, dict), "workflow-runs response must be an object")
    runs = value.get("workflow_runs")
    require(isinstance(runs, list), "workflow-runs list missing")
    require(len(runs) < 100, "source workflow pagination beyond 100 is not supported by bounded attestation")
    require(runs, "source pull-request workflow evidence is missing")
    failures = []
    for run in runs:
        if not isinstance(run, dict):
            continue
        status = run.get("status")
        conclusion = run.get("conclusion")
        if status != "completed" or conclusion not in SUCCESSFUL_CONCLUSIONS:
            failures.append(f"{run.get('name', '<unknown>')}:{status}/{conclusion}")
    require(not failures, "source workflow evidence is not terminal-success: " + ", ".join(failures))
    return {"observed_count": len(runs), "all_terminal_success": True}


def _pr_identity(pr: dict[str, Any], *, label: str) -> tuple[int, str, str, str, str]:
    number = pr.get("number")
    base = pr.get("base")
    head = pr.get("head")
    require(isinstance(number, int) and number > 0, f"{label} number missing")
    require(isinstance(base, dict) and isinstance(head, dict), f"{label} base/head missing")
    base_ref = base.get("ref")
    head_ref = head.get("ref")
    base_sha = require_sha(base.get("sha"), f"{label}.base.sha")
    head_sha = require_sha(head.get("sha"), f"{label}.head.sha")
    require(isinstance(base_ref, str) and base_ref, f"{label}.base.ref missing")
    require(isinstance(head_ref, str) and head_ref, f"{label}.head.ref missing")
    return number, base_ref, base_sha, head_ref, head_sha


def attest_promotion_pr(
    event: dict[str, Any],
    *,
    get: Callable[[str], Any],
) -> dict[str, Any] | None:
    pr = event.get("pull_request")
    require(isinstance(pr, dict), "pull_request payload missing")
    number, base_ref, base_sha, head_ref, carrier_sha = _pr_identity(pr, label="canonical_pr")
    if base_ref != CANONICAL_BRANCH or not head_ref.startswith(MATERIALIZE_PREFIX):
        return None

    carrier_commit = _commit(get, carrier_sha)
    _signature_valid(carrier_commit, "signed_carrier")
    carrier_tree = _tree_sha(carrier_commit, "signed_carrier")
    parents = carrier_commit.get("parents")
    require(isinstance(parents, list) and len(parents) == 1, "signed carrier must have exactly one parent")
    require(parents[0].get("sha") == base_sha, "signed carrier parent must equal canonical PR base")

    materialization_pr = _find_materialization_pr(
        get,
        materialize_ref=head_ref,
        carrier_sha=carrier_sha,
        expected_base_sha=base_sha,
    )
    mat_number, mat_base_ref, mat_base_sha, _source_ref, source_sha = _pr_identity(
        materialization_pr, label="materialization_pr"
    )
    require(mat_base_ref == head_ref, "materialization target ref mismatch")
    require(mat_base_sha == base_sha, "materialization base SHA must equal canonical base SHA")
    require(materialization_pr.get("merged_at"), "materialization PR must be merged")
    require(materialization_pr.get("merge_commit_sha") == carrier_sha, "materialization merge SHA must equal carrier SHA")

    source_commit = _commit(get, source_sha)
    source_tree = _tree_sha(source_commit, "qualified_source")
    require(source_tree == carrier_tree, "qualified source tree must equal signed carrier tree")

    source_pr = _find_source_pr(get, source_sha, base_sha)
    source_number, source_base_ref, source_base_sha, _source_head_ref, source_pr_sha = _pr_identity(
        source_pr, label="source_pr"
    )
    require(source_base_ref == CANONICAL_BRANCH, "source PR must target main")
    require(source_base_sha == base_sha, "source PR base must equal canonical base")
    require(source_pr_sha == source_sha, "source PR head SHA mismatch")

    source_paths = _pull_files(get, source_number)
    canonical_paths = _pull_files(get, number)
    require(source_paths == canonical_paths, "source and canonical promotion changed-path sets must be identical")

    checks = _source_checks(get, source_sha)
    workflows = _source_workflow_runs(get, source_sha)

    return {
        "schema_version": "orchestra.tree-attested-promotion.v1",
        "mode": MODE_ATTESTED,
        "event": "pull_request",
        "canonical_pr": number,
        "canonical_base_sha": base_sha,
        "source_pr": source_number,
        "source_sha": source_sha,
        "source_tree": source_tree,
        "materialization_pr": mat_number,
        "carrier_sha": carrier_sha,
        "carrier_tree": carrier_tree,
        "changed_paths": list(source_paths),
        "source_checks": checks,
        "source_workflows": workflows,
        "authority": "EVIDENCE_ONLY_NON_AUTHORIZING",
    }


def attest_canonical_push(
    event: dict[str, Any],
    *,
    get: Callable[[str], Any],
) -> dict[str, Any] | None:
    ref = event.get("ref")
    after = event.get("after")
    before = event.get("before")
    if ref != "refs/heads/main":
        return None
    canonical_sha = require_sha(after, "push.after")
    before_sha = require_sha(before, "push.before")

    canonical_pr_matches = []
    for pr in _associated_pulls(get, canonical_sha):
        base = pr.get("base")
        if (
            pr.get("merged_at")
            and pr.get("merge_commit_sha") == canonical_sha
            and isinstance(base, dict)
            and base.get("ref") == CANONICAL_BRANCH
        ):
            canonical_pr_matches.append(pr)
    if not canonical_pr_matches:
        return None
    require(len(canonical_pr_matches) == 1, f"expected exactly one canonical merged PR, found {len(canonical_pr_matches)}")
    canonical_pr = canonical_pr_matches[0]
    _number, base_ref, base_sha, head_ref, carrier_sha = _pr_identity(canonical_pr, label="canonical_pr")
    if not head_ref.startswith(MATERIALIZE_PREFIX):
        return None
    require(base_ref == CANONICAL_BRANCH, "canonical PR base must be main")
    require(base_sha == before_sha, "canonical PR base must equal push before SHA")

    canonical_commit = _commit(get, canonical_sha)
    _signature_valid(canonical_commit, "canonical_commit")
    canonical_tree = _tree_sha(canonical_commit, "canonical_commit")
    parents = canonical_commit.get("parents")
    require(isinstance(parents, list) and len(parents) == 1, "canonical commit must have exactly one parent")
    require(parents[0].get("sha") == before_sha, "canonical parent must equal push before SHA")

    synthetic_event = {"pull_request": canonical_pr}
    attestation = attest_promotion_pr(synthetic_event, get=get)
    require(attestation is not None, "canonical push promotion chain is not attestable")
    require(attestation["carrier_sha"] == carrier_sha, "canonical PR carrier mismatch")
    require(attestation["carrier_tree"] == canonical_tree, "canonical tree must equal signed carrier tree")
    require(attestation["source_tree"] == canonical_tree, "canonical tree must equal qualified source tree")
    attestation = dict(attestation)
    attestation.update(
        {
            "event": "push",
            "canonical_sha": canonical_sha,
            "canonical_tree": canonical_tree,
            "canonical_parent": before_sha,
        }
    )
    return attestation


def determine_mode(
    event_name: str,
    event: dict[str, Any],
    *,
    get: Callable[[str], Any],
) -> tuple[str, dict[str, Any] | None]:
    if event_name == "pull_request":
        result = attest_promotion_pr(event, get=get)
        return (MODE_ATTESTED, result) if result is not None else (MODE_FULL, None)
    if event_name == "push":
        result = attest_canonical_push(event, get=get)
        return (MODE_ATTESTED, result) if result is not None else (MODE_FULL, None)
    return MODE_FULL, None


def _write_github_output(path: str | None, mode: str) -> None:
    if not path:
        return
    with Path(path).open("a", encoding="utf-8") as handle:
        handle.write(f"mode={mode}\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="validate-governance-promotion-attestation")
    parser.add_argument("--event", default=os.environ.get("GITHUB_EVENT_PATH"))
    parser.add_argument("--event-name", default=os.environ.get("GITHUB_EVENT_NAME", ""))
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN", ""))
    parser.add_argument("--github-output", default=os.environ.get("GITHUB_OUTPUT"))
    parser.add_argument("--evidence-output")
    args = parser.parse_args(argv)
    try:
        require(bool(args.event), "GitHub event path is required")
        event = load_json(args.event)
        event_name = str(args.event_name).strip()
        if event_name not in {"pull_request", "push"}:
            _write_github_output(args.github_output, MODE_FULL)
            print(f"PROMOTION_ASSURANCE_MODE={MODE_FULL}")
            return 0

        require(bool(args.repository), "GITHUB_REPOSITORY is required")
        require(bool(args.token), "GITHUB_TOKEN is required")
        mode, evidence = determine_mode(
            event_name,
            event,
            get=github_getter(args.repository, args.token),
        )
        _write_github_output(args.github_output, mode)
        if evidence is not None and args.evidence_output:
            output = Path(args.evidence_output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"PROMOTION_ASSURANCE_MODE={mode}")
        if evidence is not None:
            print(json.dumps(evidence, indent=2, sort_keys=True))
        return 0
    except (PromotionAttestationError, OSError, json.JSONDecodeError) as exc:
        print(f"PROMOTION_ASSURANCE=FAIL: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
