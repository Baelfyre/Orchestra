from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / "docs" / "architecture" / "contracts" / "registry-o7-runtime-state.v1.json"
WORKFLOW = ROOT / ".github" / "workflows" / "registry-o7-joint-conformance.yml"
VALIDATOR = ROOT / "scripts" / "validate_registry_o7_joint_conformance.py"


class RegistryO7JointConformanceContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = json.loads(STATE.read_text(encoding="utf-8"))

    def test_trusted_release_identity_is_frozen(self) -> None:
        release = self.state["trusted_release"]
        self.assertEqual("registry-v0.4.0", release["release_tag"])
        self.assertEqual("0.4.0", release["registry_version"])
        self.assertEqual(4, release["release_sequence"])
        self.assertEqual("488c979b37dd84d8645fd8e6c288d297375c4e5b", release["source_commit_sha"])
        self.assertEqual("040d6576cf10e9f7e3a9a051792869541c1d33b7af3c665fad8eecb939c7baaa", release["release_manifest_sha256"])
        self.assertEqual("e0457a75837d169d7bb8a7da14d8f4141d35a691952ff8f8978ef793e3cf92d3", release["bundle_sha256"])
        self.assertTrue(release["immutable"])
        self.assertFalse(release["draft"])
        self.assertFalse(release["prerelease"])

    def test_registry_post_release_runtime_is_frozen(self) -> None:
        dependency = self.state["registry_dependency"]
        self.assertEqual("4926a3b5f48122dd45f3c8e83a12b8d071dd5387", dependency["canonical_commit_sha"])
        self.assertEqual("01be27bde90f6faa59ab74d60ba13af480c11b1d", dependency["canonical_tree_sha"])
        self.assertEqual("VERIFIED", dependency["signature"])
        self.assertEqual("PASS", dependency["canonical_validation"])

    def test_three_transport_gate_is_fail_closed_and_non_authorizing(self) -> None:
        conformance = self.state["joint_conformance"]
        self.assertEqual(
            ["DIRECT_LOCAL_JSON_QUERY", "DIRECT_LOCAL_INDEXED_GATEWAY", "OPTIONAL_MCP_TRANSPORT"],
            conformance["required_transports"],
        )
        self.assertTrue(conformance["same_release_identity_required"])
        self.assertTrue(conformance["semantic_parity_required"])
        self.assertTrue(conformance["exact_source_and_obligation_identity_required"])
        self.assertTrue(conformance["freshness_parity_required"])
        self.assertTrue(conformance["normalized_compliance_query_receipt_required"])
        self.assertFalse(conformance["authority_expansion_allowed"])
        self.assertTrue(conformance["canonicalization_requires_gate_pass"])
        self.assertFalse(self.state["authority_expansion"])
        self.assertFalse(self.state["release_boundary"]["orchestra_release_integration_authorized_by_this_state"])

    def test_mcp_is_optional_read_only_transport(self) -> None:
        self.assertIn("cap.transport.mcp.v1>=1.0.0", self.state["compatibility"]["r7_optional_capabilities"])
        self.assertTrue(self.state["transport"]["mcp_currently_available"])
        self.assertTrue(self.state["transport"]["mcp_read_only"])
        self.assertFalse(self.state["transport"]["registry_gateway_semantics_are_reimplemented_in_orchestra"])

    def test_benchmark_does_not_overclaim_efficiency(self) -> None:
        boundary = self.state["benchmark_boundary"]
        self.assertTrue(boundary["r7_9_complete"])
        self.assertFalse(boundary["projected_byte_benefit_established"])
        self.assertFalse(boundary["token_efficiency_established"])
        self.assertFalse(boundary["token_efficiency_claim_allowed"])

    def test_workflow_and_validator_bind_exact_cross_repo_identities(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        validator = VALIDATOR.read_text(encoding="utf-8")
        for token in (
            "4926a3b5f48122dd45f3c8e83a12b8d071dd5387",
            "01be27bde90f6faa59ab74d60ba13af480c11b1d",
            "registry-v0.4.0",
            "488c979b37dd84d8645fd8e6c288d297375c4e5b",
            "040d6576cf10e9f7e3a9a051792869541c1d33b7af3c665fad8eecb939c7baaa",
            "e0457a75837d169d7bb8a7da14d8f4141d35a691952ff8f8978ef793e3cf92d3",
        ):
            self.assertIn(token, workflow)
            self.assertIn(token, validator)
        self.assertIn("RegistryMcpAdapter", validator)
        self.assertIn("DIRECT_JSON", validator)
        self.assertIn("DIRECT_INDEXED", validator)
        self.assertIn("OPTIONAL_MCP", validator)
        self.assertIn("canonical_registry_json_remains_authority", validator)
        self.assertIn('workflow_stage="steward_requirements_traceability"', validator)

    def test_completed_state_cannot_precede_trusted_release(self) -> None:
        complete = self.state["release_boundary"]["joint_r7_o7_conformance_complete"]
        self.assertIsInstance(complete, bool)
        if complete:
            self.assertTrue(self.state["release_boundary"]["trusted_registry_v0_4_0_published"])
            self.assertTrue(self.state["release_boundary"]["trusted_registry_v0_4_0_immutable_verified"])
            self.assertTrue(self.state["release_boundary"]["r7_7_mcp_implemented"])
            self.assertTrue(self.state["release_boundary"]["r7_8_trusted_release_integration_implemented"])
            self.assertTrue(self.state["release_boundary"]["r7_9_benchmark_complete"])


if __name__ == "__main__":
    unittest.main()
