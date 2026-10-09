from pathlib import Path

import pytest

from orchestra_runtime.governance_kernel import (
    ArbiterKernelInput,
    GovernanceDecisionRecord,
    evaluate_arbiter,
)
from orchestra_runtime.machine_contracts import command_route_map
from orchestra_runtime.models import Command, ContextPackage
from orchestra_runtime.repositories import ManifestRepository, SkillSourceRepository
from orchestra_runtime.services import GovernanceValidator, RouterService, SkillRegistry
from orchestra_runtime.shadow_conformance import (
    LegacyWorkflowClaim,
    MigrationStage,
    ShadowConformanceReport,
    ShadowDiscrepancy,
    compare_shadow_claim,
)


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_A = "a" * 64
EVIDENCE_B = "b" * 64


def _runtime(command_name: str, metadata: dict | None = None):
    routes = command_route_map(ROOT)
    registry = SkillRegistry(ManifestRepository(ROOT), SkillSourceRepository(ROOT))
    router = RouterService(registry)
    governance = GovernanceValidator()
    command = Command(name=command_name, raw_input=command_name, adapter_name="codex")
    context = ContextPackage(
        adapter_name="codex",
        prompt=command_name,
        project_root=ROOT,
        available_commands=tuple(routes),
        manifest_version="1.4.0",
        metadata=metadata or {},
    )
    route = router.route(command, context)
    validation = governance.validate(route, context)
    return route, validation


def _arbiter():
    return evaluate_arbiter(
        ArbiterKernelInput(
            project_id="orchestra",
            unit_id="shadow-fixture",
            governance_decisions=(
                GovernanceDecisionRecord(
                    reviewer="shadow-fixture",
                    project_context="shadow-fixture",
                    decision="APPROVED",
                    reason="fixture",
                    evidence_refs=("receipt:fixture",),
                ),
            ),
        )
    )


def _claim(command_name="review-architecture", **overrides):
    route, validation = _runtime(command_name)
    values = {
        "command_name": command_name,
        "specialist_id": route.skill_slug,
        "governance_required": route.governance_required,
        "validation_allowed": validation.allowed,
        "arbiter_disposition": _arbiter().disposition.value,
        "evidence_digests": (EVIDENCE_A, EVIDENCE_B),
    }
    values.update(overrides)
    return LegacyWorkflowClaim(**values), validation


def test_matching_direct_route_has_zero_discrepancies():
    claim, validation = _claim()
    record = compare_shadow_claim(
        claim,
        machine_validation_allowed=validation.allowed,
        machine_arbiter_result=_arbiter(),
        root=ROOT,
    )
    assert record.matches is True
    assert record.discrepancy_codes == ()
    assert record.machine_route_id == "architecture-structure"
    assert record.machine_specialist_id == "clockwork"


def test_wrong_legacy_specialist_is_detected():
    claim, validation = _claim(specialist_id="ponytail")
    record = compare_shadow_claim(claim, machine_validation_allowed=validation.allowed, machine_arbiter_result=_arbiter(), root=ROOT)
    assert record.discrepancy_codes == (ShadowDiscrepancy.SPECIALIST_MISMATCH,)


def test_unknown_legacy_specialist_is_detected_separately():
    claim, validation = _claim(specialist_id="imaginary-specialist")
    record = compare_shadow_claim(claim, machine_validation_allowed=validation.allowed, machine_arbiter_result=_arbiter(), root=ROOT)
    assert record.discrepancy_codes == (
        ShadowDiscrepancy.UNKNOWN_LEGACY_SPECIALIST,
        ShadowDiscrepancy.SPECIALIST_MISMATCH,
    )


def test_governance_required_mismatch_is_detected():
    claim, validation = _claim(governance_required=True)
    record = compare_shadow_claim(claim, machine_validation_allowed=validation.allowed, machine_arbiter_result=_arbiter(), root=ROOT)
    assert record.discrepancy_codes == (ShadowDiscrepancy.GOVERNANCE_REQUIRED_MISMATCH,)


def test_validation_mismatch_is_detected():
    claim, validation = _claim(validation_allowed=False)
    record = compare_shadow_claim(claim, machine_validation_allowed=validation.allowed, machine_arbiter_result=_arbiter(), root=ROOT)
    assert record.discrepancy_codes == (ShadowDiscrepancy.VALIDATION_MISMATCH,)


def test_claimed_arbiter_disposition_mismatch_is_detected():
    claim, validation = _claim(arbiter_disposition="STOP")
    record = compare_shadow_claim(claim, machine_validation_allowed=validation.allowed, machine_arbiter_result=_arbiter(), root=ROOT)
    assert record.discrepancy_codes == (ShadowDiscrepancy.ARBITER_DISPOSITION_MISMATCH,)


def test_unknown_legacy_disposition_is_detected_without_becoming_authority():
    claim, validation = _claim(arbiter_disposition="MAGIC_CONTINUE")
    record = compare_shadow_claim(claim, machine_validation_allowed=validation.allowed, machine_arbiter_result=_arbiter(), root=ROOT)
    assert record.discrepancy_codes == (ShadowDiscrepancy.UNKNOWN_LEGACY_DISPOSITION,)
    assert record.matches is False


def test_missing_evidence_digest_is_detected():
    claim, validation = _claim(evidence_digests=())
    record = compare_shadow_claim(claim, machine_validation_allowed=validation.allowed, machine_arbiter_result=_arbiter(), root=ROOT)
    assert record.discrepancy_codes == (ShadowDiscrepancy.MISSING_EVIDENCE_DIGEST,)


def test_invalid_evidence_digest_is_rejected_at_claim_boundary():
    with pytest.raises(ValueError, match="SHA-256"):
        _claim(evidence_digests=("abc",))


def test_multi_record_report_is_deterministic_independent_of_input_order():
    first_claim, first_validation = _claim("review-architecture")
    second_claim, second_validation = _claim("review-docs")
    first = compare_shadow_claim(first_claim, machine_validation_allowed=first_validation.allowed, machine_arbiter_result=_arbiter(), root=ROOT)
    second = compare_shadow_claim(second_claim, machine_validation_allowed=second_validation.allowed, machine_arbiter_result=_arbiter(), root=ROOT)
    a = ShadowConformanceReport(records=(first, second))
    b = ShadowConformanceReport(records=(second, first))
    assert a.to_dict() == b.to_dict()
    assert a.digest == b.digest
    assert a.discrepancy_count == 0
    assert a.eligible_for_separately_governed_next_stage is True
    assert a.authorizes_execution is False


def test_any_discrepancy_blocks_next_stage_eligibility():
    good_claim, good_validation = _claim("review-architecture")
    bad_claim, bad_validation = _claim("review-docs", specialist_id="clockwork")
    good = compare_shadow_claim(good_claim, machine_validation_allowed=good_validation.allowed, machine_arbiter_result=_arbiter(), root=ROOT)
    bad = compare_shadow_claim(bad_claim, machine_validation_allowed=bad_validation.allowed, machine_arbiter_result=_arbiter(), root=ROOT)
    report = ShadowConformanceReport(records=(good, bad))
    assert report.discrepancy_count == 1
    assert report.eligible_for_separately_governed_next_stage is False
    assert report.authorizes_execution is False


def test_empty_report_cannot_claim_next_stage_eligibility():
    report = ShadowConformanceReport(records=())
    assert report.discrepancy_count == 0
    assert report.eligible_for_separately_governed_next_stage is False


def test_p9_report_rejects_authority_stage_advancement():
    with pytest.raises(ValueError, match="restricted to SHADOW"):
        ShadowConformanceReport(records=(), migration_stage=MigrationStage.ADVISORY)
