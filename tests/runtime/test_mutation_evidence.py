from pathlib import Path

import pytest

from scripts.validation import build_mutation_evidence as mutation_evidence


SHA = "a" * 40
OTHER_SHA = "b" * 40
PATTERN = "orchestra_runtime.services.RouterService.route*"
SURVIVOR = "orchestra_runtime.services.xǁRouterServiceǁroute__mutmut_3"
KILLED = "orchestra_runtime.services.xǁRouterServiceǁroute__mutmut_4"


def _config(tmp_path: Path) -> Path:
    path = tmp_path / "isolated.cfg"
    path.write_text(
        "[mutmut]\n"
        "source_paths=orchestra_runtime/\n"
        "only_mutate=\n"
        "    orchestra_runtime/services.py\n"
        "mutate_only_covered_lines=true\n"
        "max_stack_depth=-1\n",
        encoding="utf-8",
    )
    return path


def _raw_outputs(
    tmp_path: Path,
    *,
    target_output: str | None = None,
    target_results: str | None = None,
) -> tuple[Path, Path, Path, Path]:
    run_output = tmp_path / "run.txt"
    results_output = tmp_path / "results.txt"
    target_run = tmp_path / "target-run.txt"
    target_result = tmp_path / "target-results.txt"
    target_output = target_output or f"Mutant results\n🎉 {KILLED}\n🙁 {SURVIVOR}\n"
    target_results = target_results if target_results is not None else f"    {SURVIVOR}: survived\n"
    run_output.write_text(target_output, encoding="utf-8")
    results_output.write_text(target_results, encoding="utf-8")
    target_run.write_text(target_output, encoding="utf-8")
    target_result.write_text(target_results, encoding="utf-8")
    return run_output, results_output, target_run, target_result


def _build(
    tmp_path: Path,
    *,
    target_output: str | None = None,
    target_results: str | None = None,
    run_exit_code: int = 0,
    tested_sha: str = SHA,
    source_head_sha: str = SHA,
):
    run_output, results_output, target_run, target_result = _raw_outputs(
        tmp_path,
        target_output=target_output,
        target_results=target_results,
    )
    return mutation_evidence.build_mutation_evidence(
        run_output=run_output,
        results_output=results_output,
        config_path=_config(tmp_path),
        target_run_specs=[f"{PATTERN}={target_run}"],
        target_result_specs=[f"{PATTERN}={target_result}"],
        run_exit_code=run_exit_code,
        tool_version="3.6.0",
        tested_sha=tested_sha,
        source_head_sha=source_head_sha,
        repository="Baelfyre/Orchestra",
        workflow_run_id="123",
        workflow_run_attempt="1",
        event_name="pull_request",
        ref_name="299/merge",
    )


def test_classified_exact_head_target_builds_valid_score(tmp_path: Path):
    evidence = _build(tmp_path)

    assert evidence["schema_version"] == "orchestra.mutation-evidence.v2"
    assert evidence["tested_sha"] == SHA
    assert evidence["source_head_sha"] == SHA
    assert evidence["scope"]["modules"] == ["orchestra_runtime/services.py"]
    assert evidence["scope"]["mutant_patterns"] == [PATTERN]
    assert evidence["scope"]["mutate_only_covered_lines"] is True
    assert evidence["scope"]["max_stack_depth"] == -1
    assert evidence["execution"]["score_status"] == "VALID_CLASSIFIED_SCORE"
    assert evidence["execution"]["classification_status"] == "COMPLETE"
    assert evidence["execution"]["target_mutant_total"] == 2
    assert evidence["execution"]["target_killed_count"] == 1
    assert evidence["execution"]["target_survived_count"] == 1
    assert evidence["execution"]["target_score_percent"] == 50.0
    assert evidence["execution"]["not_checked_count"] == 0


def test_top_level_and_class_mutant_identifiers_normalize_to_public_patterns():
    assert (
        mutation_evidence._normalize_mutant_identifier(
            "orchestra_runtime.models.x___getattr____mutmut_4"
        )
        == "orchestra_runtime.models.__getattr__"
    )
    assert (
        mutation_evidence._normalize_mutant_identifier(
            "orchestra_runtime.services.xǁRouterServiceǁroute__mutmut_27"
        )
        == "orchestra_runtime.services.RouterService.route"
    )
    assert (
        mutation_evidence._normalize_mutant_identifier(
            "orchestra_runtime.services.x__default_governance_rules__mutmut_2"
        )
        == "orchestra_runtime.services._default_governance_rules"
    )


def test_nonzero_mutmut_run_is_rejected(tmp_path: Path):
    with pytest.raises(ValueError, match="mutation execution failed with exit code 1"):
        _build(tmp_path, run_exit_code=1)


def test_target_not_checked_result_is_rejected(tmp_path: Path):
    with pytest.raises(ValueError, match="non-classified statuses: not checked"):
        _build(tmp_path, target_results=f"    {SURVIVOR}: not checked\n")


def test_target_timeout_outcome_is_rejected(tmp_path: Path):
    with pytest.raises(ValueError, match="non-classified outcomes"):
        _build(tmp_path, target_output=f"Mutant results\n⏰ {SURVIVOR}\n")


def test_all_killed_target_is_valid_with_empty_results(tmp_path: Path):
    evidence = _build(
        tmp_path,
        target_output=f"Mutant results\n🎉 {KILLED}\n",
        target_results="",
    )
    assert evidence["execution"]["target_mutant_total"] == 1
    assert evidence["execution"]["target_killed_count"] == 1
    assert evidence["execution"]["target_survived_count"] == 0
    assert evidence["execution"]["target_score_percent"] == 100.0


def test_target_run_without_classified_mutants_is_rejected(tmp_path: Path):
    with pytest.raises(ValueError, match="contains no classified target mutants"):
        _build(tmp_path, target_output="Running mutation testing\n", target_results="")


def test_survivor_results_must_reconcile_with_run_output(tmp_path: Path):
    with pytest.raises(ValueError, match="do not reconcile with run-output survivors"):
        _build(tmp_path, target_results="")


def test_synthetic_merge_sha_cannot_substitute_for_source_head(tmp_path: Path):
    with pytest.raises(ValueError, match="tested_sha must exactly match source_head_sha"):
        _build(tmp_path, tested_sha=OTHER_SHA)


def test_fatal_stats_collection_marker_is_rejected(tmp_path: Path):
    run_output, results_output, target_run, target_result = _raw_outputs(tmp_path)
    run_output.write_text("failed to collect stats. runner returned 1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="fatal instrumentation marker"):
        mutation_evidence.build_mutation_evidence(
            run_output=run_output,
            results_output=results_output,
            config_path=_config(tmp_path),
            target_run_specs=[f"{PATTERN}={target_run}"],
            target_result_specs=[f"{PATTERN}={target_result}"],
            run_exit_code=0,
            tool_version="3.6.0",
            tested_sha=SHA,
            source_head_sha=SHA,
            repository="Baelfyre/Orchestra",
            workflow_run_id="123",
            workflow_run_attempt="1",
            event_name="pull_request",
            ref_name="299/merge",
        )
