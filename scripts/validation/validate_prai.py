#!/usr/bin/env python3
"""Validate one PRAI work-unit receipt against current repository identity."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from orchestra_runtime.domain.adaptive.prai import (  # noqa: E402
    PraiWorkUnit,
    evaluate_post_run_assurance,
    validate_prai_contract,
    validate_schema_runtime_parity,
)


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument("--work-unit", type=Path, required=True)
    value.add_argument("--repository", required=True)
    value.add_argument("--source-ref", required=True)
    value.add_argument("--candidate-sha", required=True)
    value.add_argument("--tree-sha", required=True)
    value.add_argument("--work-item-ref", required=True)
    value.add_argument("--freshness-ref", required=True)
    value.add_argument(
        "--contract",
        type=Path,
        default=ROOT / "machine" / "adaptive" / "prai-post-run-assurance.v1.json",
    )
    value.add_argument(
        "--schema",
        type=Path,
        default=ROOT / "machine" / "schemas" / "prai-post-run-assurance.v1.schema.json",
    )
    value.add_argument("--output", type=Path)
    return value


def main() -> int:
    args = parser().parse_args()
    try:
        contract = read_json(args.contract)
        validate_prai_contract(contract)
        validate_schema_runtime_parity(contract)
        work = PraiWorkUnit.from_mapping(read_json(args.work_unit))
        decision = evaluate_post_run_assurance(
            work,
            current_repository=args.repository,
            current_source_ref=args.source_ref,
            current_candidate_sha=args.candidate_sha,
            current_tree_sha=args.tree_sha,
            current_work_item_ref=args.work_item_ref,
            current_freshness_ref=args.freshness_ref,
        )
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print("PRAI_RESULT=INVALID", file=sys.stderr)
        print(f"PRAI_ERROR={type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    rendered = json.dumps(decision.to_dict(), indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    print(f"PRAI_RESULT={decision.result}")
    print("PRAI_FAILURE_CODES=" + ",".join(decision.failure_codes))
    return 0 if decision.compliant else 1


if __name__ == "__main__":
    raise SystemExit(main())
