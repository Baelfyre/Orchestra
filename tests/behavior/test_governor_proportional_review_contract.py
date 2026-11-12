# @codebase_provenance_JEO
"""Static prose-contract coverage, not runtime enforcement or release evidence."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]


def _read(relative: str) -> str:
    return " ".join((ROOT / relative).read_text(encoding="utf-8").split())


def _require(source: str, *fragments: str) -> None:
    missing = [fragment for fragment in fragments if fragment not in source]
    assert not missing, f"Missing tracked guidance fragments: {missing}"


def test_high_risk_decision_is_proportional_and_domain_alone_does_not_set_flag() -> None:
    layer = _read("docs/governance/GOVERNANCE_LAYER.md")
    governor = _read("docs/governance/GOVERNOR.md")
    _require(
        layer,
        "`HIGH` | Public release, user accounts, PII, payments, AI outputs, legal/health/finance domain, copyrighted content, open-source distribution, commercial use | Expanded review; human review only when an applicable control or material uncertainty requires human authority for the current decision. |",
    )
    _require(
        governor,
        "`HIGH` (expanded review; human review for the current high-risk decision when an applicable control or material uncertainty requires human authority; domain membership alone does not set the flag).",
        "For a release-scoped rights finding, see the action-applicability limits in the Governor's [Human Escalation Boundaries Guide](../../skills/the-governor/HUMAN_ESCALATION_BOUNDARIES_GUIDE.md) and [the Governance Layer's Need-To-Only Governance section](GOVERNANCE_LAYER.md#need-to-only-governance).",
    )


def test_release_rights_stay_blocked_and_local_units_keep_all_current_gates() -> None:
    layer = _read("docs/governance/GOVERNANCE_LAYER.md")
    guide = _read("skills/the-governor/HUMAN_ESCALATION_BOUNDARIES_GUIDE.md")
    _require(
        layer,
        "## Freedom-First Development",
        "Conductor keeps development freedom-first and need-based. Ideation, planning, drafting, prompt refinement, brainstorming, prototyping, and concept exploration stay unblocked. Governance checks activate at implementation, file or architecture changes, or material risk triggers.",
        "## Need-To-Only Governance",
        "Full review applies in Release, Audit, or for material risks; low-risk work receives light, non-blocking review.",
    )
    assert "### Release-scoped rights applicability" not in layer
    _require(
        guide,
        "A rights finding scoped to public distribution/release blocks that release decision and actions dependent on its clearance.",
        "It does not automatically block a separate non-protected read-only or isolated implementation/testing unit when that unit has separate current authorization",
        "and its operating mode, envelope/phase, allowed paths, baseline, applicable requirements, and security/policy gates permit the work, and it does not exercise the blocked publication/release path.",
        "Keep the finding open; local work is not rights clearance or permission to commit, push, merge, release, or publish.",
        "Lifecycle contexts in the Governor applicability record classify scope only and grant no execution authority;",
        "existing mode, authorization, protected-path, security, and Arbiter gates remain.",
        "A human_review_required: true in the current unit's active governance evidence still pauses that unit under the shared protocol.",
        "This section does not filter, downgrade, or clear a true flag.",
        "Ideation, Prototype, Implementation, Audit, and Release mode requirements continue.",
    )
    assert "](../../docs/" not in guide


def test_finding_identity_evidence_reuse_and_reentry_are_source_bound() -> None:
    guide = _read("skills/the-governor/HUMAN_ESCALATION_BOUNDARIES_GUIDE.md")
    _require(
        guide,
        "## Proportional finding identity and evidence reuse",
        "stable identity derived from requirement/control + subject + action/distribution scope + evidence scope",
        "exact operational decision and lifecycle stage",
        "candidate/tree and source/asset/evidence identity",
        "authoritative evidence references with source version/effective date",
        "source-backed closure evidence or corrective action",
        "named human decision owner",
        "## Release-scoped rights applicability",
        "This guide's [Release-scoped rights applicability section](#release-scoped-rights-applicability) defines the release-only rights scope; the current-unit true-flag rule remains governed by the shared Governance Decision Protocol (docs/governance/GOVERNANCE_DECISION_PROTOCOL.md#shared-gate-contract).",
        "Reuse evidence only when it is verified, unchanged, current, and still applicable; record any required periodic external-source re-check.",
        "Re-enter on changes to candidate/tree, source, asset, evidence scope, use/distribution/channel, jurisdiction, governing source/version/effective date, material facts, or expiry.",
    )


def test_applicability_contexts_require_source_backed_closure_and_owner() -> None:
    guide = _read("skills/the-governor/HUMAN_ESCALATION_BOUNDARIES_GUIDE.md")
    _require(
        guide,
        "Classify applicability across ideation/read-only inspection, isolated implementation/testing, local commit/draft review, branch push, protected merge, public installation/distribution, and release.",
        "This is an applicability map only and grants no authorization.",
        "If legal interpretation or risk acceptance is needed, record the question for the human owner; the Governor does not provide binding legal conclusions or accept owner risk.",
        "Human owner approval remains required for policy activation and release",
    )


def test_current_unit_true_flag_and_actual_blocks_remain_fail_closed() -> None:
    guide = _read("skills/the-governor/HUMAN_ESCALATION_BOUNDARIES_GUIDE.md")
    protocol = _read("docs/governance/GOVERNANCE_DECISION_PROTOCOL.md")
    _require(
        guide,
        "A human_review_required: true in the current unit's active governance evidence still pauses that unit under the shared protocol.",
        "security/policy gates permit the work",
        "existing mode, authorization, protected-path, security, and Arbiter gates remain.",
        "This section does not filter, downgrade, or clear a true flag.",
    )
    _require(
        protocol,
        "Conductor pauses on",
        "human_review_required: true",
        "Conductor stops on",
        "BLOCKED",
        "Execution specialists cannot bypass governance.",
    )


def test_missing_rights_and_loop_suppression_cannot_clear_a_finding() -> None:
    guide = _read("skills/the-governor/HUMAN_ESCALATION_BOUNDARIES_GUIDE.md")
    _require(
        guide,
        "Keep the finding open; local work is not rights clearance or permission to commit, push, merge, release, or publish.",
        "Repeated unchanged findings remain open and gated;",
        "No retry/loop-suppression count approves, dismisses, or waives a finding.",
        "missing sources are NOT_FOUND and unknown facts remain UNKNOWN.",
        "Governor cannot approve its own exception;",
        "Steward and Arbiter retain independent decisions.",
        "Governor approval is not release, publication, policy activation, deployment, or risk-acceptance authority.",
    )


def test_two_step_emblem_provenance_does_not_establish_clearance() -> None:
    # Owner-supplied sample photo/hash; the brainstorming date is not capture or transformation provenance.
    emblem_case = {
        "origin": "hand-drawn",
        "refinement": "ChatGPT",
        "sample_photo": "owner-supplied sample photo (present; hash-verified)",
        "sample_photo_sha256": "B5D803E0228C94BF82E9FFBEA674FF249915345489FFEB6F86DA312CEA4E23E8",
        "sample_photo_sha256_status": "verified file identity",
        "photo_creation_or_capture_date": "NOT_FOUND",
        "brainstorming_design_session_date": "2026-11-10 local",
        "brainstorming_context": "ways to rebrand Orchestra to Kontrolled Kaos",
        "sketch_execution_date": "NOT_FOUND",
        "source_to_final_prompt": "NOT_FOUND",
        "transformation": "NOT_FOUND",
        "chatgpt_generation_transformation_date": "NOT_FOUND",
        "candidate_sha256": "0c22c8ecf56ba103639bfce1eda290e55de0b8fa94f9d404fe79e3c359611e4f",
        "candidate_sha256_status": "owner-approved for A5 integration",
        "candidate_sha256_scope": "A5 integration scope only",
        "merge_or_release_authority": "NOT_GRANTED",
        "visual_acceptance": "owner-attested",
        "input_rights": "UNKNOWN",
        "third_party_reference_rights": "UNKNOWN",
        "trademark_clearance": "UNKNOWN",
        "distribution_clearance": "UNKNOWN",
    }
    assert emblem_case["origin"] == "hand-drawn"
    assert emblem_case["refinement"] == "ChatGPT"
    assert emblem_case["sample_photo"] == "owner-supplied sample photo (present; hash-verified)"
    assert emblem_case["sample_photo_sha256"] == "B5D803E0228C94BF82E9FFBEA674FF249915345489FFEB6F86DA312CEA4E23E8"
    assert emblem_case["sample_photo_sha256_status"] == "verified file identity"
    assert emblem_case["brainstorming_design_session_date"] == "2026-11-10 local"
    assert emblem_case["brainstorming_context"] == "ways to rebrand Orchestra to Kontrolled Kaos"
    assert emblem_case["candidate_sha256"] == "0c22c8ecf56ba103639bfce1eda290e55de0b8fa94f9d404fe79e3c359611e4f"
    assert emblem_case["candidate_sha256_status"] == "owner-approved for A5 integration"
    assert emblem_case["candidate_sha256_scope"] == "A5 integration scope only"
    assert emblem_case["merge_or_release_authority"] == "NOT_GRANTED"
    assert emblem_case["visual_acceptance"] == "owner-attested"
    assert all(
        emblem_case[field] == "NOT_FOUND"
        for field in (
            "photo_creation_or_capture_date",
            "sketch_execution_date",
            "source_to_final_prompt",
            "transformation",
            "chatgpt_generation_transformation_date",
        )
    )
    assert all(
        emblem_case[field] == "UNKNOWN"
        for field in ("input_rights", "third_party_reference_rights", "trademark_clearance", "distribution_clearance")
    )
    guide = _read("skills/the-governor/HUMAN_ESCALATION_BOUNDARIES_GUIDE.md")
    layer = _read("docs/governance/GOVERNANCE_LAYER.md")
    _require(
        guide,
        "A rights finding scoped to public distribution/release blocks that release decision",
        "local work is not rights clearance or permission to commit, push, merge, release, or publish.",
        "Owner-attested AI generation, candidate hash, or visual approval does not establish third-party rights, license, or trademark clearance;",
        "missing sources are NOT_FOUND and unknown facts remain UNKNOWN.",
        "An owner-supplied photo hash proves file identity only; it does not establish that the photo was the exact AI input or prove the final-work lineage, and a visible HONOR X9b watermark is a provenance question, not presumed third-party infringement.",
        "Public release requires the `IP/copyright cleared` release gate to pass, any required human review to be complete, and all required publication approvals to be recorded.",
        "Unsupported, unparticularized AI-output similarity concerns or inability to reconstruct every intermediate AI-generation step alone may remain a scoped `RISKS` warning only after proportionate review, when no concrete conflict or material uncertainty remains, every applicable gate independently passes, and no separate `human_review_required` flag is pending.",
        "Unknown required evidence, unresolved material facts, or concrete rights conflicts remain blocking; this does not claim or grant rights clearance, and deferring or restricting use does not itself establish clearance.",
    )


def test_output_formats_record_current_decision_and_applicability_scope() -> None:
    formats = _read("skills/the-governor/OUTPUT_FORMATS.md")
    assert formats.count("OPERATIONAL_DECISION: [value]") == 3
    assert formats.count("APPLICABILITY_SCOPE: [value]") == 3
    _require(
        formats,
        "OPERATIONAL_DECISION` records the exact current action/transition or `NOT_FOUND` if missing.",
        "APPLICABILITY_SCOPE` lists affected actions/channels; use `UNKNOWN` if unresolved and `NOT_APPLICABLE` only with assessed rationale.",
    )


def test_existing_arbiter_human_review_escalation_still_passes() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/runtime/test_governance_kernel.py::ArbiterKernelTests::test_human_review_required_escalates",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


_PROSE_TESTS = (
    test_high_risk_decision_is_proportional_and_domain_alone_does_not_set_flag,
    test_release_rights_stay_blocked_and_local_units_keep_all_current_gates,
    test_finding_identity_evidence_reuse_and_reentry_are_source_bound,
    test_applicability_contexts_require_source_backed_closure_and_owner,
    test_current_unit_true_flag_and_actual_blocks_remain_fail_closed,
    test_missing_rights_and_loop_suppression_cannot_clear_a_finding,
    test_two_step_emblem_provenance_does_not_establish_clearance,
    test_output_formats_record_current_decision_and_applicability_scope,
    test_existing_arbiter_human_review_escalation_still_passes,
)


def main() -> int:
    for test in _PROSE_TESTS:
        test()
    print(f"Proportional review contract assertions passed: {len(_PROSE_TESTS)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
