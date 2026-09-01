from __future__ import annotations

import copy
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
    repository_root,
    resolve_host_update_record,
)

ROOT = Path(__file__).resolve().parents[2]
CURRENT_VERSION = "1.8.0"


def _canonical_contract() -> dict[str, object]:
    return copy.deepcopy(load_host_update_contract(ROOT))


def _write_contract_repo(
    tmp_path: Path,
    contract: object,
    *,
    plugin_version: object = CURRENT_VERSION,
) -> Path:
    contract_path = tmp_path / "machine" / "hosts" / "update-contract.v1.json"
    contract_path.parent.mkdir(parents=True, exist_ok=True)
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    (tmp_path / "plugin.json").write_text(
        json.dumps({"version": plugin_version}), encoding="utf-8"
    )
    return tmp_path


def _host(contract: dict[str, object], host_id: str) -> dict[str, object]:
    hosts = contract["hosts"]
    assert isinstance(hosts, list)
    return next(record for record in hosts if isinstance(record, dict) and record["host_id"] == host_id)


def test_contract_preserves_exact_host_maturity_boundary_and_version_parity() -> None:
    contract = load_host_update_contract(ROOT)
    plugin = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    by_id = {record["host_id"]: record for record in contract["hosts"]}

    assert contract["package_version"] == plugin["version"]
    assert {host for host, record in by_id.items() if record["maturity"] == "SUPPORTED"} == SUPPORTED_HOSTS
    assert {host for host, record in by_id.items() if record["maturity"] == "SCAFFOLD_ONLY"} == SCAFFOLD_ONLY_HOSTS
    assert set(by_id) == SUPPORTED_HOSTS | SCAFFOLD_ONLY_HOSTS
    assert repository_root() == ROOT


def test_supported_hosts_are_plan_only_until_separate_authority_exists() -> None:
    for host in sorted(SUPPORTED_HOSTS):
        plan = build_host_update_plan(host, root=ROOT)
        payload = plan.to_dict()
        assert plan.default_behavior == "READ_ONLY_PLAN"
        assert plan.execution_support == "EXPLICIT_AUTHORIZATION_REQUIRED"
        assert plan.execution_authorized is False
        assert plan.execution_requires_separate_authorization is True
        assert plan.automatic_installed_integration_refresh is False
        assert plan.update_mechanism == "GIT_FAST_FORWARD_THEN_MANUAL_HOST_REFRESH"
        assert any("git pull --ff-only" in item for item in plan.update_instructions)
        assert all("force push" not in item.lower() for item in plan.update_instructions)
        assert isinstance(payload["update_instructions"], list)
        assert isinstance(payload["validation_commands"], list)
        assert isinstance(payload["recovery_hints"], list)


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
    plan = build_host_update_plan("VSCODIUM", root=ROOT)
    record = resolve_host_update_record("VSCODIUM", ROOT)
    assert plan.requested_host == "vscodium"
    assert plan.host_id == "vscode"
    assert plan.maturity == "SCAFFOLD_ONLY"
    assert plan.execution_support == "INSTRUCTION_ONLY"
    assert record["host_id"] == "vscode"


def test_unknown_host_fails_closed_for_record_and_plan() -> None:
    with pytest.raises(HostUpdateError, match="UNKNOWN_HOST_FAIL_CLOSED"):
        resolve_host_update_record("imaginary-marketplace-host", ROOT)
    with pytest.raises(HostUpdateError, match="UNKNOWN_HOST_FAIL_CLOSED"):
        build_host_update_plan("imaginary-marketplace-host", root=ROOT)
    with pytest.raises(HostUpdateError, match="HOST_UPDATE_CONTRACT_INVALID:host"):
        build_host_update_plan("  ", root=ROOT)


def test_update_status_is_deterministic_without_network_or_mutation() -> None:
    available = build_host_update_plan("codex", latest_version="v1.9.0", root=ROOT)
    current = build_host_update_plan("codex", latest_version=CURRENT_VERSION, root=ROOT)
    ahead = build_host_update_plan("codex", latest_version="1.7.0", root=ROOT)
    unchecked = build_host_update_plan("codex", root=ROOT)

    assert available.update_status == "UPDATE_AVAILABLE"
    assert available.latest_version == "1.9.0"
    assert current.update_status == "UP_TO_DATE"
    assert ahead.update_status == "LOCAL_AHEAD"
    assert unchecked.update_status == "NOT_CHECKED"
    with pytest.raises(HostUpdateError, match="HOST_UPDATE_VERSION_INVALID"):
        build_host_update_plan("codex", latest_version="latest", root=ROOT)


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


def test_contract_read_failures_are_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(HostUpdateError, match="HOST_UPDATE_CONTRACT_MISSING"):
        load_host_update_contract(tmp_path)

    contract_path = tmp_path / "machine" / "hosts" / "update-contract.v1.json"
    contract_path.parent.mkdir(parents=True)
    contract_path.write_text("{not-json", encoding="utf-8")
    with pytest.raises(HostUpdateError, match="HOST_UPDATE_CONTRACT_INVALID_JSON"):
        load_host_update_contract(tmp_path)

    contract_path.write_text("[]", encoding="utf-8")
    with pytest.raises(HostUpdateError, match="root must be an object"):
        load_host_update_contract(tmp_path)


def test_contract_top_level_identity_and_version_fail_closed(tmp_path: Path) -> None:
    cases = [
        ("schema_version", "other.v1", "HOST_UPDATE_CONTRACT_SCHEMA_UNSUPPORTED"),
        ("default_behavior", "EXECUTE", "HOST_UPDATE_CONTRACT_INVALID:default_behavior"),
        ("unknown_host_policy", "ALLOW", "HOST_UPDATE_CONTRACT_INVALID:unknown_host_policy"),
        ("package_version", "not-semver", "HOST_UPDATE_VERSION_INVALID"),
    ]
    for field, value, match in cases:
        contract = _canonical_contract()
        contract[field] = value
        _write_contract_repo(tmp_path, contract)
        with pytest.raises(HostUpdateError, match=match):
            load_host_update_contract(tmp_path)

    contract = _canonical_contract()
    _write_contract_repo(tmp_path, contract, plugin_version="1.8.1")
    with pytest.raises(HostUpdateError, match="HOST_UPDATE_PACKAGE_VERSION_MISMATCH"):
        load_host_update_contract(tmp_path)

    contract = _canonical_contract()
    _write_contract_repo(tmp_path, contract, plugin_version="")
    with pytest.raises(HostUpdateError, match="HOST_UPDATE_CONTRACT_INVALID:plugin.version"):
        load_host_update_contract(tmp_path)


def test_contract_authority_invariants_fail_closed(tmp_path: Path) -> None:
    contract = _canonical_contract()
    contract["authority"] = []
    _write_contract_repo(tmp_path, contract)
    with pytest.raises(HostUpdateError, match="HOST_UPDATE_CONTRACT_INVALID:authority"):
        load_host_update_contract(tmp_path)

    for field, invalid in (
        ("planning_grants_mutation_authority", True),
        ("explicit_mutation_authorization_required", False),
        ("automatic_installed_integration_refresh", True),
    ):
        contract = _canonical_contract()
        authority = contract["authority"]
        assert isinstance(authority, dict)
        authority[field] = invalid
        _write_contract_repo(tmp_path, contract)
        with pytest.raises(HostUpdateError, match=f"HOST_UPDATE_AUTHORITY_INVARIANT:{field}"):
            load_host_update_contract(tmp_path)


def test_contract_host_container_and_identity_fail_closed(tmp_path: Path) -> None:
    for invalid_hosts in (None, [], ["not-an-object"]):
        contract = _canonical_contract()
        contract["hosts"] = invalid_hosts
        _write_contract_repo(tmp_path, contract)
        pattern = "HOST_UPDATE_CONTRACT_INVALID:hosts"
        with pytest.raises(HostUpdateError, match=pattern):
            load_host_update_contract(tmp_path)

    contract = _canonical_contract()
    hosts = contract["hosts"]
    assert isinstance(hosts, list)
    hosts.append(copy.deepcopy(hosts[0]))
    _write_contract_repo(tmp_path, contract)
    with pytest.raises(HostUpdateError, match="duplicate_host:codex"):
        load_host_update_contract(tmp_path)


def test_contract_host_maturity_and_execution_boundaries_fail_closed(tmp_path: Path) -> None:
    mutations = [
        ("codex", "maturity", "SCAFFOLD_ONLY", "HOST_UPDATE_MATURITY_DRIFT:codex"),
        ("cursor", "maturity", "SUPPORTED", "HOST_UPDATE_MATURITY_DRIFT:cursor"),
        ("codex", "execution_support", "INSTRUCTION_ONLY", "HOST_UPDATE_EXECUTION_BOUNDARY_DRIFT:codex"),
        ("cursor", "execution_support", "EXPLICIT_AUTHORIZATION_REQUIRED", "HOST_UPDATE_EXECUTION_BOUNDARY_DRIFT:cursor"),
        ("codex", "automatic_installed_integration_refresh", True, "HOST_UPDATE_AUTO_REFRESH_FORBIDDEN:codex"),
    ]
    for host_id, field, value, match in mutations:
        contract = _canonical_contract()
        _host(contract, host_id)[field] = value
        _write_contract_repo(tmp_path, contract)
        with pytest.raises(HostUpdateError, match=match):
            load_host_update_contract(tmp_path)


def test_contract_required_host_fields_and_lists_fail_closed(tmp_path: Path) -> None:
    for field in ("adapter_path", "update_mechanism", "plan_command"):
        contract = _canonical_contract()
        _host(contract, "codex")[field] = "  "
        _write_contract_repo(tmp_path, contract)
        with pytest.raises(HostUpdateError, match="HOST_UPDATE_CONTRACT_INVALID"):
            load_host_update_contract(tmp_path)

    for field, value in (
        ("update_instructions", []),
        ("validation_commands", ["same", "same"]),
        ("recovery_hints", [""]),
    ):
        contract = _canonical_contract()
        _host(contract, "codex")[field] = value
        _write_contract_repo(tmp_path, contract)
        with pytest.raises(HostUpdateError, match="HOST_UPDATE_CONTRACT_INVALID"):
            load_host_update_contract(tmp_path)


def test_contract_alias_and_host_set_integrity_fail_closed(tmp_path: Path) -> None:
    contract = _canonical_contract()
    _host(contract, "codex")["aliases"] = ["codex-alias"]
    _write_contract_repo(tmp_path, contract)
    with pytest.raises(HostUpdateError, match="canonical_alias_missing:codex"):
        load_host_update_contract(tmp_path)

    contract = _canonical_contract()
    _host(contract, "cursor")["aliases"] = ["cursor", "CODEX"]
    _write_contract_repo(tmp_path, contract)
    with pytest.raises(HostUpdateError, match="duplicate_alias:codex"):
        load_host_update_contract(tmp_path)

    contract = _canonical_contract()
    hosts = contract["hosts"]
    assert isinstance(hosts, list)
    hosts[:] = [record for record in hosts if isinstance(record, dict) and record["host_id"] != "zed"]
    _write_contract_repo(tmp_path, contract)
    with pytest.raises(HostUpdateError, match="HOST_UPDATE_HOST_SET_MISMATCH"):
        load_host_update_contract(tmp_path)

    contract = _canonical_contract()
    extra = copy.deepcopy(_host(contract, "cursor"))
    extra["host_id"] = "extra-host"
    extra["aliases"] = ["extra-host"]
    hosts = contract["hosts"]
    assert isinstance(hosts, list)
    hosts.append(extra)
    _write_contract_repo(tmp_path, contract)
    with pytest.raises(HostUpdateError, match="HOST_UPDATE_HOST_SET_MISMATCH"):
        load_host_update_contract(tmp_path)


def test_cli_emits_machine_plan_and_has_no_execute_flag() -> None:
    command = [
        sys.executable,
        str(ROOT / "scripts" / "host_update.py"),
        "--host",
        "antigravity",
        "--latest-version",
        CURRENT_VERSION,
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


def test_cli_unknown_host_fails_closed() -> None:
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "host_update.py"), "--host", "unknown-host", "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 2
    assert completed.stdout == ""
    assert "UNKNOWN_HOST_FAIL_CLOSED" in completed.stderr
