import json
import runpy
import sys

import pytest

from orchestra_runtime.context_state import ContinuityEvent, CurrentProjectState
from orchestra_runtime.test_evidence import parse_coverage


SHA40 = "a" * 40


def _state(**overrides):
    values = dict(
        project_id="orchestra",
        repository="Baelfyre/Orchestra",
        canonical_sha=SHA40,
        phase="P9",
        authority_mode="FULL_AUTONOMOUS_BOUNDED",
        current_task="critical-gap-closeout",
        blockers=(),
        critical_receipt_refs=(),
        evidence_index_refs=(),
        revision=1,
        updated_at="2026-08-15T11:00:00Z",
    )
    values.update(overrides)
    return CurrentProjectState(**values)


def test_context_text_rejects_blank_value():
    with pytest.raises(ValueError, match="must be non-empty"):
        _state(project_id=" ")


def test_current_state_rejects_unknown_schema_version():
    with pytest.raises(ValueError, match="unsupported current-state schema"):
        _state(schema_version="orchestra.context-state.v999")


def test_continuity_event_rejects_unknown_schema_version():
    with pytest.raises(ValueError, match="unsupported continuity event schema"):
        ContinuityEvent(
            sequence=1,
            project_id="orchestra",
            event_type="STATE_CREATED",
            occurred_at="2026-08-15T11:00:00Z",
            payload={},
            previous_event_digest=None,
            schema_version="orchestra.context-state.v999",
        )


def test_coverage_parser_rejects_nonnegative_but_inconsistent_branch_totals(tmp_path):
    coverage = tmp_path / "coverage.json"
    coverage.write_text(
        json.dumps(
            {
                "totals": {
                    "num_statements": 2,
                    "covered_lines": 2,
                    "missing_lines": 0,
                    "num_branches": 4,
                    "covered_branches": 2,
                    "missing_branches": 1,
                }
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="branch totals are inconsistent"):
        parse_coverage(coverage)


def test_test_evidence_module_entrypoint_executes_under_coverage(tmp_path, monkeypatch, capsys):
    coverage = tmp_path / "coverage.json"
    coverage.write_text(
        json.dumps(
            {
                "totals": {
                    "num_statements": 10,
                    "covered_lines": 10,
                    "missing_lines": 0,
                    "num_branches": 2,
                    "covered_branches": 2,
                    "missing_branches": 0,
                }
            }
        ),
        encoding="utf-8",
    )
    junit = tmp_path / "runtime-junit.xml"
    junit.write_text(
        '<testsuites tests="2" failures="0" errors="0" skipped="0"></testsuites>\n',
        encoding="utf-8",
    )
    output = tmp_path / "test-evidence.json"
    monkeypatch.setenv("SOURCE_HEAD_SHA", SHA40)
    monkeypatch.setenv("RUNTIME_TEST_OUTCOME", "success")
    monkeypatch.setenv("GITHUB_REPOSITORY", "Baelfyre/Orchestra")
    monkeypatch.setenv("GITHUB_RUN_ID", "local-entrypoint")
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", "1")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "workflow_dispatch")
    monkeypatch.setenv("GITHUB_REF_NAME", "local")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "orchestra_runtime.test_evidence",
            "--coverage",
            str(coverage),
            "--junit",
            str(junit),
            "--output",
            str(output),
            "--minimum-statement-coverage",
            "95",
        ],
    )

    with pytest.raises(SystemExit) as exc:
        runpy.run_module("orchestra_runtime.test_evidence", run_name="__main__")
    assert exc.value.code == 0
    assert json.loads(output.read_text(encoding="utf-8"))["result"] == "PASS"
    assert '"result": "PASS"' in capsys.readouterr().out
