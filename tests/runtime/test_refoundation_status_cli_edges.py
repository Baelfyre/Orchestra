from pathlib import Path

from orchestra_runtime.status import (
    ContractStatus,
    DiagnosticsStatus,
    GitStatus,
    OrchestraStatusProjection,
    ProjectStatus,
    ValidationStatus,
    main as status_main,
)


def _projection(*, git_repo=True, warnings=()):
    return OrchestraStatusProjection(
        projection_version="1.0",
        timestamp="2026-08-15T12:00:00Z",
        git=GitStatus(is_git_repo=git_repo),
        project=ProjectStatus(),
        contracts=ContractStatus(),
        validation=ValidationStatus(),
        diagnostics=DiagnosticsStatus(warnings=tuple(warnings)),
    )


def test_status_cli_git_unavailable_path_is_explicit_failure(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(
        "orchestra_runtime.status.build_status_projection",
        lambda path: _projection(git_repo=False, warnings=("Git executable unavailable or access denied.",)),
    )
    assert status_main(["--repo", str(tmp_path)]) == 1
    assert "Git executable unavailable" in capsys.readouterr().err


def test_status_cli_json_and_human_output_paths(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("orchestra_runtime.status.build_status_projection", lambda path: _projection())
    assert status_main(["--repo", str(tmp_path), "--json"]) == 0
    assert '"projection_version": "1.0"' in capsys.readouterr().out

    assert status_main(["--repo", str(tmp_path)]) == 0
    assert "ORCHESTRA STATUS" in capsys.readouterr().out


def test_status_cli_quiet_success_emits_nothing(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("orchestra_runtime.status.build_status_projection", lambda path: _projection())
    assert status_main(["--repo", str(tmp_path), "--quiet"]) == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
