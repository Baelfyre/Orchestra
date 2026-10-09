import json
import subprocess
import sys
import tempfile
from pathlib import Path


def run_case(script_path, project_root, name, args, expected_exit, expected_fields):
    with tempfile.TemporaryDirectory(prefix=f"dagger-guardrail-{name}-") as temp_dir:
        report_path = Path(temp_dir) / "report.json"
        command = [
            sys.executable,
            str(script_path),
            "--project-root",
            str(project_root),
            "--report-file",
            str(report_path),
            *args,
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != expected_exit:
            raise AssertionError(
                f"{name}: expected exit {expected_exit}, got {result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            )
        if "DAGGER_GUARDRAIL_RESULT" not in result.stdout:
            raise AssertionError(f"{name}: missing human-readable summary output")
        if not report_path.is_file():
            raise AssertionError(f"{name}: report file was not created")

        report = json.loads(report_path.read_text(encoding="utf-8"))
        for field_name, expected_value in expected_fields.items():
            actual_value = report.get(field_name)
            if actual_value != expected_value:
                raise AssertionError(
                    f"{name}: expected report[{field_name!r}]={expected_value!r}, got {actual_value!r}"
                )


def main():
    project_root = Path(__file__).resolve().parent.parent
    script_path = project_root / "scripts" / "dagger_guardrail.py"

    cases = [
        (
            "missing_confirmation",
            [
                "--action",
                "delete_file",
                "--target-path",
                "README.md",
                "--dry-run",
                "--rollback-plan",
                "restore from git",
            ],
            1,
            {
                "approval_status": "missing",
                "decision": "blocked",
                "status": "BLOCKED",
            },
        ),
        (
            "missing_rollback",
            [
                "--action",
                "delete_file",
                "--target-path",
                "README.md",
                "--confirm",
                "--dry-run",
            ],
            1,
            {
                "rollback_status": "missing",
                "decision": "blocked",
                "status": "BLOCKED",
            },
        ),
        (
            "out_of_scope_path",
            [
                "--action",
                "delete_file",
                "--target-path",
                "../outside.txt",
                "--confirm",
                "--dry-run",
                "--rollback-plan",
                "restore from backup",
            ],
            1,
            {
                "scope_validation": "invalid",
                "decision": "blocked",
                "status": "BLOCKED",
            },
        ),
        (
            "protected_directory",
            [
                "--action",
                "delete_file",
                "--target-path",
                ".agents/skills/dagger/SKILL.md",
                "--confirm",
                "--dry-run",
                "--rollback-plan",
                "restore from backup",
            ],
            1,
            {
                "scope_validation": "invalid",
                "decision": "blocked",
                "status": "BLOCKED",
            },
        ),
        (
            "valid_dry_run",
            [
                "--action",
                "delete_file",
                "--target-path",
                "README.md",
                "--confirm",
                "--dry-run",
                "--rollback-plan",
                "restore from git",
            ],
            0,
            {
                "dry_run_status": "completed",
                "decision": "allowed",
                "live_execution": "blocked",
                "status": "PASS",
            },
        ),
        (
            "live_execution_blocked",
            [
                "--action",
                "delete_file",
                "--target-path",
                "README.md",
                "--confirm",
                "--rollback-plan",
                "restore from git",
            ],
            1,
            {
                "dry_run_status": "missing",
                "decision": "blocked",
                "live_execution": "blocked",
                "status": "BLOCKED",
            },
        ),
    ]

    failures = []
    for name, args, expected_exit, expected_fields in cases:
        try:
            run_case(script_path, project_root, name, args, expected_exit, expected_fields)
            print(f"[PASS] {name}")
        except AssertionError as exc:
            failures.append(str(exc))
            print(f"[FAIL] {name}")

    if failures:
        print("\n".join(failures), file=sys.stderr)
        sys.exit(1)

    print("All dagger guardrail simulation tests passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
