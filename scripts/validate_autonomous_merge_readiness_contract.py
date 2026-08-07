import json
import re
import sys
from pathlib import Path

SCHEMA_VERSION = "orchestra-autonomous-merge-readiness-v1"

REQUIRED_CHECKS = (
    ("Governance Check", "governance-check"),
    ("validate", "validate"),
    ("validate", "runtime-tests"),
    ("Cross-platform Validation", "native-windows-latest"),
    ("Cross-platform Validation", "native-ubuntu-latest"),
    ("Cross-platform Validation", "native-macos-latest"),
)

CHECK_STATUSES = {"queued", "in_progress", "completed"}
PASS_CONCLUSION = "success"
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


def evaluate_pre_merge(snapshot):
    if snapshot.get("base_health") != "GREEN":
        return "REMEDIATE_BASELINE_FIRST"

    current_head = str(snapshot.get("current_head_sha", ""))
    if not SHA40.fullmatch(current_head):
        return "BLOCK"

    if snapshot.get("unresolved_blockers", 0) != 0:
        return "BLOCK"

    if snapshot.get("changelog_required") and not snapshot.get("changelog_updated"):
        return "BLOCK"

    mergeable = snapshot.get("mergeable")
    if mergeable is False:
        return "BLOCK"

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
    if snapshot.get("merge_api_result") != "success":
        return "MERGE_STATE_UNVERIFIED"
    if not snapshot.get("canonical_read_completed"):
        return "MERGE_STATE_UNVERIFIED"
    if snapshot.get("pr_merged") is not True:
        return "MERGE_STATE_UNVERIFIED"
    if snapshot.get("main_contains_reviewed_head") is not True:
        return "MERGE_STATE_UNVERIFIED"

    reviewed = str(snapshot.get("reviewed_head_sha", ""))
    canonical_main = str(snapshot.get("canonical_main_sha", ""))
    if not SHA40.fullmatch(reviewed) or not SHA40.fullmatch(canonical_main):
        return "MERGE_STATE_UNVERIFIED"

    return "MERGED_VERIFIED"


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
            actual = evaluate_pre_merge(case["snapshot"])
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
        "NO_CHECK_DATA = WAIT_FOR_EVIDENCE",
        "mergeable",
        "expected_head_sha",
        "MERGED_VERIFIED",
        "canonical remote read",
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
