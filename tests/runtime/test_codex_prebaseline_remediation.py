from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXECUTOR_PATH = ROOT / "scripts" / "codex_benchmark_executor.py"
EXISTING_TEST_PATH = ROOT / "tests" / "runtime" / "test_comparative_benchmark_codex_executor.py"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


codex = _load_module("codex_benchmark_executor_prebaseline", EXECUTOR_PATH)
fixtures = _load_module("codex_benchmark_executor_existing_tests", EXISTING_TEST_PATH)


def _completed(args, *, returncode: int, stdout: str = "", stderr: str = ""):
    return subprocess.CompletedProcess(args=args, returncode=returncode, stdout=stdout, stderr=stderr)


def _execute_live(tmp_path: Path, *, git_runner, run_command):
    return codex.execute_request(
        fixtures._request(),
        expected_cli_version=fixtures.CLI_VERSION,
        expected_model=fixtures.MODEL,
        expected_reasoning_effort=fixtures.EFFORT,
        workspace_dir=tmp_path,
        run_command=run_command,
        version_runner=fixtures._never_run,
        git_runner=git_runner,
        raw_jsonl=None,
        observed_cli_version=fixtures.CLI_VERSION,
    )


def test_existing_non_git_directory_is_corrupted_starting_state_and_never_invokes_codex(tmp_path: Path) -> None:
    calls = {"codex": 0}

    def git_not_repo(args, **kwargs):
        assert args[:4] == ["git", "-C", str(tmp_path.resolve()), "rev-parse"]
        assert args[-1] == "--is-inside-work-tree"
        return _completed(args, returncode=128, stderr="fatal: not a git repository")

    def codex_must_not_run(*args, **kwargs):
        calls["codex"] += 1
        raise AssertionError("codex process must not run for a non-Git workspace")

    result = _execute_live(tmp_path, git_runner=git_not_repo, run_command=codex_must_not_run)

    assert calls["codex"] == 0
    assert result["outcome"]["status"] == "INVALID_RUN"
    assert result["outcome"]["invalid_reason"] == "CORRUPTED_STARTING_STATE"
    assert "Git worktree" in result["raw_evidence"]["error"]


def test_nonzero_codex_exit_with_structured_error_jsonl_remains_provider_outage(tmp_path: Path) -> None:
    raw = "\n".join(
        [
            json.dumps({"type": "thread.started", "thread_id": "t"}),
            json.dumps({"type": "error", "message": "synthetic provider failure"}),
        ]
    )

    def git_ok(args, **kwargs):
        return _completed(args, returncode=0, stdout="true\n")

    def codex_failed(args, **kwargs):
        return _completed(args, returncode=1, stdout=raw, stderr="provider failure")

    result = _execute_live(tmp_path, git_runner=git_ok, run_command=codex_failed)

    assert result["outcome"]["status"] == "INVALID_RUN"
    assert result["outcome"]["invalid_reason"] == "PROVIDER_OUTAGE"
    assert result["raw_evidence"]["returncode"] == 1


def test_nonzero_codex_exit_without_structured_provider_evidence_is_measurement_failure(tmp_path: Path) -> None:
    def git_ok(args, **kwargs):
        return _completed(args, returncode=0, stdout="true\n")

    def codex_failed(args, **kwargs):
        return _completed(args, returncode=2, stdout="", stderr="local invocation failure")

    result = _execute_live(tmp_path, git_runner=git_ok, run_command=codex_failed)

    assert result["outcome"]["status"] == "INVALID_RUN"
    assert result["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"
    assert result["raw_evidence"]["returncode"] == 2
    assert "without structured provider failure evidence" in result["raw_evidence"]["error"]
