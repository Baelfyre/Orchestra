import json

import pytest

from orchestra_runtime.test_evidence import build_test_evidence


SHA = "a" * 40


def _reports(tmp_path, *, branch_percent):
    statements = 100
    covered_statements = 98
    branches = 100
    covered_branches = int(branch_percent)
    coverage = tmp_path / "coverage.json"
    coverage.write_text(
        json.dumps(
            {
                "totals": {
                    "num_statements": statements,
                    "covered_lines": covered_statements,
                    "missing_lines": statements - covered_statements,
                    "num_branches": branches,
                    "covered_branches": covered_branches,
                    "missing_branches": branches - covered_branches,
                }
            }
        ),
        encoding="utf-8",
    )
    junit = tmp_path / "runtime-junit.xml"
    junit.write_text(
        '<testsuites tests="10" failures="0" errors="0" skipped="0"></testsuites>\n',
        encoding="utf-8",
    )
    return coverage, junit


def _build(tmp_path, *, branch_percent, branch_floor):
    coverage, junit = _reports(tmp_path, branch_percent=branch_percent)
    return build_test_evidence(
        coverage_path=coverage,
        junit_path=junit,
        tested_sha=SHA,
        source_head_sha=SHA,
        runtime_test_outcome="success",
        minimum_statement_coverage=97,
        minimum_branch_coverage=branch_floor,
        repository="Baelfyre/Orchestra",
        workflow_run_id="branch-gate",
        workflow_run_attempt="1",
        event_name="pull_request",
        ref_name="293/merge",
    )


def test_branch_gate_passes_at_exact_floor(tmp_path):
    evidence = _build(tmp_path, branch_percent=95, branch_floor=95)
    assert evidence["result"] == "PASS"
    assert evidence["coverage"]["branch_gate_enabled"] is True
    assert evidence["coverage"]["minimum_branch_coverage"] == 95.0
    assert evidence["coverage"]["branch_percent"] == 95.0


def test_branch_gate_fails_below_floor_even_when_statement_gate_passes(tmp_path):
    evidence = _build(tmp_path, branch_percent=94, branch_floor=95)
    assert evidence["coverage"]["statement_percent"] == 98.0
    assert evidence["coverage"]["branch_percent"] == 94.0
    assert evidence["result"] == "FAIL"


def test_branch_gate_can_remain_disabled_for_legacy_callers(tmp_path):
    coverage, junit = _reports(tmp_path, branch_percent=1)
    evidence = build_test_evidence(
        coverage_path=coverage,
        junit_path=junit,
        tested_sha=SHA,
        source_head_sha=SHA,
        runtime_test_outcome="success",
        minimum_statement_coverage=97,
        repository="Baelfyre/Orchestra",
        workflow_run_id="legacy",
        workflow_run_attempt="1",
        event_name="local",
        ref_name="local",
    )
    assert evidence["coverage"]["branch_gate_enabled"] is False
    assert evidence["coverage"]["minimum_branch_coverage"] is None
    assert evidence["result"] == "PASS"


def test_branch_gate_rejects_invalid_floor(tmp_path):
    coverage, junit = _reports(tmp_path, branch_percent=100)
    with pytest.raises(ValueError, match="minimum_branch_coverage"):
        build_test_evidence(
            coverage_path=coverage,
            junit_path=junit,
            tested_sha=SHA,
            source_head_sha=SHA,
            runtime_test_outcome="success",
            minimum_statement_coverage=97,
            minimum_branch_coverage=101,
            repository="Baelfyre/Orchestra",
            workflow_run_id="bad-floor",
            workflow_run_attempt="1",
            event_name="local",
            ref_name="local",
        )