import copy
import json
import sys
from pathlib import Path


SCHEMA_VERSION = "orchestra-governed-autonomy-modes-v1"
PROFILES = {
    "HUMAN_GOVERNED": {
        "analyze",
        "implement",
        "validate",
        "remediate",
    },
    "SEMI_AUTONOMOUS": {
        "analyze",
        "implement",
        "validate",
        "remediate",
        "stage",
        "commit",
        "push",
        "create_pr",
        "monitor_ci",
    },
    "FULL_AUTONOMOUS": {
        "analyze",
        "implement",
        "validate",
        "remediate",
        "stage",
        "commit",
        "push",
        "create_pr",
        "monitor_ci",
        "merge",
        "advance_phase",
    },
}
PROFILE_RANK = {
    "HUMAN_GOVERNED": 0,
    "SEMI_AUTONOMOUS": 1,
    "FULL_AUTONOMOUS": 2,
}
HARD_BOUNDARIES = {
    "release",
    "deploy",
    "policy_activation",
    "force_push",
    "history_rewrite",
    "destructive_operation",
}
KNOWN_ACTIONS = set().union(*PROFILES.values(), HARD_BOUNDARIES)
DISPOSITIONS = {
    "AUTO_CONTINUE",
    "AUTO_REMEDIATE_AND_REVALIDATE",
    "WAIT_FOR_EVIDENCE",
    "ESCALATE_HUMAN",
    "STOP",
}
WRITE_ACTIONS = {
    "stage",
    "commit",
    "push",
    "create_pr",
    "merge",
    "advance_phase",
}


def selected_profile(snapshot):
    value = snapshot.get("selected_profile")
    return "HUMAN_GOVERNED" if value in (None, "") else str(value)


def evaluate(snapshot):
    profile = selected_profile(snapshot)
    action = str(snapshot.get("action", ""))
    if profile not in PROFILES or action not in KNOWN_ACTIONS:
        return "STOP"
    if snapshot.get("authority_valid") is not True:
        return "STOP"
    if snapshot.get("bypass_used") is not False:
        return "STOP"

    previous = str(snapshot.get("previous_profile", profile))
    if previous not in PROFILES:
        return "STOP"
    if PROFILE_RANK[profile] > PROFILE_RANK[previous] and snapshot.get("increase_authorized") is not True:
        return "ESCALATE_HUMAN"

    parent = snapshot.get("parent_profile")
    if parent is not None:
        if parent not in PROFILES:
            return "STOP"
        if PROFILE_RANK[profile] > PROFILE_RANK[parent]:
            return "ESCALATE_HUMAN"

    if snapshot.get("continuity_matches") is not True:
        return "WAIT_FOR_EVIDENCE"
    if snapshot.get("repository_policy_current") is not True:
        return "WAIT_FOR_EVIDENCE"

    evidence = str(snapshot.get("evidence_state", ""))
    if evidence in {"MISSING", "PENDING", "STALE", "UNVERIFIED"}:
        return "WAIT_FOR_EVIDENCE"
    if evidence == "BOUNDED_FAILURE":
        if (
            action == "remediate"
            and snapshot.get("defect_caused_by_current_change") is True
            and snapshot.get("remediation_in_scope") is True
            and snapshot.get("remediation_allowed") is True
        ):
            return "AUTO_REMEDIATE_AND_REVALIDATE"
        return "STOP"
    if evidence != "GREEN":
        return "STOP"

    if action in HARD_BOUNDARIES:
        return "ESCALATE_HUMAN"

    if action == "merge":
        merge_method = snapshot.get("selected_merge_method")
        if merge_method != "squash":
            return "STOP"
        merge_evidence = snapshot.get("merge_evidence")
        if merge_evidence == "MISSING":
            return "WAIT_FOR_EVIDENCE"
        if merge_evidence != "VERIFIED":
            return "STOP"

    if action in WRITE_ACTIONS and snapshot.get("write_verified") is not True:
        return "WAIT_FOR_EVIDENCE"

    if action not in PROFILES[profile]:
        return "ESCALATE_HUMAN"

    for key in (
        "explicit_grant_actions",
        "repository_allowed_actions",
        "project_allowed_actions",
        "host_capabilities",
    ):
        allowed = snapshot.get(key)
        if not isinstance(allowed, list) or action not in allowed:
            return "ESCALATE_HUMAN"

    return "AUTO_CONTINUE"


def materialize_case(data, case):
    snapshot = copy.deepcopy(data["base_snapshot"])
    snapshot.update(copy.deepcopy(case.get("overrides", {})))
    return snapshot


def validate_fixture(data):
    errors = []
    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must equal {SCHEMA_VERSION}")
    if data.get("profile_actions") != {
        name: sorted(actions) for name, actions in PROFILES.items()
    }:
        errors.append("profile_actions must match the canonical action matrix")
    if data.get("hard_boundaries") != sorted(HARD_BOUNDARIES):
        errors.append("hard_boundaries must match the canonical protected actions")

    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append("cases must be a non-empty list")
        return errors

    seen = set()
    for case in cases:
        case_id = str(case.get("id", ""))
        if not case_id or case_id in seen:
            errors.append("cases must have unique non-empty ids")
            continue
        seen.add(case_id)
        expected = case.get("expected_disposition")
        if expected not in DISPOSITIONS:
            errors.append(f"{case_id}: unknown expected disposition")
            continue
        actual = evaluate(materialize_case(data, case))
        if actual != expected:
            errors.append(f"{case_id}: expected {expected} but evaluator returned {actual}")
    return errors


def validate(root):
    root = Path(root)
    fixture_path = root / "tests/behavior/governed-autonomy-modes-fixtures.json"
    required_docs = {
        "docs/governance/GOVERNED_AUTONOMY_MODES.md": (
            "HUMAN_GOVERNED",
            "SEMI_AUTONOMOUS",
            "FULL_AUTONOMOUS",
            "AUTONOMOUS_CAPABILITY != AUTONOMOUS_AUTHORITY",
            "CHILD_AUTHORITY <= PARENT_AUTHORITY",
            "BYPASS_CAPABILITY != GOVERNANCE_AUTHORIZATION",
            "HUMAN_GOVERNED is the safe default",
        ),
        "docs/governance/GOVERNED_AUTONOMOUS_EXECUTION_PROTOCOL.md": (
            "AUTO_CONTINUE",
            "AUTO_REMEDIATE_AND_REVALIDATE",
            "WAIT_FOR_EVIDENCE",
            "WAIT_FOR_CAPACITY",
            "ESCALATE_HUMAN",
            "STOP",
            "Squash",
            "verified signature",
            "R8",
        ),
        "docs/routing/EXECUTION_MODES_POLICY.md": (
            "Risk Mode != Governance Profile",
            "HUMAN_GOVERNED",
            "SEMI_AUTONOMOUS",
            "FULL_AUTONOMOUS",
        ),
        "skills/conductor/SKILL.md": (
            "Governance Profile Selection Gate",
            "HUMAN_GOVERNED",
            "effective authority preview",
        ),
        "adapters/codex/skills/conductor/SKILL.md": (
            "Governance Profile Selection Gate",
            "HUMAN_GOVERNED",
            "effective authority preview",
        ),
    }
    errors = []
    if not fixture_path.is_file():
        return ["missing governed autonomy modes fixture"]
    try:
        data = json.loads(fixture_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"fixture JSON is invalid: {exc}"]
    errors.extend(validate_fixture(data))
    for relative, terms in required_docs.items():
        path = root / relative
        if not path.is_file():
            errors.append(f"missing required contract file: {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        for term in terms:
            if term not in text:
                errors.append(f"{relative}: missing required term: {term}")
    return errors


def main():
    root = Path(__file__).resolve().parents[1]
    errors = validate(root)
    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1
    print("[PASS] Governed autonomy modes contract is valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
