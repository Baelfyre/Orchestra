import subprocess
import sys
import re
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[2]
    checker = root / "scripts" / "check_prompt_load_thresholds.py"
    result = subprocess.run(
        [sys.executable, str(checker)],
        cwd=root,
        capture_output=True,
        text=True,
    )
    output = f"{result.stdout}{result.stderr}"
    required_terms = [
        "Group A:",
        "Group B:",
        "Group C:",
        "Group D:",
        "Grand Total:",
        "Conductor:",
        "--- Largest Contributors ---",
        "docs/performance/PROMPT_LOAD_THRESHOLD_POLICY.md",
        "advisory/report-only",
    ]
    missing = [term for term in required_terms if term not in output]
    missing_statuses = [
        group for group in ("Group B", "Group C")
        if not re.search(rf"\[(?:PASS|EXCEEDED)\] {group}", output)
    ]
    if result.returncode != 0 or missing or missing_statuses:
        print("Prompt-load threshold regression failed.")
        print(f"Exit code: {result.returncode}")
        if missing:
            print(f"Missing output: {', '.join(missing)}")
        if missing_statuses:
            print(f"Missing threshold statuses: {', '.join(missing_statuses)}")
        print(output)
        return 1
    print("Prompt-load threshold reporting regression passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
