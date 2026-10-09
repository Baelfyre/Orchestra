#!/usr/bin/env python3
"""Validate one AQ-6 coverage manifest against current execution evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from orchestra_runtime.domain.adaptive.gate_coverage import (  # noqa: E402
    evaluate_gate_coverage,
    validate_gate_coverage_contract,
)


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument("--manifest", type=Path, required=True)
    value.add_argument("--executions", type=Path, required=True)
    value.add_argument("--repository", required=True)
    value.add_argument("--source-ref", required=True)
    value.add_argument("--candidate-sha", required=True)
    value.add_argument("--tree-sha", required=True)
    value.add_argument("--work-item-ref", required=True)
    value.add_argument("--available-test", action="append", default=[])
    value.add_argument("--workflow", action="append", type=Path, default=[])
    value.add_argument("--test-coverage", type=Path)
    value.add_argument(
        "--contract",
        type=Path,
        default=ROOT / "machine" / "adaptive" / "aq6-gate-coverage.v1.json",
    )
    value.add_argument("--output", type=Path)
    return value


def main() -> int:
    args = parser().parse_args()
    try:
        contract = read_json(args.contract)
        manifest = read_json(args.manifest)
        executions = read_json(args.executions)
        validate_gate_coverage_contract(contract)
        workflows = {
            path.as_posix(): path.read_text(encoding="utf-8")
            for path in args.workflow
        }
        coverage = read_json(args.test_coverage) if args.test_coverage else {}
        decision = evaluate_gate_coverage(
            manifest,
            executions,
            current_repository=args.repository,
            current_source_ref=args.source_ref,
            current_candidate_sha=args.candidate_sha,
            current_tree_sha=args.tree_sha,
            current_work_item_ref=args.work_item_ref,
            available_test_ids=args.available_test,
            workflow_texts=workflows,
            test_coverage=coverage,
        )
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print("AQ6_RESULT=INVALID", file=sys.stderr)
        print(f"AQ6_ERROR={type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    rendered = json.dumps(decision.to_dict(), indent=2, sort_keys=True) + chr(10)
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    print(f"AQ6_RESULT={decision.result}")
    print("AQ6_FAILURE_CODES=" + ",".join(decision.failure_codes))
    return 0 if decision.compliant else 1


if __name__ == "__main__":
    raise SystemExit(main())
