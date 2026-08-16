from pathlib import Path

import pytest

from scripts.validation import build_mutation_evidence as mutation_evidence


SHA = "a" * 40
OTHER_SHA = "b" * 40


def _config(tmp_path: Path) -> Path:
    path = tmp_path / "isolated.cfg"
    path.write_text(
        "[mutmut]\n"
        "source_paths=orchestra_runtime/\n"
        "only_mutate=\n"
        "    orchestra_runtime/services.py\n"
        "mutate_only_covered_lines=true\n"
        "max_stack_depth=8\n",
        encoding="utf-8",
    )
    return path


def _raw_outputs(tmp_path: Path, *, results: str) -> tuple[Path, Path]:
    run_output = tmp_path / "run.txt"
    results_output = tmp_path / "results.txt"
    run_output.write_text("Generating mutants\nRunning stats done\n", encoding="utf-8")
    results_output.write_text(results, encoding="utf-8")
    return run_output, results_output


def _build(
    tmp_path: Path,
    *,
    results: str,
    run_exit_code: int = 0,
    tested_sha: str = SHA,
    source_head_sha: str = SHA,
):
    run_output, results_output = _raw_outputs(tmp_path, results=results)
    return mutation_evidence.build_mutation_evidence(
        run_output=run_output,
        results_output=results_output,
        config_path=_config(tmp_path),
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


def test_classified_exact_head_run_builds_valid_baseline(tmp_path: Path):
    evidence = _build(
        tmp_path,
        results=(
            "    orchestra_runtime.services.x_one__mutmut_1: killed\n"
            "    orchestra_runtime.services.x_two__mutmut_1: survived\n"
        ),
    )

    assert evidence["tested_sha"] == SHA
    assert evidence["source_head_sha"] == SHA
    assert evidence["scope"]["modules"] == ["orchestra_runtime/services.py"]
    assert evidence["execution"]["classification_status"] == "COMPLETE"
    assert evidence["execution"]["result_record_count"] == 2
    assert evidence["execution"]["not_checked_count"] == 0
    assert evidence["execution"]["status_counts"] == {"killed": 1, "survived": 1}


def test_nonzero_mutmut_run_is_rejected(tmp_path: Path):
    with pytest.raises(ValueError, match="mutation execution failed with exit code 1"):
        _build(tmp_path, results="    mutant: killed\n", run_exit_code=1)


def test_not_checked_mutants_are_rejected(tmp_path: Path):
    with pytest.raises(ValueError, match="not checked mutants"):
        _build(tmp_path, results="    mutant: not checked\n")


def test_empty_mutation_results_are_rejected(tmp_path: Path):
    with pytest.raises(ValueError, match="no mutant classification records"):
        _build(tmp_path, results="")


def test_synthetic_merge_sha_cannot_substitute_for_source_head(tmp_path: Path):
    with pytest.raises(ValueError, match="tested_sha must exactly match source_head_sha"):
        _build(tmp_path, results="    mutant: killed\n", tested_sha=OTHER_SHA)


def test_fatal_stats_collection_marker_is_rejected(tmp_path: Path):
    run_output, results_output = _raw_outputs(tmp_path, results="    mutant: killed\n")
    run_output.write_text("failed to collect stats. runner returned 1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="fatal instrumentation marker"):
        mutation_evidence.build_mutation_evidence(
            run_output=run_output,
            results_output=results_output,
            config_path=_config(tmp_path),
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
