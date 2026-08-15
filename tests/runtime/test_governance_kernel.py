from dataclasses import FrozenInstanceError
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import orchestra_runtime.governance_kernel as governance_kernel
from orchestra_runtime import machine_contracts
from orchestra_runtime.governance_kernel import (
    ArbiterKernelInput,
    ArbiterReasonCode,
    DEFAULT_MAX_IDENTICAL_FAILURE_REPETITIONS,
    DEFAULT_MAX_REMEDIATION_ATTEMPTS,
    GOVERNANCE_KERNEL_SCHEMA_VERSION,
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

    def test_machine_policy_precedence_selects_between_valid_candidates(self):
        candidate = ArbiterKernelInput(
            "project",
            "unit",
            (decision(),),
            authority_valid=False,
            evidence_fresh=False,
        )
        reordered = (
            "WAIT_FOR_EVIDENCE",
            "STOP",
            "ESCALATE_HUMAN",
            "WAIT_FOR_CAPACITY",
            "AUTO_REMEDIATE_AND_REVALIDATE",
            "AUTO_CONTINUE",
        )
        with patch.object(governance_kernel, "transition_precedence", return_value=reordered):
            result = evaluate_arbiter(candidate)
        self.assertEqual(TransitionDisposition.WAIT_FOR_EVIDENCE, result.disposition)
        self.assertIn(ArbiterReasonCode.EVIDENCE_STALE, result.reason_codes)

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

    def test_remediation_budget_boundary_is_monotonic(self):
        bounded = dict(
            governance_decisions=(decision("REVISION_REQUIRED"),),
            deterministic_defect=True,
            remediation_authorized=True,
            remediation_in_scope=True,
            maximum_remediation_attempts=3,
        )
        below = evaluate_arbiter(ArbiterKernelInput("project", "below", remediation_attempt_count=2, **bounded))
        at = evaluate_arbiter(ArbiterKernelInput("project", "at", remediation_attempt_count=3, **bounded))
        beyond = evaluate_arbiter(ArbiterKernelInput("project", "beyond", remediation_attempt_count=4, **bounded))
        self.assertEqual(TransitionDisposition.AUTO_REMEDIATE_AND_REVALIDATE, below.disposition)
        self.assertEqual(TransitionDisposition.ESCALATE_HUMAN, at.disposition)
        self.assertEqual(TransitionDisposition.ESCALATE_HUMAN, beyond.disposition)

    def test_identical_failure_boundary_escalates_only_beyond_limit(self):
        bounded = dict(
            governance_decisions=(decision("REVISION_REQUIRED"),),
            deterministic_defect=True,
            remediation_authorized=True,
            remediation_in_scope=True,
            maximum_identical_failure_repetitions=2,
        )
        at = evaluate_arbiter(AriterKernelInput("project", "at", identical_failure_repetitions=2, **bounded))
        beyond = evaluate_arbiter(ArbiterKernelInput("project", "beyond", identical_failure_repetitions=3, **bounded))
        self.assertEqual(TransitionDisposition.AUTO_REMEDIATE_AND_REVALIDATE, at.disposition)
        self.assertEqual(TransitionDisposition.ESCALATE_HUMAN, beyond.disposition)
        self.assertIn(ArbiterReasonCode.IDENTICAL_FAILURE_LIMIT_EXCEEDED, beyond.reason_codes)

    def test_default_remediation_limits_are_machine_policy_values(self):
        kernel_input = ArbiterKernelInput("project", "unit", (decision(),))
        remediation = machine_contracts.default_remediation_limits()
        self.assertEqual(
            remediation["maximum_remediation_attempts_per_unit"],
            DEFAULT_MAX_REMEDIATION_ATTEMPTS,
        )
        self.assertEqual(
            remediation["maximum_identical_failure_repetitions"],
            DEFAULT_MAX_IDENTICAL_FAILURE_REPETITIONS,
        )
        self.assertEqual(DEFAULT_MAX_REMEDIATION_ATTEMPTS, kernel_input.maximum_remediation_attempts)
        self.assertEqual(
            DEFAULT_MAX_IDENTICAL_FAILURE_REPETITIONS,
            kernel_input.maximum_identical_failure_repetitions,
        )

    def test_positive_limit_boundaries_accept_one_and_reject_zero_or_negative(self):
        valid = ArbiterKernelInput(
            "project",
            "unit",
            (decision(),),
            maximum_remediation_attempts=1,
            maximum_identical_failure_repetitions=1,
        )
        self.assertEqual(1, valid.maximum_remediation_attempts)
        self.assertEqual(1, valid.maximum_identical_failure_repetitions)
        for field in ("maximum_remediation_attempts", "maximum_identical_failure_repetitions"):
            for invalid in (0, -1):
                with self.subTest(field=field, invalid=invalid), self.assertRaises(ValueError):
                    ArbiterKernelInput("project", "unit", (decision(),), **{field: invalid})

    def test_schema_version_rejects_lower_and_higher_but_accepts_equal_value(self):
        dynamic_equal = "".join(["1", ".0", ".0"])
        self.assertEqual(GOVERNANCE_KERNEL_SCHEMA_VERSION, dynamic_equal)
        self.assertIsNot(GOVERNANCE_KERNEL_SCHEMA_VERSION, dynamic_equal)
        self.assertEqual(dynamic_equal, decision().schema_version)
        for invalid in ("0.9.0", "9.0.0"):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                GovernanceDecisionRecord(
                    reviewer="arbiter",
                    project_context="fixture",
                    decision="APPROVED",
                    reason="fixture",
                    schema_version=invalid,
                )
            with self.subTest(input_invalid=invalid), self.assertRaises(ValueError):
                ArbiterKernelInput("project", "unit", (decision(),), schema_version=invalid)

    def test_governance_records_are_immutable(self):
        record = decision()
        with self.assertRaises(FrozenInstanceError):
            record.reason = "changed"  # type: ignore[misc]

    def test_unknown_governance_decision_rejected_at_typed_boundary(self):
        with self.assertRaises(ValueError):
            decision("PASS_WITH_FINDINGS")

    def test_claimed_disposition_cannot_override_kernel(self):
        result = evaluate_arbiter(
            ArbiterKernelInput("project", "unit", (decision(),), evidence_fresh=False)
        )
        with self.assertRaises(ValueError):
            result.assert_claimed_disposition("AUTO_CONTINUE")
        result.assert_claimed_disposition("WAIT_FOR_EVIDENCE")

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
