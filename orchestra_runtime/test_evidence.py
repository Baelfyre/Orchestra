from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any
import xml.etree.ElementTree as ET


TEST_EVIDENCE_SCHEMA_VERSION = "orchestra.test-evidence.v1"
_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_sha(value: str, field_name: str) -> str:
    cleaned = str(value or "").strip().lower()
    if _GIT_SHA_RE.fullmatch(cleaned) is None:
        raise ValueError(f"{field_name} must be an exact 40-character Git SHA")
    return cleaned


def _actual_tested_sha() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return _git_sha(completed.stdout, "tested_sha")


def _int_attr(element: ET.Element, name: str) -> int:
    value = element.attrib.get(name, "0")
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"JUnit attribute {name!r} must be an integer") from exc


def parse_junit(path: Path) -> dict[str, int]:
    root = ET.parse(path).getroot()
    if root.tag not in {"testsuite", "testsuites"}:
        raise ValueError(f"unsupported JUnit root element: {root.tag!r}")

    if "tests" in root.attrib:
        total = _int_attr(root, "tests")
        failures = _int_attr(root, "failures")
        errors = _int_attr(root, "errors")
        skipped = _int_attr(root, "skipped")
    else:
        suites = tuple(root.findall("testsuite"))
        total = sum(_int_attr(item, "tests") for item in suites)
        failures = sum(_int_attr(item, "failures") for item in suites)
        errors = sum(_int_attr(item, "errors") for item in suites)
        skipped = sum(_int_attr(item, "skipped") for item in suites)

    passed = total - failures - errors - skipped
    if min(total, failures, errors, skipped, passed) < 0:
        raise ValueError("JUnit counts are internally inconsistent")
    return {
        "total": total,
        "passed": passed,
        "failures": failures,
        "errors": errors,
        "skipped": skipped,
    }


def parse_coverage(path: Path) -> dict[str, int | float]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    totals = payload.get("totals")
    if not isinstance(totals, dict):
        raise ValueError("coverage JSON does not contain totals")

    statements = int(totals.get("num_statements", 0))
    covered_statements = int(totals.get("covered_lines", 0))
    missing_statements = int(totals.get("missing_lines", statements - covered_statements))
    if statements <= 0 or covered_statements < 0 or missing_statements < 0:
        raise ValueError("coverage statement totals are invalid")
    if covered_statements + missing_statements != statements:
        raise ValueError("coverage statement totals are inconsistent")

    branches = int(totals.get("num_branches", 0))
    covered_branches = int(totals.get("covered_branches", 0))
    missing_branches = int(totals.get("missing_branches", branches - covered_branches))
    if min(branches, covered_branches, missing_branches) < 0:
        raise ValueError("coverage branch totals are invalid")
    if covered_branches + missing_branches != branches:
        raise ValueError("coverage branch totals are inconsistent")

    statement_percent = round((covered_statements / statements) * 100, 2)
    branch_percent = round((covered_branches / branches) * 100, 2) if branches else 100.0
    return {
        "statements": statements,
        "covered_statements": covered_statements,
        "missing_statements": missing_statements,
        "statement_percent": statement_percent,
        "branches": branches,
        "covered_branches": covered_branches,
        "missing_branches": missing_branches,
        "branch_percent": branch_percent,
    }


def build_test_evidence(
    *,
    coverage_path: Path,
    junit_path: Path,
    tested_sha: str,
    source_head_sha: str,
    runtime_test_outcome: str,
    minimum_statement_coverage: float,
    repository: str,
    workflow_run_id: str,
    workflow_run_attempt: str,
    event_name: str,
    ref_name: str,
    minimum_branch_coverage: float | None = None,
) -> dict[str, Any]:
    tests = parse_junit(junit_path)
    coverage = parse_coverage(coverage_path)
    outcome = str(runtime_test_outcome or "").strip().lower()
    if outcome not in {"success", "failure", "cancelled", "skipped"}:
        raise ValueError(f"unsupported runtime_test_outcome: {runtime_test_outcome!r}")
    minimum = float(minimum_statement_coverage)
    if not 0 <= minimum <= 100:
        raise ValueError("minimum_statement_coverage must be between 0 and 100")
    branch_minimum = None if minimum_branch_coverage is None else float(minimum_branch_coverage)
    if branch_minimum is not None and not 0 <= branch_minimum <= 100:
        raise ValueError("minimum_branch_coverage must be between 0 and 100")
    branch_gate_enabled = branch_minimum is not None

    passed = (
        outcome == "success"
        and tests["failures"] == 0
        and tests["errors"] == 0
        and float(coverage["statement_percent"]) >= minimum
        and (
            not branch_gate_enabled
            or float(coverage["branch_percent"]) >= float(branch_minimum)
        )
    )
    return {
        "schema_version": TEST_EVIDENCE_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "repository": str(repository or "").strip(),
        "tested_sha": _git_sha(tested_sha, "tested_sha"),
        "source_head_sha": _git_sha(source_head_sha, "source_head_sha"),
        "workflow": {
            "run_id": str(workflow_run_id or "").strip(),
            "run_attempt": str(workflow_run_attempt or "").strip(),
            "event_name": str(event_name or "").strip(),
            "ref_name": str(ref_name or "").strip(),
        },
        "runtime": {
            "python_version": sys.version.split()[0],
            "test_outcome": outcome,
        },
        "tests": tests,
        "coverage": {
            **coverage,
            "minimum_statement_coverage": minimum,
            "minimum_branch_coverage": branch_minimum,
            "branch_gate_enabled": branch_gate_enabled,
        },
        "reports": {
            "coverage_json": coverage_path.name,
            "coverage_json_sha256": _sha256_file(coverage_path),
            "junit_xml": junit_path.name,
            "junit_xml_sha256": _sha256_file(junit_path),
        },
        "result": "PASS" if passed else "FAIL",
    }


def write_test_evidence(
    *,
    coverage_path: Path,
    junit_path: Path,
    output_path: Path,
    minimum_statement_coverage: float,
    minimum_branch_coverage: float | None = None,
) -> dict[str, Any]:
    source_head = os.getenv("SOURCE_HEAD_SHA") or os.getenv("GITHUB_SHA") or _actual_tested_sha()
    evidence = build_test_evidence(
        coverage_path=coverage_path,
        junit_path=junit_path,
        tested_sha=_actual_tested_sha(),
        source_head_sha=source_head,
        runtime_test_outcome=os.getenv("RUNTIME_TEST_OUTCOME", "success"),
        minimum_statement_coverage=minimum_statement_coverage,
        minimum_branch_coverage=minimum_branch_coverage,
        repository=os.getenv("GITHUB_REPOSITORY", "unknown/unknown"),
        workflow_run_id=os.getenv("GITHUB_RUN_ID", "local"),
        workflow_run_attempt=os.getenv("GITHUB_RUN_ATTEMPT", "1"),
        event_name=os.getenv("GITHUB_EVENT_NAME", "local"),
        ref_name=os.getenv("GITHUB_REF_NAME", "local"),
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return evidence


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build Orchestra runtime test evidence")
    parser.add_argument("--coverage", type=Path, required=True)
    parser.add_argument("--junit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--minimum-statement-coverage", type=float, default=90.0)
    parser.add_argument("--minimum-branch-coverage", type=float)
    args = parser.parse_args(argv)
    evidence = write_test_evidence(
        coverage_path=args.coverage,
        junit_path=args.junit,
        output_path=args.output,
        minimum_statement_coverage=args.minimum_statement_coverage,
        minimum_branch_coverage=args.minimum_branch_coverage,
    )
    print(json.dumps({
        "result": evidence["result"],
        "tested_sha": evidence["tested_sha"],
        "source_head_sha": evidence["source_head_sha"],
        "tests": evidence["tests"],
        "coverage": evidence["coverage"],
    }, sort_keys=True))
    return 0 if evidence["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())