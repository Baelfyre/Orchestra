"""
Behavioral tests for Scribe Post-SSU Governance Documentation Integration (OR-GOV-8D).
Validates Scribe's deterministic post-SSU governance documentation discipline:
  T1  - Governance documentation requirement gate
  T2  - Core governance documentation tenets (Evidence-Bound, Zero Invented Facts, Non-Coercion, etc.)
  T3  - SSU operating mode integration (SPEC_TO_SYSTEM, SYSTEM_TO_DOCS, RECONCILE)
  T4  - Steward specialist contract documentation (ProductIntentContract, CapacityEnvelope)
  T5  - Governor specialist contract documentation (compliance decisions, license obligations)
  T6  - Clockwork specialist contract documentation (ArchitectureComplexityDecision, runtime zones, ADRs)
  T7  - Chronicler specialist contract documentation (MigrationRiskContract, unknown-production gap preserved)
  T8  - Cipher specialist contract documentation (tenancy model, authorization chains, default-deny)
  T9  - Cloak specialist contract documentation (UI/UX specs, design tokens, CUIR rules)
  T10 - Overseer specialist contract documentation (ArchitectureValidationContract, proof states documented not evaluated)
  T11 - Arbiter specialist contract documentation (transition dispositions, exact commit/tree binding)
  T12 - The Tuner specialist contract documentation (cross-specialist coordination, contradiction detection)
  T13 - Governance lifecycle state model (PROPOSED -> APPROVED -> PLANNED -> IMPLEMENTED -> VALIDATED)
  T14 - Prohibited silent promotions (PROPOSED to APPROVED, IMPLEMENTED to VALIDATED, etc.)
  T15 - Anomaly and drift states (DOC_DRIFT, IMPLEMENTATION_DRIFT, MISSING_EVIDENCE, etc.)
  T16 - Changelog and ADR maintenance protocol (exact lineage binding, immutable history)
  T17 - Non-authorizing constraints (v1.8 publication hold, v1.7.0 public release, Run A conclusion)
  T18 - Byte-identical Codex parity mirror (GOVERNANCE_DOCUMENTATION_INTEGRATION_GUIDE.md)
  T19 - Byte-identical Codex parity mirror (OUTPUT_FORMATS.md)
  T20 - Progressive disclosure integration in SKILL.md
  T21 - Specialist boundary and non-ownership adherence
  T22 - SSU foundation preservation (SSU guides and project documentation preserved)
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

GUIDE_SOURCE = ROOT / "skills" / "scribe" / "GOVERNANCE_DOCUMENTATION_INTEGRATION_GUIDE.md"
GUIDE_CODEX = ROOT / "adapters" / "codex" / "skills" / "scribe" / "GOVERNANCE_DOCUMENTATION_INTEGRATION_GUIDE.md"
OUTPUT_FORMATS_SOURCE = ROOT / "skills" / "scribe" / "OUTPUT_FORMATS.md"
OUTPUT_FORMATS_CODEX = ROOT / "adapters" / "codex" / "skills" / "scribe" / "OUTPUT_FORMATS.md"
SKILL_MD = ROOT / "skills" / "scribe" / "SKILL.md"
SKILL_MD_CODEX = ROOT / "adapters" / "codex" / "skills" / "scribe" / "SKILL.md"
SSU_PROJECT_DOC = ROOT / "docs" / "project" / "SCRIBE_SPECIALIST_UPGRADE_SSU.md"
DOMAIN_GUIDE = ROOT / "skills" / "scribe" / "DOMAIN_NARRATIVE_MODELING_GUIDE.md"
REQ_GUIDE = ROOT / "skills" / "scribe" / "REQUIREMENTS_TRACEABILITY_GUIDE.md"
CAPSTONE_GUIDE = ROOT / "skills" / "scribe" / "RESEARCH_CAPSTONE_DOCUMENTATION_GUIDE.md"
RECONCILE_GUIDE = ROOT / "skills" / "scribe" / "DOCUMENTATION_SYSTEM_RECONCILIATION_GUIDE.md"


def _guide_text():
    assert GUIDE_SOURCE.exists(), "skills/scribe/GOVERNANCE_DOCUMENTATION_INTEGRATION_GUIDE.md must exist"
    return GUIDE_SOURCE.read_text(encoding="utf-8")


# ===== T1: Governance documentation requirement gate =====
def test_t1_governance_documentation_gate():
    text = _guide_text()
    assert "DOCUMENTATION_REQUIRES_VERIFIED_EVIDENCE = TRUE" in text
    assert "DOCS_EXIST != GOVERNANCE_APPROVED" in text
    assert "EVIDENCE_CLAIMED != EVIDENCE_VERIFIED" in text
    assert "PUBLIC_RELEASE_HELD = TRUE (v1.7.0)" in text


# ===== T2: Core governance documentation tenets =====
def test_t2_core_governance_documentation_tenets():
    text = _guide_text()
    assert "Evidence-Bound Representation" in text
    assert "Zero Invented Facts" in text
    assert "Non-Coercion of Unknown States" in text
    assert "Bidirectional Traceability" in text
    assert "Tracked Source of Truth" in text


# ===== T3: SSU operating mode integration =====
def test_t3_ssu_operating_mode_integration():
    text = _guide_text()
    assert "SPEC_TO_SYSTEM" in text
    assert "SYSTEM_TO_DOCS" in text
    assert "RECONCILE" in text
    assert "DOC_DRIFT" in text
    assert "IMPLEMENTATION_DRIFT" in text


# ===== T4: Steward specialist contract documentation =====
def test_t4_steward_contract_documentation():
    text = _guide_text()
    assert "ProductIntentContract" in text
    assert "CapacityEnvelope" in text
    assert "The Steward" in text


# ===== T5: Governor specialist contract documentation =====
def test_t5_governor_contract_documentation():
    text = _guide_text()
    assert "The Governor" in text
    assert "compliance decisions" in text or "license obligations" in text


# ===== T6: Clockwork specialist contract documentation =====
def test_t6_clockwork_contract_documentation():
    text = _guide_text()
    assert "ArchitectureComplexityDecision" in text
    assert "Clockwork" in text
    assert "architectural zones" in text or "ADRs" in text


# ===== T7: Chronicler specialist contract documentation =====
def test_t7_chronicler_contract_documentation():
    text = _guide_text()
    assert "MigrationRiskContract" in text
    assert "Chronicler" in text
    assert "unknown-production" in text or "rollback" in text


# ===== T8: Cipher specialist contract documentation =====
def test_t8_cipher_contract_documentation():
    text = _guide_text()
    assert "Cipher" in text
    assert "tenancy_model" in text
    assert "default-deny" in text


# ===== T9: Cloak specialist contract documentation =====
def test_t9_cloak_contract_documentation():
    text = _guide_text()
    assert "Cloak" in text
    assert "design tokens" in text or "accessibility" in text or "CUIR" in text


# ===== T10: Overseer specialist contract documentation =====
def test_t10_overseer_contract_documentation():
    text = _guide_text()
    assert "Overseer" in text
    assert "ArchitectureValidationContract" in text
    assert "PROVEN" in text
    assert "NOT_PROVEN" in text


# ===== T11: Arbiter specialist contract documentation =====
def test_t11_arbiter_contract_documentation():
    text = _guide_text()
    assert "Arbiter" in text
    assert "transition evaluations" in text or "execution envelopes" in text or "freshness" in text


# ===== T12: The Tuner specialist contract documentation =====
def test_t12_tuner_contract_documentation():
    text = _guide_text()
    assert "The Tuner" in text
    assert "invalidation" in text


# ===== T13: Governance lifecycle state model =====
def test_t13_governance_lifecycle_state_model():
    text = _guide_text()
    assert "PROPOSED" in text
    assert "APPROVED" in text
    assert "PLANNED" in text
    assert "IMPLEMENTED" in text
    assert "VALIDATED" in text


# ===== T14: Prohibited silent promotions =====
def test_t14_prohibited_silent_promotions():
    text = _guide_text()
    assert "Prohibited Silent Promotions" in text
    assert "PROPOSED` to `APPROVED" in text or "PROPOSED to APPROVED" in text
    assert "PLANNED` to `IMPLEMENTED" in text or "PLANNED to IMPLEMENTED" in text
    assert "IMPLEMENTED` to `VALIDATED" in text or "IMPLEMENTED to VALIDATED" in text


# ===== T15: Anomaly and drift states =====
def test_t15_anomaly_and_drift_states():
    text = _guide_text()
    assert "DOC_DRIFT" in text
    assert "IMPLEMENTATION_DRIFT" in text
    assert "MISSING_EVIDENCE" in text
    assert "STALE_INVALIDATED" in text
    assert "UNRESOLVED" in text


# ===== T16: Changelog and ADR maintenance protocol =====
def test_t16_changelog_and_adr_maintenance():
    text = _guide_text()
    assert "CHANGELOG.md" in text
    assert "Exact-Lineage Binding" in text or "Lineage" in text
    assert "SUPERSEDED" in text


# ===== T17: Non-authorizing constraints =====
def test_t17_non_authorizing_constraints():
    text = _guide_text()
    assert "Non-Authorizing Constraints" in text
    assert "v1.8 publication hold" in text
    assert "v1.7.0" in text
    assert "OR-GOV-8D" in text


# ===== T18: Byte-identical Codex parity mirror (guide) =====
def test_t18_codex_parity_mirror_guide():
    assert GUIDE_SOURCE.exists(), "skills/scribe/GOVERNANCE_DOCUMENTATION_INTEGRATION_GUIDE.md must exist"
    assert GUIDE_CODEX.exists(), "adapters/codex/skills/scribe/GOVERNANCE_DOCUMENTATION_INTEGRATION_GUIDE.md must exist"
    source_bytes = GUIDE_SOURCE.read_bytes().replace(b"\r\n", b"\n")
    codex_bytes = GUIDE_CODEX.read_bytes().replace(b"\r\n", b"\n")
    assert source_bytes == codex_bytes, "Scribe guide must be byte-identical between skills/ and adapters/"


# ===== T19: Byte-identical Codex parity mirror (OUTPUT_FORMATS.md) =====
def test_t19_codex_parity_mirror_output_formats():
    assert OUTPUT_FORMATS_SOURCE.exists(), "skills/scribe/OUTPUT_FORMATS.md must exist"
    assert OUTPUT_FORMATS_CODEX.exists(), "adapters/codex/skills/scribe/OUTPUT_FORMATS.md must exist"
    source_bytes = OUTPUT_FORMATS_SOURCE.read_bytes().replace(b"\r\n", b"\n")
    codex_bytes = OUTPUT_FORMATS_CODEX.read_bytes().replace(b"\r\n", b"\n")
    assert source_bytes == codex_bytes, "OUTPUT_FORMATS.md must be byte-identical between skills/ and adapters/"
    assert "GOVERNANCE_DOCUMENTATION_RECONCILIATION" in OUTPUT_FORMATS_SOURCE.read_text(encoding="utf-8")


# ===== T20: Progressive disclosure integration in SKILL.md =====
def test_t20_progressive_disclosure_integration():
    skill_text = SKILL_MD.read_text(encoding="utf-8")
    assert "GOVERNANCE_DOCUMENTATION_INTEGRATION_GUIDE.md" in skill_text
    codex_skill_text = SKILL_MD_CODEX.read_text(encoding="utf-8")
    assert "GOVERNANCE_DOCUMENTATION_INTEGRATION_GUIDE.md" in codex_skill_text


# ===== T21: Specialist boundary and non-ownership adherence =====
def test_t21_specialist_boundary_adherence():
    skill_text = SKILL_MD.read_text(encoding="utf-8")
    assert "Scribe does not own" in skill_text or "avoid_when" in skill_text
    assert "architecture" in skill_text.lower()
    assert "persistence" in skill_text.lower() or "database" in skill_text.lower()
    assert "security" in skill_text.lower()


# ===== T22: SSU foundation preservation =====
def test_t22_ssu_foundation_preservation():
    assert SSU_PROJECT_DOC.exists(), "SCRIBE_SPECIALIST_UPGRADE_SSU.md must exist"
    assert DOMAIN_GUIDE.exists(), "DOMAIN_NARRATIVE_MODELING_GUIDE.md must exist"
    assert REQ_GUIDE.exists(), "REQUIREMENTS_TRACEABILITY_GUIDE.md must exist"
    assert CAPSTONE_GUIDE.exists(), "RESEARCH_CAPSTONE_DOCUMENTATION_GUIDE.md must exist"
    assert RECONCILE_GUIDE.exists(), "DOCUMENTATION_SYSTEM_RECONCILIATION_GUIDE.md must exist"


ALL_TESTS = [
    ("T1: Governance documentation gate", test_t1_governance_documentation_gate),
    ("T2: Core governance documentation tenets", test_t2_core_governance_documentation_tenets),
    ("T3: SSU operating mode integration", test_t3_ssu_operating_mode_integration),
    ("T4: Steward specialist contract documentation", test_t4_steward_contract_documentation),
    ("T5: Governor specialist contract documentation", test_t5_governor_contract_documentation),
    ("T6: Clockwork specialist contract documentation", test_t6_clockwork_contract_documentation),
    ("T7: Chronicler specialist contract documentation", test_t7_chronicler_contract_documentation),
    ("T8: Cipher specialist contract documentation", test_t8_cipher_contract_documentation),
    ("T9: Cloak specialist contract documentation", test_t9_cloak_contract_documentation),
    ("T10: Overseer specialist contract documentation", test_t10_overseer_contract_documentation),
    ("T11: Arbiter specialist contract documentation", test_t11_arbiter_contract_documentation),
    ("T12: The Tuner specialist contract documentation", test_t12_tuner_contract_documentation),
    ("T13: Governance lifecycle state model", test_t13_governance_lifecycle_state_model),
    ("T14: Prohibited silent promotions", test_t14_prohibited_silent_promotions),
    ("T15: Anomaly and drift states", test_t15_anomaly_and_drift_states),
    ("T16: Changelog and ADR maintenance protocol", test_t16_changelog_and_adr_maintenance),
    ("T17: Non-authorizing constraints", test_t17_non_authorizing_constraints),
    ("T18: Byte-identical Codex parity mirror (guide)", test_t18_codex_parity_mirror_guide),
    ("T19: Byte-identical Codex parity mirror (OUTPUT_FORMATS.md)", test_t19_codex_parity_mirror_output_formats),
    ("T20: Progressive disclosure integration in SKILL.md", test_t20_progressive_disclosure_integration),
    ("T21: Specialist boundary and non-ownership adherence", test_t21_specialist_boundary_adherence),
    ("T22: SSU foundation preservation", test_t22_ssu_foundation_preservation),
]


def run_all():
    passed = 0
    failed = 0
    print(f"Running {len(ALL_TESTS)} Scribe Governance Documentation Integration behavioral tests...")
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
