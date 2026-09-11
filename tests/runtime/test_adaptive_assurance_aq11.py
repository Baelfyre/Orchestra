# @codebase_provenance_JEO
# @codebase_rights_JEO
"""AQ11 controlled remediation-effectiveness pilot regressions."""
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

from orchestra_runtime.domain.adaptive.remediation_effectiveness import (  # noqa: E402
    CUD10_HOLD_STATE, PILOT_MODE, REQUIRED_ESCAPE_CLASSES, TARGET_CANONICAL_SHA,
    TARGET_INCIDENT, TARGET_REPOSITORY, PilotContext, RemediationCase,
    evaluate_remediation_pilot,
)
from scripts.validation.classify_adaptive_assurance_scope import NOT_APPLICABLE, classify_paths  # noqa: E402

CONTRACT_PATH = ROOT / "machine/adaptive/aq11-remediation-effectiveness-pilot.v1.json"
SCHEMA_PATH = ROOT / "machine/schemas/aq11-remediation-effectiveness-pilot.v1.schema.json"


def context(**overrides):
    data = {
        "repository": TARGET_REPOSITORY, "canonical_sha": TARGET_CANONICAL_SHA,
        "incident_reference": TARGET_INCIDENT, "mode": PILOT_MODE,
        "cud10_state": CUD10_HOLD_STATE, "source_mutation_performed": False,
        "production_evidence": False,
    }
    data.update(overrides)
    return PilotContext(**data)


def cases(after="PREVENTED", independent=True, recurrence=False):
    return tuple(
        RemediationCase(
            case_id=f"CASE-{index}-{escape_class}", escape_class=escape_class,
            before_result="REPRODUCED_DEFECT" if index < 4 else "STATIC_RISK_CONFIRMED",
            after_result=after, remediation_actions=(f"LOCK_{escape_class}",),
            evidence_ids=(f"EVIDENCE-{index}",), independent_evidence=independent,
            recurrence_observed=recurrence,
        )
        for index, escape_class in enumerate(REQUIRED_ESCAPE_CLASSES)
    )


def test_contract_is_draft_2020_12_valid_and_non_authorizing() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(contract, schema)
    assert contract["pilot_boundary"]["organic_effectiveness_claimed"] is False
    assert all(value is False for value in contract["authority"].values())


def test_registered_exact_aq11_scope_is_separated_from_historical_gates() -> None:
    inventory = tuple(json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))["implementation_inventory"])
    for gate in ("prai", "aq5", "aq7"):
        assert classify_paths(inventory, gate) == NOT_APPLICABLE


def test_controlled_complete_pilot_passes_without_admission_authority() -> None:
    summary = evaluate_remediation_pilot(context(), cases())
    assert summary.disposition == "PASS"
    assert summary.case_count == 6
    assert summary.effective_count == 6
    assert summary.unresolved_count == 0
    assert summary.effectiveness_bps == 10000
    assert summary.authority_granted is False
    assert summary.cud10_admission_authorized is False
    assert summary.production_readiness_claimed is False
    assert summary.organic_effectiveness_claimed is False
    assert "AQ11_PASS_IS_NON_ADMITTING" in summary.reason_codes


def test_pilot_is_order_invariant() -> None:
    baseline = evaluate_remediation_pilot(context(), cases())
    shuffled = list(cases())
    random.Random(20260911).shuffle(shuffled)
    observed = evaluate_remediation_pilot(context(), shuffled)
    assert observed == baseline


def test_remaining_escape_forces_revision_required_and_preserves_hold() -> None:
    sample = list(cases())
    item = sample[0]
    sample[0] = RemediationCase(item.case_id, item.escape_class, item.before_result, "STILL_ESCAPES", item.remediation_actions, item.evidence_ids, True, False)
    summary = evaluate_remediation_pilot(context(), sample)
    assert summary.disposition == "REVISION_REQUIRED"
    assert summary.effectiveness_bps < 10000
    assert summary.cud10_admission_authorized is False
    assert "AQ11_CUD10_HOLD_PRESERVED" in summary.reason_codes


def test_recurrence_forces_revision_required() -> None:
    sample = list(cases())
    item = sample[1]
    sample[1] = RemediationCase(item.case_id, item.escape_class, item.before_result, item.after_result, item.remediation_actions, item.evidence_ids, True, True)
    assert evaluate_remediation_pilot(context(), sample).disposition == "REVISION_REQUIRED"


def test_non_independent_or_inconclusive_evidence_waits() -> None:
    assert evaluate_remediation_pilot(context(), cases(independent=False)).disposition == "WAIT_FOR_EVIDENCE"
    assert evaluate_remediation_pilot(context(), cases(after="INCONCLUSIVE")).disposition == "WAIT_FOR_EVIDENCE"


def test_missing_or_duplicate_required_class_fails_closed() -> None:
    sample = list(cases())
    with pytest.raises(ValueError):
        evaluate_remediation_pilot(context(), sample[:-1])
    duplicate = list(cases())
    duplicate[-1] = RemediationCase(
        duplicate[0].case_id + "-ALT", duplicate[0].escape_class,
        duplicate[-1].before_result, duplicate[-1].after_result,
        duplicate[-1].remediation_actions, duplicate[-1].evidence_ids, True, False,
    )
    with pytest.raises(ValueError):
        evaluate_remediation_pilot(context(), duplicate)


def test_duplicate_case_identity_fails_closed() -> None:
    sample = list(cases())
    last = sample[-1]
    sample[-1] = RemediationCase(sample[0].case_id, last.escape_class, last.before_result, last.after_result, last.remediation_actions, last.evidence_ids, True, False)
    with pytest.raises(ValueError):
        evaluate_remediation_pilot(context(), sample)


def test_unknown_class_and_unsafe_context_are_rejected() -> None:
    with pytest.raises(ValueError):
        RemediationCase("X", "UNKNOWN", "REPRODUCED_DEFECT", "PREVENTED", ("ACTION",), ("E",), True, False)
    with pytest.raises(ValueError):
        context(source_mutation_performed=True)
    with pytest.raises(ValueError):
        context(production_evidence=True)
    with pytest.raises(ValueError):
        context(canonical_sha="0" * 40)
    with pytest.raises(ValueError):
        context(cud10_state="AUTHORIZED")


def test_context_identity_fields_fail_closed_on_drift() -> None:
    with pytest.raises(ValueError):
        context(repository="Baelfyre/Other")
    with pytest.raises(ValueError):
        context(incident_reference="Baelfyre/Padayon#999")
    with pytest.raises(ValueError):
        context(mode="PRODUCTION")


def test_case_scalar_and_collection_validation_fails_closed() -> None:
    with pytest.raises(TypeError):
        RemediationCase(123, REQUIRED_ESCAPE_CLASSES[0], "REPRODUCED_DEFECT", "PREVENTED", ("ACTION",), ("E",), True, False)
    with pytest.raises(ValueError):
        RemediationCase("", REQUIRED_ESCAPE_CLASSES[0], "REPRODUCED_DEFECT", "PREVENTED", ("ACTION",), ("E",), True, False)
    with pytest.raises(ValueError):
        RemediationCase("BAD\x01ID", REQUIRED_ESCAPE_CLASSES[0], "REPRODUCED_DEFECT", "PREVENTED", ("ACTION",), ("E",), True, False)
    with pytest.raises(TypeError):
        RemediationCase("X", REQUIRED_ESCAPE_CLASSES[0], "REPRODUCED_DEFECT", "PREVENTED", "ACTION", ("E",), True, False)
    with pytest.raises(ValueError):
        RemediationCase("X", REQUIRED_ESCAPE_CLASSES[0], "REPRODUCED_DEFECT", "PREVENTED", (), ("E",), True, False)
    with pytest.raises(ValueError):
        RemediationCase("X", REQUIRED_ESCAPE_CLASSES[0], "REPRODUCED_DEFECT", "PREVENTED", ("ACTION", "ACTION"), ("E",), True, False)
    with pytest.raises(ValueError):
        RemediationCase("X", REQUIRED_ESCAPE_CLASSES[0], "UNKNOWN", "PREVENTED", ("ACTION",), ("E",), True, False)
    with pytest.raises(TypeError):
        RemediationCase("X", REQUIRED_ESCAPE_CLASSES[0], "REPRODUCED_DEFECT", "PREVENTED", ("ACTION",), ("E",), 1, False)
    with pytest.raises(TypeError):
        RemediationCase("X", REQUIRED_ESCAPE_CLASSES[0], "REPRODUCED_DEFECT", "PREVENTED", ("ACTION",), ("E",), True, 0)


def test_case_mapping_contract_fails_closed() -> None:
    with pytest.raises(TypeError):
        RemediationCase.from_mapping("not-a-mapping")
    with pytest.raises(ValueError):
        RemediationCase.from_mapping({"case_id": "X"})


def test_pilot_container_types_fail_closed() -> None:
    with pytest.raises(TypeError):
        evaluate_remediation_pilot("not-a-context", cases())
    with pytest.raises(TypeError):
        evaluate_remediation_pilot(context(), "not-cases")
    sample = list(cases())
    sample[-1] = object()
    with pytest.raises(TypeError):
        evaluate_remediation_pilot(context(), sample)
