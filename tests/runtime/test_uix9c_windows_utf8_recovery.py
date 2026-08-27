from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from scripts import uix9c_windows_utf8_launcher as launcher


def test_launcher_forces_python_utf8_mode() -> None:
    command = launcher.build_command([
        "execute",
        "--execution-mode",
        "live",
        "--live-call-gate",
    ])

    assert command[0] == launcher.sys.executable
    assert command[1:3] == ["-X", "utf8"]
    assert Path(command[3]).resolve() == launcher.RUNNER.resolve()
    assert command[4:] == ["execute", "--execution-mode", "live", "--live-call-gate"]


def test_launcher_preserves_child_exit_code_and_does_not_use_shell(monkeypatch) -> None:
    seen: dict[str, object] = {}

    def fake_run(command, **kwargs):
        seen["command"] = command
        seen.update(kwargs)
        return SimpleNamespace(returncode=17)

    monkeypatch.setattr(launcher.subprocess, "run", fake_run)

    result = launcher.main(["verify-frozen-identities"])

    assert result == 17
    assert seen["command"][1:3] == ["-X", "utf8"]
    assert seen["cwd"] == launcher.ROOT
    assert seen["shell"] is False
    assert seen["check"] is False
