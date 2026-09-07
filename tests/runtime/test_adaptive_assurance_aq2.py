from __future__ import annotations

import json
from dataclasses import replace
from itertools import combinations
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from orchestra_runtime.domain.adaptive import (
    ASSURANCE_ORDER,
    AQ2_RISK_PROFILER_SCHEMA_VERSION,
    AdaptiveRiskProfile,
    BASE_QUALITY_DIMENSIONS,
    DaggerDecision,
    INVARIANT_EXAMPLES,
    INVARIANT_RULES,
    ORCHESTRA_OVERLAYS,
    QUALITY_DIMENSIONS,
    RISK_CHARACTERISTICS,
    RISK_RULES,
    RiskProfileInput,
    SPECIALIST_ORDER,
    profile_adaptive_risk,
    profile_risk,
)


ROOT = Path(__file__).parents[2]
CONTRACT_PATH = ROOT / "machine" / "adaptive" / "aq2-adaptive-risk-profiler.v1.json"
SCHEMA_PATH = ROOT / "machine" / "schemas" / "adaptive-risk-profiler.v1.schema.json"


def _json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _profile(**overrides: object):
    values: dict[str, object] = {
        "development_mode": "SPEC_FIRST",
        "material_behavior": "bounded material behavior",
        "authority_boundary": ("IMPLEMENTATION",),
        "changed_domains": (),
        "changed_paths": (),
        "quality_dimensions": (),
        "risk_characteristics": (),
        "invariants": (),
        "protected_gates": (),
    }
    values.update(overrides)
    return profile_risk(**values)


def _rule_map(
    rules: dict[str, tuple[tuple[str, ...], tuple[str, ...], bool]],
) -> dict[str, object]:
    return {
        name: {
            "assurance_classes": list(assurance_classes),
            "specialists": list(specialists),
            "dagger_trigger": dagger_trigger,
        }
        for name, (assurance_classes, specialists, dagger_trigger) in rules.items()
    }


def test_contract_matches_domain_model() -> None:
    contract = _json(CONTRACT_PATH)
    schema = _json(SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    assert list(Draft202012Validator(schema).iter_errors(contract)) == []
    assert contract["schema_version"] == AQ2_RISK_PROFILER_SCHEMA_VERSION
    assert contract["base_quality_dimensions"] == list(BASE_QUALITY_DIMENSIONS)
    assert contract["orchestra_overlays"] == list(ORCHESTRA_OVERLAYS)
    assert contract["risk_characteristics"] == list(RISK_CHARACTERISTICS)
    assert contract["invariant_examples"] == list(INVARIANT_EXAMPLES)
    assert contract["specialist_order"] == list(SPECIALIST_ORDER)
    assert contract["assurance_order"] == list(ASSURANCE_ORDER)
    assert contract["risk_rules"] == _rule_map(RISK_RULES)
    assert contract["invariant_rules"] == _rule_map(INVARIANT_RULES)
    assert contract["authority"]["profiler_expands_authority"] is False


def test_documentation_fixture_is_small_and_does_not_invoke_dagger() -> None:
    result = _profile(
        changed_domains=("documentation",),
        changed_paths=("docs/README.md",),
        material_behavior="correct a harmless documentation typo",
    )
    assert result.recommended_specialists == ("scribe", "overseer")
    assert result.dagger_required is False
    assert result.required_assurance_classes == ("DOCUMENTATION_RECONCILIATION", "INDEPENDENT_QA")


@pytest.mark.parametrize(
    ("risk", "specialist"),
    [
        ("UI_ACCESSIBILITY", "cloak"),
        ("MIGRATION", "chronicler"),
        ("AUTHORIZATION", "cipher"),
    ],
)
def test_single_owner_routing_fixtures(risk: str, specialist: str) -> None:
    result = _profile(risk_characteristics=(risk,))
    assert specialist in result.recommended_specialists
    assert "overseer" in result.recommended_specialists
    assert result.dagger_required is False


def test_concurrent_privilege_fixture_keeps_dagger_without_engine_path() -> None:
    result = _profile(
        risk_characteristics=("AUTHORIZATION", "CONCURRENCY", "PRIVILEGE_MUTATION"),
    )
    assert result.recommended_specialists == ("cipher", "chronicler", "overseer", "dagger")
    assert result.dagger_decision.triggered_by == ("CONCURRENCY", "PRIVILEGE_MUTATION")
    assert result.dagger_decision.execution_authorized is False


def test_architecture_fixture_adds_clockwork_and_relevant_owner() -> None:
    result = _profile(
        changed_domains=("domain", "application"),
        material_behavior="cross-domain architecture boundary change",
        risk_characteristics=("TRANSACTION",),
    )
    assert result.recommended_specialists == ("clockwork", "chronicler", "overseer")
    assert "ARCHITECTURE_BOUNDARY" in result.required_assurance_classes


def test_normalization_is_order_invariant_and_deduplicates() -> None:
    first = _profile(
        changed_domains=("Application", "Domain"),
        changed_paths=(r"src\B.py", "src/a.py"),
        quality_dimensions=("SECURITY", "RELIABILITY", "SECURITY"),
        risk_characteristics=("CONCURRENCY", "AUTHORIZATION", "CONCURRENCY"),
        invariants=("FAILED_VALIDATION_MUST_NOT_BECOME_PASS", "FAILED_VALIDATION_MUST_NOT_BECOME_PASS"),
        protected_gates=("human_review", "human_review"),
    )
    second = _profile(
        changed_domains=("domain", "application"),
        changed_paths=("src/a.py", "SRC/B.PY"),
        quality_dimensions=("RELIABILITY", "SECURITY"),
        risk_characteristics=("AUTHORIZATION", "CONCURRENCY"),
        invariants=("FAILED_VALIDATION_MUST_NOT_BECOME_PASS",),
        protected_gates=("HUMAN_REVIEW",),
    )
    assert first.risk_fingerprint == second.risk_fingerprint
    assert first.required_assurance_classes == second.required_assurance_classes
    assert first.recommended_specialists == second.recommended_specialists


def test_authority_and_provider_boundaries_are_preserved() -> None:
    result = _profile(
        authority_boundary={"mutation": ("repository",), "read": "source"},
        risk_characteristics=("EXTERNAL_PROVIDER",),
        protected_gates=("HUMAN_REVIEW",),
    )
    assert result.authority_boundary == ("MUTATION:REPOSITORY", "READ:SOURCE")
    assert result.authority_expansion is False
    assert result.provider_activation is False
    assert result.production_action is False
    assert "EXTERNAL_PROVIDER_CLASSIFIED_WITHOUT_PROVIDER_ACTIVATION" in result.explanation


def test_human_decision_gate_is_added_and_nonwaivable() -> None:
    result = _profile(risk_characteristics=("HUMAN_DECISION_AUTHORITY",))
    assert "HUMAN_DECISION_AUTHORITY" in result.protected_gates
    assert "HUMAN_DECISION_AUTHORITY_GATE_IS_NONWAIVABLE" in result.explanation


def test_security_critical_empty_profile_fails_closed() -> None:
    with pytest.raises(ValueError, match="security-critical"):
        _profile(quality_dimensions=("SECURITY",))
    with pytest.raises(ValueError, match="security-critical"):
        _profile(material_behavior="change authorization behavior")


@pytest.mark.parametrize(
    "description",
    (
        "change RBAC permission checks",
        "change access control",
        "change role assignment",
        "change token/session validation",
    ),
)
def test_security_critical_empty_descriptions_fail_closed(description: str) -> None:
    with pytest.raises(ValueError, match="security-critical"):
        _profile(material_behavior=description)


@pytest.mark.parametrize(
    "field,value",
    [("quality_dimensions", ("UNKNOWN",)), ("risk_characteristics", ("UNKNOWN",))],
)
def test_unknown_quality_or_risk_fails_closed(field: str, value: tuple[str, ...]) -> None:
    with pytest.raises(ValueError, match="unsupported"):
        _profile(**{field: value})


def test_invalid_input_shapes_fail_closed() -> None:
    with pytest.raises(TypeError, match="iterable"):
        _profile(risk_characteristics="CONCURRENCY")
    with pytest.raises(ValueError, match="authority_boundary"):
        _profile(authority_boundary=())
    with pytest.raises(ValueError, match="invariants"):
        _profile(invariants=("not valid",))
    with pytest.raises(ValueError, match="development mode"):
        _profile(development_mode="UNKNOWN")


def test_normalized_input_defaults_and_boundary_limits() -> None:
    result = _profile(
        changed_domains=None,
        changed_paths=None,
        quality_dimensions=None,
        risk_characteristics=None,
        invariants=None,
        protected_gates=None,
    )
    assert result.changed_domains == ()
    assert result.changed_paths == ()

    with pytest.raises(TypeError, match="material_behavior must be a string"):
        _profile(material_behavior=1)
    with pytest.raises(ValueError, match="must be non-empty"):
        _profile(material_behavior="  ")
    with pytest.raises(ValueError, match="exceeds 4096"):
        _profile(material_behavior="x" * 4097)

    with pytest.raises(TypeError, match="iterable"):
        _profile(changed_domains=1)
    with pytest.raises(ValueError, match="exceeds 64"):
        _profile(changed_domains=tuple(str(index) for index in range(65)))
    with pytest.raises(ValueError, match="must not contain empty"):
        _profile(changed_domains=("",))

    with pytest.raises(TypeError, match="changed_paths"):
        _profile(changed_paths="src/main.py")
    with pytest.raises(TypeError, match="changed_paths"):
        _profile(changed_paths=1)
    with pytest.raises(ValueError, match="exceeds 128"):
        _profile(changed_paths=tuple(f"src/{index}.py" for index in range(129)))
    with pytest.raises(ValueError, match="must not contain empty"):
        _profile(changed_paths=("",))


def test_mapping_and_request_type_boundaries_fail_closed() -> None:
    with pytest.raises(TypeError, match="mapping"):
        RiskProfileInput.from_mapping([])
    with pytest.raises(TypeError, match="RiskProfileInput"):
        profile_risk(object())

    request = RiskProfileInput(
        development_mode="SPEC_FIRST",
        material_behavior="keyword alias behavior",
        authority_boundary=("IMPLEMENTATION",),
    )
    assert profile_risk(request).material_behavior == "keyword alias behavior"
    aliased = profile_risk(
        development_mode="SPEC_FIRST",
        material_behavioral_description="keyword alias behavior",
        authority_boundary=("IMPLEMENTATION",),
    )
    assert aliased.material_behavior == "keyword alias behavior"


def test_unknown_invariant_is_retained_without_implicit_routing() -> None:
    result = _profile(invariants=("UNMAPPED_INVARIANT",))
    assert result.invariants == ("UNMAPPED_INVARIANT",)
    assert result.dagger_required is False


def test_dagger_decision_and_profile_guards_fail_closed() -> None:
    with pytest.raises(TypeError, match="exact booleans"):
        DaggerDecision(required=1, triggered_by=())
    with pytest.raises(ValueError, match="cannot authorize"):
        DaggerDecision(required=True, triggered_by=("CONCURRENCY",), execution_authorized=True)
    with pytest.raises(ValueError, match="match its trigger"):
        DaggerDecision(required=False, triggered_by=("CONCURRENCY",))

    result = _profile()
    assert isinstance(result, AdaptiveRiskProfile)
    assert result.risk_fingerprint == result.normalized_risk_fingerprint
    assert result.specialist_topology == result.recommended_specialists
    assert result.recommended_specialist_topology == result.recommended_specialists

    with pytest.raises(ValueError, match="unsupported AQ2"):
        replace(result, schema_version="other.v1")
    with pytest.raises(ValueError, match="cannot set authority_expansion"):
        replace(result, authority_expansion=True)
    with pytest.raises(TypeError, match="DaggerDecision"):
        replace(result, dagger_decision=object())


def test_mapping_input_and_alias_entrypoint() -> None:
    request = {
        "development_mode": "SPEC_FIRST",
        "material_behavioral_description": "authorization boundary change",
        "explicit_authority_boundary": ["IMPLEMENTATION"],
        "risks": ["AUTHORIZATION"],
    }
    direct = profile_adaptive_risk(request)
    keyword = _profile(
        material_behavior="authorization boundary change",
        risk_characteristics=("AUTHORIZATION",),
    )
    assert direct.risk_fingerprint == keyword.risk_fingerprint


def test_every_declared_quality_and_risk_rule_is_executable() -> None:
    for quality in QUALITY_DIMENSIONS:
        risks = ("AUTHENTICATION",) if quality == "SECURITY" else ()
        result = _profile(
            quality_dimensions=(quality,),
            risk_characteristics=risks,
            material_behavior="ordinary behavior",
        )
        assert result.required_assurance_classes
    for risk in RISK_CHARACTERISTICS:
        result = _profile(risk_characteristics=(risk,))
        assert result.required_assurance_classes
        assert result.recommended_specialists


def test_every_invariant_example_preserves_assurance() -> None:
    for invariant in INVARIANT_EXAMPLES:
        result = _profile(invariants=(invariant,))
        assert "INVARIANT_PRESERVATION_ASSURANCE" in result.required_assurance_classes


def test_assurance_and_dagger_monotonicity() -> None:
    risks = ("AUTHORIZATION", "CONCURRENCY", "PRIVILEGE_MUTATION", "MIGRATION")
    profiles = {
        subset: _profile(risk_characteristics=subset)
        for size in range(len(risks) + 1)
        for subset in combinations(risks, size)
    }
    for smaller, smaller_profile in profiles.items():
        for larger, larger_profile in profiles.items():
            if not set(smaller).issubset(larger):
                continue
            assert set(smaller_profile.required_assurance_classes).issubset(
                larger_profile.required_assurance_classes
            )
            assert set(smaller_profile.recommended_specialists).issubset(
                larger_profile.recommended_specialists
            )
            if smaller_profile.dagger_required:
                assert larger_profile.dagger_required


def test_output_is_json_serializable_and_receipt_ready() -> None:
    output = _profile(risk_characteristics=("PROVENANCE",)).to_dict()
    encoded = json.dumps(output, sort_keys=True)
    decoded = json.loads(encoded)
    assert decoded["normalized_risk_fingerprint"]
    assert decoded["dagger_decision"]["execution_authorized"] is False
    assert decoded["authority_expansion"] is False
