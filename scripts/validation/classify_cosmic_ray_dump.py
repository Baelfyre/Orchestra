from __future__ import annotations

import argparse
import ast
from collections import Counter
import json
from pathlib import Path
import re
from typing import Any


SCHEMA_VERSION = "orchestra.cosmic-ray-classification.v1"
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_JOB_ID_RE = re.compile(r"^[0-9a-f]{32}$")
_BITOR_PREFIX = "core/ReplaceBinaryOperator_BitOr_"
_KILLED = "KILLED"
_SURVIVED = "SURVIVED"


def _git_sha(value: str) -> str:
    cleaned = str(value or "").strip().lower()
    if _SHA_RE.fullmatch(cleaned) is None:
        raise ValueError("source_head_sha must be an exact 40-character Git SHA")
    return cleaned


def _job_id(value: Any, line_number: int) -> str:
    if not isinstance(value, str):
        raise ValueError(f"dump line {line_number} has invalid job_id")
    cleaned = value.strip().lower()
    if _JOB_ID_RE.fullmatch(cleaned) is None:
        raise ValueError(f"dump line {line_number} has invalid job_id")
    return cleaned


def _annotation_bit_or_positions(tree: ast.AST) -> set[tuple[int, int]]:
    positions: set[tuple[int, int]] = set()

    def collect(node: ast.AST | None) -> None:
        if node is None:
            return
        for descendant in ast.walk(node):
            if isinstance(descendant, ast.BinOp) and isinstance(descendant.op, ast.BitOr):
                positions.add((descendant.lineno, descendant.col_offset))

    for node in ast.walk(tree):
        if isinstance(node, ast.arg):
            collect(node.annotation)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            collect(node.returns)
        elif isinstance(node, ast.AnnAssign):
            collect(node.annotation)
    return positions


def _module_bit_or_profile(source_path: Path) -> tuple[bool, int, int]:
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(source_path))
    postponed = any(
        isinstance(node, ast.ImportFrom)
        and node.module == "__future__"
        and any(alias.name == "annotations" for alias in node.names)
        for node in tree.body
    )
    annotation_positions = _annotation_bit_or_positions(tree)
    all_positions = {
        (node.lineno, node.col_offset)
        for node in ast.walk(tree)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr)
    }
    runtime_positions = all_positions - annotation_positions
    return postponed, len(annotation_positions), len(runtime_positions)


def _parse_dump_line(raw_line: str, line_number: int) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        payload = json.loads(raw_line)
    except json.JSONDecodeError as exc:
        raise ValueError(f"dump line {line_number} is not valid JSON") from exc
    if not isinstance(payload, list) or len(payload) != 2:
        raise ValueError(f"dump line {line_number} must be a two-object JSON array")
    spec, result = payload
    if not isinstance(spec, dict) or not isinstance(result, dict):
        raise ValueError(f"dump line {line_number} must contain object spec/result values")
    mutations = spec.get("mutations")
    if not isinstance(mutations, list) or len(mutations) != 1 or not isinstance(mutations[0], dict):
        raise ValueError(f"dump line {line_number} must describe exactly one mutation")
    return spec, result


def _bit_or_is_proven_annotation_only(
    *,
    module_path: str,
    repository_root: Path,
    module_profiles: dict[str, tuple[bool, int, int]],
) -> bool:
    if module_path not in module_profiles:
        source_path = (repository_root / module_path).resolve()
        root = repository_root.resolve()
        try:
            source_path.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"mutation module_path escapes repository root: {module_path}") from exc
        if not source_path.is_file():
            raise ValueError(f"mutation source module does not exist: {module_path}")
        module_profiles[module_path] = _module_bit_or_profile(source_path)
    postponed, annotation_count, runtime_count = module_profiles[module_path]
    return postponed and annotation_count > 0 and runtime_count == 0


def classify_dump(*, dump_path: Path, repository_root: Path, source_head_sha: str) -> dict[str, Any]:
    if not dump_path.is_file():
        raise ValueError("Cosmic Ray dump file does not exist")
    if not repository_root.is_dir():
        raise ValueError("repository_root must be a directory")

    source_sha = _git_sha(source_head_sha)
    jobs: list[dict[str, Any]] = []
    raw_outcomes: Counter[str] = Counter()
    excluded: Counter[str] = Counter()
    module_profiles: dict[str, tuple[bool, int, int]] = {}

    lines = [line for line in dump_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return {
            "schema_version": SCHEMA_VERSION,
            "source_head_sha": source_sha,
            "raw": {"total": 0, "killed": 0, "survived": 0, "other": 0},
            "runtime_relevant": {"total": 0, "killed": 0, "survived": 0, "score_percent": None},
            "excluded_equivalent": {"count": 0, "classifications": {}},
            "jobs": [],
            "score_status": "UNSCORED_EMPTY",
        }

    seen_job_ids: set[str] = set()
    for line_number, raw_line in enumerate(lines, start=1):
        spec, result = _parse_dump_line(raw_line, line_number)
        job_id = _job_id(spec.get("job_id"), line_number)
        if job_id in seen_job_ids:
            raise ValueError(f"duplicate Cosmic Ray job_id {job_id}")
        seen_job_ids.add(job_id)

        mutation = spec["mutations"][0]
        module_path = mutation.get("module_path")
        operator_name = mutation.get("operator_name")
        worker_outcome = result.get("worker_outcome")
        test_outcome = result.get("test_outcome")
        if not isinstance(module_path, str) or not module_path.strip():
            raise ValueError(f"dump line {line_number} has invalid module_path")
        if not isinstance(operator_name, str) or not operator_name.strip():
            raise ValueError(f"dump line {line_number} has invalid operator_name")
        if not isinstance(worker_outcome, str) or not worker_outcome.strip():
            raise ValueError(f"dump line {line_number} has invalid worker_outcome")
        if not isinstance(test_outcome, str) or not test_outcome.strip():
            raise ValueError(f"dump line {line_number} has invalid test_outcome")
        module_path = module_path.strip().replace("\\", "/")
        operator_name = operator_name.strip()
        worker_outcome = worker_outcome.strip().upper()
        test_outcome = test_outcome.strip().upper()
        raw_outcomes[test_outcome] += 1

        classification: str
        rationale: str
        if test_outcome in {_KILLED, _SURVIVED} and operator_name.startswith(_BITOR_PREFIX) and _bit_or_is_proven_annotation_only(
            module_path=module_path,
            repository_root=repository_root,
            module_profiles=module_profiles,
        ):
            classification = "NON_RUNTIME_POSTPONED_ANNOTATION"
            rationale = (
                "BitOr mutation is confined to annotations in a module using "
                "from __future__ import annotations; AST analysis found no runtime BitOr expression."
            )
            excluded[classification] += 1
        elif test_outcome == _KILLED:
            classification = "RUNTIME_RELEVANT_KILLED"
            rationale = "Mutation was killed by the configured test command."
        elif test_outcome == _SURVIVED:
            classification = "RUNTIME_RELEVANT_SURVIVED"
            rationale = "Mutation survived and is runtime-relevant unless explicitly proven equivalent."
        else:
            classification = "UNRECOGNIZED_OUTCOME"
            rationale = f"Test outcome {test_outcome!r} is not KILLED or SURVIVED; score must fail closed."

        jobs.append(
            {
                "job_id": job_id,
                "module_path": module_path,
                "operator_name": operator_name,
                "worker_outcome": worker_outcome,
                "test_outcome": test_outcome,
                "classification": classification,
                "rationale": rationale,
            }
        )

    raw_killed = raw_outcomes[_KILLED]
    raw_survived = raw_outcomes[_SURVIVED]
    raw_other = sum(count for outcome, count in raw_outcomes.items() if outcome not in {_KILLED, _SURVIVED})
    runtime_killed = sum(1 for job in jobs if job["classification"] == "RUNTIME_RELEVANT_KILLED")
    runtime_survived = sum(1 for job in jobs if job["classification"] == "RUNTIME_RELEVANT_SURVIVED")
    runtime_total = runtime_killed + runtime_survived
    score = round((runtime_killed / runtime_total) * 100.0, 2) if runtime_total else None
    if raw_other:
        score_status = "UNSCORED_UNKNOWN_OUTCOME"
        score = None
    elif runtime_total:
        score_status = "VALID_RUNTIME_RELEVANT_SCORE"
    else:
        score_status = "UNSCORED_EMPTY"

    return {
        "schema_version": SCHEMA_VERSION,
        "source_head_sha": source_sha,
        "raw": {
            "total": len(jobs),
            "killed": raw_killed,
            "survived": raw_survived,
            "other": raw_other,
        },
        "runtime_relevant": {
            "total": runtime_total,
            "killed": runtime_killed,
            "survived": runtime_survived,
            "score_percent": score,
        },
        "excluded_equivalent": {
            "count": sum(excluded.values()),
            "classifications": dict(sorted(excluded.items())),
        },
        "jobs": jobs,
        "score_status": score_status,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Classify Cosmic Ray mutation outcomes conservatively")
    parser.add_argument("--dump", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--source-head-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    classification = classify_dump(
        dump_path=args.dump,
        repository_root=args.repository_root,
        source_head_sha=args.source_head_sha,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(classification, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "score_status": classification["score_status"],
        "raw": classification["raw"],
        "runtime_relevant": classification["runtime_relevant"],
        "excluded_equivalent": classification["excluded_equivalent"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
