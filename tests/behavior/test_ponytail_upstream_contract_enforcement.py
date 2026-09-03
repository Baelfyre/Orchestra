"""
Behavioral tests for Ponytail Upstream-Contract Enforcement (OR-GOV-8C).
Validates Ponytail's deterministic upstream-contract consumption and implementation discipline:
  T1  - Upstream contract requirement gate
  T2  - Core operational tenets (Minimal Safe Solution, Caveman, zero invented facts, etc.)
  T3  - Steward upstream contract consumption (ProductIntentContract, CapacityEnvelope)
  T4  - Governor upstream contract consumption (GOVERNOR_DECISION_OR_NOT_APPLICABLE, legal/compliance)
  T5  - Clockwork upstream contract consumption (ArchitectureComplexityDecision, runtime zones)
  T6  - Chronicler upstream contract consumption (MigrationRiskContract, schema/DDL rules)
  T7  - Cipher upstream contract consumption (tenancy model, server-verified context, default-deny)
  T8  - Cloak upstream contract consumption (UI/UX specifications, design tokens, accessibility)
  T9  - Overseer upstream contract consumption (ArchitectureValidationContract, proof states, no Ponytail proof marking)
  T10 - Arbiter upstream contract consumption (transition dispositions, exact commit/tree binding, stop on STOP)
  T11 - The Tuner upstream contract consumption (cross-specialist coordination, invalidation halting)
  T12 - Strict implementation ownership (PROJECT_NATIVE_IMPLEMENTATION, diff hygiene)
  T13 - Disclaimed non-ownership boundaries (ARCHITECTURE, GOVERNANCE_REVIEW, RENDERED_EVIDENCE, etc.)
  T14 - Fail-closed protocol for contract gaps (missing contract, ambiguous spec, stale contract, scope creep)
  T15 - Diff hygiene and verification gates (git diff --check, PROJECT_NATIVE_IMPLEMENTATION_DELTA)
  T16 - Non-authorizing constraints (CODE_EXISTS != APPROVED_TO_MERGE, v1.8 publication hold)
  T17 - Byte-identical Codex parity mirror (UPSTREAM_CONTRACT_ENFORCEMENT_GUIDE.md)
  T18 - Byte-identical Codex parity mirror (OUTPUT_FORMATS.md)
  T19 - UIX-9 frozen SKILL.md preservation (digest match for skills/ponytail/SKILL.md)
  T20 - Specialist integration flow schema adherence (ownership, handoff_rules)
  T21 - Runtime architecture boundaries adherence
  T22 - UPSTREAM_REFERENCE provenance boundaries preserved
"""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

GUIDE_SOURCE = ROOT / "skills" / "ponytail" / "UPSTREAM_CONTRACT_ENFORCEMENT_GUIDE.md"
GUIDE_CODEX = ROOT / "adapters" / "codex" / "skills" / "ponytail" / "UPSTREAM_CONTRACT_ENFORCEMENT_GUIDE.md"
OUTPUT_FORMATS_SOURCE = ROOT / "skills" / "ponytail" / "OUTPUT_FORMATS.md"
OUTPUT_FORMATS_CODEX = ROOT / "adapters" / "codex" / "skills" / "ponytail" / "OUTPUT_FORMATS.md"
SKILL_MD = ROOT / "skills" / "ponytail" / "SKILL.md"
SKILL_MD_CODEX = ROOT / "adapters" / "codex" / "skills" / "ponytail" / "SKILL.md"
UPSTREAM_REF = ROOT / "skills" / "ponytail" / "UPSTREAM_REFERENCE.md"
UIX9_MANIFEST = ROOT / "machine" / "ui" / "uix9-live-guidance-manifest.v1.json"
SPECIALIST_FLOW = ROOT / "machine" / "ui" / "specialist-integration-flow.v1.json"
RUNTIME_BOUNDARIES = ROOT / "machine" / "governance" / "runtime-architecture-boundaries.v1.json"


def _guide_text():
    assert GUIDE_SOURCE.exists(), "skills/ponytail/UPSTREAM_CONTRACT_ENFORCEMENT_GUIDE.md must exist"
    return GUIDE_SOURCE.read_text(encoding="utf-8")


# ===== T1: Upstream contract requirement gate =====
def test_t1_upstream_contract_requirement_gate():
    text = _guide_text()
    assert "IMPLEMENTATION_REQUIRES_UPSTREAM_CONTRACTS = TRUE" in text
    assert "PLATFORM_CAN_EXECUTE != GOVERNANCE_READY_TO_IMPLEMENT" in text
    assert "CODE_EXISTS != APPROVED_TO_MERGE" in text
    assert "TESTS_PASS != GOVERNANCE_READY" in text


# ===== T2: Core operational tenets =====
def test_t2_core_operational_tenets():
    text = _guide_text()
    assert "Minimal Safe Solution (Caveman Filter)" in text
    assert "Zero Invented Facts" in text
    assert "Reversibility and Modularity" in text
    assert "Native-First and Dependency Discipline" in text
    assert "Tracked Source of Truth" in text


# ===== T3: Steward upstream contract consumption =====
def test_t3_steward_contract_consumption():
    text = _guide_text()
    assert "ProductIntentContract" in text
    assert "CapacityEnvelope" in text
    assert "bounded product intent" in text or "speculative features" in text


# ===== T4: Governor upstream contract consumption =====
def test_t4_governor_contract_consumption():
    text = _guide_text()
    assert "GOVERNOR_DECISION_OR_NOT_APPLICABLE" in text
    assert "license boundaries" in text
    assert "third-party provenance" in text


# ===== T5: Clockwork upstream contract consumption =====
def test_t5_clockwork_contract_consumption():
    text = _guide_text()
    assert "ArchitectureComplexityDecision" in text
    assert "runtime-architecture-boundaries.v1.json" in text
    assert "declared architectural zones" in text


# ===== T6: Chronicler upstream contract consumption =====
def test_t6_chronicler_contract_consumption():
    text = _guide_text()
    assert "MigrationRiskContract" in text
    assert "unauthorized DDL" in text or "unbatched backfills" in text
    assert "destructive schema mutations" in text


# ===== T7: Cipher upstream contract consumption =====
def test_t7_cipher_contract_consumption():
    text = _guide_text()
    assert "tenancy_model" in text
    assert "TENANT_SECURITY_GOVERNANCE_GUIDE.md" in text
    assert "server-verified tenant context" in text
    assert "default-deny across tenant boundaries" in text


# ===== T8: Cloak upstream contract consumption =====
def test_t8_cloak_contract_consumption():
    text = _guide_text()
    assert "Cloak" in text
    assert "design tokens" in text or "accessibility" in text or "CUIR corpus rules" in text
    assert "project-native UI" in text


# ===== T9: Overseer upstream contract consumption =====
def test_t9_overseer_contract_consumption():
    text = _guide_text()
    assert "ArchitectureValidationContract" in text
    assert "Ponytail never declares proof states" in text or "release readiness" in text


# ===== T10: Arbiter upstream contract consumption =====
def test_t10_arbiter_contract_consumption():
    text = _guide_text()
    assert "Arbiter" in text
    assert "transition dispositions" in text or "execution envelopes" in text
    assert "STOP" in text
    assert "ESCALATE_HUMAN" in text


# ===== T11: The Tuner upstream contract consumption =====
def test_t11_tuner_contract_consumption():
    text = _guide_text()
    assert "The Tuner" in text
    assert "invalidation" in text
    assert "re-entry" in text


# ===== T12: Strict implementation ownership =====
def test_t12_implementation_ownership():
    text = _guide_text()
    assert "PROJECT_NATIVE_IMPLEMENTATION" in text
    assert "syntax-correct" in text
    assert "Focused regression testing" in text
    assert "Diff hygiene" in text


# ===== T13: Disclaimed non-ownership boundaries =====
def test_t13_disclaimed_non_ownership():
    text = _guide_text()
    assert "DESIGN_UX_REQUIREMENTS" in text
    assert "ARCHITECTURE" in text
    assert "GOVERNANCE_REVIEW" in text
    assert "RENDERED_EVIDENCE" in text
    assert "TRANSITION_DISPOSITION" in text
    assert "PERSISTENCE_DESIGN" in text
    assert "SECURITY_POLICY" in text


# ===== T14: Fail-closed protocol for contract gaps =====
def test_t14_fail_closed_protocol():
    text = _guide_text()
    assert "Fail-Closed Protocol for Contract Gaps" in text
    assert "Missing Contract" in text
    assert "Ambiguous Specification" in text
    assert "Stale Evidence or Contract" in text
    assert "Scope Creep Request" in text


# ===== T15: Diff hygiene and verification gates =====
def test_t15_diff_hygiene_and_verification():
    text = _guide_text()
    assert "git diff --check" in text
    assert "zero committed secrets" in text or "whitespace errors" in text
    assert "PROJECT_NATIVE_IMPLEMENTATION_DELTA" in text


# ===== T16: Non-authorizing constraints =====
def test_t16_non_authorizing_constraints():
    text = _guide_text()
    assert "Non-Authorizing Constraints" in text
    assert "v1.8 publication hold" in text
    assert "v1.7.0" in text


# ===== T17: Byte-identical Codex parity mirror (guide) =====
def test_t17_codex_parity_mirror_guide():
    assert GUIDE_SOURCE.exists(), "skills/ponytail/UPSTREAM_CONTRACT_ENFORCEMENT_GUIDE.md must exist"
    assert GUIDE_CODEX.exists(), "adapters/codex/skills/ponytail/UPSTREAM_CONTRACT_ENFORCEMENT_GUIDE.md must exist"
    source_bytes = GUIDE_SOURCE.read_bytes().replace(b"\r\n", b"\n")
    codex_bytes = GUIDE_CODEX.read_bytes().replace(b"\r\n", b"\n")
    assert source_bytes == codex_bytes, "Ponytail guide must be byte-identical between skills/ and adapters/"


# ===== T18: Byte-identical Codex parity mirror (OUTPUT_FORMATS.md) =====
def test_t18_codex_parity_mirror_output_formats():
    assert OUTPUT_FORMATS_SOURCE.exists(), "skills/ponytail/OUTPUT_FORMATS.md must exist"
    assert OUTPUT_FORMATS_CODEX.exists(), "adapters/codex/skills/ponytail/OUTPUT_FORMATS.md must exist"
    source_bytes = OUTPUT_FORMATS_SOURCE.read_bytes().replace(b"\r\n", b"\n")
    codex_bytes = OUTPUT_FORMATS_CODEX.read_bytes().replace(b"\r\n", b"\n")
    assert source_bytes == codex_bytes, "OUTPUT_FORMATS.md must be byte-identical between skills/ and adapters/"
    assert "UPSTREAM_CONTRACT_COMPLIANCE" in OUTPUT_FORMATS_SOURCE.read_text(encoding="utf-8")


# ===== T19: UIX-9 frozen SKILL.md preservation =====
def test_t19_uix9_frozen_skill_md_preservation():
    manifest_data = json.loads(UIX9_MANIFEST.read_text(encoding="utf-8"))
    ponytail_entries = [
        entry for entry in manifest_data.get("materials", [])
        if entry.get("path") == "skills/ponytail/SKILL.md"
    ]
    assert len(ponytail_entries) == 1, "skills/ponytail/SKILL.md must be registered in uix9 manifest"
    expected_digest = ponytail_entries[0]["canonical_blob_digest"]
    skill_content = SKILL_MD.read_bytes().replace(b"\r\n", b"\n")
    actual_digest = hashlib.sha256(skill_content).hexdigest()
    assert actual_digest == expected_digest, (
        f"skills/ponytail/SKILL.md was modified! Expected digest {expected_digest} but found {actual_digest}"
    )


# ===== T20: Specialist integration flow schema adherence =====
def test_t20_specialist_integration_flow_adherence():
    flow = json.loads(SPECIALIST_FLOW.read_text(encoding="utf-8"))
    ponytail_ownership = flow.get("ownership", {}).get("ponytail", {})
    assert "PROJECT_NATIVE_IMPLEMENTATION" in ponytail_ownership.get("owns", [])
    assert "ARCHITECTURE" in ponytail_ownership.get("does_not_own", [])
    assert "DESIGN_UX_REQUIREMENTS" in ponytail_ownership.get("does_not_own", [])
    assert "GOVERNANCE_REVIEW" in ponytail_ownership.get("does_not_own", [])
    assert "RENDERED_EVIDENCE" in ponytail_ownership.get("does_not_own", [])
    assert "TRANSITION_DISPOSITION" in ponytail_ownership.get("does_not_own", [])

    # Check handoff requires upstream contracts
    gov_to_ponytail = [
        r for r in flow.get("handoff_rules", [])
        if r.get("from") == "the-governor" and r.get("to") == "ponytail"
    ]
    assert len(gov_to_ponytail) == 1
    assert "FROZEN_UPSTREAM_CONTRACTS" in gov_to_ponytail[0].get("requires", [])


# ===== T21: Runtime architecture boundaries adherence =====
def test_t21_runtime_architecture_boundaries_adherence():
    assert RUNTIME_BOUNDARIES.exists(), "runtime-architecture-boundaries.v1.json must exist"
    bounds = json.loads(RUNTIME_BOUNDARIES.read_text(encoding="utf-8"))
    assert "repository_zones" in bounds
    text = _guide_text()
    assert "machine/governance/runtime-architecture-boundaries.v1.json" in text


# ===== T22: UPSTREAM_REFERENCE provenance boundaries preserved =====
def test_t22_upstream_reference_preserved():
    assert UPSTREAM_REF.exists(), "skills/ponytail/UPSTREAM_REFERENCE.md must exist"
    text = UPSTREAM_REF.read_text(encoding="utf-8")
    assert "DietrichGebert/ponytail" in text
    assert "Baelfyre/ponytail" in text
    assert "specialist ownership boundaries" in text


ALL_TESTS = [
    ("T1: Upstream contract requirement gate", test_t1_upstream_contract_requirement_gate),
    ("T2: Core operational tenets", test_t2_core_operational_tenets),
    ("T3: Steward upstream contract consumption", test_t3_steward_contract_consumption),
    ("T4: Governor upstream contract consumption", test_t4_governor_contract_consumption),
    ("T5: Clockwork upstream contract consumption", test_t5_clockwork_contract_consumption),
    ("T6: Chronicler upstream contract consumption", test_t6_chronicler_contract_consumption),
    ("T7: Cipher upstream contract consumption", test_t7_cipher_contract_consumption),
    ("T8: Cloak upstream contract consumption", test_t8_cloak_contract_consumption),
    ("T9: Overseer upstream contract consumption", test_t9_overseer_contract_consumption),
    ("T10: Arbiter upstream contract consumption", test_t10_arbiter_contract_consumption),
    ("T11: The Tuner upstream contract consumption", test_t11_tuner_contract_consumption),
    ("T12: Strict implementation ownership", test_t12_implementation_ownership),
    ("T13: Disclaimed non-ownership boundaries", test_t13_disclaimed_non_ownership),
    ("T14: Fail-closed protocol for contract gaps", test_t14_fail_closed_protocol),
    ("T15: Diff hygiene and verification gates", test_t15_diff_hygiene_and_verification),
    ("T16: Non-authorizing constraints", test_t16_non_authorizing_constraints),
    ("T17: Byte-identical Codex parity mirror (guide)", test_t17_codex_parity_mirror_guide),
    ("T18: Byte-identical Codex parity mirror (OUTPUT_FORMATS.md)", test_t18_codex_parity_mirror_output_formats),
    ("T19: UIX-9 frozen SKILL.md preservation", test_t19_uix9_frozen_skill_md_preservation),
    ("T20: Specialist integration flow schema adherence", test_t20_specialist_integration_flow_adherence),
    ("T21: Runtime architecture boundaries adherence", test_t21_runtime_architecture_boundaries_adherence),
    ("T22: UPSTREAM_REFERENCE provenance boundaries preserved", test_t22_upstream_reference_preserved),
]


def run_all():
    passed = 0
    failed = 0
    print(f"Running {len(ALL_TESTS)} Ponytail Upstream-Contract Enforcement behavioral tests...")
    for name, test_fn in ALL_TESTS:
        try:
            test_fn()
            print(f"  [PASS] {name}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
            failed += 1
    print(f"\nResults: {passed} passed, {failed} failed out of {len(ALL_TESTS)} tests.")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_all())
