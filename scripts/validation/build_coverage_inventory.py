from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


COVERAGE_INVENTORY_SCHEMA_VERSION = "orchestra.coverage-inventory.v1"
CRITICAL_MODULES = (
    "orchestra_runtime/evidence.py",
    "orchestra_runtime/machine_contracts.py",
    "orchestra_runtime/compliance_protocol.py",
    "orchestra_runtime/governance_kernel.py",
    "orchestra_runtime/preexecution.py",
    "orchestra_runtime/context_state.py",
    "orchestra_runtime/host_protocol.py",
    "orchestra_runtime/remediation_circuit.py",
    "orchestra_runtime/shadow_conformance.py",
    "orchestra_runtime/test_evidence.py",
    "orchestra_runtime/workflow_contracts.py",
)


def _percent(covered: int, total: int) -> float:
    return round((covered / total) * 100, 2) if total else 100.0


def _summary(record: dict[str, Any]) -> dict[str, Any]:
    summary = record.get("summary")
    if not isinstance(summary, dict):
        raise ValueError("coverage file record is missing summary")
    statements = int(summary.get("num_statements", 0))
    covered_statements = int(summary.get("covered_lines", 0))
    missing_statements = int(summary.get("missing_lines", statements - covered_statements))
    branches = int(summary.get("num_branches", 0))
    covered_branches = int(summary.get("covered_branches", 0))
    missing_branches = int(summary.get("missing_branches", branches - covered_branches))
    if min(statements, covered_statements, missing_statements, branches, covered_branches, missing_branches) < 0:
        raise ValueError("coverage summary contains negative totals")
    if covered_statements + missing_statements != statements:
        raise ValueError("coverage statement totals are inconsistent")
    if covered_branches + missing_branches != branches:
        raise ValueError("coverage branch totals are inconsistent")
    return {
        "statements": statements,
        "covered_statements": covered_statements,
        "missing_statements": missing_statements,
        "statement_percent": _percent(covered_statements, statements),
        "branches": branches,
        "covered_branches": covered_branches,
        "missing_branches": missing_branches,
        "branch_percent": _percent(covered_branches, branches),
    }


def build_inventory(
    coverage_path: Path,
    *,
    minimum_critical_statement: float = 98.0,
    minimum_critical_branch: float = 95.0,
) -> dict[str, Any]:
    payload = json.loads(coverage_path.read_text(encoding="utf-8"))
    files = payload.get("files")
    totals = payload.get("totals")
    if not isinstance(files, dict) or not isinstance(totals, dict):
        raise ValueError("coverage JSON must contain file records and totals")

    modules: list[dict[str, Any]] = []
    critical_failures: list[dict[str, Any]] = []
    for path in sorted(files):
        record = files[path]
        if not isinstance(record, dict):
            raise ValueError(f"coverage file record must be an object: {path}")
        metrics = _summary(record)
        missing_lines = tuple(int(item) for item in record.get("missing_lines", ()))
        excluded_lines = tuple(int(item) for item in record.get("excluded_lines", ()))
        module = {
            "path": path,
            "critical": path in CRITICAL_MODULES,
            **metrics,
            "missing_lines": list(missing_lines),
            "excluded_lines": list(excluded_lines),
        }
        modules.append(module)
        if module["critical"]:
            reasons = []
            if module["statement_percent"] < minimum_critical_statement:
                reasons.append("CRITICAL_STATEMENT_COVERAGE_BELOW_FLOOR")
            if module["branch_percent"] < minimum_critical_branch:
                reasons.append("CRITICAL_BRANCH_COVERAGE_BELOW_FLOOR")
            if reasons:
                critical_failures.append({"path": path, "reasons": reasons, **metrics})

    aggregate_statements = int(totals.get("num_statements", 0))
    aggregate_covered_statements = int(totals.get("covered_lines", 0))
    aggregate_branches = int(totals.get("num_branches", 0))
    aggregate_covered_branches = int(totals.get("covered_branches", 0))
    aggregate = {
        "statements": aggregate_statements,
        "covered_statements": aggregate_covered_statements,
        "missing_statements": aggregate_statements - aggregate_covered_statements,
        "statement_percent": _percent(aggregate_covered_statements, aggregate_statements),
        "branches": aggregate_branches,
        "covered_branches": aggregate_covered_branches,
        "missing_branches": aggregate_branches - aggregate_covered_branches,
        "branch_percent": _percent(aggregate_covered_branches, aggregate_branches),
    }
    return {
        "schema_version": COVERAGE_INVENTORY_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "coverage_source": coverage_path.name,
        "critical_policy": {
            "modules": list(CRITICAL_MODULES),
            "minimum_statement_percent": float(minimum_critical_statement),
            "minimum_branch_percent": float(minimum_critical_branch),
        },
        "aggregate": aggregate,
        "critical_ready": not critical_failures,
        "critical_failures": critical_failures,
        "modules": modules,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build Orchestra machine-readable coverage inventory")
    parser.add_argument("--coverage", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--critical-statement-floor", type=float, default=98.0)
    parser.add_argument("--critical-branch-floor", type=float, default=95.0)
    args = parser.parse_args(argv)
    inventory = build_inventory(
        args.coverage,
        minimum_critical_statement=args.critical_statement_floor,
        minimum_critical_branch=args.critical_branch_floor,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"aggregate": inventory["aggregate"], "critical_ready": inventory["critical_ready"], "critical_failures": inventory["critical_failures"]}, sort_keys=True))
    return 0 if inventory["critical_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
