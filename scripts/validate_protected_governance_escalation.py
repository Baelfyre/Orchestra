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
REQUIRED_WHITELIST_MUTATIONS = (
    "CREATE_WHITELIST",
    "ADD_WHITELIST_ENTRY",
    "REMOVE_WHITELIST_ENTRY",
    "EXPAND_WHITELIST_MATCH",
    "NARROW_WHITELIST_MATCH",
    "REINTERPRET_WHITELIST_SCOPE",
    "CHANGE_WHITELIST_PRECEDENCE",
    "CHANGE_WHITELIST_TRANSITIVITY",
    "CHANGE_WHITELIST_EXPIRATION",
    "CHANGE_WHITELIST_CONSUMPTION",
    "CHANGE_WHITELIST_REASON_CODE",
    "DELETE_OR_DISABLE_WHITELIST",
)
WHITELIST_AUTHORITY_ORIGIN = "Padayon:c8798f848df0830d04d5f25b4f0680d288768839"
IDENTITY_QUALIFICATION_FIELD = "originating_run_identity_governance_qualification"
IDENTITY_QUALIFICATION = "UNQUALIFIED"

REQUIRED_TEXT = {
    "docs/governance/PROTECTED_GOVERNANCE_ESCALATION_PROTOCOL.md": (
        "RUN_N_DISCOVERS_GOVERNANCE_CHANGE",
        "HUMAN_REVIEW_REQUIRED",
        "NEW_EXECUTION_CONTEXT_REQUIRED",
        "The originating run must not create and consume its own exception",
        "FAIL_POLICY_SELF_MODIFICATION",
        "`VERIFIED` status, run IDs, and reference strings are structural claims only",
        "`UNQUALIFIED` for governance consumption",
        "A `VERIFIED` packet must carry `originating_run_identity_governance_qualification: UNQUALIFIED`",
        "cannot establish run identity, source authenticity, a separate human decision, or governance authority",
        "Whitelist authority is human-only.",
        "`FULL_AUTONOMOUS` does not authorize whitelist mutation.",
        WHITELIST_AUTHORITY_ORIGIN,
    ),
    "docs/governance/ORCHESTRA_PRIME_DIRECTIVE.md": (
        "A run that discovers a protected governance change cannot execute that change in the same run.",
        "PROTECTED_GOVERNANCE_ESCALATION_PROTOCOL.md",
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
        "Whitelist mutation is always a protected governance change.",
        "`FULL_AUTONOMOUS` cannot authorize whitelist mutation.",
    ),
    "docs/architecture/ADAPTIVE_ASSURANCE_PRAI.md": (
        "GOVERNANCE_ESCALATION_REQUIRED",
        "FAIL_POLICY_SELF_MODIFICATION",
        "new execution context",
    ),
}

FORBIDDEN_DUPLICATED_TEXT = {
    "docs/governance/GOVERNANCE_DECISION_PROTOCOL.md": (
        "## Protected Governance Escalation",
        "FAIL_POLICY_SELF_MODIFICATION",
        "APPROVE_POLICY_AMENDMENT",
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
    identity_provenance = contract.get("originating_run_identity_provenance", {})
    if not isinstance(identity_provenance, dict):
        identity_provenance = {}
    require(
        identity_provenance.get("verified_governance_qualification") == IDENTITY_QUALIFICATION,
        errors,
        "VERIFIED run identity must remain unqualified for governance consumption",
    )
    require(
        identity_provenance.get("run_id_and_reference_values_are_structural_claims_only") is True,
        errors,
        "run IDs and reference values must remain structural claims only",
    )
    require(
        identity_provenance.get("trusted_source_authenticator_available") is False,
        errors,
        "no trusted source authenticator may be claimed by this contract",
    )
    require(
        identity_provenance.get("authority_effect") == "NONE",
        errors,
        "run identity claims must have no authority effect",
    )
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
        "WHITELIST_MUTATION_REQUIRED" in contract.get("additional_triggers", ()),
        errors,
        "whitelist mutation must trigger protected governance escalation",
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

    whitelist_authority = contract.get("whitelist_authority", {})
    require(
        whitelist_authority.get("authority_class") == "HUMAN_POLICY",
        errors,
        "whitelist authority must be HUMAN_POLICY",
    )
    require(
        whitelist_authority.get("authority_origin_record") == WHITELIST_AUTHORITY_ORIGIN,
        errors,
        "whitelist authority origin record mismatch",
    )
    require(
        whitelist_authority.get("human_approval_required") is True,
        errors,
        "whitelist mutation must require human approval",
    )
    require(
        whitelist_authority.get("human_decision_record_required") is True,
        errors,
        "whitelist mutation must require a human decision record",
    )
    require(
        whitelist_authority.get("ai_recommendation_allowed") is True,
        errors,
        "AI must remain allowed to recommend whitelist changes",
    )
    require(
        whitelist_authority.get("ai_approval_allowed") is False,
        errors,
        "AI must not approve whitelist changes",
    )
    require(
        whitelist_authority.get("ai_mutation_without_human_decision_allowed") is False,
        errors,
        "AI must not mutate whitelist policy without a human decision",
    )
    require(
        whitelist_authority.get("full_autonomous_override_allowed") is False,
        errors,
        "FULL_AUTONOMOUS must not override whitelist human authority",
    )
    require(
        whitelist_authority.get("fresh_execution_context_required") is True,
        errors,
        "whitelist mutation must require a fresh execution context",
    )
    require(
        whitelist_authority.get("same_run_creation_and_consumption_forbidden") is True,
        errors,
        "same-run whitelist creation and consumption must be forbidden",
    )
    require(
        whitelist_authority.get("precedent_is_authority") is False,
        errors,
        "whitelist precedent must not create authority",
    )
    require(
        tuple(whitelist_authority.get("protected_mutations", ())) == REQUIRED_WHITELIST_MUTATIONS,
        errors,
        "whitelist protected mutation vocabulary mismatch",
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

    policy_whitelist_authority = escalation_policy.get("whitelist_authority", {})
    require(
        policy_whitelist_authority.get("authority_class") == "HUMAN_POLICY",
        errors,
        "governance policy whitelist authority must be HUMAN_POLICY",
    )
    require(
        policy_whitelist_authority.get("human_approval_required") is True,
        errors,
        "governance policy must require human approval for whitelist mutation",
    )
    require(
        policy_whitelist_authority.get("human_decision_record_required") is True,
        errors,
        "governance policy must require a human whitelist decision record",
    )
    require(
        policy_whitelist_authority.get("ai_recommendation_allowed") is True,
        errors,
        "governance policy must allow AI whitelist recommendations",
    )
    require(
        policy_whitelist_authority.get("ai_approval_allowed") is False,
        errors,
        "governance policy must forbid AI whitelist approval",
    )
    require(
        policy_whitelist_authority.get("ai_mutation_without_human_decision_allowed") is False,
        errors,
        "governance policy must forbid AI whitelist mutation without human decision",
    )
    require(
        policy_whitelist_authority.get("full_autonomous_override_allowed") is False,
        errors,
        "governance policy must forbid FULL_AUTONOMOUS whitelist override",
    )
    require(
        policy_whitelist_authority.get("fresh_execution_context_required") is True,
        errors,
        "governance policy must require fresh execution context for whitelist mutation",
    )
    require(
        policy_whitelist_authority.get("same_run_creation_and_consumption_forbidden") is True,
        errors,
        "governance policy must forbid same-run whitelist creation and consumption",
    )
    require(
        policy_whitelist_authority.get("precedent_is_authority") is False,
        errors,
        "governance policy must not treat whitelist precedent as authority",
    )

    require(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", errors, "schema draft mismatch")
    require(isinstance(schema.get("oneOf"), list) and len(schema["oneOf"]) == 2, errors, "schema must define escalation and human-decision records")
    schema_records = schema.get("oneOf") if isinstance(schema.get("oneOf"), list) else []
    packet_schema = next(
        (record for record in schema_records if record.get("title") == "GovernanceEscalationPacket"),
        {},
    )
    decision_schema = next(
        (record for record in schema_records if record.get("title") == "HumanGovernanceDecisionRecord"),
        {},
    )
    packet_properties = packet_schema.get("properties", {})
    packet_required = packet_schema.get("required", ())
    decision_required = decision_schema.get("required", ())
    packet_all_of = packet_schema.get("allOf", ())
    verified_identity_then = next(
        (
            clause.get("then", {})
            for clause in packet_all_of
            if clause.get("if", {}).get("properties", {}).get("originating_run_identity_status", {}).get("const") == "VERIFIED"
        ),
        {},
    )
    verified_identity_required = verified_identity_then.get("required", ())
    verified_identity_properties = verified_identity_then.get("properties", {})
    identity_qualification_schema = packet_properties.get(IDENTITY_QUALIFICATION_FIELD)
    human_review_schema = packet_properties.get("human_review_required")
    next_action_schema = packet_properties.get("next_allowed_action")
    require(
        IDENTITY_QUALIFICATION_FIELD not in packet_required,
        errors,
        "identity qualification marker must remain optional for UNAVAILABLE_DOCUMENTED packets",
    )
    require(
        IDENTITY_QUALIFICATION_FIELD in verified_identity_required,
        errors,
        "VERIFIED escalation packets must require the identity governance qualification marker",
    )
    require(
        identity_qualification_schema.get("const") == IDENTITY_QUALIFICATION,
        errors,
        "escalation packet identity governance qualification must remain UNQUALIFIED",
    )
    require(
        verified_identity_properties.get(IDENTITY_QUALIFICATION_FIELD, {}).get("const") == IDENTITY_QUALIFICATION,
        errors,
        "VERIFIED escalation packets must require the UNQUALIFIED marker",
    )
    require(
        human_review_schema.get("const") is True
        and next_action_schema.get("const") == "HUMAN_GOVERNANCE_REVIEW",
        errors,
        "escalation packets must remain human-gated",
    )
    require(
        "human_authority_source" in decision_required and "decision" in decision_required,
        errors,
        "human authority must remain a separate decision record",
    )

    for relative, needles in REQUIRED_TEXT.items():
        path = ROOT / relative
        require(path.is_file(), errors, f"missing governed surface: {relative}")
        if not path.is_file():
            continue
        body = path.read_text(encoding="utf-8")
        for needle in needles:
            require(needle in body, errors, f"{relative} missing protected-escalation invariant: {needle}")

    for relative, needles in FORBIDDEN_DUPLICATED_TEXT.items():
        path = ROOT / relative
        require(path.is_file(), errors, f"missing governed surface: {relative}")
        if not path.is_file():
            continue
        body = path.read_text(encoding="utf-8")
        for needle in needles:
            require(
                needle not in body,
                errors,
                f"{relative} must not duplicate protected-escalation detail: {needle}",
            )

    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1

    print("[PASS] protected governance escalation is machine-bound and cross-surface consistent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
