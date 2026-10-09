from __future__ import annotations

import copy
import json
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / 'machine' / 'schemas' / 'ui-implementation-profile.v1.schema.json'
CANONICAL_MODEL_PATH = ROOT / 'machine' / 'ui' / 'ui-implementation-profile.v1.json'
FIXTURES_DIR = ROOT / 'tests' / 'fixtures' / 'ui'

VALID_FIXTURES = (
    FIXTURES_DIR / 'uief1-valid-minimal-safe.json',
    FIXTURES_DIR / 'uief1-valid-contract-fidelity.json',
)

INVALID_FIXTURES = (
    FIXTURES_DIR / 'uief1-invalid-unknown-profile.json',
    FIXTURES_DIR / 'uief1-invalid-missing-evidence.json',
    FIXTURES_DIR / 'uief1-invalid-ponytail-selector.json',
    FIXTURES_DIR / 'uief1-invalid-malformed-pattern-ref.json',
    FIXTURES_DIR / 'uief1-invalid-unauthorized-downgrade.json',
    FIXTURES_DIR / 'uief1-invalid-contaminated-execution-mode.json',
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def _validator() -> jsonschema.Draft202012Validator:
    schema = _load(SCHEMA_PATH)
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


def test_uief1_schema_and_canonical_reference_are_valid() -> None:
    validator = _validator()
    canonical_model = _load(CANONICAL_MODEL_PATH)
    validator.validate(canonical_model)

    assert canonical_model['schema_version'] == 'orchestra.ui-implementation-profile.v1'
    assert canonical_model['profile'] == 'UI_CONTRACT_FIDELITY'
    assert canonical_model['selected_by'] == 'conductor'
    assert canonical_model['authority']['ponytail_can_self_select'] is False
    assert canonical_model['authority']['ponytail_can_downgrade'] is False
    assert canonical_model['authority']['grants_specialist_authority'] is False
    assert canonical_model['authority']['grants_implementation_authority'] is False
    assert canonical_model['required_fidelity']['preserve_macro_composition'] is True
    assert canonical_model['required_fidelity']['preserve_visual_hierarchy'] is True
    assert canonical_model['required_fidelity']['preserve_interaction_states'] is True
    assert canonical_model['required_fidelity']['preserve_responsive_transformation'] is True


@pytest.mark.parametrize('fixture_path', VALID_FIXTURES)
def test_uief1_valid_fixtures_pass(fixture_path: Path) -> None:
    validator = _validator()
    data = _load(fixture_path)
    validator.validate(data)


@pytest.mark.parametrize('fixture_path', INVALID_FIXTURES)
def test_uief1_invalid_fixtures_are_rejected(fixture_path: Path) -> None:
    validator = _validator()
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(_load(fixture_path))


def test_uief1_contract_fidelity_requires_mandatory_handoff_evidence() -> None:
    validator = _validator()
    contract = _load(FIXTURES_DIR / 'uief1-valid-contract-fidelity.json')
    validator.validate(contract)

    # Missing design_contract_ref
    broken = copy.deepcopy(contract)
    del broken['design_contract_ref']
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(broken)

    # Missing cloak_handoff_ref
    broken = copy.deepcopy(contract)
    del broken['cloak_handoff_ref']
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(broken)

    # Empty pattern_refs
    broken = copy.deepcopy(contract)
    broken['pattern_refs'] = []
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(broken)

    # Empty composition_refs
    broken = copy.deepcopy(contract)
    broken['composition_refs'] = []
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(broken)

    # Missing clockwork_boundary_ref
    broken = copy.deepcopy(contract)
    del broken['clockwork_boundary_ref']
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(broken)


def test_uief1_contract_fidelity_requires_macro_fidelity_flags_true() -> None:
    validator = _validator()
    contract = _load(FIXTURES_DIR / 'uief1-valid-contract-fidelity.json')

    fidelity_keys = [
        'preserve_macro_composition',
        'preserve_visual_hierarchy',
        'preserve_interaction_states',
        'preserve_responsive_transformation',
    ]
    for key in fidelity_keys:
        broken = copy.deepcopy(contract)
        broken['required_fidelity'][key] = False
        with pytest.raises(jsonschema.ValidationError):
            validator.validate(broken)


def test_uief1_conductor_exclusive_selector_authority() -> None:
    validator = _validator()
    contract = _load(FIXTURES_DIR / 'uief1-valid-minimal-safe.json')

    unauthorized_selectors = ['ponytail', 'cloak', 'the-steward', 'clockwork', 'user']
    for selector in unauthorized_selectors:
        broken = copy.deepcopy(contract)
        broken['selected_by'] = selector
        with pytest.raises(jsonschema.ValidationError):
            validator.validate(broken)


def test_uief1_authority_flags_strictly_immutable_false() -> None:
    validator = _validator()
    contract = _load(FIXTURES_DIR / 'uief1-valid-minimal-safe.json')

    authority_keys = [
        'grants_specialist_authority',
        'grants_implementation_authority',
        'ponytail_can_self_select',
        'ponytail_can_downgrade',
    ]
    for key in authority_keys:
        escalated = copy.deepcopy(contract)
        escalated['authority'][key] = True
        with pytest.raises(jsonschema.ValidationError):
            validator.validate(escalated)


def test_uief1_pattern_ref_source_kinds_strictly_bounded() -> None:
    validator = _validator()
    contract = _load(FIXTURES_DIR / 'uief1-valid-contract-fidelity.json')

    valid_kinds = [
        'CUIR_NORMALIZED',
        'PROJECT_NATIVE',
        'OPEN_SOURCE_COMPONENT',
        'PUBLIC_PROVIDER_GUIDANCE',
        'OBSERVED_PROVIDER_OUTPUT',
    ]
    for kind in valid_kinds:
        sample = copy.deepcopy(contract)
        sample['pattern_refs'][0]['source_kind'] = kind
        validator.validate(sample)

    invalid_kinds = ['UNVERIFIED_BLOG', 'RANDOM_GITHUB', 'INVENTED']
    for kind in invalid_kinds:
        sample = copy.deepcopy(contract)
        sample['pattern_refs'][0]['source_kind'] = kind
        with pytest.raises(jsonschema.ValidationError):
            validator.validate(sample)
