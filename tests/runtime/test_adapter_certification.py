import json
import subprocess
import sys
from pathlib import Path

import pytest

from orchestra_runtime.factories import AdapterFactory
from orchestra_runtime.protocol import PRAP_V1, AdapterCapabilities, AdapterProtocol
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
    target = tmp_path / 'machine' / 'protocol' / 'prap-certification-contract.v1.json'
    target.parent.mkdir(parents=True)
    target.write_text(json.dumps(contract), encoding='utf-8')
    with pytest.raises(CertificationError, match='PRAP_CERTIFICATION_HOST_PROMOTION_FORBIDDEN'):
        load_prap_certification_contract(tmp_path)


def test_runtime_protocol_validation_failure_is_not_certified(monkeypatch):
    class InvalidAdapter:
        def protocol_metadata(self):
            return AdapterProtocol(
                adapter_id='codex',
                display_name='Codex',
                runtime_adapter='codex',
                host_type='ai-assistant',
                protocol_version='PRAP v2',
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

    monkeypatch.setattr(AdapterFactory, 'create', staticmethod(lambda *_args, **_kwargs: InvalidAdapter()))
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
