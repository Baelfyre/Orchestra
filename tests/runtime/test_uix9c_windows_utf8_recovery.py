from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from scripts import uix9b_live_proof_runner_v2 as runner


def _successful_jsonl_bytes() -> bytes:
    events = [
        {"type": "thread.started"},
        {"type": "item.completed", "item": {"type": "agent_message", "text": "UTF-8 right quote: \u201d"}},
        {"type": "turn.completed", "usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2}},
    ]
    return ("\n".join(json.dumps(event, ensure_ascii=False) for event in events) + "\n").encode("utf-8")


def test_live_codex_capture_is_binary_then_utf8_decoded(monkeypatch, tmp_path: Path) -> None:
    seen: dict[str, object] = {}

    monkeypatch.setattr(runner, "verify_codex_cli_version", lambda: runner.EXPECTED_CODEX_CLI_VERSION)
    monkeypatch.setattr(runner, "build_codex_command", lambda **_kwargs: ["codex", "exec"])

    def fake_run(*_args, **kwargs):
        seen.update(kwargs)
        return SimpleNamespace(returncode=0, stdout=_successful_jsonl_bytes(), stderr=b"")

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    result = runner.run_codex_session(tmp_path, "task")

    assert seen["capture_output"] is True
    assert seen["text"] is False
    assert result["classification"] == "OUTPUT_CAPTURED_PENDING_VALIDATOR"
    assert result["parsed"]["response"] == "UTF-8 right quote: \u201d"


def test_invalid_utf8_capture_is_host_crash_not_scientific_output(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(runner, "verify_codex_cli_version", lambda: runner.EXPECTED_CODEX_CLI_VERSION)
    monkeypatch.setattr(runner, "build_codex_command", lambda **_kwargs: ["codex", "exec"])

    def fake_run(*_args, **_kwargs):
        return SimpleNamespace(returncode=0, stdout=b"\x9d", stderr=b"")

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    result = runner.run_codex_session(tmp_path, "task")

    assert result["classification"] == "HOST_CRASH"
    assert result["error"].startswith("CODEX_STDOUT_UTF8_DECODE_FAILURE:")
    assert len(result["stdout_sha256"]) == 64
