from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from orchestra_runtime.host_updates import HostUpdateError, resolve_host_update_record

from .adapter_protocol import PRAP_V1, AdapterError, ProtocolValidator


PRAP_CERTIFICATION_CONTRACT_SCHEMA_VERSION = 'orchestra.prap-certification-contract.v1'
PRAP_CERTIFICATION_EVIDENCE_SCHEMA_VERSION = 'orchestra.prap-certification-evidence.v1'
ADAPTER_SDK_SURFACE_VERSION = 'orchestra.adapter-sdk.v1'
_CONTRACT_ID = 'orchestra-prap-v1-certification'
_CONTRACT_PATH = Path('machine') / 'protocol' / 'prap-certification-contract.v1.json'
_SCHEMA_PATH = Path('machine') / 'schemas' / 'prap-certification-evidence.schema.json'
_HOST_MATURITY_SOURCE = 'machine/hosts/update-contract.v1.json'
_CERTIFIABLE_STATUSES = frozenset({'supported', 'compatible'})
_NON_CERTIFIABLE_STATUSES = frozenset({'reserved', 'rejected'})
_EXPECTED_TARGETS = (
    'codex',
    'antigravity',
    'claude-code',
    'cursor',
    'windsurf',
    'vscode',
    'vscodium',
    'jetbrains',
    'zed',
    'neovim',
)
_EXPECTED_SDK_EXPORTS = frozenset(
    {
        'AdapterCapabilities',
        'AdapterProtocol',
        'AdapterContext',
        'AdapterResponse',
        'AdapterError',
        'ProtocolValidator',
        'AdapterCertificationEvidence',
        'CertificationError',
        'certify_adapter',
        'certify_all_adapters',
    }
)


class CertificationError(ValueError):
    pass


@dataclass(frozen=True)
class AdapterCertificationEvidence:
    schema_version: str
    contract_schema_version: str
    contract_id: str
    sdk_surface_version: str
    requested_adapter_id: str
    protocol_adapter_id: str
    runtime_adapter: str
    protocol_version: str
    compatibility_status: str
    certification_status: str
    observed_host_id: str
    observed_host_maturity: str
    certification_promotes_host_maturity: bool
    prap_compatible: bool
    runtime_authority_granted: bool
    runtime_capabilities_granted: bool
    mutation_performed: bool
    installed_integration_refresh_performed: bool
    capabilities: dict[str, Any]
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload['reasons'] = list(self.reasons)
        return payload


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _root(root: Path | str | None) -> Path:
    return repository_root() if root is None else Path(root)


def _load_json(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError as exc:
        raise CertificationError(f'{label}_MISSING:{path}') from exc
    except json.JSONDecodeError as exc:
        raise CertificationError(f'{label}_INVALID_JSON:{path}:{exc}') from exc
    if not isinstance(value, dict):
        raise CertificationError(f'{label}_INVALID:root must be an object')
    return value


def _string_list(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise CertificationError(f'PRAP_CERTIFICATION_CONTRACT_INVALID:{field}')
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise CertificationError(f'PRAP_CERTIFICATION_CONTRACT_INVALID:{field}')
    items = tuple(item.strip() for item in value)
    if len(set(items)) != len(items):
        raise CertificationError(f'PRAP_CERTIFICATION_CONTRACT_INVALID:{field}:duplicates')
    return items


def load_prap_certification_contract(root: Path | str | None = None) -> dict[str, Any]:
    repo_root = _root(root)
    contract = _load_json(repo_root / _CONTRACT_PATH, label='PRAP_CERTIFICATION_CONTRACT')
    if contract.get('schema_version') != PRAP_CERTIFICATION_CONTRACT_SCHEMA_VERSION:
        raise CertificationError('PRAP_CERTIFICATION_CONTRACT_SCHEMA_UNSUPPORTED')
    if contract.get('contract_id') != _CONTRACT_ID:
        raise CertificationError('PRAP_CERTIFICATION_CONTRACT_INVALID:contract_id')
    if contract.get('sdk_surface_version') != ADAPTER_SDK_SURFACE_VERSION:
        raise CertificationError('PRAP_CERTIFICATION_CONTRACT_INVALID:sdk_surface_version')
    if contract.get('protocol_version') != PRAP_V1:
        raise CertificationError('PRAP_CERTIFICATION_PROTOCOL_VERSION_DRIFT')
    if contract.get('certification_behavior') != 'READ_ONLY_EVIDENCE':
        raise CertificationError('PRAP_CERTIFICATION_CONTRACT_INVALID:certification_behavior')
    if contract.get('unknown_adapter_policy') != 'FAIL_CLOSED':
        raise CertificationError('PRAP_CERTIFICATION_CONTRACT_INVALID:unknown_adapter_policy')

    certifiable = frozenset(_string_list(contract.get('certifiable_compatibility_statuses'), 'certifiable_compatibility_statuses'))
    if certifiable != _CERTIFIABLE_STATUSES:
        raise CertificationError('PRAP_CERTIFICATION_STATUS_SET_DRIFT:certifiable')
    non_certifiable = frozenset(_string_list(contract.get('non_certifiable_compatibility_statuses'), 'non_certifiable_compatibility_statuses'))
    if non_certifiable != _NON_CERTIFIABLE_STATUSES:
        raise CertificationError('PRAP_CERTIFICATION_STATUS_SET_DRIFT:non_certifiable')
    targets = _string_list(contract.get('certification_targets'), 'certification_targets')
    if targets != _EXPECTED_TARGETS:
        raise CertificationError('PRAP_CERTIFICATION_TARGET_SET_DRIFT')
    exports = frozenset(_string_list(contract.get('sdk_exports'), 'sdk_exports'))
    if exports != _EXPECTED_SDK_EXPORTS:
        raise CertificationError('ADAPTER_SDK_EXPORT_SET_DRIFT')

    authority = contract.get('authority')
    if not isinstance(authority, dict):
        raise CertificationError('PRAP_CERTIFICATION_CONTRACT_INVALID:authority')
    authority_invariants = {
        'certification_grants_runtime_authority': False,
        'certification_grants_runtime_capabilities': False,
        'certification_grants_mutation_authority': False,
        'automatic_installed_integration_refresh': False,
    }
    for key, expected in authority_invariants.items():
        if authority.get(key) is not expected:
            raise CertificationError(f'PRAP_CERTIFICATION_AUTHORITY_INVARIANT:{key}')

    host_maturity = contract.get('host_maturity')
    if not isinstance(host_maturity, dict):
        raise CertificationError('PRAP_CERTIFICATION_CONTRACT_INVALID:host_maturity')
    if host_maturity.get('source') != _HOST_MATURITY_SOURCE:
        raise CertificationError('PRAP_CERTIFICATION_HOST_MATURITY_SOURCE_DRIFT')
    if host_maturity.get('certification_can_promote') is not False:
        raise CertificationError('PRAP_CERTIFICATION_HOST_PROMOTION_FORBIDDEN')

    future_transport = contract.get('future_transport')
    if not isinstance(future_transport, dict):
        raise CertificationError('PRAP_CERTIFICATION_CONTRACT_INVALID:future_transport')
    if future_transport.get('mcp_is_transport_not_authority') is not True:
        raise CertificationError('PRAP_CERTIFICATION_MCP_AUTHORITY_DRIFT')
    if future_transport.get('mcp_implementation_in_this_contract') is not False:
        raise CertificationError('PRAP_CERTIFICATION_MCP_IMPLEMENTATION_FORBIDDEN')

    if contract.get('evidence_schema') != str(_SCHEMA_PATH).replace('\\', '/'):
        raise CertificationError('PRAP_CERTIFICATION_EVIDENCE_SCHEMA_DRIFT')
    schema = _load_json(repo_root / _SCHEMA_PATH, label='PRAP_CERTIFICATION_EVIDENCE_SCHEMA')
    if schema.get('type') != 'object':
        raise CertificationError('PRAP_CERTIFICATION_EVIDENCE_SCHEMA_INVALID')
    return contract


def certify_adapter(
    adapter_name: str,
    *,
    root: Path | str | None = None,
) -> AdapterCertificationEvidence:
    if not isinstance(adapter_name, str) or not adapter_name.strip():
        raise CertificationError('PRAP_CERTIFICATION_ADAPTER_REQUIRED')
    requested = adapter_name.strip().lower()
    repo_root = _root(root)
    contract = load_prap_certification_contract(repo_root)

    try:
        record = ProtocolValidator.compatibility_for(requested)
    except AdapterError as exc:
        raise CertificationError(f'UNKNOWN_ADAPTER_FAIL_CLOSED:{requested}') from exc
    if record.compatibility_status not in _CERTIFIABLE_STATUSES:
        raise CertificationError(
            f'PRAP_CERTIFICATION_NOT_CERTIFIABLE:{requested}:{record.compatibility_status}'
        )
    if record.protocol_version != contract['protocol_version']:
        raise CertificationError(f'PRAP_CERTIFICATION_MATRIX_PROTOCOL_DRIFT:{requested}')

    from orchestra_runtime.factories import AdapterFactory

    try:
        adapter = AdapterFactory.create(requested, repo_root)
    except ValueError as exc:
        raise CertificationError(f'PRAP_CERTIFICATION_RUNTIME_ADAPTER_UNAVAILABLE:{requested}') from exc
    errors = ProtocolValidator.validate_adapter(adapter)
    if errors:
        raise CertificationError('PRAP_CERTIFICATION_PROTOCOL_INVALID:' + '|'.join(errors))
    protocol = adapter.protocol_metadata()

    if protocol.protocol_version != contract['protocol_version']:
        raise CertificationError(f'PRAP_CERTIFICATION_PROTOCOL_VERSION_DRIFT:{requested}')
    if record.runtime_adapter != protocol.runtime_adapter:
        raise CertificationError(f'PRAP_CERTIFICATION_RUNTIME_MAPPING_DRIFT:{requested}')
    if record.host_type != protocol.host_type:
        raise CertificationError(f'PRAP_CERTIFICATION_HOST_TYPE_DRIFT:{requested}')
    if requested == 'vscodium':
        if protocol.adapter_id != 'vscode' or record.compatibility_status != 'compatible':
            raise CertificationError('PRAP_CERTIFICATION_VSCODIUM_MAPPING_DRIFT')
    elif record.adapter_id != protocol.adapter_id:
        raise CertificationError(f'PRAP_CERTIFICATION_ADAPTER_ID_DRIFT:{requested}')

    try:
        host_record = resolve_host_update_record(requested, repo_root)
    except HostUpdateError as exc:
        raise CertificationError(f'PRAP_CERTIFICATION_HOST_MATURITY_UNAVAILABLE:{requested}:{exc}') from exc
    host_id = str(host_record.get('host_id', ''))
    maturity = str(host_record.get('maturity', ''))
    if maturity not in {'SUPPORTED', 'SCAFFOLD_ONLY'}:
        raise CertificationError(f'PRAP_CERTIFICATION_HOST_MATURITY_DRIFT:{requested}:{maturity}')
    if requested == 'vscodium':
        if host_id != 'vscode':
            raise CertificationError('PRAP_CERTIFICATION_VSCODIUM_HOST_MAPPING_DRIFT')
    elif host_id != requested:
        raise CertificationError(f'PRAP_CERTIFICATION_HOST_MAPPING_DRIFT:{requested}:{host_id}')

    return AdapterCertificationEvidence(
        schema_version=PRAP_CERTIFICATION_EVIDENCE_SCHEMA_VERSION,
        contract_schema_version=PRAP_CERTIFICATION_CONTRACT_SCHEMA_VERSION,
        contract_id=_CONTRACT_ID,
        sdk_surface_version=ADAPTER_SDK_SURFACE_VERSION,
        requested_adapter_id=requested,
        protocol_adapter_id=protocol.adapter_id,
        runtime_adapter=protocol.runtime_adapter,
        protocol_version=protocol.protocol_version,
        compatibility_status=record.compatibility_status,
        certification_status='PASS',
        observed_host_id=host_id,
        observed_host_maturity=maturity,
        certification_promotes_host_maturity=False,
        prap_compatible=True,
        runtime_authority_granted=False,
        runtime_capabilities_granted=False,
        mutation_performed=False,
        installed_integration_refresh_performed=False,
        capabilities=protocol.capabilities.to_metadata(),
        reasons=(
            'PRAP_PROTOCOL_VALID',
            'COMPATIBILITY_STATUS_CERTIFIABLE',
            'HOST_MATURITY_PRESERVED',
            'READ_ONLY_CERTIFICATION',
        ),
    )


def certify_all_adapters(
    *,
    root: Path | str | None = None,
) -> tuple[AdapterCertificationEvidence, ...]:
    repo_root = _root(root)
    contract = load_prap_certification_contract(repo_root)
    return tuple(certify_adapter(adapter_id, root=repo_root) for adapter_id in contract['certification_targets'])
