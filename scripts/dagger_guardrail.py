import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

PROTECTED_SEGMENTS = {".git", ".agents"}
DESTRUCTIVE_KEYWORDS = (
    "delete",
    "destroy",
    "remove",
    "overwrite",
    "corrupt",
    "drop",
    "truncate",
    "wipe",
    "purge",
    "format",
    "rename",
    "move",
)


def get_default_project_root():
    return Path(__file__).resolve().parent.parent


def is_absolute_input(path_text):
    return (
        Path(path_text).is_absolute()
        or bool(re.match(r"^[A-Za-z]:[\\/]", path_text))
        or path_text.startswith("\\\\")
        or path_text.startswith("//")
    )


def classify_action(action_text):
    normalized = action_text.strip().lower()
    if not normalized:
        return "unclear"
    if any(keyword in normalized for keyword in DESTRUCTIVE_KEYWORDS):
        return "destructive"
    return "unclear"


def validate_scope(project_root, target_path):
    if not target_path.strip():
        return "invalid", None, "Target path is missing."

    if is_absolute_input(target_path):
        return "invalid", None, "Absolute target paths are blocked. Use a repository-relative path."

    raw_target = Path(target_path)
    if any(part == ".." for part in raw_target.parts):
        return "invalid", None, "Parent traversal is blocked."

    resolved_target = (project_root / raw_target).resolve()
    try:
        relative_target = resolved_target.relative_to(project_root)
    except ValueError:
        return "invalid", None, "Target path escapes the approved project root."

    if any(part in PROTECTED_SEGMENTS for part in relative_target.parts):
        return "invalid", None, "Protected directories (.git, .agents) are out of scope."

    return "valid", str(relative_target).replace("\\", "/"), ""


def build_report(args):
    project_root = Path(args.project_root).resolve() if args.project_root else get_default_project_root()
    action_type = classify_action(args.action)
    scope_validation, normalized_target, scope_reason = validate_scope(project_root, args.target_path)
    timestamp = datetime.now(timezone.utc).isoformat()

    approval_status = "present" if args.confirm else "missing"
    dry_run_status = "completed" if args.dry_run else "missing"
    rollback_status = "present" if args.rollback_plan and args.rollback_plan.strip() else "missing"
    decision = "allowed"
    status = "PASS"
    reasons = []
    remediation = []

    if action_type != "destructive":
        decision = "blocked"
        status = "BLOCKED"
        reasons.append("Action type is unclear. Dagger only validates explicitly destructive requests.")
        remediation.append("Use a destructive action label such as delete_file or overwrite_fixture.")

    if approval_status != "present":
        decision = "blocked"
        status = "BLOCKED"
        reasons.append("Explicit confirmation is missing.")
        remediation.append("Re-run with --confirm only after manual approval is present.")

    if scope_validation != "valid":
        decision = "blocked"
        status = "BLOCKED"
        reasons.append(scope_reason)
        remediation.append("Use a repository-relative target inside the approved project root.")

    if rollback_status != "present":
        decision = "blocked"
        status = "BLOCKED"
        reasons.append("Rollback or backup instructions are missing.")
        remediation.append("Provide --rollback-plan with recovery steps before requesting validation.")

    if dry_run_status != "completed":
        decision = "blocked"
        status = "BLOCKED"
        reasons.append("Phase 2 is simulation-only. Live destructive execution is blocked.")
        remediation.append("Re-run with --dry-run. Live destructive execution remains blocked until a later phase.")

    if decision == "allowed":
        reasons.append("Simulation-only request passed all required guardrail checks.")
        remediation.append("Keep Dagger in dry-run mode. Do not execute destructive operations from this script.")

    report = {
        "timestamp": timestamp,
        "status": status,
        "action_type": action_type,
        "action": args.action,
        "target_path": args.target_path,
        "normalized_target_path": normalized_target,
        "project_root": str(project_root),
        "scope_validation": scope_validation,
        "approval_status": approval_status,
        "dry_run_status": dry_run_status,
        "rollback_status": rollback_status,
        "decision": decision,
        "reason": " ".join(reasons),
        "remediation": remediation,
        "execution_mode": "validation_only",
        "live_execution": "blocked",
        "report_version": 2,
    }
    return report


def write_report(report, report_file):
    report_path = Path(report_file)
    if not report_path.is_absolute():
        report_path = Path(report["project_root"]) / report_path
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report_path


def print_summary(report, report_path):
    print("DAGGER_GUARDRAIL_RESULT")
    print("")
    print(f"Status: {report['status']}")
    print(f"Action Type: {report['action_type']}")
    print(f"Target Path: {report['target_path']}")
    print(f"Scope Validation: {report['scope_validation']}")
    print(f"Approval: {report['approval_status']}")
    print(f"Dry Run: {report['dry_run_status']}")
    print(f"Rollback: {report['rollback_status']}")
    print(f"Decision: {report['decision']}")
    print(f"Reason: {report['reason']}")
    print("Remediation:")
    for item in report["remediation"]:
        print(f"- {item}")
    print(f"Report File: {report_path}")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Validate Dagger destructive-action requests. This script does not execute destructive "
            "operations. Phase 2 is simulation-only and blocks live destructive execution."
        )
    )
    parser.add_argument("--action", required=True, help="Destructive action label, for example delete_file or corrupt_fixture.")
    parser.add_argument("--target-path", required=True, help="Repository-relative target path for the requested action.")
    parser.add_argument("--project-root", help="Optional project root override for CI or local execution.")
    parser.add_argument("--confirm", action="store_true", help="Marks that explicit manual approval is present.")
    parser.add_argument("--dry-run", action="store_true", help="Required for Phase 2. Without it, the request is blocked.")
    parser.add_argument("--rollback-plan", help="Required rollback or backup instructions. The value is not echoed in reports.")
    parser.add_argument(
        "--report-file",
        default="artifacts/dagger_guardrail_report.json",
        help="JSON report output path. Relative paths are resolved from the project root.",
    )

    args, _ = parser.parse_known_args()

    report = build_report(args)
    report_path = write_report(report, args.report_file)
    print_summary(report, report_path)
    sys.exit(0 if report["decision"] == "allowed" else 1)


if __name__ == "__main__":
    main()
