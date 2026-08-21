#!/usr/bin/env python3
"""Hardened live entrypoint for the Orchestra Codex comparative benchmark.

This wrapper preserves the canonical Codex measurement executor and adds the
live-host controls discovered during the 2026-08-21 qualification diagnostic:

1. the workspace must already be a Git worktree before any Codex invocation;
2. a non-zero ``codex exec`` process exit without structured provider evidence
   is a local/measurement failure, not automatically a provider outage.

Structured ``turn.failed``/``error`` JSONL events remain provider outages in the
canonical executor. The wrapper does not alter task prompts, validators, token
mapping, communication treatments, or the frozen benchmark subject.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import codex_benchmark_executor as base  # noqa: E402

LOCAL_EXEC_FAILURE_MARKER = "codex exec returned non-zero"


def _git_worktree_preflight(
    workspace: Path,
    *,
    git_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> tuple[bool, dict[str, Any]]:
    """Verify that ``workspace`` is an existing Git worktree without mutation."""
    if not workspace.is_dir():
        return False, {
            "error": "workspace_dir must resolve to an existing directory",
            "workspace": str(workspace),
            "preflight": "GIT_WORKTREE_REQUIRED",
        }

    try:
        cp = git_runner(
            ["git", "-C", str(workspace.resolve()), "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            check=False,
            shell=False,
        )
    except OSError as exc:
        return False, {
            "error": f"cannot execute Git workspace preflight: {exc}",
            "workspace": str(workspace.resolve()),
            "preflight": "GIT_WORKTREE_REQUIRED",
        }

    stdout = (cp.stdout or "").strip().lower()
    if cp.returncode != 0 or stdout != "true":
        return False, {
            "error": "Codex benchmark workspace must be inside a Git worktree",
            "workspace": str(workspace.resolve()),
            "preflight": "GIT_WORKTREE_REQUIRED",
            "git_returncode": cp.returncode,
            "git_stdout": cp.stdout,
            "git_stderr": cp.stderr,
        }

    return True, {
        "workspace": str(workspace.resolve()),
        "preflight": "GIT_WORKTREE_VERIFIED",
    }


def _reclassify_local_exec_failure(
    request: dict[str, Any], result: dict[str, Any]
) -> dict[str, Any]:
    """Do not label an unstructured non-zero CLI exit as a provider outage."""
    outcome = result.get("outcome")
    evidence = result.get("raw_evidence")
    if not isinstance(outcome, dict) or not isinstance(evidence, dict):
        return result

    if (
        outcome.get("status") == "INVALID_RUN"
        and outcome.get("invalid_reason") == "PROVIDER_OUTAGE"
        and evidence.get("error") == LOCAL_EXEC_FAILURE_MARKER
    ):
        hardened_evidence = dict(evidence)
        hardened_evidence.update(
            {
                "classification_original": "PROVIDER_OUTAGE",
                "classification_hardened": "MEASUREMENT_CAPTURE_FAILURE",
                "classification_basis": "NONZERO_CODEX_PROCESS_EXIT_WITHOUT_STRUCTURED_PROVIDER_EVENT",
            }
        )
        return base._invalid_result(  # noqa: SLF001 - bounded adapter reuse
            request,
            "MEASUREMENT_CAPTURE_FAILURE",
            hardened_evidence,
        )

    return result


def execute_request(
    request: dict[str, Any],
    *,
    expected_cli_version: str | None,
    expected_model: str | None,
    expected_reasoning_effort: str | None,
    workspace_dir: Path | str | None,
    run_command: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    version_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    git_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    raw_jsonl: str | None = None,
    observed_cli_version: str | None = None,
    caveman_policy_content: str | bytes | None = None,
    caveman_policy_path: Path | str | None = None,
    caveman_repo_path: Path | str | None = None,
    presentation_root: Path | str | None = None,
) -> dict[str, Any]:
    """Run the canonical Codex executor behind fail-closed live preflights."""
    workspace = Path(workspace_dir) if workspace_dir is not None else Path("")
    ok, preflight = _git_worktree_preflight(workspace, git_runner=git_runner)
    if not ok:
        evidence = {
            "benchmark_subject": {
                "sha": base.BENCHMARK_SUBJECT_SHA,
                "tree": base.BENCHMARK_SUBJECT_TREE,
            },
            "common_measurement_core_baseline": {
                "sha": base.COMMON_MEASUREMENT_CORE_SHA,
                "tree": base.COMMON_MEASUREMENT_CORE_TREE,
            },
            "taskset_digest": base.TASKSET_DIGEST,
            "host": "codex-cli",
            "transport": base.TRANSPORT_ID,
            "live_execution_authorized_by_adapter": False,
            "workspace_preflight": preflight,
        }
        return base._invalid_result(  # noqa: SLF001 - bounded adapter reuse
            request,
            "CORRUPTED_STARTING_STATE",
            evidence,
        )

    result = base.execute_request(
        request,
        expected_cli_version=expected_cli_version,
        expected_model=expected_model,
        expected_reasoning_effort=expected_reasoning_effort,
        workspace_dir=workspace.resolve(),
        run_command=run_command,
        version_runner=version_runner,
        raw_jsonl=raw_jsonl,
        observed_cli_version=observed_cli_version,
        caveman_policy_content=caveman_policy_content,
        caveman_policy_path=caveman_policy_path,
        caveman_repo_path=caveman_repo_path,
        presentation_root=presentation_root,
    )

    hardened = _reclassify_local_exec_failure(request, result)
    evidence = hardened.get("raw_evidence")
    if isinstance(evidence, dict):
        evidence.setdefault("workspace_preflight", preflight)
    return hardened


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Hardened Codex measurement executor for Orchestra benchmark."
    )
    parser.add_argument("--expected-cli-version", required=True)
    parser.add_argument("--expected-model", required=True)
    parser.add_argument(
        "--expected-reasoning-effort",
        required=True,
        choices=sorted(base.ALLOWED_REASONING_EFFORTS),
    )
    parser.add_argument("--workspace-dir", type=Path, required=True)
    parser.add_argument("--caveman-policy-path", type=Path)
    parser.add_argument("--caveman-repo-path", type=Path)
    parser.add_argument("--presentation-root", type=Path)
    parser.add_argument("--request-file", type=Path)
    parser.add_argument("--output-file", type=Path)
    args = parser.parse_args(argv)

    try:
        request = (
            json.loads(args.request_file.read_text(encoding="utf-8"))
            if args.request_file
            else json.load(sys.stdin)
        )
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": f"cannot load benchmark request: {exc}"}), file=sys.stderr)
        return 2
    if not isinstance(request, dict):
        print(json.dumps({"error": "benchmark request must be a JSON object"}), file=sys.stderr)
        return 2

    result = execute_request(
        request,
        expected_cli_version=args.expected_cli_version,
        expected_model=args.expected_model,
        expected_reasoning_effort=args.expected_reasoning_effort,
        workspace_dir=args.workspace_dir,
        caveman_policy_path=args.caveman_policy_path,
        caveman_repo_path=args.caveman_repo_path,
        presentation_root=args.presentation_root,
    )
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output_file:
        args.output_file.write_text(encoded, encoding="utf-8")
    else:
        sys.stdout.write(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
