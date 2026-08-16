from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any


MUTATION_EVIDENCE_SCHEMA_VERSION = "orchestra.mutation-evidence.v1"
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_RESULT_RE = re.compile(r"^\s*(?P<mutant>\S+):\s*(?P<status>.+?)\s*$")
_FATAL_RUN_MARKERS = (
    "failed to collect stats",
    "failed to collect stats, no active tests found",
    "stopping early, because we could not find any test case for any mutant",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_sha(value: str, field: str) -> str:
    cleaned = str(value or "").strip().lower()
    if _SHA_RE.fullmatch(cleaned) is None:
        raise ValueError(f"{field} must be an exact 40-character Git SHA")
    return cleaned


def _read_modules(config_path: Path) -> list[str]:
    lines = config_path.read_text(encoding="utf-8").splitlines()
    modules: list[str] = []
    collecting = False
    for line in lines:
        stripped = line.strip()
        if stripped == "only_mutate=":
            collecting = True
            continue
        if collecting:
            if not line.startswith((" ", "\t")) or not stripped:
                break
            modules.append(stripped)
    if not modules:
        raise ValueError("mutation configuration contains no only_mutate entries")
    if len(modules) != len(set(modules)):
        raise ValueError("mutation scope contains duplicate modules")
    return modules


def _read_mutant_statuses(results_output: Path) -> list[str]:
    statuses: list[str] = []
    for line in results_output.read_text(encoding="utf-8", errors="replace").splitlines():
        match = _RESULT_RE.match(line)
        if match is None:
            continue
        statuses.append(match.group("status").strip().casefold())
    if not statuses:
        raise ValueError("mutation results contain no mutant classification records")
    return statuses


def build_mutation_evidence(
    *,
    run_output: Path,
    results_output: Path,
    config_path: Path,
    run_exit_code: int,
    tool_version: str,
    tested_sha: str,
    source_head_sha: str,
    repository: str,
    workflow_run_id: str,
    workflow_run_attempt: str,
    event_name: str,
    ref_name: str,
) -> dict[str, Any]:
    if not run_output.is_file() or not results_output.is_file():
        raise ValueError("mutation raw output files must exist")
    version = str(tool_version or "").strip()
    if not version:
        raise ValueError("tool_version must be non-empty")
    repo = str(repository or "").strip()
    if "/" not in repo:
        raise ValueError("repository must use owner/name form")

    tested = _git_sha(tested_sha, "tested_sha")
    source_head = _git_sha(source_head_sha, "source_head_sha")
    if tested != source_head:
        raise ValueError("tested_sha must exactly match source_head_sha")
    if int(run_exit_code) != 0:
        raise ValueError(f"mutation execution failed with exit code {int(run_exit_code)}")

    run_text = run_output.read_text(encoding="utf-8", errors="replace").casefold()
    fatal_markers = [marker for marker in _FATAL_RUN_MARKERS if marker in run_text]
    if fatal_markers:
        raise ValueError(f"mutation execution contains fatal instrumentation marker: {fatal_markers[0]}")

    statuses = _read_mutant_statuses(results_output)
    status_counts = Counter(statuses)
    not_checked_count = status_counts.get("not checked", 0)
    interrupted_count = status_counts.get("check was interrupted by user", 0)
    if not_checked_count:
        raise ValueError(f"mutation results contain {not_checked_count} not checked mutants")
    if interrupted_count:
        raise ValueError(f"mutation results contain {interrupted_count} interrupted mutants")

    return {
        "schema_version": MUTATION_EVIDENCE_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "repository": repo,
        "tested_sha": tested,
        "source_head_sha": source_head,
        "workflow": {
            "run_id": str(workflow_run_id or "").strip(),
            "run_attempt": str(workflow_run_attempt or "").strip(),
            "event_name": str(event_name or "").strip(),
            "ref_name": str(ref_name or "").strip(),
        },
        "tool": {"name": "mutmut", "version": version},
        "scope": {
            "modules": _read_modules(config_path),
            "configuration": config_path.name,
            "mutate_only_covered_lines": True,
            "max_stack_depth": 8,
        },
        "execution": {
            "run_exit_code": int(run_exit_code),
            "score_status": "UNSCORED_BASELINE",
            "classification_status": "COMPLETE",
            "result_record_count": len(statuses),
            "not_checked_count": not_checked_count,
            "status_counts": dict(sorted(status_counts.items())),
            "interpretation": (
                "Mutmut completed on the exact source head and every reported mutant record was classified. "
                "This remains an unscored baseline; surviving or suspicious mutants remain explicit confidence findings."
            ),
        },
        "reports": {
            "run_output": run_output.name,
            "run_output_sha256": _sha256(run_output),
            "results_output": results_output.name,
            "results_output_sha256": _sha256(results_output),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build Orchestra mutation evidence baseline")
    parser.add_argument("--run-output", type=Path, required=True)
    parser.add_argument("--results-output", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=Path("setup.cfg"))
    parser.add_argument("--run-exit-code", type=int, required=True)
    parser.add_argument("--tool-version", required=True)
    parser.add_argument("--tested-sha", required=True)
    parser.add_argument("--source-head-sha", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--workflow-run-id", required=True)
    parser.add_argument("--workflow-run-attempt", required=True)
    parser.add_argument("--event-name", required=True)
    parser.add_argument("--ref-name", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    evidence = build_mutation_evidence(
        run_output=args.run_output,
        results_output=args.results_output,
        config_path=args.config,
        run_exit_code=args.run_exit_code,
        tool_version=args.tool_version,
        tested_sha=args.tested_sha,
        source_head_sha=args.source_head_sha,
        repository=args.repository,
        workflow_run_id=args.workflow_run_id,
        workflow_run_attempt=args.workflow_run_attempt,
        event_name=args.event_name,
        ref_name=args.ref_name,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "tested_sha": evidence["tested_sha"],
                "source_head_sha": evidence["source_head_sha"],
                "run_exit_code": evidence["execution"]["run_exit_code"],
                "score_status": evidence["execution"]["score_status"],
                "classification_status": evidence["execution"]["classification_status"],
                "result_record_count": evidence["execution"]["result_record_count"],
                "not_checked_count": evidence["execution"]["not_checked_count"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
