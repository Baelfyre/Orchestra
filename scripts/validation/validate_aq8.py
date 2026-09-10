"""Validate the AQ8 machine contract and optional evidence observations."""

# @codebase_provenance_JEO
# @codebase_rights_JEO

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "machine/adaptive/aq8-high-risk-assurance-packs.v1.json"
DEFAULT_SCHEMA = ROOT / "machine/schemas/aq8-high-risk-assurance-packs.v1.schema.json"


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate AQ8 contract parity and optional state-bound observations."
    )
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument(
        "--context",
        type=Path,
        help="Optional JSON AssuranceContext for an executable pack evaluation.",
    )
    parser.add_argument(
        "--observations",
        type=Path,
        help="Optional JSON pack-to-case observations for an executable pack evaluation.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if (args.context is None) != (args.observations is None):
        print("AQ8_RESULT=FAIL")
        print("Both --context and --observations are required together.", file=sys.stderr)
        return 1

    try:
        contract = _read_json(args.contract)
        schema = _read_json(args.schema)
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(contract)

        sys.path.insert(0, str(ROOT))
        from orchestra_runtime.domain.adaptive.high_risk_assurance import (
            AssuranceContext,
            run_all_high_risk_packs,
            validate_aq8_contract,
        )

        validate_aq8_contract(contract)
        print("AQ8_CONTRACT=PASS")

        if args.context is None:
            return 0

        context = AssuranceContext.from_mapping(_read_json(args.context))
        decision = run_all_high_risk_packs(context, _read_json(args.observations))
        print(
            json.dumps(
                {
                    "result": decision.result,
                    "compliant": decision.compliant,
                    "candidate_sha": context.candidate_sha,
                    "tree_sha": context.tree_sha,
                    "transition_owner": decision.transition_owner,
                    "authority_granted": decision.authority_granted,
                    "failure_codes": list(decision.failure_codes),
                    "packs": [
                        {
                            "pack": pack.pack,
                            "result": pack.result,
                            "case_count": len(pack.cases),
                            "controlled_case_count": pack.controlled_case_count,
                            "organic_case_count": pack.organic_case_count,
                            "failure_codes": list(pack.failure_codes),
                        }
                        for pack in decision.packs
                    ],
                    "decision_digest": decision.decision_digest,
                },
                sort_keys=True,
            )
        )
        print(f"AQ8_RESULT={decision.result}")
        return 0 if decision.result == "PASS" else 1
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print("AQ8_CONTRACT=FAIL")
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())