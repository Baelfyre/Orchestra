"""Regression tests for explicit Orchestra evidence-baseline resolution."""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER_PATH = ROOT / "tests" / "behavior" / "run_tests.py"

spec = importlib.util.spec_from_file_location("orchestra_behavior_runner", RUNNER_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("Could not load tests/behavior/run_tests.py")
runner = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = runner
spec.loader.exec_module(runner)

CONTROLLED_ENV = (
    "ORCHESTRA_APPROVED_BASE_SHA",
    "GITHUB_EVENT_PATH",
    "GITHUB_EVENT_NAME",
    "GITHUB_ACTIONS",
    "GITHUB_SHA",
)


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def _remove_readonly(func, path, exc_info):
    error = exc_info[1]
    if not isinstance(error, PermissionError):
        raise error
    mode = stat.S_IWRITE | stat.S_IREAD
    if os.path.isdir(path):
        mode |= stat.S_IEXEC
    os.chmod(path, mode)
    func(path)


def _cleanup(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, onerror=_remove_readonly)


def _make_repo() -> tuple[Path, str, str]:
    repo = Path(tempfile.mkdtemp(prefix="orchestra-baseline-resolution-"))
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Orchestra Test")
    _git(repo, "checkout", "-B", "main")
    (repo / "tracked.txt").write_text("baseline\n", encoding="utf-8", newline="\n")
    _git(repo, "add", "tracked.txt")
    _git(repo, "commit", "-m", "baseline")
    baseline = _git(repo, "rev-parse", "HEAD")

    (repo / "tracked.txt").write_text(
        "baseline\ncurrent\n",
        encoding="utf-8",
        newline="\n",
    )
    _git(repo, "add", "tracked.txt")
    _git(repo, "commit", "-m", "current")
    current = _git(repo, "rev-parse", "HEAD")
    return repo, baseline, current


@contextmanager
def _environment(**values):
    original = {key: os.environ.get(key) for key in CONTROLLED_ENV}
    try:
        for key in CONTROLLED_ENV:
            os.environ.pop(key, None)
        for key, value in values.items():
            if value is not None:
                os.environ[key] = value
        yield
    finally:
        for key in CONTROLLED_ENV:
            os.environ.pop(key, None)
        for key, value in original.items():
            if value is not None:
                os.environ[key] = value


@contextmanager
def _event(payload: dict):
    handle, name = tempfile.mkstemp(prefix="orchestra-baseline-event-", suffix=".json")
    os.close(handle)
    path = Path(name)
    path.write_text(json.dumps(payload), encoding="utf-8")
    try:
        yield path
    finally:
        path.unlink(missing_ok=True)


def _assert_requires_explicit(repo: Path) -> None:
    try:
        runner.resolve_evidence_baseline(str(repo))
    except RuntimeError as exc:
        assert "explicit approved baseline" in str(exc).lower()
    else:
        raise AssertionError("implicit evidence baseline was accepted")


def test_local_execution_requires_explicit_baseline():
    repo, baseline, current = _make_repo()
    try:
        _git(repo, "update-ref", "refs/remotes/origin/main", baseline)
        with _environment():
            _assert_requires_explicit(repo)

        _git(repo, "update-ref", "refs/remotes/origin/main", current)
        with _environment():
            _assert_requires_explicit(repo)
    finally:
        _cleanup(repo)


def test_workflow_dispatch_requires_explicit_baseline():
    repo, _, current = _make_repo()
    try:
        with _event({"ref": "refs/heads/main"}) as event_path:
            with _environment(
                GITHUB_EVENT_PATH=str(event_path),
                GITHUB_EVENT_NAME="workflow_dispatch",
                GITHUB_ACTIONS="true",
                GITHUB_SHA=current,
            ):
                _assert_requires_explicit(repo)
    finally:
        _cleanup(repo)


def test_explicit_environment_baseline_succeeds():
    repo, baseline, _ = _make_repo()
    try:
        with _environment(ORCHESTRA_APPROVED_BASE_SHA=baseline):
            assert runner.resolve_evidence_baseline(str(repo)) == baseline
    finally:
        _cleanup(repo)


def test_unavailable_explicit_baseline_fails():
    repo, _, _ = _make_repo()
    try:
        with _environment(ORCHESTRA_APPROVED_BASE_SHA="f" * 40):
            try:
                runner.resolve_evidence_baseline(str(repo))
            except RuntimeError as exc:
                assert "not available locally" in str(exc)
            else:
                raise AssertionError("unavailable explicit baseline was accepted")
    finally:
        _cleanup(repo)


def test_fabricated_pull_request_event_outside_github_actions_fails():
    repo, baseline, _ = _make_repo()
    try:
        payload = {"pull_request": {"base": {"sha": baseline}}}
        with _event(payload) as event_path:
            with _environment(
                GITHUB_EVENT_PATH=str(event_path),
                GITHUB_EVENT_NAME="pull_request",
            ):
                _assert_requires_explicit(repo)
    finally:
        _cleanup(repo)


def test_fabricated_push_event_outside_github_actions_fails():
    repo, baseline, _ = _make_repo()
    try:
        with _event({"before": baseline}) as event_path:
            with _environment(
                GITHUB_EVENT_PATH=str(event_path),
                GITHUB_EVENT_NAME="push",
            ):
                _assert_requires_explicit(repo)
    finally:
        _cleanup(repo)


def test_github_actions_false_does_not_verify_event():
    repo, baseline, _ = _make_repo()
    try:
        payload = {"pull_request": {"base": {"sha": baseline}}}
        with _event(payload) as event_path:
            with _environment(
                GITHUB_EVENT_PATH=str(event_path),
                GITHUB_EVENT_NAME="pull_request",
                GITHUB_ACTIONS="false",
            ):
                _assert_requires_explicit(repo)
    finally:
        _cleanup(repo)


def test_pull_request_event_base_succeeds_in_github_actions():
    repo, baseline, _ = _make_repo()
    try:
        payload = {"pull_request": {"base": {"sha": baseline}}}
        with _event(payload) as event_path:
            with _environment(
                GITHUB_EVENT_PATH=str(event_path),
                GITHUB_EVENT_NAME="pull_request",
                GITHUB_ACTIONS="true",
            ):
                assert runner.resolve_evidence_baseline(str(repo)) == baseline
    finally:
        _cleanup(repo)


def test_push_before_event_succeeds_in_github_actions():
    repo, baseline, _ = _make_repo()
    try:
        with _event({"before": baseline}) as event_path:
            with _environment(
                GITHUB_EVENT_PATH=str(event_path),
                GITHUB_EVENT_NAME="push",
                GITHUB_ACTIONS="true",
            ):
                assert runner.resolve_evidence_baseline(str(repo)) == baseline
    finally:
        _cleanup(repo)


def test_event_payload_is_not_reused_for_wrong_event_type():
    repo, baseline, current = _make_repo()
    try:
        payload = {
            "pull_request": {"base": {"sha": baseline}},
            "before": baseline,
        }
        with _event(payload) as event_path:
            with _environment(
                GITHUB_EVENT_PATH=str(event_path),
                GITHUB_EVENT_NAME="workflow_dispatch",
                GITHUB_ACTIONS="true",
                GITHUB_SHA=current,
            ):
                _assert_requires_explicit(repo)
    finally:
        _cleanup(repo)


def main() -> int:
    test_local_execution_requires_explicit_baseline()
    test_workflow_dispatch_requires_explicit_baseline()
    test_explicit_environment_baseline_succeeds()
    test_unavailable_explicit_baseline_fails()
    test_fabricated_pull_request_event_outside_github_actions_fails()
    test_fabricated_push_event_outside_github_actions_fails()
    test_github_actions_false_does_not_verify_event()
    test_pull_request_event_base_succeeds_in_github_actions()
    test_push_before_event_succeeds_in_github_actions()
    test_event_payload_is_not_reused_for_wrong_event_type()
    print("Evidence baseline resolution tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
