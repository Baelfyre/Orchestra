from pathlib import Path

import pytest

from scripts.validation import build_mutation_evidence as mutation_evidence


SHA = "a" * 40
OTHER_SHA = "b" * 40
PATTERN = "orchestra_runtime.services.RouterService.route*"


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
    results: str,
    target_progress: str = "13/13",
) -> tuple[Path, Path, Path]:
    run_output = tmp_path / "run.txt"
    target_output = tmp_path / "target-run.txt"
    results_output = tmp_path / "results.txt"
    target_text = f"Generating mutants\nRunning stats done\n{target_progress}  🎉 10  🙁 3\n"
    run_output.write_text(target_text, encoding="utf-8")
    target_output.write_text(target_text, encoding="utf-8")
    results_output.write_text(results, encoding="utf-8")
    return run_output, results_output, target_output


def _build(
    tmp_path: Path,
    *,
    results: str,
    run_exit_code: int = 0,
    tested_sha: str = SHA,
    source_head_sha: str = SHA,
    target_progress: str = "13/13",
):
    run_output, results_output, target_output = _raw_outputs(
        tmp_path,
        results=results,
        target_progress=target_progress,
    )
    return mutation_evidence.build_mutation_evidence(
        run_output=run_output,
        results_output=results_output,
        config_path=_config(tmp_path),
        target_run_specs=[f"{PATTERN}={target_output}"],
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


def test_classified_exact_head_target_builds_bounded_evidence(tmp_path: Path):
    evidence = _build(
        tmp_path,
        results=(
            "    orchestra_runtime.services.xǁRouterServiceǁroute__mutmut_3: survived\n"
            "    orchestra_runtime.services.xǁRouterServiceǁroute__mutmut_5: survived\n"
            "    orchestra_runtime.services.xǁRouterServiceǁroute__mutmut_9: survived\n"
            "    orchestra_runtime.services.xǁRuntimeExecutorǁ_execute__mutmut_1: not checked\n"
        ),
    )

    assert evidence["tested_sha"] == SHA
    assert evidence["source_head_sha"] == SHA
    assert evidence["scope"]["modules"] == ["orchestra_runtime/services.py"]
    assert evidence["scope"]["mutant_patterns"] == [PATTERN]
    assert evidence["scope"]["mutate_only_covered_lines"] is True
    assert evidence["scope"]["max_stack_depth"] == -1
    assert evidence["execution"]["classification_status"] == "COMPLETE"
    assert evidence["execution"]["target_mutant_total"] == 13
    assert evidence["execution"]["target_killed_count"] == 10
    assert evidence["execution"]["target_survived_count"] == 3
    assert evidence["execution"]["target_score_percent"] == 76.92
    assert evidence["execution"]["not_checked_count"] == 0
    assert evidence["execution"]["out_of_scope_result_record_count"] == 1
    assert evidence["execution"]["status_counts"] == {"survived": 3}


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
        _build(tmp_path, results="", run_exit_code=1)


def test_scoped_not_checked_mutants_are_rejected(tmp_path: Path):
    with pytest.raises(ValueError, match="scoped mutation results contain 1 not checked mutants"):
        _build(
            tmp_path,
            results="    orchestra_runtime.services.xǁRouterServiceǁroute__mutmut_3: not checked\n",
        )


def test_scoped_suspicious_outcome_is_rejected(tmp_path: Path):
    with pytest.raises(ValueError, match="non-classified outcomes: suspicious"):
        _build(
            tmp_path,
            results="    orchestra_runtime.services.xǁRouterServiceǁroute__mutmut_3: suspicious\n",
        )


def test_all_killed_target_is_valid_with_empty_results(tmp_path: Path):
    evidence = _build(tmp_path, results="")
    assert evidence["execution"]["target_mutant_total"] == 13
    assert evidence["execution"]["target_killed_count"] == 13
    assert evidence["execution"]["target_survived_count"] == 0
    assert evidence["execution"]["target_score_percent"] == 100.0


def test_incomplete_target_run_is_rejected(tmp_path: Path):
    with pytest.raises(ValueError, match="incomplete: completed 12 of 13 mutants"):
        _build(tmp_path, results="", target_progress="12/13")


def test_zero_mutant_target_run_is_rejected(tmp_path: Path):
    with pytest.raises(ValueError, match="executed zero mutants"):
        _build(tmp_path, results="", target_progress="0/0")


def test_synthetic_merge_sha_cannot_substitute_for_source_head(tmp_path: Path):
    with pytest.raises(ValueError, match="tested_sha must exactly match source_head_sha"):
        _build(tmp_path, results="", tested_sha=OTHER_SHA)


def test_fatal_stats_collection_marker_is_rejected(tmp_path: Path):
    run_output, results_output, target_output = _raw_outputs(tmp_path, results="")
    run_output.write_text("failed to collect stats. runner returned 1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="fatal instrumentation marker"):
        mutation_evidence.build_mutation_evidence(
            run_output=run_output,
            results_output=results_output,
            config_path=_config(tmp_path),
            target_run_specs=[f"{PATTERN}={target_output}"],
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
