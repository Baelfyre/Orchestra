from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from fnmatch import fnmatchcase
import hashlib
import json
from pathlib import Path
import re
from typing import Any


MUTATION_EVIDENCE_SCHEMA_VERSION = "orchestra.mutation-evidence.v1"
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_RESULT_RE = re.compile(r"^\s*(?P<mutant>\S+):\s*(?P<status>.+?)\s*$")
_MUTANT_SUFFIX_RE = re.compile(r"__mutmut_\d+$")
_PROGRESS_RE = re.compile(r"(?P<done>\d+)\s*/\s*(?P<total>\d+)")
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


def _config_lines(config_path: Path) -> list[str]:
    return config_path.read_text(encoding="utf-8").splitlines()


def _read_modules(config_path: Path) -> list[str]:
    lines = _config_lines(config_path)
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


def _read_config_value(config_path: Path, key: str) -> str:
    prefix = f"{key}="
    for line in _config_lines(config_path):
        stripped = line.strip()
        if stripped.startswith(prefix):
            return stripped[len(prefix) :].strip()
    raise ValueError(f"mutation configuration is missing {key}")


def _read_bool_config(config_path: Path, key: str) -> bool:
    value = _read_config_value(config_path, key).casefold()
    if value == "true":
        return True
    if value == "false":
        return False
    raise ValueError(f"mutation configuration {key} must be true or false")


def _read_int_config(config_path: Path, key: str) -> int:
    value = _read_config_value(config_path, key)
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"mutation configuration {key} must be an integer") from exc


def _normalize_mutant_identifier(identifier: str) -> str:
    normalized = _MUTANT_SUFFIX_RE.sub("", identifier.strip())
    if ".xǁ" in normalized:
        normalized = normalized.replace(".xǁ", ".", 1).replace("ǁ", ".")
    elif ".x_" in normalized:
        normalized = normalized.replace(".x_", ".", 1)
    return normalized


def _parse_result_records(results_output: Path) -> list[tuple[str, str]]:
    records: list[tuple[str, str]] = []
    for line in results_output.read_text(encoding="utf-8", errors="replace").splitlines():
        match = _RESULT_RE.match(line)
        if match is None:
            continue
        records.append(
            (
                _normalize_mutant_identifier(match.group("mutant")),
                match.group("status").strip().casefold(),
            )
        )
    return records


def _parse_target_run_spec(raw: str) -> tuple[str, Path]:
    pattern, separator, path_text = str(raw or "").partition("=")
    pattern = pattern.strip()
    path_text = path_text.strip()
    if not separator or not pattern or not path_text:
        raise ValueError("target_run must use PATTERN=PATH form")
    return pattern, Path(path_text)


def _read_target_runs(target_run_specs: list[str]) -> list[dict[str, Any]]:
    if not target_run_specs:
        raise ValueError("at least one target_run is required")
    summaries: list[dict[str, Any]] = []
    seen_patterns: set[str] = set()
    for raw_spec in target_run_specs:
        pattern, path = _parse_target_run_spec(raw_spec)
        if pattern in seen_patterns:
            raise ValueError(f"duplicate mutation target pattern: {pattern}")
        seen_patterns.add(pattern)
        if not path.is_file():
            raise ValueError(f"target mutation run output does not exist: {path}")
        text = path.read_text(encoding="utf-8", errors="replace")
        folded = text.casefold()
        fatal_markers = [marker for marker in _FATAL_RUN_MARKERS if marker in folded]
        if fatal_markers:
            raise ValueError(
                f"target mutation run {pattern} contains fatal instrumentation marker: {fatal_markers[0]}"
            )
        progress = list(_PROGRESS_RE.finditer(text))
        if not progress:
            raise ValueError(f"target mutation run {pattern} contains no completion count")
        done = int(progress[-1].group("done"))
        total = int(progress[-1].group("total"))
        if total <= 0:
            raise ValueError(f"target mutation run {pattern} executed zero mutants")
        if done != total:
            raise ValueError(
                f"target mutation run {pattern} incomplete: completed {done} of {total} mutants"
            )
        summaries.append(
            {
                "pattern": pattern,
                "completed": done,
                "total": total,
                "output": path.name,
                "output_sha256": _sha256(path),
            }
        )
    return summaries


def build_mutation_evidence(
    *,
    run_output: Path,
    results_output: Path,
    config_path: Path,
    target_run_specs: list[str],
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

    target_runs = _read_target_runs(target_run_specs)
    patterns = [item["pattern"] for item in target_runs]
    all_records = _parse_result_records(results_output)
    scoped_records = [
        (identifier, status)
        for identifier, status in all_records
        if any(fnmatchcase(identifier, pattern) for pattern in patterns)
    ]
    scoped_status_counts = Counter(status for _, status in scoped_records)
    not_checked_count = scoped_status_counts.get("not checked", 0)
    interrupted_count = scoped_status_counts.get("check was interrupted by user", 0)
    if not_checked_count:
        raise ValueError(f"scoped mutation results contain {not_checked_count} not checked mutants")
    if interrupted_count:
        raise ValueError(f"scoped mutation results contain {interrupted_count} interrupted mutants")

    unexpected_statuses = sorted(status for status in scoped_status_counts if status != "survived")
    if unexpected_statuses:
        raise ValueError(
            "scoped mutation results contain non-classified outcomes: " + ", ".join(unexpected_statuses)
        )

    target_total = sum(int(item["total"]) for item in target_runs)
    survived_count = scoped_status_counts.get("survived", 0)
    if survived_count > target_total:
        raise ValueError("scoped survivor count exceeds executed target mutant count")
    killed_count = target_total - survived_count
    score_percent = round((killed_count / target_total) * 100.0, 2)

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
            "mutant_patterns": patterns,
            "target_runs": target_runs,
            "configuration": config_path.name,
            "mutate_only_covered_lines": _read_bool_config(config_path, "mutate_only_covered_lines"),
            "max_stack_depth": _read_int_config(config_path, "max_stack_depth"),
        },
        "execution": {
            "run_exit_code": int(run_exit_code),
            "score_status": "UNSCORED_BASELINE",
            "classification_status": "COMPLETE",
            "target_mutant_total": target_total,
            "target_killed_count": killed_count,
            "target_survived_count": survived_count,
            "target_score_percent": score_percent,
            "scoped_result_record_count": len(scoped_records),
            "out_of_scope_result_record_count": len(all_records) - len(scoped_records),
            "not_checked_count": not_checked_count,
            "status_counts": dict(sorted(scoped_status_counts.items())),
            "interpretation": (
                "Mutmut completed every declared LEGACY_RETIRED target pattern on the exact source head. "
                "Scoped non-killed results contain only survived mutants; no scoped not-checked, interrupted, "
                "timeout, suspicious, or unknown outcome is accepted. The percentage is diagnostic and no "
                "numeric acceptance threshold is introduced by this bounded evidence."
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
    parser = argparse.ArgumentParser(description="Build Orchestra bounded mutation evidence")
    parser.add_argument("--run-output", type=Path, required=True)
    parser.add_argument("--results-output", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=Path("setup.cfg"))
    parser.add_argument(
        "--target-run",
        action="append",
        dest="target_run_specs",
        default=[],
        help="Required bounded Mutmut target in PATTERN=PATH form; repeat for each target pattern.",
    )
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
        target_run_specs=args.target_run_specs,
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
                "target_mutant_total": evidence["execution"]["target_mutant_total"],
                "target_killed_count": evidence["execution"]["target_killed_count"],
                "target_survived_count": evidence["execution"]["target_survived_count"],
                "target_score_percent": evidence["execution"]["target_score_percent"],
                "not_checked_count": evidence["execution"]["not_checked_count"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
