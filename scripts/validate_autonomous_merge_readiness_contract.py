import copy
import json
import re
import sys
from pathlib import Path

SCHEMA_VERSION = "orchestra-autonomous-merge-readiness-v4"

REQUIRED_CHECKS = (
    ("Governance Check", "governance-check"),
    ("validate", "validate"),
    ("validate", "runtime-tests"),
    ("Cross-platform Validation", "native-windows-latest"),
    ("Cross-platform Validation", "native-ubuntu-latest"),
    ("Cross-platform Validation", "native-macos-latest"),
    ("Required Analysis Compatibility", "Compatibility CodeQL (python)"),
)

REQUIRED_STATUS_CONTEXTS = (
    "governance-check",
    "validate",
    "runtime-tests",
    "native-windows-latest",
    "native-ubuntu-latest",
    "native-macos-latest",
    "Compatibility CodeQL (python)",
)

EXPECTED_RULESET = {
    "required_approvals": 0,
    "dismiss_stale_approvals": True,
    "require_specific_teams": False,
    "require_code_owner_review": False,
    "require_latest_push_approval": False,
    "require_conversation_resolution": True,
    "allowed_merge_methods": ["squash"],
    "require_linear_history": True,
    "require_signed_commits": True,
    "require_pull_request": True,
    "require_status_checks": True,
    "require_branches_up_to_date": True,
    "block_force_pushes": True,
    "restrict_deletions": True,
    "required_status_contexts": list(REQUIRED_STATUS_CONTEXTS),
}

CHECK_STATUSES = {"queued", "in_progress", "completed"}
PASS_CONCLUSION = "success"
ORDINARY_MERGEABLE_STATE = "clean"
PENDING_MERGEABLE_STATES = {"unknown"}
PRE_MERGE_DISPOSITIONS = {
    "READY_FOR_MERGE",
    "WAIT_FOR_EVIDENCE",
    "STALE_EVIDENCE",
    "REMEDIATE_BASELINE_FIRST",
    "BLOCK",
}
POST_MERGE_DISPOSITIONS = {"MERGED_VERIFIED", "MERGE_STATE_UNVERIFIED"}
SHA40 = re.compile(r"^[0-9a-f]{40}$")


def check_key(check):
    return (str(check.get("workflow", "")), str(check.get("job", "")))


def check_token(check):
    return f"{check.get('workflow', '')}/{check.get('job', '')}"


def ruleset_matches(snapshot):
    ruleset = snapshot.get("ruleset")
    if not isinstance(ruleset, dict):
        return False
    return all(ruleset.get(key) == value for key, value in EXPECTED_RULESET.items())


def evaluate_mergeability(snapshot):
    mergeable = snapshot.get("mergeable")
    if mergeable is False:
        return "BLOCK"
    if mergeable is not True:
        return "WAIT_FOR_EVIDENCE"

    mergeable_state = snapshot.get("mergeable_state")
    if not isinstance(mergeable_state, str) or not mergeable_state.strip():
        return "WAIT_FOR_EVIDENCE"

    normalized_state = mergeable_state.strip().lower()
    if normalized_state in PENDING_MERGEABLE_STATES:
        return "WAIT_FOR_EVIDENCE"
    if normalized_state != ORDINARY_MERGEABLE_STATE:
        return "BLOCK"
    return None


def evaluate_pre_merge(snapshot):
    if snapshot.get("base_health") != "GREEN":
        return "REMEDIATE_BASELINE_FIRST"

    current_head = str(snapshot.get("current_head_sha", ""))
    if not SHA40.fullmatch(current_head):
        return "BLOCK"

    if not ruleset_matches(snapshot):
        return "BLOCK"

    if snapshot.get("selected_merge_method") != "squash":
        return "BLOCK"

    if snapshot.get("bypass_used") is not False:
        return "BLOCK"

    if snapshot.get("unresolved_blockers", 0) != 0:
        return "BLOCK"

    if snapshot.get("unresolved_review_threads", 0) != 0:
        return "BLOCK"

    if snapshot.get("changelog_required") and not snapshot.get("changelog_updated"):
        return "BLOCK"

    mergeability_disposition = evaluate_mergeability(snapshot)
    if mergeability_disposition is not None:
        return mergeability_disposition

    if not snapshot.get("head_reconfirmed"):
        return "WAIT_FOR_EVIDENCE"

    checks = snapshot.get("checks")
    if not isinstance(checks, list):
        return "WAIT_FOR_EVIDENCE"

    by_key = {}
    for check in checks:
        key = check_key(check)
        if key in by_key:
            return "BLOCK"
        by_key[key] = check

    for required in REQUIRED_CHECKS:
        check = by_key.get(required)
        if check is None:
            return "WAIT_FOR_EVIDENCE"

        if str(check.get("head_sha", "")) != current_head:
            return "STALE_EVIDENCE"

        status = str(check.get("status", ""))
        if status not in CHECK_STATUSES:
            return "BLOCK"
        if status != "completed":
            return "WAIT_FOR_EVIDENCE"

        if check.get("conclusion") != PASS_CONCLUSION:
            return "BLOCK"

    return "READY_FOR_MERGE"


def evaluate_post_merge(snapshot):
    if snapshot.get("pre_merge_disposition") != "READY_FOR_MERGE":
        return "MERGE_STATE_UNVERIFIED"
    if str(snapshot.get("pre_merge_mergeable_state", "")).strip().lower() != ORDINARY_MERGEABLE_STATE:
        return "MERGE_STATE_UNVERIFIED"
    if snapshot.get("bypass_used") is not False:
        return "MERGE_STATE_UNVERIFIED"
    if snapshot.get("merge_api_result") != "success":
        return "MERGE_STATE_UNVERIFIED"
    if not snapshot.get("canonical_read_completed"):
        return "MERGE_STATE_UNVERIFIED"
    if snapshot.get("pr_merged") is not True:
        return "MERGE_STATE_UNVERIFIED"
    if snapshot.get("merge_method") != "squash":
        return "MERGE_STATE_UNVERIFIED"

    reviewed = str(snapshot.get("reviewed_head_sha", ""))
    canonical_main = str(snapshot.get("canonical_main_sha", ""))
    reviewed_tree = str(snapshot.get("reviewed_tree_sha", ""))
    canonical_tree = str(snapshot.get("canonical_tree_sha", ""))
    pre_merge_base = str(snapshot.get("pre_merge_base_sha", ""))
    canonical_parent = str(snapshot.get("canonical_parent_sha", ""))

    for value in (
        reviewed,
        canonical_main,
        reviewed_tree,
        canonical_tree,
        pre_merge_base,
        canonical_parent,
    ):
        if not SHA40.fullmatch(value):
            return "MERGE_STATE_UNVERIFIED"

    if reviewed_tree != canonical_tree:
        return "MERGE_STATE_UNVERIFIED"
    if snapshot.get("content_diff_empty") is not True:
        return "MERGE_STATE_UNVERIFIED"
    if canonical_parent != pre_merge_base:
        return "MERGE_STATE_UNVERIFIED"
    if snapshot.get("canonical_signature_verified") is not True:
        return "MERGE_STATE_UNVERIFIED"

    return "MERGED_VERIFIED"


def materialize_pre_merge_case(data, case):
    snapshot = copy.deepcopy(data["base_snapshot"])

    for key, value in case.get("overrides", {}).items():
        snapshot[key] = copy.deepcopy(value)

    ruleset_overrides = case.get("ruleset_overrides", {})
    if ruleset_overrides:
        snapshot.setdefault("ruleset", {}).update(copy.deepcopy(ruleset_overrides))

    remove_check = case.get("remove_check")
    if remove_check:
        snapshot["checks"] = [
            item for item in snapshot.get("checks", [])
            if check_token(item) != remove_check
        ]

    check_overrides = case.get("check_overrides", {})
    if check_overrides:
        for check in snapshot.get("checks", []):
            patch = check_overrides.get(check_token(check))
            if patch:
                check.update(copy.deepcopy(patch))

    return snapshot


def validate_fixtures(data):
    errors = []

    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must equal {SCHEMA_VERSION}")

    declared = data.get("required_checks")
    expected_declared = [
        {"workflow": workflow, "job": job} for workflow, job in REQUIRED_CHECKS
    ]
    if declared != expected_declared:
        errors.append(
            "required_checks must match the canonical exact required-check inventory"
        )

    if data.get("expected_ruleset") != EXPECTED_RULESET:
        errors.append("expected_ruleset must match the canonical Protect main profile")

    base_snapshot = data.get("base_snapshot")
    if not isinstance(base_snapshot, dict):
        errors.append("base_snapshot must be an object")
    elif evaluate_pre_merge(base_snapshot) != "READY_FOR_MERGE":
        errors.append("base_snapshot must represent a fully green ready-to-merge state")

    cases = data.get("pre_merge_cases")
    if not isinstance(cases, list) or not cases:
        errors.append("pre_merge_cases must be a non-empty list")
    else:
        seen = set()
        for case in cases:
            case_id = str(case.get("id", ""))
            if not case_id or case_id in seen:
                errors.append("pre_merge_cases must use unique non-empty ids")
                continue
            seen.add(case_id)
            expected = case.get("expected_disposition")
            if expected not in PRE_MERGE_DISPOSITIONS:
                errors.append(f"{case_id}: unknown expected pre-merge disposition")
                continue
            snapshot = materialize_pre_merge_case(data, case)
            actual = evaluate_pre_merge(snapshot)
            if actual != expected:
                errors.append(
                    f"{case_id}: expected {expected} but evaluator returned {actual}"
                )

    post_cases = data.get("post_merge_cases")
    if not isinstance(post_cases, list) or not post_cases:
        errors.append("post_merge_cases must be a non-empty list")
    else:
        seen = set()
        for case in post_cases:
            case_id = str(case.get("id", ""))
            if not case_id or case_id in seen:
                errors.append("post_merge_cases must use unique non-empty ids")
                continue
            seen.add(case_id)
            expected = case.get("expected_disposition")
            if expected not in POST_MERGE_DISPOSITIONS:
                errors.append(f"{case_id}: unknown expected post-merge disposition")
                continue
            actual = evaluate_post_merge(case["snapshot"])
            if actual != expected:
                errors.append(
                    f"{case_id}: expected {expected} but evaluator returned {actual}"
                )

    return errors


def validate(root):
    root = Path(root)
    fixture_path = root / "tests/behavior/autonomous-merge-readiness-fixtures.json"
    protocol_path = root / "docs/governance/AUTONOMOUS_MERGE_READINESS_PROTOCOL.md"
    errors = []

    if not fixture_path.is_file():
        errors.append("missing autonomous merge readiness fixture file")
        return errors
    if not protocol_path.is_file():
        errors.append("missing autonomous merge readiness protocol")
        return errors

    try:
        data = json.loads(fixture_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"fixture JSON is invalid: {exc}")
        return errors

    errors.extend(validate_fixtures(data))

    protocol = protocol_path.read_text(encoding="utf-8")
    required_terms = (
        "Platform capability is not governance readiness",
        "PLATFORM_CAN_EXECUTE != GOVERNANCE_READY_TO_TRANSITION",
        "GITHUB_CAN_MERGE != GOVERNANCE_READY_TO_MERGE",
        "API_SUCCESS != VERIFIED_STATE",
        "NO_EVIDENCE != APPROVAL",
        "BYPASS_CAPABILITY != GOVERNANCE_AUTHORIZATION",
        "NO_CHECK_DATA = WAIT_FOR_EVIDENCE",
        "MERGEABLE_STATE_BLOCKED = BLOCK",
        "DUPLICATE_REQUIRED_STATUS_CONTEXT = BLOCK",
        "Compatibility CodeQL (python)",
        "mergeable_state == clean",
        "Squash",
        "expected_head_sha",
        "MERGED_VERIFIED",
        "canonical remote read",
        "canonical tree",
        "verified signature",
        "red canonical baseline",
    )
    for term in required_terms:
        if term not in protocol:
            errors.append(f"protocol missing required fail-closed term: {term}")

    return errors


def main():
    root = Path(__file__).resolve().parents[1]
    errors = validate(root)
    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1
    print("[PASS] Autonomous merge readiness contract is valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
