# @codebase_provenance_JEO
# @codebase_rights_JEO
# @codebase_verified_JEO
"""AQ10 deterministic defect-escape RCA regressions."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
import json
from pathlib import Path
import sys

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from orchestra_runtime.domain.adaptive.defect_escape_rca import (  # noqa: E402
    DefectEscapeObservation,
    analyze_defect_escapes,
    classify_defect_escape,
)

CONTRACT_PATH = ROOT / "machine/adaptive/aq10-defect-escape-rca.v1.json"
SCHEMA_PATH = ROOT / "machine/schemas/aq10-defect-escape-rca.v1.schema.json"


def _contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _observation(
    defect_id: str = "D-1",
    *,
    signals: tuple[str, ...] = ("MISSING_TEST_SURFACE",),
    escaped_gates: tuple[str, ...] = ("VALIDATE",),
    detection_gate: str = "COSMIC_RAY",
    evidence_ids: tuple[str, ...] = ("E-1",),
) -> DefectEscapeObservation:
    return DefectEscapeObservation(
        defect_id=defect_id,
        phase_detected="AQ10",
        escaped_gates=escaped_gates,
        detection_gate=detection_gate,
        signals=signals,
        evidence_ids=evidence_ids,
    )


def test_aq10_contract_is_schema_valid_and_non_authorizing() -> None:
    contract = _contract()
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(contract, schema)
    assert contract["authority_model"] == "EVIDENCE_ONLY_NON_AUTHORIZING"
    assert all(value is False for value in contract["authority"].values())
    assert contract["validation"]["runtime"] == "orchestra_runtime/domain/adaptive/defect_escape_rca.py"


@pytest.mark.parametrize(
    ("signal", "expected"),
    [
        ("MISSING_TEST_SURFACE", "COVERAGE_GAP"),
        ("WEAK_ASSERTION", "ASSERTION_GAP"),
        ("WRONG_EXPECTED_RESULT", "ORACLE_GAP"),
        ("INCORRECT_SCOPE_CLASSIFICATION", "SCOPE_CLASSIFICATION_GAP"),
        ("MISSING_OPTIONAL_DEPENDENCY", "DEPENDENCY_ENVIRONMENT_GAP"),
        ("MUTATION_OPERATOR_CRASH", "ASSURANCE_TOOL_COMPATIBILITY"),
        ("MISSING_GOVERNANCE_CONTRACT", "PROCESS_GOVERNANCE_GAP"),
        ("CAUSE_UNRESOLVED", "UNKNOWN"),
    ],
)
def test_each_taxonomy_family_is_reachable_from_explicit_evidence(signal: str, expected: str) -> None:
    finding = classify_defect_escape(_observation(signals=(signal,)))
    assert finding.root_cause == expected
    assert finding.authority_granted is False
    assert finding.automatic_policy_change is False


def test_signal_order_does_not_change_cause_or_prevention_output() -> None:
    left = classify_defect_escape(
        _observation(signals=("MISSING_OPTIONAL_DEPENDENCY", "MUTATION_OPERATOR_CRASH"))
    )
    right = classify_defect_escape(
        _observation(signals=("MUTATION_OPERATOR_CRASH", "MISSING_OPTIONAL_DEPENDENCY"))
    )
    assert left.root_cause == right.root_cause == "ASSURANCE_TOOL_COMPATIBILITY"
    assert left.contributing_causes == right.contributing_causes == ("DEPENDENCY_ENVIRONMENT_GAP",)
    assert left.prevention_actions == right.prevention_actions
    assert left.reason_codes == right.reason_codes


def test_unresolved_cause_requires_human_review_without_authority() -> None:
    finding = classify_defect_escape(_observation(signals=("CAUSE_UNRESOLVED",)))
    assert finding.root_cause == "UNKNOWN"
    assert finding.confidence == "LOW"
    assert finding.human_review_required is True
    assert "HUMAN_RCA_REVIEW_REQUIRED" in finding.prevention_actions
    assert finding.authority_granted is False
    assert finding.automatic_policy_change is False


def test_unknown_signal_and_duplicate_identity_fail_closed() -> None:
    with pytest.raises(ValueError):
        _observation(signals=("NOT_REGISTERED",))
    with pytest.raises(ValueError):
        _observation(signals=("MISSING_TEST_SURFACE", "MISSING_TEST_SURFACE"))
    with pytest.raises(ValueError):
        _observation(escaped_gates=("AQ5", "aq5"))
    with pytest.raises(ValueError):
        _observation(evidence_ids=("E-1", "E-1"))


def test_findings_are_immutable_evidence() -> None:
    finding = classify_defect_escape(_observation())
    with pytest.raises(FrozenInstanceError):
        finding.root_cause = "UNKNOWN"  # type: ignore[misc]


def test_summary_is_deterministic_and_rejects_duplicate_defect_ids() -> None:
    first = _observation("D-2", signals=("WEAK_ASSERTION",), evidence_ids=("E-2",))
    second = _observation("D-1", signals=("MUTATION_OPERATOR_CRASH",), evidence_ids=("E-1",))
    forward = analyze_defect_escapes((first, second))
    reverse = analyze_defect_escapes((second, first))
    assert forward == reverse
    assert tuple(item.defect_id for item in forward.findings) == ("D-1", "D-2")
    assert forward.authority_granted is False
    assert forward.automatic_policy_change is False
    with pytest.raises(ValueError):
        analyze_defect_escapes((first, first))


def test_reference_incidents_reproduce_contract_expected_causes() -> None:
    for index, incident in enumerate(_contract()["reference_incidents"], start=1):
        observation = DefectEscapeObservation(
            defect_id=incident["incident_id"],
            phase_detected=incident["phase_detected"],
            escaped_gates=tuple(incident["escaped_gates"]),
            detection_gate=incident["detection_gate"],
            signals=tuple(incident["signals"]),
            evidence_ids=(f"REFERENCE-{index}",),
        )
        finding = classify_defect_escape(observation)
        assert finding.root_cause == incident["expected_root_cause"]
        assert finding.authority_granted is False
        assert finding.automatic_policy_change is False
