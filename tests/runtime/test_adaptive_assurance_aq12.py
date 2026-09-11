# @codebase_provenance_JEO
# @codebase_rights_JEO
"""AQ12 controlled Orchestra adversarial self-test regressions."""
from __future__ import annotations

import json
from pathlib import Path
import random
import sys

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from orchestra_runtime.domain.adaptive.adversarial_self_test import (  # noqa: E402
    CANONICAL_START_SHA,
    CUD10_HOLD_STATE,
    EXPECTED_CONTROLS,
    REQUIRED_ATTACK_CLASSES,
    SELF_TEST_MODE,
    TARGET_REPOSITORY,
    AdversarialCase,
    SelfTestContext,
    evaluate_adversarial_self_test,
)
from scripts.validation.classify_adaptive_assurance_scope import NOT_APPLICABLE, classify_paths  # noqa: E402

CONTRACT_PATH = ROOT / "machine/adaptive/aq12-adversarial-self-test.v1.json"
SCHEMA_PATH = ROOT / "machine/schemas/aq12-adversarial-self-test.v1.schema.json"


def context(**overrides):
    data = {
        "repository": TARGET_REPOSITORY,
        "canonical_sha": CANONICAL_START_SHA,
        "mode": SELF_TEST_MODE,
        "cud10_state": CUD10_HOLD_STATE,
        "protected_policy_mutation_performed": False,
        "production_mutation_performed": False,
        "provider_activation_performed": False,
        "telemetry_activation_performed": False,
        "release_or_deploy_performed": False,
    }
    data.update(overrides)
    return SelfTestContext(**data)


def cases(result="BLOCKED", independent=True, replay=True):
    return tuple(
        AdversarialCase(
            case_id=f"CASE-{index}-{attack_class}",
            attack_class=attack_class,
            expected_control=EXPECTED_CONTROLS[attack_class],
            observed_result=result,
            evidence_ids=(f"EVIDENCE-{index}",),
            independent_evidence=independent,
            deterministic_replay_match=replay,
        )
        for index, attack_class in enumerate(REQUIRED_ATTACK_CLASSES)
    )


def test_contract_is_draft_2020_12_valid_and_non_authorizing() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(contract, schema)
    assert all(value is False for value in contract["authority"].values())
    assert all(value is False for key, value in contract["self_test_boundary"].items() if key.endswith("_allowed"))


def test_registered_exact_aq12_scope_is_separated_from_historical_gates() -> None:
    inventory = tuple(json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))["implementation_inventory"])
    for gate in ("prai", "aq5", "aq7"):
        assert classify_paths(inventory, gate) == NOT_APPLICABLE


def test_complete_self_test_passes_without_authority() -> None:
    summary = evaluate_adversarial_self_test(context(), cases())
    assert summary.disposition == "PASS"
    assert summary.case_count == 6
    assert summary.effective_count == 6
    assert summary.unresolved_count == 0
    assert summary.effectiveness_bps == 10000
    assert summary.authority_granted is False
    assert summary.transition_authorized is False
    assert summary.release_authorized is False
    assert summary.cud10_admission_authorized is False
    assert summary.production_readiness_claimed is False
    assert "AQ12_PASS_IS_NON_AUTHORIZING" in summary.reason_codes


def test_self_test_is_order_invariant() -> None:
    baseline = evaluate_adversarial_self_test(context(), cases())
    shuffled = list(cases())
    random.Random(20260911).shuffle(shuffled)
    assert evaluate_adversarial_self_test(context(), shuffled) == baseline


def test_escape_forces_revision_required() -> None:
    sample = list(cases())
    item = sample[0]
    sample[0] = AdversarialCase(
        item.case_id, item.attack_class, item.expected_control, "ESCAPED",
        item.evidence_ids, True, True,
    )
    summary = evaluate_adversarial_self_test(context(), sample)
    assert summary.disposition == "REVISION_REQUIRED"
    assert summary.effectiveness_bps < 10000
    assert "AQ12_ADVERSARIAL_ESCAPE_DETECTED" in summary.reason_codes


def test_deterministic_replay_mismatch_forces_revision_required() -> None:
    summary = evaluate_adversarial_self_test(context(), cases(replay=False))
    assert summary.disposition == "REVISION_REQUIRED"
    assert "AQ12_DETERMINISM_FAILURE" in summary.reason_codes


def test_non_independent_or_inconclusive_evidence_waits() -> None:
    assert evaluate_adversarial_self_test(context(), cases(independent=False)).disposition == "WAIT_FOR_EVIDENCE"
    assert evaluate_adversarial_self_test(context(), cases(result="INCONCLUSIVE")).disposition == "WAIT_FOR_EVIDENCE"


def test_missing_or_duplicate_required_class_fails_closed() -> None:
    sample = list(cases())
    with pytest.raises(ValueError):
        evaluate_adversarial_self_test(context(), sample[:-1])
    duplicate = list(cases())
    last = duplicate[-1]
    first = duplicate[0]
    duplicate[-1] = AdversarialCase(
        "ALT-ID", first.attack_class, first.expected_control, last.observed_result,
        last.evidence_ids, True, True,
    )
    with pytest.raises(ValueError):
        evaluate_adversarial_self_test(context(), duplicate)


def test_duplicate_case_identity_fails_closed() -> None:
    sample = list(cases())
    last = sample[-1]
    sample[-1] = AdversarialCase(
        sample[0].case_id, last.attack_class, last.expected_control, last.observed_result,
        last.evidence_ids, True, True,
    )
    with pytest.raises(ValueError):
        evaluate_adversarial_self_test(context(), sample)


def test_unknown_class_and_control_drift_are_rejected() -> None:
    with pytest.raises(ValueError):
        AdversarialCase("X", "UNKNOWN", "CONTROL", "BLOCKED", ("E",), True, True)
    with pytest.raises(ValueError):
        AdversarialCase("X", REQUIRED_ATTACK_CLASSES[0], "WRONG_CONTROL", "BLOCKED", ("E",), True, True)


def test_context_identity_and_unsafe_actions_fail_closed() -> None:
    with pytest.raises(ValueError):
        context(repository="Baelfyre/Other")
    with pytest.raises(ValueError):
        context(canonical_sha="0" * 40)
    with pytest.raises(ValueError):
        context(mode="PRODUCTION")
    with pytest.raises(ValueError):
        context(cud10_state="AUTHORIZED")
    for flag in (
        "protected_policy_mutation_performed", "production_mutation_performed",
        "provider_activation_performed", "telemetry_activation_performed", "release_or_deploy_performed",
    ):
        with pytest.raises(ValueError):
            context(**{flag: True})
    with pytest.raises(TypeError):
        context(production_mutation_performed=1)


def test_case_scalar_and_collection_validation_fails_closed() -> None:
    attack_class = REQUIRED_ATTACK_CLASSES[0]
    control = EXPECTED_CONTROLS[attack_class]
    with pytest.raises(TypeError):
        AdversarialCase(123, attack_class, control, "BLOCKED", ("E",), True, True)
    with pytest.raises(ValueError):
        AdversarialCase("", attack_class, control, "BLOCKED", ("E",), True, True)
    with pytest.raises(ValueError):
        AdversarialCase("BAD\x01ID", attack_class, control, "BLOCKED", ("E",), True, True)
    with pytest.raises(TypeError):
        AdversarialCase("X", attack_class, control, "BLOCKED", "E", True, True)
    with pytest.raises(ValueError):
        AdversarialCase("X", attack_class, control, "BLOCKED", (), True, True)
    with pytest.raises(ValueError):
        AdversarialCase("X", attack_class, control, "BLOCKED", ("E", "E"), True, True)
    with pytest.raises(ValueError):
        AdversarialCase("X", attack_class, control, "UNKNOWN", ("E",), True, True)
    with pytest.raises(TypeError):
        AdversarialCase("X", attack_class, control, "BLOCKED", ("E",), 1, True)
    with pytest.raises(TypeError):
        AdversarialCase("X", attack_class, control, "BLOCKED", ("E",), True, 1)


def test_case_mapping_contract_fails_closed() -> None:
    with pytest.raises(TypeError):
        AdversarialCase.from_mapping("not-a-mapping")
    with pytest.raises(ValueError):
        AdversarialCase.from_mapping({"case_id": "X"})
    attack_class = REQUIRED_ATTACK_CLASSES[0]
    value = {
        "case_id": "X",
        "attack_class": attack_class,
        "expected_control": EXPECTED_CONTROLS[attack_class],
        "observed_result": "BLOCKED",
        "evidence_ids": ["E"],
        "independent_evidence": True,
        "deterministic_replay_match": True,
    }
    assert AdversarialCase.from_mapping(value).case_id == "X"


def test_self_test_container_types_fail_closed() -> None:
    with pytest.raises(TypeError):
        evaluate_adversarial_self_test("not-a-context", cases())
    with pytest.raises(TypeError):
        evaluate_adversarial_self_test(context(), "not-cases")
    sample = list(cases())
    sample[-1] = object()
    with pytest.raises(TypeError):
        evaluate_adversarial_self_test(context(), sample)
