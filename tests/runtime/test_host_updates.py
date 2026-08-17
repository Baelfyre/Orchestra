from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from orchestra_runtime.host_updates import (
    HostUpdateError,
    SCAFFOLD_ONLY_HOSTS,
    SUPPORTED_HOSTS,
    build_host_update_plan,
    load_host_update_contract,
    resolve_host_update_record,
)

ROOT = Path(__file__).resolve().parents[2]


def test_contract_preserves_exact_host_maturity_boundary_and_version_parity() -> None:
    contract = load_host_update_contract(ROOT)
    plugin = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    by_id = {record["host_id"]: record for record in contract["hosts"]}

    assert contract["package_version"] == plugin["version"]
    assert {host for host, record in by_id.items() if record["maturity"] == "SUPPORTED"} == SUPPORTED_HOSTS
    assert {host for host, record in by_id.items() if record["maturity"] == "SCAFFOLD_ONLY"} == SCAFFOLD_ONLY_HOSTS
    assert set(by_id) == SUPPORTED_HOSTS | SCAFFOLD_ONLY_HOSTS


def test_supported_hosts_are_plan_only_until_separate_authority_exists() -> None:
    for host in sorted(SUPPORTED_HOSTS):
        plan = build_host_update_plan(host, root=ROOT)
        assert plan.default_behavior == "READ_ONLY_PLAN"
        assert plan.execution_support == "EXPLICIT_AUTHORIZATION_REQUIRED"
        assert plan.execution_authorized is False
        assert plan.execution_requires_separate_authorization is True
        assert plan.automatic_installed_integration_refresh is False
        assert plan.update_mechanism == "GIT_FAST_FORWARD_THEN_MANUAL_HOST_REFRESH"
        assert any("git pull --ff-only" in item for item in plan.update_instructions)
        assert all("force push" not in item.lower() for item in plan.update_instructions)


def test_scaffold_hosts_remain_instruction_only_and_cannot_imply_live_mutation() -> None:
    for host in sorted(SCAFFOLD_ONLY_HOSTS):
        plan = build_host_update_plan(host, root=ROOT)
        assert plan.maturity == "SCAFFOLD_ONLY"
        assert plan.execution_support == "INSTRUCTION_ONLY"
        assert plan.execution_authorized is False
        assert plan.execution_requires_separate_authorization is False
        assert plan.automatic_installed_integration_refresh is False
        assert plan.update_mechanism == "INSTRUCTION_ONLY"


def test_vscodium_alias_resolves_to_vscode_without_promoting_maturity() -> None:
    plan = build_host_update_plan("vscodium", root=ROOT)
    assert plan.requested_host == "vscodium"
    assert plan.host_id == "vscode"
    assert plan.maturity == "SCAFFOLD_ONLY"
    assert plan.execution_support == "INSTRUCTION_ONLY"


def test_unknown_host_fails_closed() -> None:
    with pytest.raises(HostUpdateError, match="UNKNOWN_HOST_FAIL_CLOSED"):
        resolve_host_update_record("imaginary-marketplace-host", ROOT)


def test_update_status_is_deterministic_without_network_or_mutation() -> None:
    available = build_host_update_plan("codex", latest_version="v1.6.0", root=ROOT)
    current = build_host_update_plan("codex", latest_version="1.5.0", root=ROOT)
    ahead = build_host_update_plan("codex", latest_version="1.4.0", root=ROOT)
    unchecked = build_host_update_plan("codex", root=ROOT)

    assert available.update_status == "UPDATE_AVAILABLE"
    assert current.update_status == "UP_TO_DATE"
    assert ahead.update_status == "LOCAL_AHEAD"
    assert unchecked.update_status == "NOT_CHECKED"


def test_supported_git_recovery_contract_is_non_destructive_and_validation_bound() -> None:
    contract = load_host_update_contract(ROOT)
    for record in contract["hosts"]:
        if record["host_id"] not in SUPPORTED_HOSTS:
            continue
        joined_hints = " ".join(record["recovery_hints"]).lower()
        joined_validation = " ".join(record["validation_commands"])
        assert "reset --hard" not in joined_hints
        assert "force push" in joined_hints
        assert "governance_check.py --strict" in joined_validation


def test_cli_emits_machine_plan_and_has_no_execute_flag() -> None:
    command = [
        sys.executable,
        str(ROOT / "scripts" / "host_update.py"),
        "--host",
        "antigravity",
        "--latest-version",
        "1.5.0",
        "--json",
    ]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["host_id"] == "antigravity"
    assert payload["update_status"] == "UP_TO_DATE"
    assert payload["execution_authorized"] is False
    assert payload["automatic_installed_integration_refresh"] is False
    assert "ORCHESTRA_HOST_UPDATE=READ_ONLY_PLAN" in completed.stderr

    rejected = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "host_update.py"), "--host", "codex", "--execute"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert rejected.returncode != 0
    assert "unrecognized arguments: --execute" in rejected.stderr
