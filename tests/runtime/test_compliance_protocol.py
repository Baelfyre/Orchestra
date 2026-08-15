import pytest

from orchestra_runtime.compliance_protocol import (
    ComplianceConsumptionReceipt,
    ComplianceExclusion,
    ComplianceQueryReceipt,
    StewardTraceabilityReceipt,
    evaluate_compliance_set_equality,
    evaluate_compliance_with_arbiter,
)
from orchestra_runtime.governance_kernel import (
    ArbiterKernelInput,
    GovernanceDecisionRecord,
    TransitionDisposition,
)


PH_OBLIGATIONS = (
    "PH-PRIVACY-PIA",
    "PH-PRIVACY-MANAGEMENT-PROGRAM",
    "PH-PRIVACY-BY-DESIGN-DEFAULT",
    "PH-PRIVACY-RETENTION",
    "PH-PRIVACY-ACCESS-CONTROL",
    "PH-PRIVACY-BUSINESS-CONTINUITY",
)


def _status():
    return {
        "registry_status": "VERIFIED",
        "canonical_repository": "Baelfyre/Orchestra-Compliance-Registry",
        "registry_version": "0.1.0",
        "release_sequence": 1,
        "release_tag": "registry-v0.1.0",
        "manifest_sha256": "a" * 64,
    }


def _query_result(reverse=False):
    obligations = [{"obligation_id": item} for item in PH_OBLIGATIONS]
    if reverse:
        obligations.reverse()
    return {
        "registry_version": "0.1.0",
        "release_sequence": 1,
        "sources": [{"source_id": "PH-NPC-DPA"}],
        "obligations": obligations,
    }


def _query(reverse=False):
    return ComplianceQueryReceipt.from_registry_result(
        _status(),
        _query_result(reverse),
        filters={"jurisdiction": "PH", "domain": "privacy"},
    )


def _consumption(query, *, obligations=PH_OBLIGATIONS, verdict="REVISION_REQUIRED", exclusions=()):
    obligations = tuple(obligations)
    return ComplianceConsumptionReceipt(
        query_digest=query.digest,
        source_ids=("PH-NPC-DPA",),
        obligation_ids=obligations,
        classifications=tuple((item, "EVIDENCE_MISSING") for item in obligations),
        verdict=verdict,
        exclusions=tuple(exclusions),
    )


def _traceability(query, *, obligations=PH_OBLIGATIONS):
    return StewardTraceabilityReceipt(
        query_digest=query.digest,
        source_ids=("PH-NPC-DPA",),
        obligation_ids=tuple(obligations),
        evidence_refs=("docs/privacy-review.md",),
    )


def _kernel_input(**overrides):
    values = {
        "project_id": "orderly",
        "unit_id": "ph-privacy-review",
        "governance_decisions": (
            GovernanceDecisionRecord(
                reviewer="the-governor",
                project_context="orderly-ph-privacy",
                decision="REVISION_REQUIRED",
                reason="evidence gaps remain",
                evidence_refs=("receipt:compliance",),
            ),
        ),
        "deterministic_defect": True,
        "remediation_authorized": True,
        "remediation_in_scope": True,
    }
    values.update(overrides)
    return ArbiterKernelInput(**values)


def test_exact_six_obligation_consumption_and_traceability_pass_set_equality():
    query = _query()
    gate = evaluate_compliance_set_equality(query, _consumption(query), _traceability(query))
    assert gate.ready is True
    assert gate.error_codes == ()
    assert gate.excluded_obligation_ids == ()


def test_query_receipt_digest_is_independent_of_registry_record_order():
    assert _query().digest == _query(reverse=True).digest


def test_omitted_obligation_fails_closed():
    query = _query()
    obligations = PH_OBLIGATIONS[1:]
    gate = evaluate_compliance_set_equality(
        query,
        _consumption(query, obligations=obligations),
        _traceability(query),
    )
    assert gate.ready is False
    assert gate.error_codes == ("CONSUMED_OBLIGATION_SET_MISMATCH",)


def test_renamed_nonexistent_obligation_fails_closed():
    query = _query()
    obligations = tuple(
        "PH-PRIVACY-PROGRAM" if item == "PH-PRIVACY-MANAGEMENT-PROGRAM" else item
        for item in PH_OBLIGATIONS
    )
    gate = evaluate_compliance_set_equality(
        query,
        _consumption(query, obligations=obligations),
        _traceability(query),
    )
    assert gate.ready is False
    assert gate.error_codes == ("CONSUMED_OBLIGATION_SET_MISMATCH",)


def test_extra_unknown_obligation_fails_closed():
    query = _query()
    obligations = PH_OBLIGATIONS + ("PH-PRIVACY-UNKNOWN",)
    gate = evaluate_compliance_set_equality(
        query,
        _consumption(query, obligations=obligations),
        _traceability(query),
    )
    assert gate.ready is False
    assert gate.error_codes == ("CONSUMED_OBLIGATION_SET_MISMATCH",)


def test_duplicate_obligation_id_is_rejected_by_receipt_constructor():
    query = _query()
    duplicate = PH_OBLIGATIONS + (PH_OBLIGATIONS[0],)
    with pytest.raises(ValueError, match="duplicate IDs"):
        _consumption(query, obligations=duplicate)


def test_traceability_omission_fails_closed():
    query = _query()
    gate = evaluate_compliance_set_equality(
        query,
        _consumption(query),
        _traceability(query, obligations=PH_OBLIGATIONS[:-1]),
    )
    assert gate.ready is False
    assert gate.error_codes == ("TRACEABILITY_OBLIGATION_SET_MISMATCH",)


def test_unsupported_pass_with_findings_verdict_is_rejected():
    query = _query()
    with pytest.raises(ValueError, match="unsupported compliance verdict"):
        _consumption(query, verdict="PASS_WITH_FINDINGS")


def test_mismatched_query_digest_fails_closed():
    query = _query()
    consumption = ComplianceConsumptionReceipt(
        query_digest="b" * 64,
        source_ids=("PH-NPC-DPA",),
        obligation_ids=PH_OBLIGATIONS,
        classifications=tuple((item, "EVIDENCE_MISSING") for item in PH_OBLIGATIONS),
        verdict="REVISION_REQUIRED",
    )
    gate = evaluate_compliance_set_equality(query, consumption, _traceability(query))
    assert gate.ready is False
    assert gate.error_codes == ("CONSUMPTION_QUERY_DIGEST_MISMATCH",)


def test_valid_machine_exclusion_is_accounted_but_visible():
    query = _query()
    excluded_id = PH_OBLIGATIONS[-1]
    exclusion = ComplianceExclusion(
        obligation_id=excluded_id,
        reason_code="VALIDATED_SCOPE_EXCLUSION",
        evidence_ref="receipt:scope-exclusion",
        authorized_by="governor-policy",
    )
    gate = evaluate_compliance_set_equality(
        query,
        _consumption(query, obligations=PH_OBLIGATIONS[:-1], exclusions=(exclusion,)),
        _traceability(query),
    )
    assert gate.ready is True
    assert gate.excluded_obligation_ids == (excluded_id,)


def test_unknown_exclusion_is_rejected_by_gate():
    query = _query()
    exclusion = ComplianceExclusion(
        obligation_id="PH-PRIVACY-NOT-IN-QUERY",
        reason_code="VALIDATED_SCOPE_EXCLUSION",
        evidence_ref="receipt:scope-exclusion",
        authorized_by="governor-policy",
    )
    gate = evaluate_compliance_set_equality(
        query,
        _consumption(query, obligations=PH_OBLIGATIONS, exclusions=(exclusion,)),
        _traceability(query),
    )
    assert gate.ready is False
    assert "EXCLUSION_UNKNOWN_OBLIGATION_ID" in gate.error_codes
    assert "CONSUMED_OBLIGATION_SET_MISMATCH" in gate.error_codes


def test_failed_compliance_gate_prevents_arbiter_continuation():
    query = _query()
    gate = evaluate_compliance_set_equality(
        query,
        _consumption(query, obligations=PH_OBLIGATIONS[1:]),
        _traceability(query),
    )
    evaluation = evaluate_compliance_with_arbiter(_kernel_input(), gate)
    assert evaluation.compliance_gate.ready is False
    assert evaluation.arbiter_result.disposition is TransitionDisposition.WAIT_FOR_EVIDENCE


def test_passing_compliance_gate_preserves_normal_arbiter_semantics():
    query = _query()
    gate = evaluate_compliance_set_equality(query, _consumption(query), _traceability(query))
    evaluation = evaluate_compliance_with_arbiter(_kernel_input(), gate)
    assert gate.ready is True
    assert evaluation.arbiter_result.disposition is TransitionDisposition.AUTO_REMEDIATE_AND_REVALIDATE


def test_compliance_gate_does_not_override_higher_priority_authority_stop():
    query = _query()
    gate = evaluate_compliance_set_equality(
        query,
        _consumption(query, obligations=PH_OBLIGATIONS[1:]),
        _traceability(query),
    )
    evaluation = evaluate_compliance_with_arbiter(_kernel_input(authority_valid=False), gate)
    assert evaluation.arbiter_result.disposition is TransitionDisposition.STOP
