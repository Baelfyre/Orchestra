import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from orchestra_runtime.factories import AdapterFactory
from orchestra_runtime.host_updates import HostUpdateError
from orchestra_runtime.protocol import PRAP_V1, AdapterCapabilities, AdapterProtocol, ProtocolValidator
from orchestra_runtime.protocol import certification as certification_module
from orchestra_runtime.protocol.certification import (
    ADAPTER_SDK_SURFACE_VERSION,
    CertificationError,
    certify_adapter,
    certify_all_adapters,
    load_prap_certification_contract,
)
from orchestra_runtime.protocol.sdk import (
    SDK_PROTOCOL_VERSION,
    SDK_SURFACE_VERSION,
    AdapterCapabilities as SdkAdapterCapabilities,
    AdapterProtocol as SdkAdapterProtocol,
)


ROOT = Path(__file__).resolve().parents[2]
EXPECTED_TARGETS = {
    'codex', 'antigravity', 'claude-code', 'cursor', 'windsurf',
    'vscode', 'vscodium', 'jetbrains', 'zed', 'neovim'
}


def _contract_copy():
    return json.loads(
        (ROOT / 'machine' / 'protocol' / 'prap-certification-contract.v1.json').read_text(encoding='utf-8')
    )


def _write_contract(tmp_path, contract):
    target = tmp_path / 'machine' / 'protocol' / 'prap-certification-contract.v1.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(contract), encoding='utf-8')
    return target


def _write_schema(tmp_path, schema):
    target = tmp_path / 'machine' / 'schemas' / 'prap-certification-evidence.schema.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(schema), encoding='utf-8')
    return target


def _adapter(
    *,
    adapter_id='codex',
    runtime_adapter='codex',
    host_type='ai-assistant',
    protocol_version=PRAP_V1,
):
    class FakeAdapter:
        def protocol_metadata(self):
            return AdapterProtocol(
                adapter_id=adapter_id,
                display_name='Test Adapter',
                runtime_adapter=runtime_adapter,
                host_type=host_type,
                protocol_version=protocol_version,
                packaging_status='marketplace',
                marketplace_status='available',
                capabilities=AdapterCapabilities(
                    supports_commands=True,
                    supports_context=True,
                    supports_file_handoff=True,
                    supports_workspace=True,
                    supports_audit_trace=True,
                    supports_streaming=False,
                    supports_governance=True,
                ),
            )

    return FakeAdapter()


def test_sdk_surface_reuses_existing_prap_v1_contract_types():
    assert SDK_SURFACE_VERSION == ADAPTER_SDK_SURFACE_VERSION
    assert SDK_PROTOCOL_VERSION == PRAP_V1
    assert SdkAdapterCapabilities is AdapterCapabilities
    assert SdkAdapterProtocol is AdapterProtocol


def test_certification_contract_is_read_only_fail_closed_and_non_authorizing():
    contract = load_prap_certification_contract(ROOT)
    assert contract['certification_behavior'] == 'READ_ONLY_EVIDENCE'
    assert contract['unknown_adapter_policy'] == 'FAIL_CLOSED'
    assert contract['protocol_version'] == PRAP_V1
    assert contract['authority'] == {
        'certification_grants_runtime_authority': False,
        'certification_grants_runtime_capabilities': False,
        'certification_grants_mutation_authority': False,
        'automatic_installed_integration_refresh': False,
    }
    assert contract['host_maturity']['certification_can_promote'] is False
    assert contract['future_transport']['mcp_is_transport_not_authority'] is True
    assert contract['future_transport']['mcp_implementation_in_this_contract'] is False


def test_all_declared_targets_certify_without_promoting_host_maturity():
    evidence = certify_all_adapters(root=ROOT)
    by_id = {item.requested_adapter_id: item for item in evidence}
    assert set(by_id) == EXPECTED_TARGETS
    assert {key for key, item in by_id.items() if item.observed_host_maturity == 'SUPPORTED'} == {
        'codex', 'antigravity'
    }
    for item in evidence:
        assert item.certification_status == 'PASS'
        assert item.prap_compatible is True
        assert item.certification_promotes_host_maturity is False
        assert item.runtime_authority_granted is False
        assert item.runtime_capabilities_granted is False
        assert item.mutation_performed is False
        assert item.installed_integration_refresh_performed is False
    for adapter_id in EXPECTED_TARGETS - {'codex', 'antigravity'}:
        assert by_id[adapter_id].observed_host_maturity == 'SCAFFOLD_ONLY'


def test_vscodium_certification_preserves_vscode_runtime_and_scaffold_mapping():
    evidence = certify_adapter('vscodium', root=ROOT)
    assert evidence.requested_adapter_id == 'vscodium'
    assert evidence.protocol_adapter_id == 'vscode'
    assert evidence.runtime_adapter == 'vscode'
    assert evidence.compatibility_status == 'compatible'
    assert evidence.observed_host_id == 'vscode'
    assert evidence.observed_host_maturity == 'SCAFFOLD_ONLY'


@pytest.mark.parametrize('adapter_id, marker', [
    ('totally-unknown', 'UNKNOWN_ADAPTER_FAIL_CLOSED'),
    ('future', 'PRAP_CERTIFICATION_NOT_CERTIFIABLE:future:reserved'),
    ('unknown', 'PRAP_CERTIFICATION_NOT_CERTIFIABLE:unknown:rejected'),
])
def test_unknown_reserved_and_rejected_adapters_fail_closed(adapter_id, marker):
    with pytest.raises(CertificationError, match=marker):
        certify_adapter(adapter_id, root=ROOT)


def test_contract_host_promotion_tampering_fails_closed(tmp_path):
    contract = load_prap_certification_contract(ROOT)
    contract['host_maturity']['certification_can_promote'] = True
    _write_contract(tmp_path, contract)
    with pytest.raises(CertificationError, match='PRAP_CERTIFICATION_HOST_PROMOTION_FORBIDDEN'):
        load_prap_certification_contract(tmp_path)


def test_runtime_protocol_validation_failure_is_not_certified(monkeypatch):
    monkeypatch.setattr(
        AdapterFactory,
        'create',
        staticmethod(lambda *_args, **_kwargs: _adapter(protocol_version='PRAP v2')),
    )
    with pytest.raises(CertificationError, match='PRAP_CERTIFICATION_PROTOCOL_INVALID'):
        certify_adapter('codex', root=ROOT)


def test_unrecognized_host_maturity_fails_closed(monkeypatch):
    monkeypatch.setattr(
        certification_module,
        'resolve_host_update_record',
        lambda *_args, **_kwargs: {'host_id': 'codex', 'maturity': 'PROMOTED'},
    )
    with pytest.raises(CertificationError, match='PRAP_CERTIFICATION_HOST_MATURITY_DRIFT'):
        certify_adapter('codex', root=ROOT)


def test_evidence_matches_machine_schema_required_and_constant_fields():
    schema = json.loads((ROOT / 'machine' / 'schemas' / 'prap-certification-evidence.schema.json').read_text(encoding='utf-8'))
    evidence = certify_adapter('codex', root=ROOT).to_dict()
    assert set(schema['required']) == set(evidence)
    for key, definition in schema['properties'].items():
        if 'const' in definition:
            assert evidence[key] == definition['const']


def test_cli_emits_read_only_json_and_has_no_execute_surface():
    command = [sys.executable, str(ROOT / 'scripts' / 'certify_adapter.py'), '--adapter', 'codex', '--json']
    completed = subprocess.run(command, cwd=ROOT, check=False, capture_output=True, text=True)
    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload['certification_status'] == 'PASS'
    assert payload['mutation_performed'] is False
    assert 'ORCHESTRA_PRAP_CERTIFICATION=READ_ONLY_PASS' in completed.stderr

    rejected = subprocess.run(command + ['--execute'], cwd=ROOT, check=False, capture_output=True, text=True)
    assert rejected.returncode != 0
    assert 'unrecognized arguments: --execute' in rejected.stderr


def test_contract_loader_fails_closed_for_missing_invalid_json_and_non_object(tmp_path):
    with pytest.raises(CertificationError, match='PRAP_CERTIFICATION_CONTRACT_MISSING'):
        load_prap_certification_contract(tmp_path)

    target = tmp_path / 'machine' / 'protocol' / 'prap-certification-contract.v1.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text('{not-json', encoding='utf-8')
    with pytest.raises(CertificationError, match='PRAP_CERTIFICATION_CONTRACT_INVALID_JSON'):
        load_prap_certification_contract(tmp_path)

    target.write_text('[]', encoding='utf-8')
    with pytest.raises(CertificationError, match='PRAP_CERTIFICATION_CONTRACT_INVALID'):
        load_prap_certification_contract(tmp_path)


@pytest.mark.parametrize(
    'field,value,marker',
    [
        ('schema_version', 'orchestra.prap-certification-contract.v2', 'PRAP_CERTIFICATION_CONTRACT_SCHEMA_UNSUPPORTED'),
        ('contract_id', 'wrong', 'PRAP_CERTIFICATION_CONTRACT_INVALID:contract_id'),
        ('sdk_surface_version', 'orchestra.adapter-sdk.v2', 'PRAP_CERTIFICATION_CONTRACT_INVALID:sdk_surface_version'),
        ('protocol_version', 'PRAP v2', 'PRAP_CERTIFICATION_PROTOCOL_VERSION_DRIFT'),
        ('certification_behavior', 'MUTATING', 'PRAP_CERTIFICATION_CONTRACT_INVALID:certification_behavior'),
        ('unknown_adapter_policy', 'ALLOW', 'PRAP_CERTIFICATION_CONTRACT_INVALID:unknown_adapter_policy'),
    ],
)
def test_top_level_contract_drift_fails_closed(tmp_path, field, value, marker):
    contract = _contract_copy()
    contract[field] = value
    _write_contract(tmp_path, contract)
    with pytest.raises(CertificationError, match=marker):
        load_prap_certification_contract(tmp_path)


@pytest.mark.parametrize(
    'field,value,marker',
    [
        ('certifiable_compatibility_statuses', ['supported'], 'PRAP_CERTIFICATION_STATUS_SET_DRIFT:certifiable'),
        ('non_certifiable_compatibility_statuses', ['rejected'], 'PRAP_CERTIFICATION_STATUS_SET_DRIFT:non_certifiable'),
        ('certification_targets', ['codex'], 'PRAP_CERTIFICATION_TARGET_SET_DRIFT'),
        ('sdk_exports', ['AdapterProtocol'], 'ADAPTER_SDK_EXPORT_SET_DRIFT'),
    ],
)
def test_contract_set_drift_fails_closed(tmp_path, field, value, marker):
    contract = _contract_copy()
    contract[field] = value
    _write_contract(tmp_path, contract)
    with pytest.raises(CertificationError, match=marker):
        load_prap_certification_contract(tmp_path)


@pytest.mark.parametrize('value', [None, [], [1], ['supported', 'supported']])
def test_contract_string_list_validation_fails_closed(value):
    with pytest.raises(CertificationError, match='PRAP_CERTIFICATION_CONTRACT_INVALID:test'):
        certification_module._string_list(value, 'test')


def test_authority_and_host_maturity_contract_drift_fail_closed(tmp_path):
    contract = _contract_copy()
    contract['authority'] = []
    _write_contract(tmp_path, contract)
    with pytest.raises(CertificationError, match='PRAP_CERTIFICATION_CONTRACT_INVALID:authority'):
        load_prap_certification_contract(tmp_path)

    contract = _contract_copy()
    contract['authority']['certification_grants_runtime_authority'] = True
    _write_contract(tmp_path, contract)
    with pytest.raises(CertificationError, match='PRAP_CERTIFICATION_AUTHORITY_INVARIANT'):
        load_prap_certification_contract(tmp_path)

    contract = _contract_copy()
    contract['host_maturity'] = []
    _write_contract(tmp_path, contract)
    with pytest.raises(CertificationError, match='PRAP_CERTIFICATION_CONTRACT_INVALID:host_maturity'):
        load_prap_certification_contract(tmp_path)

    contract = _contract_copy()
    contract['host_maturity']['source'] = 'wrong.json'
    _write_contract(tmp_path, contract)
    with pytest.raises(CertificationError, match='PRAP_CERTIFICATION_HOST_MATURITY_SOURCE_DRIFT'):
        load_prap_certification_contract(tmp_path)


def test_future_transport_and_evidence_schema_drift_fail_closed(tmp_path):
    contract = _contract_copy()
    contract['future_transport'] = []
    _write_contract(tmp_path, contract)
    with pytest.raises(CertificationError, match='PRAP_CERTIFICATION_CONTRACT_INVALID:future_transport'):
        load_prap_certification_contract(tmp_path)

    contract = _contract_copy()
    contract['future_transport']['mcp_is_transport_not_authority'] = False
    _write_contract(tmp_path, contract)
    with pytest.raises(CertificationError, match='PRAP_CERTIFICATION_MCP_AUTHORITY_DRIFT'):
        load_prap_certification_contract(tmp_path)

    contract = _contract_copy()
    contract['future_transport']['mcp_implementation_in_this_contract'] = True
    _write_contract(tmp_path, contract)
    with pytest.raises(CertificationError, match='PRAP_CERTIFICATION_MCP_IMPLEMENTATION_FORBIDDEN'):
        load_prap_certification_contract(tmp_path)

    contract = _contract_copy()
    contract['evidence_schema'] = 'wrong.json'
    _write_contract(tmp_path, contract)
    with pytest.raises(CertificationError, match='PRAP_CERTIFICATION_EVIDENCE_SCHEMA_DRIFT'):
        load_prap_certification_contract(tmp_path)


def test_invalid_evidence_schema_fails_closed(tmp_path):
    _write_contract(tmp_path, _contract_copy())
    _write_schema(tmp_path, {'type': 'array'})
    with pytest.raises(CertificationError, match='PRAP_CERTIFICATION_EVIDENCE_SCHEMA_INVALID'):
        load_prap_certification_contract(tmp_path)


def test_blank_adapter_identity_fails_closed():
    with pytest.raises(CertificationError, match='PRAP_CERTIFICATION_ADAPTER_REQUIRED'):
        certify_adapter('   ', root=ROOT)


def test_compatibility_matrix_protocol_drift_fails_closed(monkeypatch):
    record = ProtocolValidator.compatibility_for('codex')
    monkeypatch.setattr(
        ProtocolValidator,
        'compatibility_for',
        lambda _adapter_name: replace(record, protocol_version='PRAP v2'),
    )
    with pytest.raises(CertificationError, match='PRAP_CERTIFICATION_MATRIX_PROTOCOL_DRIFT'):
        certify_adapter('codex', root=ROOT)


def test_runtime_adapter_unavailable_fails_closed(monkeypatch):
    def unavailable(*_args, **_kwargs):
        raise ValueError('unavailable')

    monkeypatch.setattr(AdapterFactory, 'create', staticmethod(unavailable))
    with pytest.raises(CertificationError, match='PRAP_CERTIFICATION_RUNTIME_ADAPTER_UNAVAILABLE'):
        certify_adapter('codex', root=ROOT)


def test_post_validation_protocol_version_drift_fails_closed(monkeypatch):
    monkeypatch.setattr(AdapterFactory, 'create', staticmethod(lambda *_args, **_kwargs: _adapter(protocol_version='PRAP v2')))
    monkeypatch.setattr(ProtocolValidator, 'validate_adapter', lambda _adapter_value: [])
    with pytest.raises(CertificationError, match='PRAP_CERTIFICATION_PROTOCOL_VERSION_DRIFT:codex'):
        certify_adapter('codex', root=ROOT)


@pytest.mark.parametrize(
    'fake_adapter,marker',
    [
        (_adapter(runtime_adapter='other'), 'PRAP_CERTIFICATION_RUNTIME_MAPPING_DRIFT'),
        (_adapter(host_type='ide'), 'PRAP_CERTIFICATION_HOST_TYPE_DRIFT'),
        (_adapter(adapter_id='other'), 'PRAP_CERTIFICATION_ADAPTER_ID_DRIFT'),
    ],
)
def test_runtime_identity_mapping_drift_fails_closed(monkeypatch, fake_adapter, marker):
    monkeypatch.setattr(AdapterFactory, 'create', staticmethod(lambda *_args, **_kwargs: fake_adapter))
    with pytest.raises(CertificationError, match=marker):
        certify_adapter('codex', root=ROOT)


def test_vscodium_runtime_identity_drift_fails_closed(monkeypatch):
    fake_adapter = _adapter(adapter_id='other', runtime_adapter='vscode', host_type='ide')
    monkeypatch.setattr(AdapterFactory, 'create', staticmethod(lambda *_args, **_kwargs: fake_adapter))
    with pytest.raises(CertificationError, match='PRAP_CERTIFICATION_VSCODIUM_MAPPING_DRIFT'):
        certify_adapter('vscodium', root=ROOT)


def test_host_update_lookup_failure_is_not_certified(monkeypatch):
    def fail_host_lookup(*_args, **_kwargs):
        raise HostUpdateError('host-contract-failure')

    monkeypatch.setattr(certification_module, 'resolve_host_update_record', fail_host_lookup)
    with pytest.raises(CertificationError, match='PRAP_CERTIFICATION_HOST_MATURITY_UNAVAILABLE'):
        certify_adapter('codex', root=ROOT)


def test_vscodium_and_canonical_host_mapping_drift_fail_closed(monkeypatch):
    monkeypatch.setattr(
        certification_module,
        'resolve_host_update_record',
        lambda *_args, **_kwargs: {'host_id': 'codex', 'maturity': 'SCAFFOLD_ONLY'},
    )
    with pytest.raises(CertificationError, match='PRAP_CERTIFICATION_VSCODIUM_HOST_MAPPING_DRIFT'):
        certify_adapter('vscodium', root=ROOT)

    monkeypatch.setattr(
        certification_module,
        'resolve_host_update_record',
        lambda *_args, **_kwargs: {'host_id': 'vscode', 'maturity': 'SUPPORTED'},
    )
    with pytest.raises(CertificationError, match='PRAP_CERTIFICATION_HOST_MAPPING_DRIFT'):
        certify_adapter('codex', root=ROOT)
