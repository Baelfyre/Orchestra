from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import tomllib
from typing import Any


SCHEMA_VERSION = "orchestra.cosmic-ray-evidence.v1"
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_TOTAL_RE = re.compile(r"total jobs:\s*(\d+)", re.IGNORECASE)
_COMPLETE_RE = re.compile(r"complete:\s*(\d+)\s*\(", re.IGNORECASE)
_SURVIVING_RE = re.compile(r"surviving mutants:\s*(\d+)\s*\(", re.IGNORECASE)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _optional_sha256(path: Path) -> str | None:
    return _sha256(path) if path.is_file() else None


def _git_sha(value: str, field: str) -> str:
    cleaned = str(value or "").strip().lower()
    if _SHA_RE.fullmatch(cleaned) is None:
        raise ValueError(f"{field} must be an exact 40-character Git SHA")
    return cleaned


def _config_scope(config_path: Path) -> tuple[list[str], str]:
    data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    config = data.get("cosmic-ray")
    if not isinstance(config, dict):
        raise ValueError("config missing [cosmic-ray] table")
    raw_modules = config.get("module-path")
    modules = [raw_modules] if isinstance(raw_modules, str) else list(raw_modules or [])
    if not modules or any(not isinstance(item, str) or not item.strip() for item in modules):
        raise ValueError("config module-path must contain non-empty paths")
    if len(modules) != len(set(modules)):
        raise ValueError("config module-path contains duplicate paths")
    test_command = config.get("test-command")
    if not isinstance(test_command, str) or not test_command.strip():
        raise ValueError("config test-command must be non-empty")
    return modules, test_command.strip()


def _extract_count(pattern: re.Pattern[str], text: str) -> int | None:
    match = pattern.search(text)
    return int(match.group(1)) if match else None


def build_evidence(
    *,
    init_output: Path,
    baseline_output: Path,
    exec_output: Path,
    report_output: Path,
    dump_output: Path,
    session_database: Path,
    config_path: Path,
    init_exit_code: int,
    baseline_exit_code: int,
    exec_exit_code: int,
    tool_version: str,
    tested_sha: str,
    source_head_sha: str,
    repository: str,
    workflow_run_id: str,
    workflow_run_attempt: str,
    event_name: str,
    ref_name: str,
) -> dict[str, Any]:
    for path in (init_output, baseline_output, exec_output, report_output, dump_output, config_path):
        if not path.is_file():
            raise ValueError(f"required evidence file missing: {path}")

    version = str(tool_version or "").strip()
    if not version:
        raise ValueError("tool_version must be non-empty")
    repo = str(repository or "").strip()
    if repo.count("/") != 1:
        raise ValueError("repository must use owner/name form")

    modules, test_command = _config_scope(config_path)
    report_text = report_output.read_text(encoding="utf-8", errors="replace")
    total = _extract_count(_TOTAL_RE, report_text)
    complete = _extract_count(_COMPLETE_RE, report_text)
    surviving = _extract_count(_SURVIVING_RE, report_text)

    killed: int | None = None
    score: float | None = None
    score_status = "UNSCORED_TOOL_FAILURE"
    interpretation = "Cosmic Ray did not produce a complete, scoreable mutation session."

    tools_ok = int(init_exit_code) == 0 and int(baseline_exit_code) == 0 and int(exec_exit_code) == 0
    counts_ok = total is not None and complete is not None and surviving is not None
    if tools_ok and counts_ok and total > 0 and complete == total and 0 <= surviving <= total:
        killed = total - surviving
        score = round((killed / total) * 100.0, 2)
        score_status = "VALID_SCORE"
        interpretation = "Complete bounded mutation pilot. Score is evidence for the configured pilot scope only."
    elif tools_ok and counts_ok:
        score_status = "UNSCORED_INCOMPLETE"
        interpretation = "Cosmic Ray completed its commands but the mutation session was incomplete or contained no scoreable jobs."

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "repository": repo,
        "tested_sha": _git_sha(tested_sha, "tested_sha"),
        "source_head_sha": _git_sha(source_head_sha, "source_head_sha"),
        "workflow": {
            "run_id": str(workflow_run_id or "").strip(),
            "run_attempt": str(workflow_run_attempt or "").strip(),
            "event_name": str(event_name or "").strip(),
            "ref_name": str(ref_name or "").strip(),
        },
        "tool": {"name": "cosmic-ray", "version": version},
        "scope": {
            "modules": modules,
            "test_command": test_command,
            "configuration": config_path.name,
            "pilot": True,
        },
        "execution": {
            "init_exit_code": int(init_exit_code),
            "baseline_exit_code": int(baseline_exit_code),
            "exec_exit_code": int(exec_exit_code),
            "score_status": score_status,
            "interpretation": interpretation,
        },
        "mutation_summary": {
            "total_jobs": total,
            "complete_jobs": complete,
            "surviving_mutants": surviving,
            "killed_mutants": killed,
            "mutation_score_percent": score,
        },
        "reports": {
            "init_output": init_output.name,
            "init_output_sha256": _sha256(init_output),
            "baseline_output": baseline_output.name,
            "baseline_output_sha256": _sha256(baseline_output),
            "exec_output": exec_output.name,
            "exec_output_sha256": _sha256(exec_output),
            "report_output": report_output.name,
            "report_output_sha256": _sha256(report_output),
            "dump_output": dump_output.name,
            "dump_output_sha256": _sha256(dump_output),
            "session_database": session_database.name,
            "session_database_sha256": _optional_sha256(session_database),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build machine-readable Cosmic Ray mutation evidence")
    parser.add_argument("--init-output", type=Path, required=True)
    parser.add_argument("--baseline-output", type=Path, required=True)
    parser.add_argument("--exec-output", type=Path, required=True)
    parser.add_argument("--report-output", type=Path, required=True)
    parser.add_argument("--dump-output", type=Path, required=True)
    parser.add_argument("--session-database", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--init-exit-code", type=int, required=True)
    parser.add_argument("--baseline-exit-code", type=int, required=True)
    parser.add_argument("--exec-exit-code", type=int, required=True)
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

    evidence = build_evidence(
        init_output=args.init_output,
        baseline_output=args.baseline_output,
        exec_output=args.exec_output,
        report_output=args.report_output,
        dump_output=args.dump_output,
        session_database=args.session_database,
        config_path=args.config,
        init_exit_code=args.init_exit_code,
        baseline_exit_code=args.baseline_exit_code,
        exec_exit_code=args.exec_exit_code,
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
    print(json.dumps({
        "score_status": evidence["execution"]["score_status"],
        "mutation_score_percent": evidence["mutation_summary"]["mutation_score_percent"],
        "tested_sha": evidence["tested_sha"],
        "source_head_sha": evidence["source_head_sha"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
