# @codebase_provenance_JEO
# @codebase_rights_JEO
"""Validate the protected governance escalation contract and cross-surface invariants."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

CONTRACT_PATH = ROOT / "machine" / "governance" / "protected-governance-escalation.v1.json"
SCHEMA_PATH = ROOT / "machine" / "schemas" / "protected-governance-escalation.v1.schema.json"
POLICY_PATH = ROOT / "machine" / "governance" / "policy.v1.json"

REQUIRED_AI_RECOMMENDATIONS = (
    "DENY",
    "REQUEST_MORE_EVIDENCE",
    "RECOMMEND_BOUNDED_EXCEPTION",
    "RECOMMEND_POLICY_AMENDMENT",
)
REQUIRED_HUMAN_DECISIONS = (
    "DENY",
    "REQUEST_MORE_EVIDENCE",
    "APPROVE_BOUNDED_EXCEPTION",
    "APPROVE_POLICY_AMENDMENT",
)
REQUIRED_DEFAULT_REVIEWERS = ("ARBITER", "OVERSEER", "CLOCKWORK")

REQUIRED_TEXT = {
    "docs/governance/PROTECTED_GOVERNANCE_ESCALATION_PROTOCOL.md": (
        "RUN_N_DISCOVERS_GOVERNANCE_CHANGE",
        "HUMAN_REVIEW_REQUIRED",
        "NEW_EXECUTION_CONTEXT_REQUIRED",
        "The originating run must not create and consume its own exception",
        "FAIL_POLICY_SELF_MODIFICATION",
    ),
    "docs/governance/ORCHESTRA_PRIME_DIRECTIVE.md": (
        "A run that discovers a protected governance change cannot execute that change in the same run.",
        "PROTECTED_GOVERNANCE_ESCALATION_PROTOCOL.md",
    ),
    "docs/governance/GOVERNANCE_DECISION_PROTOCOL.md": (
        "## Protected Governance Escalation",
        "FAIL_POLICY_SELF_MODIFICATION",
        "APPROVE_POLICY_AMENDMENT",
    ),
    "docs/governance/GOVERNANCE_REVIEW_FLOW.md": (
        "## Protected Governance Escalation Flow",
        "ORIGINATING RUN TERMINATES",
        "NEW EXECUTION CONTEXT REQUIRED",
    ),
    "docs/governance/GOVERNED_AUTONOMOUS_EXECUTION_PROTOCOL.md": (
        "## Protected Governance Escalation",
        "FULL_AUTONOMOUS",
        "new execution context",
    ),
    "docs/architecture/ADAPTIVE_ASSURANCE_PRAI.md": (
        "GOVERNANCE_ESCALATION_REQUIRED",
        "FAIL_POLICY_SELF_MODIFICATION",
        "new execution context",
    ),
}


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def require(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        fail(errors, message)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []

    for path in (CONTRACT_PATH, SCHEMA_PATH, POLICY_PATH):
        require(path.is_file(), errors, f"missing required file: {path.relative_to(ROOT)}")
    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1

    contract = load_json(CONTRACT_PATH)
    schema = load_json(SCHEMA_PATH)
    policy = load_json(POLICY_PATH)

    require(
        contract.get("schema_version") == "orchestra.protected-governance-escalation.v1",
        errors,
        "protected escalation contract schema_version mismatch",
    )
    require(contract.get("same_run_policy_change_forbidden") is True, errors, "same-run policy change must be forbidden")
    require(contract.get("human_review_required") is True, errors, "human review must be required")
    require(contract.get("new_execution_context_required") is True, errors, "new execution context must be required")
    require(contract.get("candidate_freeze_required") is True, errors, "candidate freeze must be required")
    require(contract.get("ordinary_auto_remediation_allowed") is False, errors, "ordinary auto-remediation must be forbidden")
    require(contract.get("originating_run_may_resume_after_human_decision") is False, errors, "originating run must not resume")
    require(
        tuple(contract.get("ai_recommendations", ())) == REQUIRED_AI_RECOMMENDATIONS,
        errors,
        "AI recommendation vocabulary mismatch",
    )
    require(
        tuple(contract.get("human_decisions", ())) == REQUIRED_HUMAN_DECISIONS,
        errors,
        "human decision vocabulary mismatch",
    )
    require(
        tuple(contract.get("required_default_reviewers", ())) == REQUIRED_DEFAULT_REVIEWERS,
        errors,
        "default reviewer set mismatch",
    )
    require(
        "FAIL_POLICY_SELF_MODIFICATION" in contract.get("prai_failure_triggers", ()),
        errors,
        "PRAI self-modification failure must trigger escalation",
    )
    require(
        contract.get("exception_properties", {}).get("same_run_creation_and_consumption_forbidden") is True,
        errors,
        "same-run exception creation/consumption must be forbidden",
    )
    require(
        contract.get("policy_amendment_properties", {}).get(
            "self_amended_assurance_mechanism_cannot_be_claimed_as_independent_certifier"
        )
        is True,
        errors,
        "self-amended assurance mechanism cannot certify its own amendment",
    )

    escalation_policy = policy.get("protected_governance_escalation", {})
    require(
        escalation_policy.get("machine_contract")
        == "machine/governance/protected-governance-escalation.v1.json",
        errors,
        "governance policy must bind the escalation machine contract",
    )
    require(escalation_policy.get("transition_disposition") == "ESCALATE_HUMAN", errors, "policy disposition must be ESCALATE_HUMAN")
    require(escalation_policy.get("same_run_policy_change_forbidden") is True, errors, "policy must forbid same-run governance change")
    require(escalation_policy.get("new_execution_context_required") is True, errors, "policy must require a new execution context")

    require(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", errors, "schema draft mismatch")
    require(isinstance(schema.get("oneOf"), list) and len(schema["oneOf"]) == 2, errors, "schema must define escalation and human-decision records")

    for relative, needles in REQUIRED_TEXT.items():
        path = ROOT / relative
        require(path.is_file(), errors, f"missing governed surface: {relative}")
        if not path.is_file():
            continue
        body = path.read_text(encoding="utf-8")
        for needle in needles:
            require(needle in body, errors, f"{relative} missing protected-escalation invariant: {needle}")

    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1

    print("[PASS] protected governance escalation is machine-bound and cross-surface consistent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
