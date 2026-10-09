from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

HOST_UPDATE_CONTRACT_SCHEMA_VERSION = "orchestra.host-update-contract.v1"
HOST_UPDATE_PLAN_SCHEMA_VERSION = "orchestra.host-update-plan.v1"
SUPPORTED_HOSTS = frozenset({"codex", "antigravity"})
SCAFFOLD_ONLY_HOSTS = frozenset(
    {"claude-code", "cursor", "windsurf", "vscode", "jetbrains", "zed", "neovim"}
)
_EXPECTED_HOSTS = SUPPORTED_HOSTS | SCAFFOLD_ONLY_HOSTS
_CONTRACT_PATH = Path("machine") / "hosts" / "update-contract.v1.json"
_SEMVER_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")


class HostUpdateError(ValueError):
    pass


@dataclass(frozen=True)
class HostUpdatePlan:
    schema_version: str
    contract_schema_version: str
    requested_host: str
    host_id: str
    package_version: str
    latest_version: str | None
    update_status: str
    maturity: str
    update_mechanism: str
    default_behavior: str
    execution_support: str
    execution_authorized: bool
    execution_requires_separate_authorization: bool
    automatic_installed_integration_refresh: bool
    adapter_path: str
    plan_command: str
    update_instructions: tuple[str, ...]
    validation_commands: tuple[str, ...]
    recovery_hints: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in ("update_instructions", "validation_commands", "recovery_hints"):
            payload[key] = list(payload[key])
        return payload


def repository_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _root(root: Path | str | None) -> Path:
    return repository_root() if root is None else Path(root)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise HostUpdateError(f"HOST_UPDATE_CONTRACT_MISSING:{path}") from exc
    except json.JSONDecodeError as exc:
        raise HostUpdateError(f"HOST_UPDATE_CONTRACT_INVALID_JSON:{path}:{exc}") from exc
    if not isinstance(value, dict):
        raise HostUpdateError("HOST_UPDATE_CONTRACT_INVALID:root must be an object")
    return value


def _nonempty_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise HostUpdateError(f"HOST_UPDATE_CONTRACT_INVALID:{field}")
    return value.strip()


def _string_list(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise HostUpdateError(f"HOST_UPDATE_CONTRACT_INVALID:{field}")
    items = tuple(_nonempty_string(item, field) for item in value)
    if len(set(items)) != len(items):
        raise HostUpdateError(f"HOST_UPDATE_CONTRACT_INVALID:{field}:duplicates")
    return items


def _parse_semver(value: str) -> tuple[int, int, int]:
    match = _SEMVER_RE.fullmatch(value.strip())
    if match is None:
        raise HostUpdateError(f"HOST_UPDATE_VERSION_INVALID:{value}")
    return tuple(int(part) for part in match.groups())


def _package_version(repo_root: Path) -> str:
    payload = _load_json(repo_root / "plugin.json")
    return _nonempty_string(payload.get("version"), "plugin.version")


def load_host_update_contract(root: Path | str | None = None) -> dict[str, Any]:
    repo_root = _root(root)
    contract = _load_json(repo_root / _CONTRACT_PATH)
    if contract.get("schema_version") != HOST_UPDATE_CONTRACT_SCHEMA_VERSION:
        raise HostUpdateError("HOST_UPDATE_CONTRACT_SCHEMA_UNSUPPORTED")
    if contract.get("default_behavior") != "READ_ONLY_PLAN":
        raise HostUpdateError("HOST_UPDATE_CONTRACT_INVALID:default_behavior")
    if contract.get("unknown_host_policy") != "FAIL_CLOSED":
        raise HostUpdateError("HOST_UPDATE_CONTRACT_INVALID:unknown_host_policy")

    package_version = _nonempty_string(contract.get("package_version"), "package_version")
    _parse_semver(package_version)
    if package_version != _package_version(repo_root):
        raise HostUpdateError("HOST_UPDATE_PACKAGE_VERSION_MISMATCH")

    authority = contract.get("authority")
    if not isinstance(authority, dict):
        raise HostUpdateError("HOST_UPDATE_CONTRACT_INVALID:authority")
    required_authority = {
        "planning_grants_mutation_authority": False,
        "explicit_mutation_authorization_required": True,
        "automatic_installed_integration_refresh": False,
    }
    for key, expected in required_authority.items():
        if authority.get(key) is not expected:
            raise HostUpdateError(f"HOST_UPDATE_AUTHORITY_INVARIANT:{key}")

    hosts = contract.get("hosts")
    if not isinstance(hosts, list) or not hosts:
        raise HostUpdateError("HOST_UPDATE_CONTRACT_INVALID:hosts")

    host_ids: set[str] = set()
    aliases: set[str] = set()
    for index, raw in enumerate(hosts):
        if not isinstance(raw, dict):
            raise HostUpdateError(f"HOST_UPDATE_CONTRACT_INVALID:hosts[{index}]")
        host_id = _nonempty_string(raw.get("host_id"), f"hosts[{index}].host_id")
        if host_id in host_ids:
            raise HostUpdateError(f"HOST_UPDATE_CONTRACT_INVALID:duplicate_host:{host_id}")
        host_ids.add(host_id)

        maturity = raw.get("maturity")
        if host_id in SUPPORTED_HOSTS and maturity != "SUPPORTED":
            raise HostUpdateError(f"HOST_UPDATE_MATURITY_DRIFT:{host_id}")
        if host_id in SCAFFOLD_ONLY_HOSTS and maturity != "SCAFFOLD_ONLY":
            raise HostUpdateError(f"HOST_UPDATE_MATURITY_DRIFT:{host_id}")

        execution_support = raw.get("execution_support")
        if maturity == "SUPPORTED" and execution_support != "EXPLICIT_AUTHORIZATION_REQUIRED":
            raise HostUpdateError(f"HOST_UPDATE_EXECUTION_BOUNDARY_DRIFT:{host_id}")
        if maturity == "SCAFFOLD_ONLY" and execution_support != "INSTRUCTION_ONLY":
            raise HostUpdateError(f"HOST_UPDATE_EXECUTION_BOUNDARY_DRIFT:{host_id}")
        if raw.get("automatic_installed_integration_refresh") is not False:
            raise HostUpdateError(f"HOST_UPDATE_AUTO_REFRESH_FORBIDDEN:{host_id}")

        _nonempty_string(raw.get("adapter_path"), f"hosts[{index}].adapter_path")
        _nonempty_string(raw.get("update_mechanism"), f"hosts[{index}].update_mechanism")
        _nonempty_string(raw.get("plan_command"), f"hosts[{index}].plan_command")
        _string_list(raw.get("update_instructions"), f"hosts[{index}].update_instructions")
        _string_list(raw.get("validation_commands"), f"hosts[{index}].validation_commands")
        _string_list(raw.get("recovery_hints"), f"hosts[{index}].recovery_hints")

        record_aliases = _string_list(raw.get("aliases"), f"hosts[{index}].aliases")
        if host_id not in record_aliases:
            raise HostUpdateError(f"HOST_UPDATE_CONTRACT_INVALID:canonical_alias_missing:{host_id}")
        for alias in record_aliases:
            normalized = alias.lower()
            if normalized in aliases:
                raise HostUpdateError(f"HOST_UPDATE_CONTRACT_INVALID:duplicate_alias:{normalized}")
            aliases.add(normalized)

    if host_ids != _EXPECTED_HOSTS:
        missing = sorted(_EXPECTED_HOSTS - host_ids)
        extra = sorted(host_ids - _EXPECTED_HOSTS)
        raise HostUpdateError(f"HOST_UPDATE_HOST_SET_MISMATCH:missing={missing}:extra={extra}")
    return contract


def _host_index(contract: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    by_id: dict[str, dict[str, Any]] = {}
    aliases: dict[str, str] = {}
    for record in contract["hosts"]:
        host_id = str(record["host_id"])
        by_id[host_id] = record
        for alias in record["aliases"]:
            aliases[str(alias).lower()] = host_id
    return by_id, aliases


def resolve_host_update_record(host: str, root: Path | str | None = None) -> dict[str, Any]:
    requested = _nonempty_string(host, "host").lower()
    contract = load_host_update_contract(root)
    by_id, aliases = _host_index(contract)
    host_id = aliases.get(requested)
    if host_id is None:
        raise HostUpdateError(f"UNKNOWN_HOST_FAIL_CLOSED:{requested}")
    return dict(by_id[host_id])


def _update_status(current: str, latest: str | None) -> tuple[str, str | None]:
    if latest is None:
        return "NOT_CHECKED", None
    current_value = _parse_semver(current)
    latest_value = _parse_semver(latest)
    normalized_latest = latest.removeprefix("v")
    if latest_value > current_value:
        return "UPDATE_AVAILABLE", normalized_latest
    if latest_value == current_value:
        return "UP_TO_DATE", normalized_latest
    return "LOCAL_AHEAD", normalized_latest


def build_host_update_plan(
    host: str,
    *,
    latest_version: str | None = None,
    root: Path | str | None = None,
) -> HostUpdatePlan:
    repo_root = _root(root)
    contract = load_host_update_contract(repo_root)
    by_id, aliases = _host_index(contract)
    requested = _nonempty_string(host, "host").lower()
    host_id = aliases.get(requested)
    if host_id is None:
        raise HostUpdateError(f"UNKNOWN_HOST_FAIL_CLOSED:{requested}")
    record = by_id[host_id]
    current_version = str(contract["package_version"])
    status, normalized_latest = _update_status(current_version, latest_version)
    execution_support = str(record["execution_support"])

    return HostUpdatePlan(
        schema_version=HOST_UPDATE_PLAN_SCHEMA_VERSION,
        contract_schema_version=HOST_UPDATE_CONTRACT_SCHEMA_VERSION,
        requested_host=requested,
        host_id=host_id,
        package_version=current_version,
        latest_version=normalized_latest,
        update_status=status,
        maturity=str(record["maturity"]),
        update_mechanism=str(record["update_mechanism"]),
        default_behavior="READ_ONLY_PLAN",
        execution_support=execution_support,
        execution_authorized=False,
        execution_requires_separate_authorization=(execution_support == "EXPLICIT_AUTHORIZATION_REQUIRED"),
        automatic_installed_integration_refresh=False,
        adapter_path=str(record["adapter_path"]),
        plan_command=str(record["plan_command"]),
        update_instructions=tuple(str(item) for item in record["update_instructions"]),
        validation_commands=tuple(str(item) for item in record["validation_commands"]),
        recovery_hints=tuple(str(item) for item in record["recovery_hints"]),
    )
