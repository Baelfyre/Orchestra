# @codebase_provenance_JEO
# @codebase_rights_JEO

from __future__ import annotations

import unittest

from orchestra_runtime.domain.adaptive.effectiveness_qualification import (
    CANONICAL_START_SHA,
    CUD10_HOLD_STATE,
    EXPECTED_PHASE_IDENTITIES,
    QUALIFICATION_MODE,
    REQUIRED_PHASES,
    TARGET_REPOSITORY,
    PhaseEvidence,
    QualificationContext,
    evaluate_final_effectiveness,
)


class AQ14EffectivenessQualificationTests(unittest.TestCase):
    def context(self, **overrides):
        values = {
            "repository": TARGET_REPOSITORY,
            "canonical_sha": CANONICAL_START_SHA,
            "mode": QUALIFICATION_MODE,
            "cud10_state": CUD10_HOLD_STATE,
        }
        values.update(overrides)
        return QualificationContext(**values)

    def phase(self, phase_id, **overrides):
        identity = EXPECTED_PHASE_IDENTITIES[phase_id]
        values = {
            "phase_id": phase_id,
            "canonical_pr": identity["canonical_pr"],
            "canonical_sha": identity["canonical_sha"],
            "canonical_tree": identity["canonical_tree"],
            "disposition": "PASS",
            "canonical_verified": True,
            "source_assurance_pass": True,
            "promotion_assurance_pass": True,
            "post_merge_assurance_pass": True,
            "independent_evidence": True,
            "deterministic_evidence": True,
            "unresolved_critical_findings": 0,
        }
        values.update(overrides)
        return PhaseEvidence(**values)

    def healthy_chain(self):
        return tuple(self.phase(phase_id) for phase_id in REQUIRED_PHASES)

    def test_pass_qualifies_exact_chain_without_authority(self):
        result = evaluate_final_effectiveness(self.context(), self.healthy_chain())
        self.assertEqual("PASS", result.disposition)
        self.assertEqual(5, result.phase_count)
        self.assertEqual(5, result.qualified_count)
        self.assertEqual(0, result.unresolved_count)
        self.assertTrue(all(item.qualified for item in result.findings))
        self.assertIn("AQ14_CONTROLLED_EFFECTIVENESS_CHAIN_QUALIFIED", result.reason_codes)
        self.assertFalse(result.authority_granted)
        self.assertFalse(result.transition_authorized)
        self.assertFalse(result.release_authorized)
        self.assertFalse(result.production_authorized)
        self.assertFalse(result.aq15_authorized)
        self.assertFalse(result.cud10_admission_authorized)
        self.assertFalse(result.organic_effectiveness_claimed)
        self.assertFalse(result.production_readiness_claimed)

    def test_revision_disposition_forces_revision(self):
        evidence = list(self.healthy_chain())
        evidence[1] = self.phase("AQ10", disposition="REVISION_REQUIRED")
        result = evaluate_final_effectiveness(self.context(), evidence)
        self.assertEqual("REVISION_REQUIRED", result.disposition)
        self.assertIn("AQ14_PRIOR_PHASE_BLOCKING_DISPOSITION", result.findings[1].reason_codes)

    def test_hold_disposition_forces_revision(self):
        evidence = list(self.healthy_chain())
        evidence[4] = self.phase("AQ13", disposition="HOLD")
        result = evaluate_final_effectiveness(self.context(), evidence)
        self.assertEqual("REVISION_REQUIRED", result.disposition)

    def test_unresolved_critical_finding_forces_revision(self):
        evidence = list(self.healthy_chain())
        evidence[2] = self.phase("AQ11", unresolved_critical_findings=1)
        result = evaluate_final_effectiveness(self.context(), evidence)
        self.assertEqual("REVISION_REQUIRED", result.disposition)
        self.assertIn("AQ14_UNRESOLVED_CRITICAL_FINDING", result.findings[2].reason_codes)

    def test_wait_disposition_waits_for_evidence(self):
        evidence = list(self.healthy_chain())
        evidence[0] = self.phase("AQ9", disposition="WAIT_FOR_EVIDENCE")
        result = evaluate_final_effectiveness(self.context(), evidence)
        self.assertEqual("WAIT_FOR_EVIDENCE", result.disposition)
        self.assertIn("AQ14_PRIOR_PHASE_EVIDENCE_INCOMPLETE", result.findings[0].reason_codes)

    def test_each_assurance_gap_waits(self):
        fields = (
            "canonical_verified", "source_assurance_pass", "promotion_assurance_pass",
            "post_merge_assurance_pass", "independent_evidence", "deterministic_evidence",
        )
        reason_codes = (
            "AQ14_CANONICAL_VERIFICATION_REQUIRED", "AQ14_SOURCE_ASSURANCE_REQUIRED",
            "AQ14_PROMOTION_ASSURANCE_REQUIRED", "AQ14_POST_MERGE_ASSURANCE_REQUIRED",
            "AQ14_INDEPENDENT_EVIDENCE_REQUIRED", "AQ14_DETERMINISTIC_EVIDENCE_REQUIRED",
        )
        for field, reason in zip(fields, reason_codes):
            with self.subTest(field=field):
                evidence = list(self.healthy_chain())
                evidence[3] = self.phase("AQ12", **{field: False})
                result = evaluate_final_effectiveness(self.context(), evidence)
                self.assertEqual("WAIT_FOR_EVIDENCE", result.disposition)
                self.assertIn(reason, result.findings[3].reason_codes)

    def test_exact_phase_identity_is_mandatory(self):
        with self.assertRaises(ValueError):
            self.phase("AQ9", canonical_pr=999)
        with self.assertRaises(ValueError):
            self.phase("AQ10", canonical_sha="0" * 40)
        with self.assertRaises(ValueError):
            self.phase("AQ11", canonical_tree="1" * 40)

    def test_phase_mapping_requires_exact_fields(self):
        source = {
            "phase_id": "AQ12",
            "canonical_pr": 919,
            "canonical_sha": EXPECTED_PHASE_IDENTITIES["AQ12"]["canonical_sha"],
            "canonical_tree": EXPECTED_PHASE_IDENTITIES["AQ12"]["canonical_tree"],
            "disposition": "PASS",
            "canonical_verified": True,
            "source_assurance_pass": True,
            "promotion_assurance_pass": True,
            "post_merge_assurance_pass": True,
            "independent_evidence": True,
            "deterministic_evidence": True,
            "unresolved_critical_findings": 0,
        }
        item = PhaseEvidence.from_mapping(source)
        self.assertEqual("AQ12", item.phase_id)
        with self.assertRaises(ValueError):
            PhaseEvidence.from_mapping({"phase_id": "AQ12"})
        with self.assertRaises(TypeError):
            PhaseEvidence.from_mapping("not-a-mapping")

    def test_context_identity_and_authority_boundaries_fail_closed(self):
        for override in (
            {"repository": "Baelfyre/Other"},
            {"canonical_sha": "0" * 40},
            {"mode": "PRODUCTION"},
            {"cud10_state": "STARTED"},
            {"protected_policy_mutation_performed": True},
            {"production_mutation_performed": True},
            {"provider_activation_performed": True},
            {"telemetry_activation_performed": True},
            {"release_or_deploy_performed": True},
            {"aq15_authorized": True},
        ):
            with self.subTest(override=override), self.assertRaises(ValueError):
                self.context(**override)
        with self.assertRaises(TypeError):
            self.context(aq15_authorized=1)

    def test_text_and_sha_validation_fail_closed(self):
        with self.assertRaises(TypeError):
            self.context(repository=123)
        with self.assertRaises(ValueError):
            self.context(repository="  ")
        with self.assertRaises(ValueError):
            self.context(repository="Baelfyre/\nOrchestra")
        with self.assertRaises(ValueError):
            self.context(canonical_sha="ABC")
        with self.assertRaises(TypeError):
            self.phase("AQ9", canonical_sha=123)

    def test_phase_scalar_validation_fail_closed(self):
        identity = EXPECTED_PHASE_IDENTITIES["AQ9"]
        with self.assertRaises(ValueError):
            PhaseEvidence("UNKNOWN", 907, identity["canonical_sha"], identity["canonical_tree"], "PASS", True, True, True, True, True, True)
        with self.assertRaises(TypeError):
            self.phase("AQ9", canonical_pr=True)
        with self.assertRaises(ValueError):
            self.phase("AQ9", canonical_pr=0)
        with self.assertRaises(ValueError):
            self.phase("AQ9", disposition="UNKNOWN")
        with self.assertRaises(TypeError):
            self.phase("AQ9", independent_evidence=1)
        with self.assertRaises(TypeError):
            self.phase("AQ9", unresolved_critical_findings=True)
        with self.assertRaises(ValueError):
            self.phase("AQ9", unresolved_critical_findings=-1)

    def test_evaluator_requires_exact_order_and_shape(self):
        with self.assertRaises(TypeError):
            evaluate_final_effectiveness("bad", self.healthy_chain())
        with self.assertRaises(TypeError):
            evaluate_final_effectiveness(self.context(), "bad")
        with self.assertRaises(TypeError):
            evaluate_final_effectiveness(self.context(), (*self.healthy_chain()[:4], "bad"))
        with self.assertRaises(ValueError):
            evaluate_final_effectiveness(self.context(), self.healthy_chain()[:4])
        reordered = list(self.healthy_chain())
        reordered[0], reordered[1] = reordered[1], reordered[0]
        with self.assertRaises(ValueError):
            evaluate_final_effectiveness(self.context(), reordered)

    def test_multiple_gaps_accumulate_phase_reasons(self):
        evidence = list(self.healthy_chain())
        evidence[4] = self.phase(
            "AQ13",
            canonical_verified=False,
            source_assurance_pass=False,
            promotion_assurance_pass=False,
            post_merge_assurance_pass=False,
            independent_evidence=False,
            deterministic_evidence=False,
        )
        result = evaluate_final_effectiveness(self.context(), evidence)
        self.assertEqual("WAIT_FOR_EVIDENCE", result.disposition)
        self.assertEqual(6, len(result.findings[4].reason_codes))


if __name__ == "__main__":
    unittest.main()
