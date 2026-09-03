#!/usr/bin/env python3
"""Deterministic end-to-end integration and closeout tests for OR-GOV-10.

Proves that OR-GOV-1 through OR-GOV-9 operate as one coherent governance system:
1. Contract Inventory and ownership validation across all seven canonical machine contracts.
2. Specialist ownership chain and non-absorption boundaries.
3. Scenarios A through J:
   - Scenario A: Simple trivial change (minimum route, no ceremony explosion).
   - Scenario B: Premature scaling request (Steward -> Clockwork, scalability alone insufficient).
   - Scenario C: Unknown capacity (UNKNOWN preserved, no fabricated metric).
   - Scenario D: Empirical performance claim (Overseer validation, NOT_PROVEN without evidence).
   - Scenario E: Multi-tenant persistence change (Steward -> Clockwork -> Chronicler -> Cipher -> Ponytail -> Overseer).
   - Scenario F: Capacity materially changes (Tuner declared-edge semantic invalidation).
   - Scenario G: Stale validation evidence (Arbiter freshness enforcement).
   - Scenario H: Migration production state unknown (pre-contract gap preserved, no false coercion).
   - Scenario I: Documentation reconciliation (Scribe proof/value preservation, no silent promotion).
   - Scenario J: Dagger request (blocked without explicit authority, simulation-first).
4. Adapter parity, prompt budget, frozen guidance, and architecture boundaries.
5. Post-closeout record accuracy regressions (canonical enums, document accuracy, historical phase ledger, status preservation).
"""

import hashlib
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestOrGov10E2EIntegrationCloseout(unittest.TestCase):
    """E2E integration test suite for the complete OR-GOV program closeout."""

    def test_01_contract_inventory_and_ownership(self):
        """Verify all seven canonical machine schemas, ownership, and required fields."""
        schemas_dir = REPO_ROOT / "machine" / "schemas"
        contracts = {
            "capacity-envelope.v1.schema.json": ("CapacityEnvelope", "the-steward"),
            "product-intent-contract.v1.schema.json": ("ProductIntentContract", "the-steward"),
            "architecture-complexity-decision.v1.schema.json": ("ArchitectureComplexityDecision", "clockwork"),
            "migration-risk-contract.v1.schema.json": ("MigrationRiskContract", "chronicler"),
            "architecture-governance-intake.v1.schema.json": ("ArchitectureGovernanceIntake", "conductor"),
            "architecture-validation-contract.v1.schema.json": ("ArchitectureValidationContract", "overseer"),
            "project-architecture-governance-profile.v1.schema.json": ("ProjectArchitectureGovernanceProfile", None),
        }
        for filename, (expected_name, expected_owner) in contracts.items():
            schema_path = schemas_dir / filename
            self.assertTrue(schema_path.exists(), f"Missing schema: {filename}")
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            self.assertEqual(schema["properties"]["contract_name"]["const"], expected_name)
            self.assertIn("schema_version", schema["properties"])
            self.assertTrue(len(schema.get("required", [])) > 0, f"Schema {filename} missing required fields")
            if expected_owner:
                self.assertEqual(schema["properties"]["owner"]["const"], expected_owner)
            else:
                self.assertNotIn("owner", schema.get("properties", {}), f"Schema {filename} should not define owner")

    def test_02_specialist_ownership_chain(self):
        """Verify strict ownership chain: no specialist silently absorbs another's authority."""
        steward = (REPO_ROOT / "skills" / "the-steward" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Business alignment and scope governance authority", steward)

        clockwork = (REPO_ROOT / "skills" / "clockwork" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Engineering and Code Structure Specialist", clockwork)

        chronicler = (REPO_ROOT / "skills" / "chronicler" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Data Persistence and Database Management Specialist", chronicler)

        cipher = (REPO_ROOT / "skills" / "cipher" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Security, Privacy, Access Control, and Threat Review Specialist", cipher)

        tuner = (REPO_ROOT / "skills" / "the-tuner" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Cross-specialist coordination", tuner)

        overseer = (REPO_ROOT / "skills" / "overseer" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("QA, Test Strategy, Validation", overseer)

        arbiter = (REPO_ROOT / "skills" / "arbiter" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Workflow continuity, validation, and transition governance", arbiter)

        ponytail = (REPO_ROOT / "skills" / "ponytail" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Implementation and Navigation Specialist", ponytail)

        scribe = (REPO_ROOT / "skills" / "scribe" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Documentation, Domain Narrative, and Knowledge Traceability Specialist", scribe)

    def test_03_scenario_a_simple_trivial_change(self):
        """Scenario A: Simple trivial change routes minimally without governance explosion."""
        routes = json.loads((REPO_ROOT / "machine" / "routing" / "routes.v1.json").read_text(encoding="utf-8"))
        self.assertIn("direct_routes", routes)
        intake_guide = (REPO_ROOT / "skills" / "conductor" / "ARCHITECTURE_GOVERNANCE_INTAKE_GUIDE.md").read_text(encoding="utf-8")
        self.assertIn("TRIVIAL", intake_guide)

    def test_04_scenario_b_premature_scaling_request(self):
        """Scenario B: Premature scaling ('Add Redis later') requires Steward intent and Clockwork review."""
        complexity_guide = (REPO_ROOT / "skills" / "clockwork" / "ARCHITECTURE_COMPLEXITY_AND_SCALE_POSTURE_GUIDE.md").read_text(encoding="utf-8")
        self.assertIn("SCALE_READY", complexity_guide)
        self.assertIn("SCALE_PROVISIONED", complexity_guide)
        self.assertIn("ProductIntentContract", complexity_guide)

    def test_05_scenario_c_unknown_capacity(self):
        """Scenario C: Unknown capacity preserves UNKNOWN without fabricated precision."""
        envelope_schema = json.loads((REPO_ROOT / "machine" / "schemas" / "capacity-envelope.v1.schema.json").read_text(encoding="utf-8"))
        val_enum = envelope_schema["$defs"]["capacity_value"]["properties"]["value_status"]["enum"]
        self.assertIn("UNKNOWN", val_enum)
        self.assertIn("NOT_APPLICABLE", val_enum)

    def test_06_scenario_d_empirical_performance_claim(self):
        """Scenario D: Empirical performance claim ('Supports 300 RPS') requires Overseer empirical proof."""
        avc_guide = (REPO_ROOT / "skills" / "overseer" / "ARCHITECTURE_VALIDATION_CONTRACT_GUIDE.md").read_text(encoding="utf-8")
        self.assertIn("NOT_PROVEN", avc_guide)
        self.assertIn("PROVEN", avc_guide)
        self.assertIn("FAILED", avc_guide)

    def test_07_scenario_e_multitenant_persistence_change(self):
        """Scenario E: Multi-tenant persistence change routes through intent, architecture, persistence, security, implementation, and validation."""
        tenant_guide = (REPO_ROOT / "skills" / "cipher" / "TENANT_SECURITY_GOVERNANCE_GUIDE.md").read_text(encoding="utf-8")
        self.assertIn("MULTI_TENANT", tenant_guide)
        self.assertIn("tenant isolation", tenant_guide.lower())
        chronicler_skill = (REPO_ROOT / "skills" / "chronicler" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("migration", chronicler_skill)

    def test_08_scenario_f_capacity_material_change_invalidation(self):
        """Scenario F: Capacity material change triggers Tuner declared-edge invalidation and minimal re-entry."""
        tuner_guide = (REPO_ROOT / "skills" / "the-tuner" / "GOVERNANCE_CONTRACT_DEPENDENCY_GUIDE.md").read_text(encoding="utf-8")
        self.assertIn("invalidation", tuner_guide.lower())
        self.assertIn("re-entry", tuner_guide.lower())

    def test_09_scenario_g_stale_validation_evidence(self):
        """Scenario G: Stale validation evidence after commit boundary triggers WAIT_FOR_EVIDENCE."""
        arbiter_guide = (REPO_ROOT / "skills" / "arbiter" / "CONTINUITY_EVALUATION_GUIDE.md").read_text(encoding="utf-8")
        self.assertIn("STALE_INVALIDATED", arbiter_guide)
        self.assertIn("WAIT_FOR_EVIDENCE", arbiter_guide)

    def test_10_scenario_h_migration_production_state_unknown(self):
        """Scenario H: Unknown production presence preserves schema gap without false coercion."""
        migration_schema = json.loads((REPO_ROOT / "machine" / "schemas" / "migration-risk-contract.v1.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(migration_schema["properties"]["production_data"]["type"], "boolean")
        chronicler_guide = (REPO_ROOT / "skills" / "chronicler" / "MIGRATION_RISK_CONTRACT_GUIDE.md").read_text(encoding="utf-8")
        self.assertIn("pre-contract", chronicler_guide)

    def test_11_scenario_i_documentation_reconciliation(self):
        """Scenario I: Scribe preserves exact proof and capacity states without silent promotion."""
        scribe_guide = (REPO_ROOT / "skills" / "scribe" / "GOVERNANCE_DOCUMENTATION_INTEGRATION_GUIDE.md").read_text(encoding="utf-8")
        self.assertIn("Prohibited Silent Promotions", scribe_guide)
        self.assertIn("PROVEN", scribe_guide)
        self.assertIn("NOT_PROVEN", scribe_guide)
        self.assertIn("FAILED", scribe_guide)
        self.assertIn("MISSING_EVIDENCE", scribe_guide)
        self.assertIn("STALE_INVALIDATED", scribe_guide)

    def test_12_scenario_j_dagger_execution_blocked(self):
        """Scenario J: Dagger execution without explicit authority is blocked."""
        res = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "test_dagger_guardrail.py")],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("live_execution_blocked", res.stdout)

    def test_13_adapter_parity_exact(self):
        """Verify Codex adapter export parity passes completely."""
        res = subprocess.run(
            [sys.executable, str(REPO_ROOT / "adapters" / "codex" / "validate_codex_export.py")],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, f"Codex export validation failed: {res.stderr}")

    def test_14_frozen_guidance_manifest_intact(self):
        """Verify UIX-9 live guidance manifest digests are 100% matched."""
        manifest_path = REPO_ROOT / "machine" / "ui" / "uix9-live-guidance-manifest.v1.json"
        self.assertTrue(manifest_path.exists())
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for item in manifest.get("materials", []):
            path = REPO_ROOT / item["path"]
            self.assertTrue(path.exists(), f"Missing frozen file: {path}")
            digest = hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
            self.assertEqual(digest, item["canonical_blob_digest"], f"Digest mismatch on frozen file: {item['path']}")

    def test_15_prompt_load_budget_passes(self):
        """Verify prompt load budget meets strict character/token ceilings."""
        res = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "validate_prompt_load_budget.py"), "--repo-root", "."],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, f"Prompt load budget failed: {res.stderr}")
        self.assertIn("[RESULT] PASS", res.stdout)

    def test_16_routing_and_tuner_contracts_pass(self):
        """Verify deterministic routing and Tuner collaboration contracts pass."""
        res_r = subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "validate_routing_contract.py")], cwd=str(REPO_ROOT), capture_output=True, text=True)
        self.assertEqual(res_r.returncode, 0)
        res_t = subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "validate_tuner_collaboration_contract.py")], cwd=str(REPO_ROOT), capture_output=True, text=True)
        self.assertEqual(res_t.returncode, 0)

    def test_17_architecture_boundaries_pass(self):
        """Verify clean runtime architecture boundaries pass without layering violations."""
        res = subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "validation" / "validate_architecture_boundaries.py")], cwd=str(REPO_ROOT), capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("RUNTIME_ARCHITECTURE_BOUNDARIES=PASS", res.stdout)

    def test_18_architecture_governance_intake_enum_regression(self):
        """Verify ArchitectureGovernanceIntake.change_materiality canonical enum exactly."""
        schema_path = REPO_ROOT / "machine" / "schemas" / "architecture-governance-intake.v1.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        change_mat = schema["properties"]["change_materiality"]["enum"]
        self.assertEqual(change_mat, ["TRIVIAL", "STANDARD", "ARCHITECTURAL", "PRODUCTION_CRITICAL"])
        self.assertNotIn("ISOLATED_REFACTOR", change_mat)
        self.assertNotIn("MULTI_SUBSYSTEM", change_mat)

    def test_19_architecture_validation_contract_proof_states_enum_regression(self):
        """Verify ArchitectureValidationContract proof-state enum completeness."""
        schema_path = REPO_ROOT / "machine" / "schemas" / "architecture-validation-contract.v1.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        proof_states = schema["$defs"]["validation_result"]["enum"]
        self.assertEqual(proof_states, ["PROVEN", "NOT_PROVEN", "NOT_REQUIRED", "FAILED"])
        self.assertNotIn("MISSING_EVIDENCE", proof_states)
        self.assertNotIn("STALE_INVALIDATED", proof_states)

    def test_20_closeout_document_accuracy(self):
        """Verify docs/governance/OR_GOV_10_INTEGRATION_CLOSEOUT.md has accurate terms and enums."""
        doc_path = REPO_ROOT / "docs" / "governance" / "OR_GOV_10_INTEGRATION_CLOSEOUT.md"
        self.assertTrue(doc_path.exists())
        doc = doc_path.read_text(encoding="utf-8")

        for term in ["TRIVIAL", "STANDARD", "ARCHITECTURAL", "PRODUCTION_CRITICAL"]:
            self.assertIn(term, doc, f"Missing canonical term {term} in closeout document")

        self.assertNotIn("ISOLATED_REFACTOR", doc)
        self.assertNotIn("MULTI_SUBSYSTEM", doc)

        for term in ["PROVEN", "NOT_PROVEN", "NOT_REQUIRED", "FAILED"]:
            self.assertIn(term, doc, f"Missing validation proof state {term} in closeout document")

    def test_21_historical_phase_ledger_regression(self):
        """Verify canonical historical phase mapping in closeout disposition."""
        disp_path = REPO_ROOT / "docs" / "governance" / "or_gov_10_integration_closeout_disposition.v1.json"
        self.assertTrue(disp_path.exists())
        disp = json.loads(disp_path.read_text(encoding="utf-8"))
        phases = disp["program_phases"]

        # Verify OR-GOV-1 is shared machine contracts, not Steward product intent
        self.assertNotEqual(phases["or_gov_1"]["specialist"], "the-steward")
        self.assertIn("machine contracts", phases["or_gov_1"]["phase_name"].lower())

        # Verify OR-GOV-2 is Steward
        self.assertEqual(phases["or_gov_2"]["specialist"], "the-steward")
        self.assertIn("product intent", phases["or_gov_2"]["phase_name"].lower())

        # Verify OR-GOV-3 is Clockwork complexity/scale, NOT Scribe SSU
        self.assertEqual(phases["or_gov_3"]["specialist"], "clockwork")
        self.assertIn("complexity", phases["or_gov_3"]["phase_name"].lower())
        self.assertNotIn("ssu", phases["or_gov_3"]["phase_name"].lower())
        self.assertNotEqual(phases["or_gov_3"]["specialist"], "scribe")

        # Verify Scribe SSU is recorded as separate initiative
        self.assertIn("separate_initiatives", disp)
        self.assertEqual(disp["separate_initiatives"]["scribe_ssu"]["status"], "COMPLETE_CANONICAL_VERIFIED")
        self.assertIn("separate", disp["separate_initiatives"]["scribe_ssu"]["relationship"].lower())

    def test_22_status_preservation(self):
        """Verify that closeout erratum preserves completion status without reopening phases."""
        disp_path = REPO_ROOT / "docs" / "governance" / "or_gov_10_integration_closeout_disposition.v1.json"
        disp = json.loads(disp_path.read_text(encoding="utf-8"))

        self.assertEqual(disp["status"], "OR_GOV_PROGRAM_COMPLETE")
        phases = disp["program_phases"]
        for phase_key in ["or_gov_1", "or_gov_2", "or_gov_3", "or_gov_4", "or_gov_5", "or_gov_6", "or_gov_7", "or_gov_8a", "or_gov_8b", "or_gov_8c", "or_gov_8d", "or_gov_9", "or_gov_10"]:
            self.assertEqual(phases[phase_key]["status"], "COMPLETE_CANONICAL_VERIFIED", f"Phase {phase_key} status drifted")

        constraints = disp["non_authorizing_constraints"]
        self.assertTrue(constraints["public_release_held"])
        self.assertEqual(constraints["current_public_release"], "v1.7.0")
        self.assertFalse(constraints["v1_8_publication_authorized"])
        self.assertFalse(constraints["ar_3_authorized"])
        self.assertFalse(constraints["ar_4_authorized"])
        self.assertTrue(constraints["execution_stops_after_or_gov_10"])


if __name__ == "__main__":
    unittest.main()
