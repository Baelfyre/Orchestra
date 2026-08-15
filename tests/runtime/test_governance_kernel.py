import json
from pathlib import Path
import unittest

from orchestra_runtime.governance_kernel import (
    ArbiterKernelInput,
    ArbiterReasonCode,
    GovernanceDecisionRecord,
    TransitionDisposition,
    evaluate_arbiter,
    safe_evaluate_arbiter,
)


def decision(value="APPROVED", *, human=False):
    return GovernanceDecisionRecord(
        reviewer="arbiter",
        project_context="fixture-project",
        decision=value,
        reason="fixture",
        human_review_required=human,
    )


class ArbiterKernelTests(unittest.TestCase):
    def test_approved_current_evidence_continues(self):
        result = evaluate_arbiter(ArbiterKernelInput("project", "unit", (decision(),)))
        self.assertEqual(TransitionDisposition.AUTO_CONTINUE, result.disposition)

    def test_approved_stale_evidence_waits(self):
        result = evaluate_arbiter(
            ArbiterKernelInput("project", "unit", (decision(),), evidence_fresh=False)
        )
        self.assertEqual(TransitionDisposition.WAIT_FOR_EVIDENCE, result.disposition)

    def test_blocked_stops(self):
        result = evaluate_arbiter(ArbiterKernelInput("project", "unit", (decision("BLOCKED"),)))
        self.assertEqual(TransitionDisposition.STOP, result.disposition)

    def test_human_review_required_escalates(self):
        result = evaluate_arbiter(ArbiterKernelInput("project", "unit", (decision(human=True),)))
        self.assertEqual(TransitionDisposition.ESCALATE_HUMAN, result.disposition)

    def test_capacity_precedes_evidence_wait(self):
        result = evaluate_arbiter(
            ArbiterKernelInput(
                "project",
                "unit",
                (decision(),),
                host_capacity_available=False,
                evidence_fresh=False,
            )
        )
        self.assertEqual(TransitionDisposition.WAIT_FOR_CAPACITY, result.disposition)

    def test_revision_required_autoremediates_only_when_bounded(self):
        result = evaluate_arbiter(
            ArbiterKernelInput(
                "project",
                "unit",
                (decision("REVISION_REQUIRED"),),
                deterministic_defect=True,
                remediation_authorized=True,
                remediation_in_scope=True,
            )
        )
        self.assertEqual(TransitionDisposition.AUTO_REMEDIATE_AND_REVALIDATE, result.disposition)

    def test_revision_required_without_remediation_authority_escalates(self):
        result = evaluate_arbiter(
            ArbiterKernelInput(
                "project",
                "unit",
                (decision("REVISION_REQUIRED"),),
                deterministic_defect=True,
            )
        )
        self.assertEqual(TransitionDisposition.ESCALATE_HUMAN, result.disposition)

    def test_remediation_budget_exhaustion_escalates(self):
        result = evaluate_arbiter(
            ArbiterKernelInput(
                "project",
                "unit",
                (decision("REVISION_REQUIRED"),),
                deterministic_defect=True,
                remediation_authorized=True,
                remediation_in_scope=True,
                remediation_attempt_count=3,
            )
        )
        self.assertEqual(TransitionDisposition.ESCALATE_HUMAN, result.disposition)
        self.assertIn(ArbiterReasonCode.REMEDIATION_BUDGET_EXHAUSTED, result.reason_codes)

    def test_unknown_governance_decision_rejected_at_typed_boundary(self):
        with self.assertRaises(ValueError):
            decision("PASS_WITH_FINDINGS")

    def test_claimed_disposition_cannot_override_kernel(self):
        result = evaluate_arbiter(
            ArbiterKernelInput("project", "unit", (decision(),), evidence_fresh=False)
        )
        with self.assertRaises(ValueError):
            result.assert_claimed_disposition("AUTO_CONTINUE")

    def test_malformed_external_candidate_escalates(self):
        result = safe_evaluate_arbiter({"disposition": "AUTO_CONTINUE"})
        self.assertEqual(TransitionDisposition.ESCALATE_HUMAN, result.disposition)
        self.assertIn(ArbiterReasonCode.MALFORMED_INPUT, result.reason_codes)

    def test_authority_invalid_has_highest_precedence(self):
        result = evaluate_arbiter(
            ArbiterKernelInput(
                "project",
                "unit",
                (decision(),),
                authority_valid=False,
                host_capacity_available=False,
                evidence_fresh=False,
            )
        )
        self.assertEqual(TransitionDisposition.STOP, result.disposition)

    def test_machine_schemas_are_strict_and_versioned(self):
        root = Path(__file__).resolve().parents[2]
        names = (
            "governance-decision.schema.json",
            "arbiter-kernel-input.schema.json",
            "arbiter-kernel-result.schema.json",
        )
        for name in names:
            with (root / "machine" / "schemas" / name).open("r", encoding="utf-8") as handle:
                schema = json.load(handle)
            self.assertEqual("https://json-schema.org/draft/2020-12/schema", schema["$schema"])
            self.assertFalse(schema["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
