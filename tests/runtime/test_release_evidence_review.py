# @codebase_provenance_JEO
# @codebase_rights_JEO
"""Synthetic regression coverage for non-authorizing release evidence review."""

import copy
import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/validate_release_evidence_review.py"


def load_review():
    spec = importlib.util.spec_from_file_location("release_evidence_review", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


review = load_review()


def record():
    """Use synthetic candidate identities; never make these a real release decision."""
    head = "a" * 40
    digest = review.policy_fingerprint(ROOT)
    evidence = []
    for kind, id_value in (
        ("INDEPENDENT_REVIEW", "independent-synthetic"),
        ("REPOSITORY_SOURCE", "repo-synthetic"),
        ("HUMAN_DECISION", "human-synthetic"),
        ("CI_CHECK", "ci-synthetic"),
    ):
        evidence.append({
            "id": id_value,
            "kind": kind,
            "reference": "synthetic:fixture-only",
            "status": "PASS",
            "head_sha": head,
            "policy_fingerprint": digest,
            "check_status": "completed" if kind == "CI_CHECK" else None,
            "check_conclusion": "success" if kind == "CI_CHECK" else None,
        })
    gates = [
        {
            "name": name,
            "relevance": "REQUIRED",
            "rationale": "Synthetic evidence fixture for a policy gate.",
            "relevance_evidence_refs": ["repo-synthetic"],
            "validation": "PASS",
            "validation_evidence_refs": ["ci-synthetic"],
            "compliance": "PASS",
            "compliance_evidence_refs": ["independent-synthetic"],
            "human_judgment_required": False,
            "human_decision_ref": "human-synthetic" if name == "Human legal review completed (if flagged)" else None,
        }
        for name in review.release_gate_inventory(ROOT)
    ]
    return {
        "$schema": "../schemas/release-evidence-review.v1.schema.json",
        "schema_version": "orchestra.release-evidence-review.v1",
        "record_type": "RELEASE_EVIDENCE_REVIEW",
        "candidate": {
            "repository": "Baelfyre/Orchestra",
            "head_sha": head,
            "tree_sha": "b" * 40,
            "base_sha": "c" * 40,
            "release_channel": "PLUGIN_DISTRIBUTION",
        },
        "policy_fingerprint": digest,
        "gates": gates,
        "evidence": evidence,
        "unresolved_conflicts": [],
        "protected_policy_change": False,
        "remediation": {
            "deterministic_in_scope": False,
            "authorized": False,
            "scope_growth": False,
            "would_change_governing_gate": False,
            "attempts_used": 0,
        },
        "publication_authorized": False,
    }


def gate(record_value, name="Business alignment verified"):
    return next(value for value in record_value["gates"] if value["name"] == name)


def outcome(record_value):
    return review.validate_review(record_value, ROOT)


def test_synthetic_complete_review_is_only_ready_for_final_review():
    errors, disposition = outcome(record())
    assert errors == []
    assert disposition == "EVIDENCE_READY_FOR_FINAL_REVIEW"
    assert record()["publication_authorized"] is False


@pytest.mark.parametrize(
    "mutate",
    [
        lambda r: r.update(policy_fingerprint="f" * 64),
        lambda r: r["evidence"][0].update(head_sha="d" * 40),
        lambda r: r["evidence"][0].update(policy_fingerprint="f" * 64),
        lambda r: r["evidence"][0].update(id="ci-synthetic"),
        lambda r: r["evidence"][3].update(check_status=None),
        lambda r: gate(r).update(validation_evidence_refs=["missing-source"]),
        lambda r: gate(r).update(validation_evidence_refs=[]),
        lambda r: gate(r).update(compliance_evidence_refs=[]),
        lambda r: r["gates"].pop(),
        lambda r: r["gates"].append(copy.deepcopy(r["gates"][0])),
        lambda r: r.update(publication_authorized=True),
    ],
)
def test_missing_stale_duplicate_or_fabricated_evidence_fails_closed(mutate):
    r = record()
    mutate(r)
    errors, disposition = outcome(r)
    assert errors
    assert disposition == "INVALID_EVIDENCE"


def test_required_gate_cannot_be_falsely_marked_not_applicable():
    r = record()
    g = gate(r)
    g.update(relevance="NOT_APPLICABLE", validation="NOT_APPLICABLE", compliance="NOT_APPLICABLE")
    errors, disposition = outcome(r)
    assert errors
    assert disposition == "INVALID_EVIDENCE"


def test_conditional_not_applicable_requires_positive_evidence():
    r = record()
    g = gate(r, "Human legal review completed (if flagged)")
    g.update(
        relevance="NOT_APPLICABLE",
        rationale="No relevant legal review trigger on the declared scope.",
        validation="NOT_APPLICABLE",
        compliance="NOT_APPLICABLE",
        relevance_evidence_refs=[],
    )
    assert outcome(r)[1] == "INVALID_EVIDENCE"
    g["relevance_evidence_refs"] = ["independent-synthetic"]
    assert outcome(r) == ([], "EVIDENCE_READY_FOR_FINAL_REVIEW")


def test_known_deterministic_failure_may_be_remediated_within_budget():
    r = record()
    gate(r)["validation"] = "FAIL"
    r["remediation"].update(deterministic_in_scope=True, authorized=True, attempts_used=2)
    assert outcome(r) == ([], "AUTO_REMEDIATE_AND_REVALIDATE")


@pytest.mark.parametrize("remediation_change", [
    {"attempts_used": 3},
    {"scope_growth": True},
    {"authorized": False},
    {"would_change_governing_gate": True},
])
def test_exhaustion_or_unauthorized_remediation_escalates(remediation_change):
    r = record()
    gate(r)["validation"] = "FAIL"
    r["remediation"].update(deterministic_in_scope=True, authorized=True)
    r["remediation"].update(remediation_change)
    assert outcome(r) == ([], "ESCALATE_HUMAN")


def test_missing_evidence_is_not_approval_or_automatic_remediation():
    r = record()
    gate(r)["compliance"] = "PENDING"
    assert outcome(r) == ([], "WAIT_FOR_EVIDENCE")


def test_unknown_relevance_awaits_evidence():
    r = record()
    gate(r).update(relevance="UNKNOWN", validation="PENDING", compliance="PENDING")
    assert outcome(r) == ([], "WAIT_FOR_EVIDENCE")


def test_legal_judgment_requires_attributable_human_decision():
    r = record()
    g = gate(r, "Legal compliance confirmed")
    g["human_judgment_required"] = True
    assert outcome(r) == ([], "ESCALATE_HUMAN")
    g["human_decision_ref"] = "human-synthetic"
    assert outcome(r) == ([], "EVIDENCE_READY_FOR_FINAL_REVIEW")


@pytest.mark.parametrize("change", [
    lambda r: r["unresolved_conflicts"].append("Contradictory third-party license evidence"),
    lambda r: r.update(protected_policy_change=True),
])
def test_conflict_or_protected_policy_change_cannot_continue(change):
    r = record()
    change(r)
    assert outcome(r) == ([], "ESCALATE_HUMAN")


def test_human_decision_cannot_be_a_ci_check():
    r = record()
    g = gate(r, "Legal compliance confirmed")
    g.update(human_judgment_required=True, human_decision_ref="ci-synthetic")
    assert outcome(r)[1] == "INVALID_EVIDENCE"


def test_release_evidence_review_is_read_only_and_policy_bound():
    r = record()
    before = copy.deepcopy(r)
    assert outcome(r)[0] == []
    assert r == before
    assert len(review.release_gate_inventory(ROOT)) >= 15


def test_sensitive_compliance_cannot_be_cleared_only_by_green_ci():
    r = record()
    gate(r, "Legal compliance confirmed")["compliance_evidence_refs"] = ["ci-synthetic"]
    assert outcome(r)[1] == "INVALID_EVIDENCE"


def test_not_applicable_cannot_be_justified_by_ci_only():
    r = record()
    g = gate(r, "Human legal review completed (if flagged)")
    g.update(
        relevance="NOT_APPLICABLE",
        rationale="Synthetic scoped review asserts this legal trigger is not applicable.",
        validation="NOT_APPLICABLE",
        compliance="NOT_APPLICABLE",
        relevance_evidence_refs=["ci-synthetic"],
    )
    assert outcome(r)[1] == "INVALID_EVIDENCE"


def test_public_plugin_app_release_review_cannot_be_marked_not_applicable():
    r = record()
    g = gate(r, "App Release Compliance Gate reviewed")
    g.update(
        relevance="NOT_APPLICABLE",
        rationale="Incorrectly omitted for public plugin distribution.",
        validation="NOT_APPLICABLE",
        compliance="NOT_APPLICABLE",
    )
    assert outcome(r)[1] == "INVALID_EVIDENCE"


def test_unsupported_distribution_channel_does_not_pass_schema():
    r = record()
    r["candidate"]["release_channel"] = "UNVERIFIED_UNKNOWN"
    assert outcome(r)[1] == "INVALID_EVIDENCE"


def test_required_gate_needs_applicability_source_not_only_ci():
    r = record()
    gate(r)["relevance_evidence_refs"] = []
    assert outcome(r)[1] == "INVALID_EVIDENCE"
    gate(r)["relevance_evidence_refs"] = ["ci-synthetic"]
    assert outcome(r)[1] == "INVALID_EVIDENCE"
    gate(r)["relevance_evidence_refs"] = ["repo-synthetic"]
    assert outcome(r) == ([], "EVIDENCE_READY_FOR_FINAL_REVIEW")


def test_flagged_human_legal_review_cannot_be_auto_waived_by_false_boolean():
    r = record()
    g = gate(r, "Human legal review completed (if flagged)")
    g["human_judgment_required"] = False
    g["human_decision_ref"] = None
    assert outcome(r) == ([], "ESCALATE_HUMAN")
    g["human_decision_ref"] = "human-synthetic"
    assert outcome(r) == ([], "EVIDENCE_READY_FOR_FINAL_REVIEW")


def test_governing_delegated_policy_is_part_of_fingerprint(tmp_path):
    for relative in (
        review.GATE_PATH,
        review.APP_PATH,
        review.DECISION_PATH,
        review.POLICY_PATH,
        review.DELEGATED_PATH,
        review.PROTECTED_PATH,
        review.QUALIFICATION_PATH,
    ):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / relative).read_bytes())
    expected = review.policy_fingerprint(tmp_path)
    assert expected == review.policy_fingerprint(ROOT)
    target = tmp_path / review.DELEGATED_PATH
    target.write_bytes(target.read_bytes() + b"\\n# Simulated policy revision\\n")
    assert review.policy_fingerprint(tmp_path) != expected

@pytest.mark.parametrize(
    ("mutate", "expected_exit"),
    [
        (lambda r: None, 0),
        (lambda r: gate(r).update(compliance="PENDING"), 1),
        (lambda r: gate(r).update(validation="FAIL"), 3),
        (lambda r: r.update(protected_policy_change=True), 3),
        (lambda r: r.update(policy_fingerprint="f" * 64), 2),
    ],
)
def test_cli_fails_closed_unless_evidence_ready(tmp_path, capsys, mutate, expected_exit):
    import json

    r = record()
    mutate(r)
    path = tmp_path / "record.json"
    path.write_text(json.dumps(r), encoding="utf-8")
    assert review.main(["--record", str(path)]) == expected_exit
    output = capsys.readouterr().out
    if expected_exit != 2:
        assert "RELEASE_PUBLICATION_AUTHORIZED=false" in output


def exception_record():
    """Synthetic draft only. This does not authenticate human decisions or rights."""
    from datetime import datetime, timedelta, timezone

    r = record()
    r["candidate"].update(
        head_sha=review.EXCEPTION_HEAD,
        tree_sha=review.EXCEPTION_TREE,
        release_channel="PLUGIN_DISTRIBUTION",
    )
    for item in r["evidence"]:
        item["head_sha"] = review.EXCEPTION_HEAD
    r["evidence"].append({
        "id": "governor-synthetic",
        "kind": "INDEPENDENT_REVIEW",
        "reference": "synthetic:governor-reconsideration",
        "status": "PASS",
        "head_sha": review.EXCEPTION_HEAD,
        "policy_fingerprint": r["policy_fingerprint"],
        "check_status": None,
        "check_conclusion": None,
    })
    expires_at = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    for name in review.EXCEPTION_GATES:
        item = gate(r, name)
        item["compliance"] = "EXCEPTION_QUALIFIED"
        item["human_judgment_required"] = True
        item["human_decision_ref"] = "human-synthetic"
        item["compliance_evidence_refs"] = [
            "human-synthetic", "independent-synthetic", "governor-synthetic"
        ]
        item["bounded_exception"] = {
            "case_id": "ORCH-991-TRADEMARK-EXCEPTION-20261109",
            "escalation_ref": "https://github.com/Baelfyre/Orchestra/issues/1003",
            "owner_decision_ref": "human-synthetic",
            "independent_review_ref": "independent-synthetic",
            "governor_reconsideration_ref": "governor-synthetic",
            "candidate_head_sha": review.EXCEPTION_HEAD,
            "candidate_tree_sha": review.EXCEPTION_TREE,
            "release_channel": "PLUGIN_DISTRIBUTION",
            "exception_type": "POINTCROSS_ORCHESTRA_TRADEMARK_REVIEW_ONLY",
            "single_use": True,
            "consumed": False,
            "expires_at": expires_at,
            "unresolved_legal_risk": True,
            "claims_trademark_clearance": False,
            "publication_authorized": False,
        }
    return r


def test_synthetic_exception_is_distinct_from_clearance_and_not_publication_authority():
    r = exception_record()
    assert outcome(r) == ([], "EVIDENCE_READY_FOR_FINAL_REVIEW")
    assert all(g["compliance"] == "EXCEPTION_QUALIFIED"
               for g in r["gates"] if g["name"] in review.EXCEPTION_GATES)
    assert r["publication_authorized"] is False


@pytest.mark.parametrize("mutate", [
    lambda r: r["candidate"].update(head_sha="c" * 40),
    lambda r: r["candidate"].update(tree_sha="c" * 40),
    lambda r: r["candidate"].update(release_channel="MARKETPLACE"),
    lambda r: gate(r, "IP/copyright cleared")["bounded_exception"].update(
        candidate_tree_sha="d" * 40
    ),
    lambda r: gate(r, "Human legal review completed (if flagged)")["bounded_exception"].update(
        claims_trademark_clearance=True
    ),
    lambda r: gate(r, "IP/copyright cleared")["bounded_exception"].update(
        consumed=True
    ),
    lambda r: gate(r, "IP/copyright cleared")["bounded_exception"].update(
        owner_decision_ref="governor-synthetic"
    ),
    lambda r: gate(r, "IP/copyright cleared").update(human_decision_ref=None),
    lambda r: gate(r, "IP/copyright cleared")["bounded_exception"].update(
        expires_at="2020-01-01T00:00:00Z"
    ),
    lambda r: gate(r, "IP/copyright cleared").update(
        compliance_evidence_refs=["human-synthetic"]
    ),
    lambda r: gate(r, "Business alignment verified").update(
        compliance="EXCEPTION_QUALIFIED",
        bounded_exception=copy.deepcopy(gate(r, "IP/copyright cleared")["bounded_exception"]),
    ),
])
def test_synthetic_exception_fails_closed_for_bad_scope_evidence_or_clearance_claim(mutate):
    r = exception_record()
    mutate(r)
    errors, disposition = outcome(r)
    assert errors
    assert disposition == "INVALID_EVIDENCE"


def test_ordinary_gate_rejects_hidden_exception_attachment():
    r = exception_record()
    gate(r, "Business alignment verified")["bounded_exception"] = copy.deepcopy(
        gate(r, "IP/copyright cleared")["bounded_exception"]
    )
    assert outcome(r)[1] == "INVALID_EVIDENCE"


def test_unresolved_governor_block_remains_escalated_with_synthetic_exception():
    r = exception_record()
    r["unresolved_conflicts"].append("Governor BLOCKED finding not superseded")
    assert outcome(r) == ([], "ESCALATE_HUMAN")
