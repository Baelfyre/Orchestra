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


MUTATION_EVIDENCE_SCHEMA_VERSION = "orchestra.mutation-evidence.v2"
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_RESULT_RE = re.compile(r"^\s*(?P<mutant>\S+):\s*(?P<status>.+?)\s*$")
_MUTANT_SUFFIX_RE = re.compile(r"__mutmut_\d+$")
_TARGET_OUTCOME_RE = re.compile(r"^\s*(?P<icon>🎉|🙁|🫥|⏰|🤔|🔇|🧙)\s+(?P<mutant>\S+)\s*$")
_FATAL_RUN_MARKERS = (
    "failed to collect stats",
    "failed to collect stats, no active tests found",
    "stopping early, because we could not find any test case for any mutant",
)
_ALLOWED_RESULT_STATUSES = frozenset({"survived", "killed"})


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


def _parse_path_spec(raw: str, field: str) -> tuple[str, Path]:
    pattern, separator, path_text = str(raw or "").partition("=")
    pattern = pattern.strip()
    path_text = path_text.strip()
    if not separator or not pattern or not path_text:
        raise ValueError(f"{field} must use PATTERN=PATH form")
    return pattern, Path(path_text)


def _spec_map(specs: list[str], field: str) -> dict[str, Path]:
    if not specs:
        raise ValueError(f"at least one {field} is required")
    mapped: dict[str, Path] = {}
    for raw in specs:
        pattern, path = _parse_path_spec(raw, field)
        if pattern in mapped:
            raise ValueError(f"duplicate mutation target pattern in {field}: {pattern}")
        if not path.is_file():
            raise ValueError(f"{field} file does not exist: {path}")
        mapped[pattern] = path
    return mapped


def _target_run_outcomes(path: Path, pattern: str) -> dict[str, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    folded = text.casefold()
    fatal_markers = [marker for marker in _FATAL_RUN_MARKERS if marker in folded]
    if fatal_markers:
        raise ValueError(f"target mutation run {pattern} contains fatal instrumentation marker: {fatal_markers[0]}")

    outcomes: dict[str, str] = {}
    for line in text.splitlines():
        match = _TARGET_OUTCOME_RE.match(line)
        if match is None:
            continue
        mutant = match.group("mutant").strip()
        normalized = _normalize_mutant_identifier(mutant)
        if not fnmatchcase(normalized, pattern):
            continue
        icon = match.group("icon")
        outcome = "killed" if icon == "🎉" else "survived" if icon == "🙁" else f"non_classified:{icon}"
        previous = outcomes.get(mutant)
        if previous is not None and previous != outcome:
            raise ValueError(f"target mutation run {pattern} reports conflicting outcomes for {mutant}")
        outcomes[mutant] = outcome

    if not outcomes:
        raise ValueError(f"target mutation run {pattern} contains no classified target mutants")
    non_classified = sorted({outcome for outcome in outcomes.values() if outcome.startswith("non_classified:")})
    if non_classified:
        raise ValueError(
            f"target mutation run {pattern} contains non-classified outcomes: " + ", ".join(non_classified)
        )
    return outcomes


def _target_result_records(path: Path, pattern: str) -> dict[str, str]:
    records: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = _RESULT_RE.match(line)
        if match is None:
            continue
        mutant = match.group("mutant").strip()
        if not fnmatchcase(_normalize_mutant_identifier(mutant), pattern):
            continue
        status = match.group("status").strip().casefold()
        previous = records.get(mutant)
        if previous is not None and previous != status:
            raise ValueError(f"target mutation results {pattern} contain conflicting status for {mutant}")
        records[mutant] = status
    return records


def _build_target_summaries(target_run_specs: list[str], target_result_specs: list[str]) -> list[dict[str, Any]]:
    run_paths = _spec_map(target_run_specs, "target_run")
    result_paths = _spec_map(target_result_specs, "target_result")
    if run_paths.keys() != result_paths.keys():
        missing_results = sorted(run_paths.keys() - result_paths.keys())
        missing_runs = sorted(result_paths.keys() - run_paths.keys())
        raise ValueError(
            f"target run/result patterns differ; missing_results={missing_results}, missing_runs={missing_runs}"
        )

    summaries: list[dict[str, Any]] = []
    for pattern, run_path in run_paths.items():
        result_path = result_paths[pattern]
        outcomes = _target_run_outcomes(run_path, pattern)
        result_records = _target_result_records(result_path, pattern)
        result_status_counts = Counter(result_records.values())
        invalid_statuses = sorted(status for status in result_status_counts if status not in _ALLOWED_RESULT_STATUSES)
        if invalid_statuses:
            raise ValueError(
                f"target mutation results {pattern} contain non-classified statuses: " + ", ".join(invalid_statuses)
            )

        survived_ids = {mutant for mutant, outcome in outcomes.items() if outcome == "survived"}
        killed_ids = {mutant for mutant, outcome in outcomes.items() if outcome == "killed"}
        result_survived_ids = {mutant for mutant, status in result_records.items() if status == "survived"}
        result_killed_ids = {mutant for mutant, status in result_records.items() if status == "killed"}
        if result_survived_ids != survived_ids:
            raise ValueError(f"target mutation results {pattern} do not reconcile with run-output survivors")
        if not result_killed_ids.issubset(killed_ids):
            raise ValueError(f"target mutation results {pattern} contain killed records absent from run output")

        total = len(outcomes)
        killed = len(killed_ids)
        survived = len(survived_ids)
        summaries.append(
            {
                "pattern": pattern,
                "total": total,
                "killed": killed,
                "survived": survived,
                "score_percent": round((killed / total) * 100.0, 2),
                "run_output": run_path.name,
                "run_output_sha256": _sha256(run_path),
                "results_output": result_path.name,
                "results_output_sha256": _sha256(result_path),
                "result_status_counts": dict(sorted(result_status_counts.items())),
            }
        )
    return summaries


def build_mutation_evidence(
    *,
    run_output: Path,
    results_output: Path,
    config_path: Path,
    target_run_specs: list[str],
    target_result_specs: list[str],
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
    for path in (run_output, results_output, config_path):
        if not path.is_file():
            raise ValueError(f"required mutation evidence file missing: {path}")
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

    target_runs = _build_target_summaries(target_run_specs, target_result_specs)
    target_total = sum(int(item["total"]) for item in target_runs)
    killed_count = sum(int(item["killed"]) for item in target_runs)
    survived_count = sum(int(item["survived"]) for item in target_runs)
    if target_total <= 0 or target_total != killed_count + survived_count:
        raise ValueError("target mutation counts are empty or do not reconcile")
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
            "mutant_patterns": [item["pattern"] for item in target_runs],
            "target_runs": target_runs,
            "configuration": config_path.name,
            "mutate_only_covered_lines": _read_bool_config(config_path, "mutate_only_covered_lines"),
            "max_stack_depth": _read_int_config(config_path, "max_stack_depth"),
        },
        "execution": {
            "run_exit_code": int(run_exit_code),
            "score_status": "VALID_CLASSIFIED_SCORE",
            "classification_status": "COMPLETE",
            "target_mutant_total": target_total,
            "target_killed_count": killed_count,
            "target_survived_count": survived_count,
            "target_score_percent": score_percent,
            "not_checked_count": 0,
            "interpretation": (
                "Every declared LEGACY_RETIRED target completed on the exact source head. Mutmut run output and "
                "the immediately captured per-target results reconcile for all survivors, with no target-level "
                "not-checked, interrupted, timeout, suspicious, skipped, or unknown outcome accepted. The score "
                "is a classified confidence measure; no new numeric acceptance threshold is introduced."
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
    parser.add_argument("--target-run", action="append", dest="target_run_specs", default=[])
    parser.add_argument("--target-result", action="append", dest="target_result_specs", default=[])
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
        target_result_specs=args.target_result_specs,
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
