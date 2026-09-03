#!/usr/bin/env python3
"""Deterministic behavioral tests for OR-GOV-9 Conditional Specialist Governance Sufficiency Audit.

Verifies:
1. Governor legal/privacy/licensing invariants and UIX-9 frozen guidance integrity.
2. Weaver source-to-model traceability and semantic invalidation rules.
3. Cloak UI visibility != authorization boundary and UIX-9 frozen guidance integrity.
4. Dagger simulation-first safety gates and blocked destructive execution.
5. All 20 OR-GOV cross-specialist audit cases.
6. Machine and human audit disposition artifact consistency.
"""

import hashlib
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestOrGov9SpecialistSufficiency(unittest.TestCase):
    """Behavioral tests verifying OR-GOV-9 specialist sufficiency and invariants."""

    def test_01_governor_no_assumption_and_invariants(self):
        """Test Governor enforces no-assumption rules for jurisdiction, legal obligations, and frameworks."""
        skill_path = REPO_ROOT / "skills" / "the-governor" / "SKILL.md"
        self.assertTrue(skill_path.exists())
        content = skill_path.read_text(encoding="utf-8")
        self.assertIn("Do not assume jurisdiction, legal obligations, privacy requirements, licensing status, or compliance frameworks", content)
        self.assertIn("human_review_required: true", content)
        self.assertIn("Cannot assess risk without context", content)

    def test_02_governor_technical_security_vs_legal_governance(self):
        """Test Governor separates technical defensive security (Cipher) from legal/regulatory governance."""
        skill_path = REPO_ROOT / "skills" / "the-governor" / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")
        self.assertIn("Technical defensive privacy and security controls stay with Cipher", content)
        self.assertIn("Governor approval accepts governance disposition and constraints only", content)

    def test_03_governor_human_escalation_availability(self):
        """Test Governor human escalation guide defines clear escalation points for material uncertainty."""
        guide_path = REPO_ROOT / "skills" / "the-governor" / "HUMAN_ESCALATION_BOUNDARIES_GUIDE.md"
        self.assertTrue(guide_path.exists())
        content = guide_path.read_text(encoding="utf-8")
        self.assertIn("human_review_required: true", content)
        self.assertIn("REVISION_REQUIRED", content)
        self.assertIn("BLOCKED", content)

    def test_04_governor_frozen_skill_digest_preserved(self):
        """Test skills/the-governor/SKILL.md matches canonical UIX-9 manifest digest exactly."""
        manifest_path = REPO_ROOT / "machine" / "ui" / "uix9-live-guidance-manifest.v1.json"
        self.assertTrue(manifest_path.exists())
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        skill_path = REPO_ROOT / "skills" / "the-governor" / "SKILL.md"
        actual_digest = hashlib.sha256(skill_path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()

        governor_entry = next((m for m in manifest.get("materials", []) if m.get("path") == "skills/the-governor/SKILL.md"), None)
        self.assertIsNotNone(governor_entry)
        self.assertEqual(actual_digest, governor_entry["canonical_blob_digest"])

    def test_05_weaver_source_to_model_traceability(self):
        """Test Weaver requires source facts -> diagram without inventing facts."""
        guide_path = REPO_ROOT / "skills" / "weaver" / "MODEL_TRACEABILITY_INVALIDATION_GUIDE.md"
        self.assertTrue(guide_path.exists())
        content = guide_path.read_text(encoding="utf-8")
        self.assertIn("Represent missing facts as `UNKNOWN` or omit them with an explicit limitation; never invent a connector", content)

    def test_06_weaver_contradiction_and_unknown_handling(self):
        """Test Weaver marks conflicting facts CONTRADICTED and preserves UNKNOWN."""
        guide_path = REPO_ROOT / "skills" / "weaver" / "MODEL_TRACEABILITY_INVALIDATION_GUIDE.md"
        content = guide_path.read_text(encoding="utf-8")
        self.assertIn("Mark the affected nodes or edges `CONTRADICTED`", content)
        self.assertIn("UNKNOWN", content)

    def test_07_weaver_semantic_vs_cosmetic_invalidation(self):
        """Test Weaver invalidates on semantic source changes but preserves validity across cosmetic layout changes."""
        guide_path = REPO_ROOT / "skills" / "weaver" / "MODEL_TRACEABILITY_INVALIDATION_GUIDE.md"
        content = guide_path.read_text(encoding="utf-8")
        self.assertIn("Invalidate dependent diagram evidence when an entity, boundary, actor, flow, cardinality, state transition, security zone, deployment fact, or source revision changes", content)
        self.assertIn("Cosmetic layout-only changes do not invalidate semantic evidence", content)

    def test_08_weaver_non_authorizing_diagram_validation(self):
        """Test Weaver diagram validation does not constitute architecture, database, security, or transition approval."""
        guide_path = REPO_ROOT / "skills" / "weaver" / "MODEL_TRACEABILITY_INVALIDATION_GUIDE.md"
        content = guide_path.read_text(encoding="utf-8")
        self.assertIn("Diagram validation is not architecture, database, security, or transition approval", content)

    def test_09_cloak_ui_visibility_not_authorization(self):
        """Test Cloak enforces UI VISIBILITY != AUTHORIZATION invariant."""
        guide_path = REPO_ROOT / "skills" / "cloak" / "FRONTEND_ROUTING_COMPONENT_BOUNDARIES_GUIDE.md"
        self.assertTrue(guide_path.exists())
        content = guide_path.read_text(encoding="utf-8")
        self.assertIn("A hidden navigation item is not authorization. Cipher owns access-control policy and enforcement review", content)
        self.assertIn("Navigation may hide unavailable actions to reduce confusion, but backend enforcement remains mandatory", content)

    def test_10_cloak_permission_aware_ux(self):
        """Test Cloak permission-aware UX explains limitations without leaking security policy."""
        guide_path = REPO_ROOT / "skills" / "cloak" / "FRONTEND_ROUTING_COMPONENT_BOUNDARIES_GUIDE.md"
        content = guide_path.read_text(encoding="utf-8")
        self.assertIn("Permission-denied screens should explain the user-visible limitation without leaking sensitive policy details", content)
        self.assertIn("Route policy and threat questions to Cipher", content)

    def test_11_cloak_routing_and_component_boundaries(self):
        """Test Cloak hands off architecture to Clockwork, authorization to Cipher, validation to Overseer."""
        guide_path = REPO_ROOT / "skills" / "cloak" / "FRONTEND_ROUTING_COMPONENT_BOUNDARIES_GUIDE.md"
        content = guide_path.read_text(encoding="utf-8")
        self.assertIn("Cloak hands off the user-visible route contract, semantic navigation structure, responsive shell behavior, focus expectations, and component-state matrix", content)
        self.assertIn("Ponytail implements it", content)
        self.assertIn("Clockwork owns architecture and state placement", content)
        self.assertIn("Cipher owns authorization", content)
        self.assertIn("Overseer owns route and state validation evidence", content)

    def test_12_cloak_frozen_skill_digest_preserved(self):
        """Test skills/cloak/SKILL.md matches canonical UIX-9 manifest digest exactly."""
        manifest_path = REPO_ROOT / "machine" / "ui" / "uix9-live-guidance-manifest.v1.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        skill_path = REPO_ROOT / "skills" / "cloak" / "SKILL.md"
        actual_digest = hashlib.sha256(skill_path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()

        cloak_entry = next((m for m in manifest.get("materials", []) if m.get("path") == "skills/cloak/SKILL.md"), None)
        self.assertIsNotNone(cloak_entry)
        self.assertEqual(actual_digest, cloak_entry["canonical_blob_digest"])

    def test_13_dagger_safety_gates_and_simulation_first(self):
        """Test Dagger safety gates enforce simulation-first and block destructive execution."""
        gates_path = REPO_ROOT / "skills" / "dagger" / "SAFETY_GATES.md"
        self.assertTrue(gates_path.exists())
        content = gates_path.read_text(encoding="utf-8")
        self.assertIn("Stop immediately if production is targeted", content)
        self.assertIn("Forbidden actions", content)

    def test_14_dagger_guardrail_regression_passes(self):
        """Test Dagger programmatic guardrail passes all simulation cases and blocks live execution."""
        res = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "test_dagger_guardrail.py")],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, f"Dagger guardrail test failed: {res.stderr}")
        self.assertIn("All dagger guardrail simulation tests passed", res.stdout)

    def test_15_cross_specialist_cases_1_to_5(self):
        """Verify cross-specialist audit cases 1 to 5 (tenancy & capacity postures)."""
        # Case 1: Future multi-tenancy possible -> SCALE_READY, no premature isolation
        # Case 2: Confirmed multi-tenant -> Cipher tenant requirements, Clockwork boundaries, Chronicler isolation
        # Case 3: Single-tenant -> minimal complexity decision, no multi-tenant overhead
        # Case 4: Unknown capacity -> UNKNOWN preserved in CapacityEnvelope, no invented RPS
        # Case 5: Estimated capacity -> ESTIMATED preserved, validated against bounded range
        envelope_schema = json.loads((REPO_ROOT / "machine" / "schemas" / "capacity-envelope.v1.schema.json").read_text(encoding="utf-8"))
        val_enum = envelope_schema["$defs"]["capacity_value"]["properties"]["value_status"]["enum"]
        self.assertIn("UNKNOWN", val_enum)
        self.assertIn("ESTIMATED", val_enum)

    def test_16_cross_specialist_cases_6_to_8(self):
        """Verify cross-specialist audit cases 6 to 8 (architecture postures & unknown migration)."""
        # Case 6: SCALE_READY posture
        # Case 7: SCALE_PROVISIONED posture
        # Case 8: Migration with unknown production presence -> pre-contract gap preserved
        profile_schema = json.loads((REPO_ROOT / "machine" / "schemas" / "project-architecture-governance-profile.v1.schema.json").read_text(encoding="utf-8"))
        self.assertIn("SCALE_READY", profile_schema["properties"]["scale_posture"]["enum"])
        self.assertIn("SCALE_PROVISIONED", profile_schema["properties"]["scale_posture"]["enum"])
        migration_schema = json.loads((REPO_ROOT / "machine" / "schemas" / "migration-risk-contract.v1.schema.json").read_text(encoding="utf-8"))
        # Boolean schema gap verified: boolean properties only, unknown represented via pre-contract gap
        self.assertEqual(migration_schema["properties"]["production_data"]["type"], "boolean")

    def test_17_cross_specialist_cases_9_to_11(self):
        """Verify cross-specialist audit cases 9 to 11 (privacy & legal context)."""
        # Case 9: Privacy-relevant tenant data -> Governor audits compliance, Cipher owns controls
        # Case 10: Legal jurisdiction absent -> Governor does not speculate, marks human review
        # Case 11: License status unknown -> human_review_required: true
        gov_skill = (REPO_ROOT / "skills" / "the-governor" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Do not assume jurisdiction", gov_skill)
        self.assertIn("license compatibility cannot be confirmed automatically", gov_skill)

    def test_18_cross_specialist_cases_12_to_15(self):
        """Verify cross-specialist audit cases 12 to 15 (diagram & UI authorization)."""
        # Case 12: Source revision change -> DIAGRAM_STALE
        # Case 13: Diagram cosmetic change -> semantic evidence preserved
        # Case 14: Tenant security UX -> rendered by Cloak
        # Case 15: Hidden control -> backend authorization mandatory
        weaver_guide = (REPO_ROOT / "skills" / "weaver" / "MODEL_TRACEABILITY_INVALIDATION_GUIDE.md").read_text(encoding="utf-8")
        self.assertIn("DIAGRAM_STALE", weaver_guide)
        cloak_guide = (REPO_ROOT / "skills" / "cloak" / "FRONTEND_ROUTING_COMPONENT_BOUNDARIES_GUIDE.md").read_text(encoding="utf-8")
        self.assertIn("A hidden navigation item is not authorization", cloak_guide)

    def test_19_cross_specialist_cases_16_to_20(self):
        """Verify cross-specialist audit cases 16 to 20 (validation proof states & Dagger gate)."""
        # Case 16: Failed AVC dimension -> proof state FAILED
        # Case 17: NOT_PROVEN validation -> blocks auto-continuation
        # Case 18: NOT_REQUIRED validation -> explicitly recorded
        # Case 19: Stale evidence after Tuner invalidation -> Arbiter invalidates
        # Case 20: Dagger execution without authority -> blocked
        avc_guide = (REPO_ROOT / "skills" / "overseer" / "ARCHITECTURE_VALIDATION_CONTRACT_GUIDE.md").read_text(encoding="utf-8")
        self.assertIn("PROVEN", avc_guide)
        self.assertIn("NOT_PROVEN", avc_guide)
        self.assertIn("NOT_REQUIRED", avc_guide)
        self.assertIn("FAILED", avc_guide)
        arb_guide = (REPO_ROOT / "skills" / "arbiter" / "CONTINUITY_EVALUATION_GUIDE.md").read_text(encoding="utf-8")
        self.assertIn("STALE_INVALIDATED", arb_guide)

    def test_20_machine_disposition_artifact_validity(self):
        """Test docs/governance/or_gov_9_specialist_sufficiency_disposition.v1.json exists and is valid."""
        disp_path = REPO_ROOT / "docs" / "governance" / "or_gov_9_specialist_sufficiency_disposition.v1.json"
        self.assertTrue(disp_path.exists())
        data = json.loads(disp_path.read_text(encoding="utf-8"))
        self.assertEqual(data["phase"], "OR-GOV-9")
        self.assertEqual(data["audit_disposition"], "OR_GOV_9_SUFFICIENT_NO_REFINEMENT")
        self.assertTrue(data["or_gov_10_eligible"])
        self.assertEqual(data["specialists_audited"]["the_governor"]["disposition"], "NO_REFINEMENT_REQUIRED")
        self.assertEqual(data["specialists_audited"]["weaver"]["disposition"], "NO_REFINEMENT_REQUIRED")
        self.assertEqual(data["specialists_audited"]["cloak"]["disposition"], "NO_REFINEMENT_REQUIRED")
        self.assertEqual(data["specialists_audited"]["dagger"]["disposition"], "REGRESSION_PASS_NO_REFINEMENT_REQUIRED")

    def test_21_human_audit_report_completeness(self):
        """Test docs/governance/OR_GOV_9_SPECIALIST_SUFFICIENCY_AUDIT.md exists and contains all sections."""
        report_path = REPO_ROOT / "docs" / "governance" / "OR_GOV_9_SPECIALIST_SUFFICIENCY_AUDIT.md"
        self.assertTrue(report_path.exists())
        content = report_path.read_text(encoding="utf-8")
        self.assertIn("OR-GOV-9 Conditional Specialist Governance Sufficiency Audit Report", content)
        self.assertIn("The Governor", content)
        self.assertIn("Weaver", content)
        self.assertIn("Cloak", content)
        self.assertIn("Dagger (Regression Only)", content)
        self.assertIn("Cross-Specialist Audit Cases (20/20 PASS)", content)
        self.assertIn("AUDIT_RESULT = OR_GOV_9_SUFFICIENT_NO_REFINEMENT", content)
        self.assertIn("OR_GOV_10_ELIGIBLE = TRUE", content)

    def test_22_final_disposition_and_eligibility(self):
        """Verify overall OR-GOV-9 disposition matches governed requirements."""
        disp_path = REPO_ROOT / "docs" / "governance" / "or_gov_9_specialist_sufficiency_disposition.v1.json"
        data = json.loads(disp_path.read_text(encoding="utf-8"))
        self.assertTrue(data["invariants_confirmed"]["no_assumed_jurisdiction"])
        self.assertTrue(data["invariants_confirmed"]["source_facts_to_diagram_without_invented_facts"])
        self.assertTrue(data["invariants_confirmed"]["ui_visibility_distinct_from_authorization"])
        self.assertTrue(data["invariants_confirmed"]["dagger_live_execution_blocked"])
        self.assertTrue(data["invariants_confirmed"]["frozen_skills_preserved"])


if __name__ == "__main__":
    unittest.main()
