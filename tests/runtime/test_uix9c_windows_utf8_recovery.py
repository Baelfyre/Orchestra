from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import jsonschema
import pytest

from internal import uix9c_windows_utf8_launcher as launcher


def test_recovery_authorization_is_schema_valid_and_exact() -> None:
    authorization = json.loads(launcher.RECOVERY_AUTHORIZATION.read_text(encoding="utf-8"))
    schema = json.loads((launcher.RECOVERY_AUTHORIZATION.parent / "recovery-authorization.v1.schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(authorization)

    assert authorization["authorization_status"] == "APPROVED"
    assert authorization["prior_invalid_attempt"]["provider_interactions"] == 1
    assert authorization["prior_invalid_attempt"]["scientific_observation"] is False
    assert authorization["restarted_effort_ceiling"]["fresh_campaign_max_new_model_calls"] == 6
    assert authorization["restarted_effort_ceiling"]["max_valid_observations"] == 6
    assert authorization["restarted_effort_ceiling"]["overall_experimental_interaction_ceiling"] == 7
    assert authorization["restarted_effort_ceiling"]["seventh_valid_observation_authorized"] is False
    assert authorization["restarted_effort_ceiling"]["additional_ceiling_expansion_authorized"] is False


def test_launcher_forces_python_utf8_mode_and_fresh_evidence_root() -> None:
    command = launcher.build_command([
        "execute",
        "--execution-mode",
        "live",
        "--live-call-gate",
    ])

    assert command[0] == launcher.sys.executable
    assert command[1:3] == ["-X", "utf8"]
    assert Path(command[3]).resolve() == launcher.RUNNER.resolve()
    assert command[4:8] == ["execute", "--execution-mode", "live", "--live-call-gate"]
    assert command[8] == "--evidence-root"
    assert Path(command[9]).resolve() == launcher.AUTHORIZED_FRESH_EVIDENCE_ROOT.resolve()


def test_launcher_rejects_live_evidence_root_override() -> None:
    with pytest.raises(RuntimeError, match="RECOVERY_EVIDENCE_ROOT_IS_LAUNCHER_OWNED"):
        launcher.build_command([
            "execute",
            "--execution-mode",
            "live",
            "--live-call-gate",
            "--evidence-root",
            "elsewhere",
        ])


def test_launcher_rejects_tampered_recovery_ceiling(monkeypatch, tmp_path: Path) -> None:
    authorization = json.loads(launcher.RECOVERY_AUTHORIZATION.read_text(encoding="utf-8"))
    authorization["restarted_effort_ceiling"]["overall_experimental_interaction_ceiling"] = 8
    tampered = tmp_path / "recovery-authorization.v1.json"
    tampered.write_text(json.dumps(authorization), encoding="utf-8")
    monkeypatch.setattr(launcher, "RECOVERY_AUTHORIZATION", tampered)

    with pytest.raises(RuntimeError, match="RECOVERY_OVERALL_CEILING_MISMATCH"):
        launcher.build_command(["execute", "--execution-mode", "live", "--live-call-gate"])


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
