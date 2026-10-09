"""CLI adapter for the pure AQ-5 QA-compliance evaluator."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from orchestra_runtime.domain.adaptive.qa_compliance import evaluate_qa_compliance


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--receipts", required=True, type=Path)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--source-ref", required=True)
    parser.add_argument("--candidate-sha", required=True)
    parser.add_argument("--tree-sha", required=True)
    parser.add_argument("--changed-path", action="append", default=[])
    parser.add_argument("--declared-path", action="append", default=[])
    parser.add_argument("--semantic-risk", action="append")
    parser.add_argument("--protected-gate-id", action="append", default=[])
    parser.add_argument("--completion-state")
    parser.add_argument("--runtime-claimed", action="store_true")
    parser.add_argument("--caller-authority-ref")
    parser.add_argument("--integration-evidence-id", action="append", default=[])
    parser.add_argument("--completion-evidence-id", action="append", default=[])
    parser.add_argument("--executed-test-id", action="append", default=[])
    parser.add_argument("--test-coverage-json", type=Path)
    parser.add_argument("--test-claimed", action="store_true")
    parser.add_argument("--policy-modified-path", action="append", default=[])
    parser.add_argument("--policy-path", action="append", default=[])
    parser.add_argument("--policy-self-modification", action="store_true")
    parser.add_argument("--current-authority-boundary", action="append")
    parser.add_argument("--evaluated-at")
    parser.add_argument("--output", type=Path)
    return parser


def _load(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        manifest = _load(args.manifest)
        receipts = _load(args.receipts)
        coverage = _load(args.test_coverage_json) if args.test_coverage_json else None
        decision = evaluate_qa_compliance(
            manifest,
            receipts,
            current_repository=args.repository,
            current_source_ref=args.source_ref,
            current_candidate_sha=args.candidate_sha,
            current_tree_sha=args.tree_sha,
            changed_paths=args.changed_path,
            declared_paths=args.declared_path,
            semantic_risks=args.semantic_risk,
            protected_gate_ids=args.protected_gate_id,
            completion_state=args.completion_state,
            runtime_claimed=args.runtime_claimed,
            caller_authority_ref=args.caller_authority_ref,
            integration_evidence_ids=args.integration_evidence_id,
            completion_evidence_ids=args.completion_evidence_id,
            executed_test_ids=args.executed_test_id,
            test_coverage=coverage,
            test_claimed=args.test_claimed,
            policy_modified_paths=args.policy_modified_path,
            policy_self_modification=args.policy_self_modification,
            policy_paths=args.policy_path,
            current_authority_boundary=args.current_authority_boundary,
            evaluated_at=args.evaluated_at,
        )
        payload = json.dumps(decision.to_dict(), indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(payload, encoding="utf-8", newline="\n")
        print(f"QA_COMPLIANCE={decision.result}")
        if decision.failure_codes:
            print("QA_COMPLIANCE_FAILURES=" + ",".join(decision.failure_codes))
        return 0 if decision.compliant else 1
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"QA_COMPLIANCE=BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
