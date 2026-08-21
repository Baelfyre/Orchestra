from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "codex_benchmark_executor_hardened.py"

spec = importlib.util.spec_from_file_location("codex_benchmark_executor_hardened", MODULE_PATH)
assert spec and spec.loader
hardened = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hardened)


def _request() -> dict:
    return {"request_id": "codex-hardening-test"}


def _git_result(*, returncode: int, stdout: str = "", stderr: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=["git", "rev-parse"],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


def test_non_git_workspace_fails_before_canonical_executor(tmp_path: Path, monkeypatch) -> None:
    def fake_git(*args, **kwargs):
        return _git_result(
            returncode=128,
            stderr="fatal: not a git repository",
        )

    def must_not_execute(*args, **kwargs):
        raise AssertionError("canonical Codex executor must not run for non-Git workspace")

    monkeypatch.setattr(hardened.base, "execute_request", must_not_execute)

    result = hardened.execute_request(
        _request(),
        expected_cli_version="0.148.0",
        expected_model="gpt-5.6-sol",
        expected_reasoning_effort="medium",
        workspace_dir=tmp_path,
        git_runner=fake_git,
    )

    assert result["outcome"]["status"] == "INVALID_RUN"
    assert result["outcome"]["invalid_reason"] == "CORRUPTED_STARTING_STATE"
    preflight = result["raw_evidence"]["workspace_preflight"]
    assert preflight["preflight"] == "GIT_WORKTREE_REQUIRED"
    assert preflight["git_returncode"] == 128
    assert result["tokens"]["source"] == "UNAVAILABLE"


def test_git_workspace_delegates_to_canonical_executor(tmp_path: Path, monkeypatch) -> None:
    def fake_git(*args, **kwargs):
        return _git_result(returncode=0, stdout="true\n")

    sentinel = {
        "outcome": {
            "status": "PASS",
            "invalid_reason": None,
            "task_completed": True,
            "validation_passed": True,
            "governance_valid": True,
        },
        "raw_evidence": {},
    }

    def fake_execute(*args, **kwargs):
        return sentinel

    monkeypatch.setattr(hardened.base, "execute_request", fake_execute)

    result = hardened.execute_request(
        _request(),
        expected_cli_version="0.148.0",
        expected_model="gpt-5.6-sol",
        expected_reasoning_effort="medium",
        workspace_dir=tmp_path,
        git_runner=fake_git,
    )

    assert result["outcome"]["status"] == "PASS"
    assert result["raw_evidence"]["workspace_preflight"]["preflight"] == "GIT_WORKTREE_VERIFIED"


def test_unstructured_nonzero_codex_exit_is_not_provider_outage(tmp_path: Path, monkeypatch) -> None:
    def fake_git(*args, **kwargs):
        return _git_result(returncode=0, stdout="true\n")

    original = hardened.base._invalid_result(
        _request(),
        "PROVIDER_OUTAGE",
        {
            "error": "codex exec returned non-zero",
            "returncode": 1,
            "stderr": "local CLI configuration failure",
        },
    )

    monkeypatch.setattr(hardened.base, "execute_request", lambda *args, **kwargs: original)

    result = hardened.execute_request(
        _request(),
        expected_cli_version="0.148.0",
        expected_model="gpt-5.6-sol",
        expected_reasoning_effort="medium",
        workspace_dir=tmp_path,
        git_runner=fake_git,
    )

    assert result["outcome"]["status"] == "INVALID_RUN"
    assert result["outcome"]["invalid_reason"] == "MEASUREMENT_CAPTURE_FAILURE"
    evidence = result["raw_evidence"]
    assert evidence["classification_original"] == "PROVIDER_OUTAGE"
    assert evidence["classification_hardened"] == "MEASUREMENT_CAPTURE_FAILURE"
    assert evidence["classification_basis"] == "NONZERO_CODEX_PROCESS_EXIT_WITHOUT_STRUCTURED_PROVIDER_EVENT"


def test_structured_provider_outage_classification_is_preserved(tmp_path: Path, monkeypatch) -> None:
    def fake_git(*args, **kwargs):
        return _git_result(returncode=0, stdout="true\n")

    original = hardened.base._invalid_result(
        _request(),
        "PROVIDER_OUTAGE",
        {
            "error": "Codex reported turn.failed or error",
            "raw_jsonl": '{"type":"turn.failed"}',
        },
    )

    monkeypatch.setattr(hardened.base, "execute_request", lambda *args, **kwargs: original)

    result = hardened.execute_request(
        _request(),
        expected_cli_version="0.148.0",
        expected_model="gpt-5.6-sol",
        expected_reasoning_effort="medium",
        workspace_dir=tmp_path,
        git_runner=fake_git,
    )

    assert result["outcome"]["status"] == "INVALID_RUN"
    assert result["outcome"]["invalid_reason"] == "PROVIDER_OUTAGE"
    assert "classification_hardened" not in result["raw_evidence"]
