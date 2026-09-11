# @codebase_provenance_JEO
# @codebase_rights_JEO

from __future__ import annotations

import unittest

from orchestra_runtime.domain.adaptive.staged_rollout import (
    CANONICAL_START_SHA,
    CUD10_HOLD_STATE,
    ENVIRONMENT_SCOPE,
    ROLLOUT_MODE,
    TARGET_REPOSITORY,
    RolloutContext,
    StageEvidence,
    evaluate_staged_rollout,
)


class AQ13StagedRolloutTests(unittest.TestCase):
    def context(self, **overrides):
        values = {
            "repository": TARGET_REPOSITORY,
            "canonical_sha": CANONICAL_START_SHA,
            "mode": ROLLOUT_MODE,
            "environment_scope": ENVIRONMENT_SCOPE,
            "cud10_state": CUD10_HOLD_STATE,
        }
        values.update(overrides)
        return RolloutContext(**values)

    def stage(self, stage_id, **overrides):
        sequence = {"SHADOW": 1, "CANARY": 2, "LIMITED": 3, "EXPANDED": 4}[stage_id]
        values = {
            "stage_id": stage_id,
            "sequence": sequence,
            "observation_count": 10,
            "regression_count": 0,
            "critical_violation_count": 0,
            "rollback_signal": False,
            "evidence_ids": (f"evidence-{stage_id.lower()}",),
            "independent_evidence": True,
            "deterministic_replay_match": True,
        }
        values.update(overrides)
        return StageEvidence(**values)

    def healthy_stages(self):
        return tuple(self.stage(stage_id) for stage_id in ("SHADOW", "CANARY", "LIMITED", "EXPANDED"))

    def test_pass_is_non_authorizing(self):
        result = evaluate_staged_rollout(self.context(), self.healthy_stages())
        self.assertEqual("PASS", result.disposition)
        self.assertEqual(40, result.total_observations)
        self.assertEqual(0, result.total_regressions)
        self.assertEqual(0, result.total_critical_violations)
        self.assertEqual(0, result.regression_rate_bps)
        self.assertFalse(result.authority_granted)
        self.assertFalse(result.transition_authorized)
        self.assertFalse(result.release_authorized)
        self.assertFalse(result.production_authorized)
        self.assertFalse(result.cud10_admission_authorized)
        self.assertFalse(result.production_readiness_claimed)

    def test_critical_violation_forces_revision(self):
        stages = list(self.healthy_stages())
        stages[1] = self.stage("CANARY", critical_violation_count=1)
        result = evaluate_staged_rollout(self.context(), stages)
        self.assertEqual("REVISION_REQUIRED", result.disposition)
        self.assertEqual(1, result.total_critical_violations)
        self.assertIn("AQ13_CRITICAL_VIOLATION_DETECTED", result.findings[1].reason_codes)

    def test_aggregate_regression_rate_forces_revision(self):
        stages = [self.stage(stage_id, regression_count=1) for stage_id in ("SHADOW", "CANARY", "LIMITED", "EXPANDED")]
        result = evaluate_staged_rollout(self.context(), stages)
        self.assertEqual("REVISION_REQUIRED", result.disposition)
        self.assertEqual(1000, result.regression_rate_bps)
        self.assertTrue(all("AQ13_STAGE_REGRESSION_THRESHOLD_EXCEEDED" in item.reason_codes for item in result.findings))

    def test_rollback_signal_forces_hold(self):
        stages = list(self.healthy_stages())
        stages[2] = self.stage("LIMITED", rollback_signal=True)
        result = evaluate_staged_rollout(self.context(), stages)
        self.assertEqual("HOLD", result.disposition)
        self.assertIn("AQ13_ROLLBACK_SIGNAL_PRESENT", result.findings[2].reason_codes)

    def test_insufficient_stage_evidence_waits(self):
        stages = list(self.healthy_stages())
        stages[0] = self.stage("SHADOW", observation_count=9)
        result = evaluate_staged_rollout(self.context(), stages)
        self.assertEqual("WAIT_FOR_EVIDENCE", result.disposition)
        self.assertIn("AQ13_STAGE_OBSERVATIONS_INSUFFICIENT", result.findings[0].reason_codes)

    def test_non_independent_evidence_waits(self):
        stages = list(self.healthy_stages())
        stages[3] = self.stage("EXPANDED", independent_evidence=False)
        result = evaluate_staged_rollout(self.context(), stages)
        self.assertEqual("WAIT_FOR_EVIDENCE", result.disposition)
        self.assertIn("AQ13_INDEPENDENT_EVIDENCE_REQUIRED", result.findings[3].reason_codes)

    def test_replay_mismatch_waits(self):
        stages = list(self.healthy_stages())
        stages[3] = self.stage("EXPANDED", deterministic_replay_match=False)
        result = evaluate_staged_rollout(self.context(), stages)
        self.assertEqual("WAIT_FOR_EVIDENCE", result.disposition)
        self.assertIn("AQ13_DETERMINISTIC_REPLAY_MISMATCH", result.findings[3].reason_codes)

    def test_zero_observation_stage_is_safe_to_measure_but_insufficient(self):
        stages = list(self.healthy_stages())
        stages[0] = self.stage("SHADOW", observation_count=0)
        result = evaluate_staged_rollout(self.context(), stages)
        self.assertEqual("WAIT_FOR_EVIDENCE", result.disposition)
        self.assertEqual(0, result.findings[0].regression_rate_bps)

    def test_from_mapping_exact_contract(self):
        stage = StageEvidence.from_mapping({
            "stage_id": "shadow",
            "sequence": 1,
            "observation_count": 10,
            "regression_count": 0,
            "critical_violation_count": 0,
            "rollback_signal": False,
            "evidence_ids": ["one"],
            "independent_evidence": True,
            "deterministic_replay_match": True,
        })
        self.assertEqual("SHADOW", stage.stage_id)
        with self.assertRaises(ValueError):
            StageEvidence.from_mapping({"stage_id": "SHADOW"})
        with self.assertRaises(TypeError):
            StageEvidence.from_mapping("not-a-mapping")

    def test_context_identity_and_boundary_fail_closed(self):
        for override in (
            {"repository": "Baelfyre/Other"},
            {"canonical_sha": "0" * 40},
            {"mode": "PRODUCTION"},
            {"environment_scope": "PRODUCTION"},
            {"cud10_state": "STARTED"},
            {"protected_policy_mutation_performed": True},
            {"production_mutation_performed": True},
            {"provider_activation_performed": True},
            {"telemetry_activation_performed": True},
            {"release_or_deploy_performed": True},
        ):
            with self.subTest(override=override), self.assertRaises(ValueError):
                self.context(**override)
        with self.assertRaises(TypeError):
            self.context(production_mutation_performed=1)

    def test_context_text_validation(self):
        with self.assertRaises(TypeError):
            self.context(repository=123)
        with self.assertRaises(ValueError):
            self.context(repository="   ")
        with self.assertRaises(ValueError):
            self.context(repository="Baelfyre/\nOrchestra")

    def test_stage_identity_and_counts_fail_closed(self):
        with self.assertRaises(ValueError):
            StageEvidence("UNKNOWN", 1, 10, 0, 0, False, ("e",), True, True)
        with self.assertRaises(ValueError):
            self.stage("SHADOW", sequence=2)
        with self.assertRaises(TypeError):
            self.stage("SHADOW", observation_count=True)
        with self.assertRaises(ValueError):
            self.stage("SHADOW", observation_count=-1)
        with self.assertRaises(ValueError):
            self.stage("SHADOW", observation_count=1, regression_count=2)
        with self.assertRaises(ValueError):
            self.stage("SHADOW", observation_count=1, critical_violation_count=2)
        with self.assertRaises(TypeError):
            self.stage("SHADOW", rollback_signal=1)
        with self.assertRaises(TypeError):
            self.stage("SHADOW", independent_evidence=1)
        with self.assertRaises(TypeError):
            self.stage("SHADOW", deterministic_replay_match=1)

    def test_evidence_ids_fail_closed(self):
        with self.assertRaises(TypeError):
            self.stage("SHADOW", evidence_ids="one")
        with self.assertRaises(ValueError):
            self.stage("SHADOW", evidence_ids=())
        with self.assertRaises(ValueError):
            self.stage("SHADOW", evidence_ids=("one", "one"))
        with self.assertRaises(TypeError):
            self.stage("SHADOW", evidence_ids=(1,))
        with self.assertRaises(ValueError):
            self.stage("SHADOW", evidence_ids=(" ",))

    def test_evaluator_input_shape_fail_closed(self):
        with self.assertRaises(TypeError):
            evaluate_staged_rollout("bad-context", self.healthy_stages())
        with self.assertRaises(TypeError):
            evaluate_staged_rollout(self.context(), "bad-stages")
        with self.assertRaises(TypeError):
            evaluate_staged_rollout(self.context(), (*self.healthy_stages()[:3], "bad"))
        with self.assertRaises(ValueError):
            evaluate_staged_rollout(self.context(), self.healthy_stages()[:3])

    def test_duplicate_and_out_of_order_stages_fail_closed(self):
        duplicate = list(self.healthy_stages())
        duplicate[3] = self.stage("LIMITED")
        with self.assertRaises(ValueError):
            evaluate_staged_rollout(self.context(), duplicate)
        out_of_order = list(self.healthy_stages())
        out_of_order[0], out_of_order[1] = out_of_order[1], out_of_order[0]
        with self.assertRaises(ValueError):
            evaluate_staged_rollout(self.context(), out_of_order)

    def test_stage_level_regression_reason_without_aggregate_failure(self):
        stages = list(self.healthy_stages())
        stages[0] = self.stage("SHADOW", observation_count=100, regression_count=6)
        for index in range(1, 4):
            stage_id = ("CANARY", "LIMITED", "EXPANDED")[index - 1]
            stages[index] = self.stage(stage_id, observation_count=100, regression_count=0)
        result = evaluate_staged_rollout(self.context(), stages)
        self.assertEqual("PASS", result.disposition)
        self.assertEqual(150, result.regression_rate_bps)
        self.assertIn("AQ13_STAGE_REGRESSION_THRESHOLD_EXCEEDED", result.findings[0].reason_codes)


if __name__ == "__main__":
    unittest.main()
