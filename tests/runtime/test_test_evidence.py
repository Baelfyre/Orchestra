import json
from pathlib import Path

import pytest

from orchestra_runtime.test_evidence import (
    TEST_EVIDENCE_SCHEMA_VERSION,
    build_test_evidence,
    parse_coverage,
    parse_junit,
)


SHA_A = "a" * 40
SHA_B = "b" * 40


def _write_junit(path: Path, *, tests=10, failures=0, errors=0, skipped=0):
    path.write_text(
        f'<testsuites tests="{tests}" failures="{failures}" errors="{errors}" skipped="{skipped}"></testsuites>\n',
        encoding="utf-8",
    )


def _write_coverage(
    path: Path,
    *,
    statements=100,
    covered=96,
    branches=20,
    covered_branches=19,
):
    payload = {
        "meta": {"branch_coverage": True},
        "files": {},
        "totals": {
            "num_statements": statements,
            "covered_lines": covered,
            "missing_lines": statements - covered,
            "num_branches": branches,
            "covered_branches": covered_branches,
            "missing_branches": branches - covered_branches,
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_parse_junit_derives_passed_count(tmp_path):
    path = tmp_path / "runtime-junit.xml"
    _write_junit(path, tests=12, failures=1, errors=2, skipped=3)
    assert parse_junit(path) == {
        "total": 12,
        "passed": 6,
        "failures": 1,
        "errors": 2,
        "skipped": 3,
    }


def test_parse_junit_rejects_inconsistent_counts(tmp_path):
    path = tmp_path / "runtime-junit.xml"
    _write_junit(path, tests=1, failures=1, errors=1, skipped=0)
    with pytest.raises(ValueError, match="internally inconsistent"):
        parse_junit(path)


def test_parse_coverage_reports_statement_and_branch_metrics(tmp_path):
    path = tmp_path / "coverage.json"
    _write_coverage(path)
    assert parse_coverage(path) == {
        "statements": 100,
        "covered_statements": 96,
        "missing_statements": 4,
        "statement_percent": 96.0,
        "branches": 20,
        "covered_branches": 19,
        "missing_branches": 1,
        "branch_percent": 95.0,
    }


def test_parse_coverage_rejects_inconsistent_totals(tmp_path):
    path = tmp_path / "coverage.json"
    payload = {
        "totals": {
            "num_statements": 10,
            "covered_lines": 9,
            "missing_lines": 2,
            "num_branches": 0,
            "covered_branches": 0,
            "missing_branches": 0,
        }
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="statement totals are inconsistent"):
        parse_coverage(path)


def test_build_evidence_binds_tested_sha_source_head_and_report_digests(tmp_path):
    coverage = tmp_path / "coverage.json"
    junit = tmp_path / "runtime-junit.xml"
    _write_coverage(coverage, covered=97, covered_branches=20)
    _write_junit(junit, tests=15)

    evidence = build_test_evidence(
        coverage_path=coverage,
        junit_path=junit,
        tested_sha=SHA_A,
        source_head_sha=SHA_B,
        runtime_test_outcome="success",
        minimum_statement_coverage=95,
        repository="Baelfyre/Orchestra",
        workflow_run_id="123",
        workflow_run_attempt="2",
        event_name="pull_request",
        ref_name="290/merge",
    )

    assert evidence["schema_version"] == TEST_EVIDENCE_SCHEMA_VERSION
    assert evidence["tested_sha"] == SHA_A
    assert evidence["source_head_sha"] == SHA_B
    assert evidence["tests"]["total"] == 15
    assert evidence["coverage"]["statement_percent"] == 97.0
    assert evidence["coverage"]["branch_percent"] == 100.0
    assert len(evidence["reports"]["coverage_json_sha256"]) == 64
    assert len(evidence["reports"]["junit_xml_sha256"]) == 64
    assert evidence["result"] == "PASS"


def test_failed_pytest_outcome_cannot_be_presented_as_pass(tmp_path):
    coverage = tmp_path / "coverage.json"
    junit = tmp_path / "runtime-junit.xml"
    _write_coverage(coverage, covered=100, covered_branches=20)
    _write_junit(junit, tests=10)
    evidence = build_test_evidence(
        coverage_path=coverage,
        junit_path=junit,
        tested_sha=SHA_A,
        source_head_sha=SHA_A,
        runtime_test_outcome="failure",
        minimum_statement_coverage=90,
        repository="Baelfyre/Orchestra",
        workflow_run_id="123",
        workflow_run_attempt="1",
        event_name="pull_request",
        ref_name="290/merge",
    )
    assert evidence["result"] == "FAIL"


def test_below_statement_threshold_fails_evidence_even_when_tests_pass(tmp_path):
    coverage = tmp_path / "coverage.json"
    junit = tmp_path / "runtime-junit.xml"
    _write_coverage(coverage, covered=89, covered_branches=20)
    _write_junit(junit)
    evidence = build_test_evidence(
        coverage_path=coverage,
        junit_path=junit,
        tested_sha=SHA_A,
        source_head_sha=SHA_A,
        runtime_test_outcome="success",
        minimum_statement_coverage=90,
        repository="Baelfyre/Orchestra",
        workflow_run_id="123",
        workflow_run_attempt="1",
        event_name="push",
        ref_name="main",
    )
    assert evidence["coverage"]["statement_percent"] == 89.0
    assert evidence["result"] == "FAIL"


def test_invalid_sha_is_rejected(tmp_path):
    coverage = tmp_path / "coverage.json"
    junit = tmp_path / "runtime-junit.xml"
    _write_coverage(coverage)
    _write_junit(junit)
    with pytest.raises(ValueError, match="40-character"):
        build_test_evidence(
            coverage_path=coverage,
            junit_path=junit,
            tested_sha="abcdef0",
            source_head_sha=SHA_A,
            runtime_test_outcome="success",
            minimum_statement_coverage=90,
            repository="Baelfyre/Orchestra",
            workflow_run_id="123",
            workflow_run_attempt="1",
            event_name="push",
            ref_name="main",
        )
