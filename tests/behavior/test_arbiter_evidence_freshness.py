#!/usr/bin/env python3
"""
Deterministic behavioral tests for Arbiter Contract and Evidence Freshness (or-gov-8b).

  T1  - Evidence freshness taxonomy defined (FRESH_BOUND_VALID, STALE_INVALIDATED, MISSING_EVIDENCE, CONTRADICTORY_EVIDENCE)
  T2  - Six-tier transition precedence hierarchy strictly ordered
  T3  - STOP disposition criteria (unsafe, destructive, protected actions, secret exposure)
  T40 - ESCALATE_HUMAN disposition criteria (intent missing, scope drift, policy dilemma, publication hold)
  T5  - WAIT_FOR_CAPACITY disposition criteria (valid checkpoint, clean handoff identity)
  T6  - WAIT_FOR_EVIDENCE disposition criteria (stale, missing, or contradictory evidence)
  T7  - AUTO_REMEDIATE_AND_REVALIDATE criteria (deterministic defect, max 3 attempts, max 2 identical failures)
  T8  - AUTO_CONTINUE disposition criteria (strictly FRESH_BOUND_VALID, no blockers, next_eligible_unit)
  T9  - Exact commit and tree lineage binding: (CANONICAL_BASELINE, HEAD_COMMIT, WORKING_TREE)
  T10 - Head commit change invalidation rule
  T11 - Working-tree modification invalidation rule (untracked/staged files)
  T12 - Cached evidence constraints (same commit/tree, no cross-commit caching)
  T13 - Cross-specialist coordination and The Tuner collaboration (CROSS_LAYER_CONTRACT_STALE, REENTRY)
  T14 - Overseer handoff and boundary discipline (Overseer owns proof states; Arbiter owns transition)
  T15 - UIXx transition boundary (fresh revision-bound UI evidence required)
  T16 - Compliance registry evidence freshness (repository, version, sequence, digest, obligations)
  T17 - Adversarial cases evaluation (stale base, changed head, omitted untracked files, release claims)
  T18 - Fail-closed posture (API success alone is not verified state; content != identity)
  T19 - Authority boundaries and non-authorizing constraints (evidence never expands authority; v1.8 hold)
  T20 - Byte-identical Codex parity mirror for CONTINUITY_EVALUATION_GUIDE.md
  T21 - UIX-9 frozen SKILL.md preservation (digest match for skills/arbiter/SKILL.md)
  T22 - Specialist integration flow schema adherence (TRANSITION_DISPOSITION, EVIDENCE_FRESHNESS)
"""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

GUIDE_SOURCE = ROOT / "skills" / "arbiter" / "CONTINUITY_EVALUATION_GUIDE.md"
GUIDE_CODEX = ROOT / "adapters" / "codex" / "skills" / "arbiter" / "CONTINUITY_EVALUATION_GUIDE.md"
SKILL_MD = ROOT / "skills" / "arbiter" / "SKILL.md"
SKILL_MD_CODEX = ROOT / "adapters" / "codex" / "skills" / "arbiter" / "SKILL.md"
UIX9_MANIFEST = ROOT / "machine" / "ui" / "uix9-live-guidance-manifest.v1.json"
SPECIALIST_FLOW = ROOT / "machine" / "ui" / "specialist-integration-flow.v1.json"


def _guide_text():
    return GUIDE_SOURCE.read_text(encoding="utf-8")


def _skill_text():
    return SKILL_MD.read_text(encoding="utf-8")


# ===== T1: Evidence freshness taxonomy =====
def test_t1_evidence_freshness_taxonomy():
    text = _guide_text()
    for state in ["FRESH_BOUND_VALID", "STALE_INVALIDATED", "MISSING_EVIDENCE", "CONTRADICTORY_EVIDENCE"]:
        assert state in text, f"Expected freshness state {state} in CONTINUITY_EVALUATION_GUIDE.md"


# ===== T2: Six-tier transition precedence hierarchy =====
def test_t2_transition_precedence_hierarchy():
    text = _guide_text()
    dispositions = [
        "1. `STOP`",
        "2. `ESCALATE_HUMAN`",
        "3. `WAIT_FOR_CAPACITY`",
        "4. `WAIT_FOR_EVIDENCE`",
        "5. `AUTO_REMEDIATE_AND_REVALIDATE`",
        "6. `AUTO_CONTINUE`",
    ]
    last_idx = -1
    for disp in dispositions:
        idx = text.find(disp)
        assert idx != -1, f"Expected disposition {disp} in precedence section"
        assert idx > last_idx, f"Disposition {disp} not in strict precedence order"
        last_idx = idx


# ===== T3: STOP disposition criteria =====
def test_t3_stop_criteria():
    text = _guide_text()
    stop_section = text[text.find("1. `STOP`"):text.find("2. `ESCALATE_HUMAN`")]
    assert "Unsafe" in stop_section or "destructive" in stop_section
    assert "Secret" in stop_section or "credential" in stop_section or "token" in stop_section
    assert "protected" in stop_section


# ===== T4: ESCALATE_HUMAN disposition criteria =====
def test_t4_escalate_human_criteria():
    text = _guide_text()
    esc_section = text[text.find("2. `ESCALATE_HUMAN`"):text.find("3. `WAIT_FOR_CAPACITY`")]
    assert "Missing human intent" in esc_section or "ambiguous" in esc_section
    assert "legal" in esc_section or "compliance" in esc_section or "privacy" in esc_section
    assert "Mandatory human approval" in esc_section or "publication" in esc_section


# ===== T5: WAIT_FOR_CAPACITY disposition criteria =====
def test_t5_wait_for_capacity_criteria():
    text = _guide_text()
    cap_section = text[text.find("3. `WAIT_FOR_CAPACITY`"):text.find("4. `WAIT_FOR_EVIDENCE`")]
    assert "checkpoint" in cap_section
    assert "Resumable" in cap_section or "budget" in cap_section or "limits" in cap_section


# ===== T6: WAIT_FOR_EVIDENCE disposition criteria =====
def test_t6_wait_for_evidence_criteria():
    text = _guide_text()
    ev_section = text[text.find("4. `WAIT_FOR_EVIDENCE`"):text.find("5. `AUTO_REMEDIATE_AND_REVALIDATE`")]
    assert "STALE_INVALIDATED" in ev_section
    assert "MISSING_EVIDENCE" in ev_section
    assert "CONTRADICTORY_EVIDENCE" in ev_section


# ===== T7: AUTO_REMEDIATE_AND_REVALIDATE criteria =====
def test_t7_auto_remediate_criteria():
    text = _guide_text()
    rem_section = text[text.find("5. `AUTO_REMEDIATE_AND_REVALIDATE`"):text.find("6. `AUTO_CONTINUE`")]
    assert "Deterministic" in rem_section or "in-scope" in rem_section
    assert "maximum 3 attempts" in rem_section or "budget" in rem_section
    assert "maximum 2 identical failures" in rem_section


# ===== T8: AUTO_CONTINUE criteria =====
def test_t8_auto_continue_criteria():
    text = _guide_text()
    cont_section = text[text.find("6. `AUTO_CONTINUE`"):text.find("## Exact Commit")]
    assert "FRESH_BOUND_VALID" in cont_section
    assert "next_eligible_unit" in cont_section


# ===== T9: Exact commit and tree lineage binding =====
def test_t9_exact_commit_and_tree_binding():
    text = _guide_text()
    assert "PLATFORM_CAN_EXECUTE != GOVERNANCE_READY_TO_TRANSITION" in text
    assert "CANONICAL_BASELINE_SHA" in text
    assert "HEAD_COMMIT_SHA" in text
    assert "WORKING_TREE_SHA" in text


# ===== T10: Head commit change invalidation rule =====
def test_t10_head_commit_invalidation():
    text = _guide_text()
    assert "Head commit SHA, tree hash, or parent lineage changed" in text
    assert "changed head after validation" in text


# ===== T11: Workingmtree modification invalidation rule =====
def test_t11_working_tree_invalidation():
    text = _guide_text()
    assert "staged or untracked" in text.lower()
    assert "working-tree fingerprint" in text


# ===== T12: Cached evidence constraints =====
def test_t12_cached_evidence_constraints():
    text = _guide_text()
    assert "STRICTLY FORBIDDEN across" in text
    assert "Git commit boundaries" in text
    assert "Branch switches or rebases" in text
    assert "Environment transitions" in text


# ===== T13: Cross-specialist coordination and The Tuner collaboration =====
def test_t13_cross_specialist_coordination():
    text = _guide_text()
    assert "The Tuner" in text
    assert "CROSS_LAYER_CONTRACT_STALE" in text
    assert "CROSS_SPECIALIST_CONTRADICTION_REVIEW_REQUIRED" in text
    assert "SPECIALIST_REENTRY_REQUIRED" in text


# ===== T14: Overseer handoff and boundary discipline =====
def test_t14_overseer_boundary_discipline():
    text = _guide_text()
    assert "Overseer is the QA and validation specialist" in text
    assert "Arbiter consumes Overseer proof states" in text
    assert "Arbiter never defines proof states" in text
    assert "never executes test suites" in text
    assert "NOT_PROVEN" in text
    assert "FAILED" in text


# ===== T15: UIXx transition boundary =====
def test_t15_uix_transition_boundary():
    skill = _skill_text()
    assert "UIX Transition Boundary" in skill
    assert "fresh, revision-bound UI evidence" in skill


# ===== T16: Compliance registry evidence freshness =====
def test_t16_compliance_registry_freshness():
    skill = _skill_text()
    assert "Compliance Registry Evidence Freshness" in skill
    assert "Baelfyre/Orchestra-Compliance-Registry" in skill
    assert "release manifest SHA-256" in skill


# ===== T17: Adversarial cases evaluation =====
def test_t17_adversarial_cases():
    text = _guide_text()
    for phrase in [
        "stale base",
        "changed head after validation",
        "omitted untracked file",
        "mismatched staged patch",
        "expired source",
        "unresolved review thread",
        "contradictory canonical refs",
        "scaffold-only receiver claiming runtime continuity",
        "expanded child authority",
        "green checks used to claim release authority",
    ]:
        assert phrase in text, f"Expected adversarial phrase '{phrase}' in guide"


# ===== T18: Fail-closed posture =====
def test_t18_fail_closed_posture():
    text = _guide_text()
    assert "API success alone is not verified state" in text
    assert "matching content alone does not cure identity mismatch" in text


# ===== T19: Authority boundaries and non-authorizing constraints =====
def test_t19_non_authorizing_constraints():
    text = _guide_text()
    assert "Fresh evidence demonstrates compliance; it NEVER creates or expands execution authority" in text
    assert "v1.8 publication hold" in text


# ===== T20: Byte-identical Codex parity mirror =====
def test_t20_codex_parity_mirror():
    assert GUIDE_SOURCE.exists(), "skills/arbiter/CONTINUITY_EVALUATION_GUIDE.md must exist"
    assert GUIDE_CODEX.exists(), "adapters/codex/skills/arbiter/CONTINUITY_EVALUATION_GUIDE.md must exist"
    source_bytes = GUIDE_SOURCE.read_bytes().replace(b"\r\n", b"\n")
    codex_bytes = GUIDE_CODEX.read_bytes().replace(b"\r\n", b"\n")
    assert source_bytes == codex_bytes, "Arbiter continuity guide must be byte-identical between skills/ and adapters/"


# ===== T21: UIX-9 frozen SKILL.md preservation =====
def test_t21_uix9_frozen_skill_md_preservation():
    manifest_data = json.loads(UIX9_MANIFEST.read_text(encoding="utf-8"))
    arbiter_entries = [
        entry for entry in manifest_data.get("materials", [])
        if entry.get("path") == "skills/arbiter/SKILL.md"
    ]
    assert len(arbiter_entries) == 1, "skills/arbiter/SKILL.md must be registered in uix9 manifest"
    expected_digest = arbiter_entries[0]["canonical_blob_digest"]
    skill_content = SKILL_MD.read_bytes().replace(b"\r\n", b"\n")
    actual_digest = hashlib.sha256(skill_content).hexdigest()
    assert actual_digest == expected_digest, (
        f"skills/arbiter/SKILL.md was modified! Expected digest {expected_digest} but found {actual_digest}"
    )


# ===== T22: Specialist integration flow schema adherence =====
def test_t22_specialist_integration_flow_adherence():
    flow = json.loads(SPECIALIST_FLOW.read_text(encoding="utf-8"))
    arbiter_ownership = flow.get("ownership", {}).get("arbiter", {})
    assert "TRANSITION_DISPOSITION" in arbiter_ownership.get("owns", [])
    assert "EVIDENCE_FRESHNESS" in arbiter_ownership.get("owns", [])
    assert "ARCHITECTURE" in arbiter_ownership.get("does_not_own", [])
    assert "IMPLEMENTATION" in arbiter_ownership.get("does_not_own", [])
    assert "RENDERED_EVIDENCE" in arbiter_ownership.get("does_not_own", [])


ALL_TESTS = [
    ("T1: Evidence freshness taxonomy", test_t1_evidence_freshness_taxonomy),
    ("T2: Six-tier transition precedence hierarchy", test_t2_transition_precedence_hierarchy),
    ("T3: STOP disposition criteria", test_t3_stop_criteria),
    ("T4: ESCALATE_HUMAN disposition criteria", test_t4_escalate_human_criteria),
    ("T5: WAIT_FOR_CAPACITY disposition criteria", test_t5_wait_for_capacity_criteria),
    ("T6: WAIT_FOR_EVIDENCE disposition criteria", test_t6_wait_for_evidence_criteria),
    ("T7: AUTO_REMEDIATE_AND_REVALIDATE criteria", test_t7_auto_remediate_criteria),
    ("T8: AUTO_CONTINUE criteria", test_t8_auto_continue_criteria),
    ("T9: Exact commit and tree lineage binding", test_t9_exact_commit_and_tree_binding),
    ("T10: Head commit change invalidation rule", test_t10_head_commit_invalidation),
    ("T11: Working-tree modification invalidation rule", test_t11_working_tree_invalidation),
    ("T12: Cached evidence constraints", test_t12_cached_evidence_constraints),
    ("T13: Cross-specialist coordination and The Tuner collaboration", test_t13_cross_specialist_coordination),
    ("T14: Overseer handoff and boundary discipline", test_t14_overseer_boundary_discipline),
    ("T15: UIX transition boundary", test_t15_uix_transition_boundary),
    ("T16: Compliance registry evidence freshness", test_t16_compliance_registry_freshness),
    ("T17: Adversarial cases evaluation", test_t17_adversarial_cases),
    ("T18: Fail-closed posture", test_t18_fail_closed_posture),
    ("T19: Authority boundaries and non-authorizing constraints", test_t19_non_authorizing_constraints),
    ("T20: Byte-identical Codex parity mirror", test_t20_codex_parity_mirror),
    ("T21: UIX-9 frozen SKILL.md preservation", test_t21_uix9_frozen_skill_md_preservation),
    ("T22: Specialist integration flow schema adherence", test_t22_specialist_integration_flow_adherence),
]


def run_all():
    passed = 0
    failed = 0
    print(f"Running {len(ALL_TESTS)} Arbiter Evidence Freshness behavioral tests...")
    for name, test_fn in ALL_TESTS:
        try:
            test_fn()
            print(f"  [PASS] {name}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
            failed += 1
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_all())
