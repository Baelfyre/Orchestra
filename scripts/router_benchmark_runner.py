#!/usr/bin/env python3
import sys
import json
import os

# Note: This runner validates benchmark definitions, not live model behavior.
# It ensures the benchmark structure aligns with ROUTER_VALIDATION_BENCHMARKS.md.

REQUIRED_FIELDS = [
    "case_id",
    "request_type",
    "expected_mode",
    "expected_skill_route",
    "required_context",
    "excluded_context",
    "governance_status",
    "pass_criteria"
]

VALID_MODES = {"FAST", "STANDARD", "GOVERNED", "AUDIT", "DESTRUCTIVE"}
VALID_GOVERNANCE_STATUSES = {"NOT_REQUIRED", "CONDITIONAL", "REQUIRED", "BLOCKED_PENDING_AUTHORIZATION"}

def main():
    print("=" * 60)
    print(" Router Benchmark Definition Runner")
    print(" Note: Validates structure, NOT live model routing.")
    print("=" * 60)

    fixture_path = os.path.join(os.path.dirname(__file__), "..", "tests", "fixtures", "router_benchmarks.json")

    try:
        with open(fixture_path, "r", encoding="utf-8") as f:
            fixture_data = json.load(f)

        if not isinstance(fixture_data, dict):
            print(f"[ERROR] Fixture {fixture_path} root must be a dictionary")
            sys.exit(1)

        if "schema_version" not in fixture_data:
            print(f"[ERROR] Fixture {fixture_path} is missing schema_version")
            sys.exit(1)

        if fixture_data["schema_version"] != "1.0":
            print(f"[ERROR] Fixture {fixture_path} schema_version must be '1.0'")
            sys.exit(1)

        if "benchmarks" not in fixture_data:
            print(f"[ERROR] Fixture {fixture_path} is missing benchmarks list")
            sys.exit(1)

        if not isinstance(fixture_data["benchmarks"], list):
            print(f"[ERROR] Fixture {fixture_path} 'benchmarks' must be a list")
            sys.exit(1)

        BENCHMARK_CASES = fixture_data["benchmarks"]
    except Exception as e:
        print(f"[ERROR] Failed to load {fixture_path}: {e}")
        sys.exit(1)

    total_cases = len(BENCHMARK_CASES)
    mode_coverage = {}
    governance_coverage = {}
    destructive_coverage = 0
    case_ids = set()
    errors = 0

    for idx, case in enumerate(BENCHMARK_CASES):
        missing = [f for f in REQUIRED_FIELDS if f not in case]
        if missing:
            print(f"[ERROR] Case index {idx} missing fields: {missing}")
            errors += 1
            continue

        case_id = case.get("case_id")
        if case_id in case_ids:
            print(f"[ERROR] Case index {idx} has duplicate case_id: {case_id}")
            errors += 1
        case_ids.add(case_id)

        mode = case.get("expected_mode")
        if mode not in VALID_MODES:
            print(f"[ERROR] Case index {idx} ({case_id}) has invalid expected_mode: {mode}")
            errors += 1
        mode_coverage[mode] = mode_coverage.get(mode, 0) + 1

        gov = case.get("governance_status")
        if gov not in VALID_GOVERNANCE_STATUSES:
            print(f"[ERROR] Case index {idx} ({case_id}) has invalid governance_status: {gov}")
            errors += 1
        governance_coverage[gov] = governance_coverage.get(gov, 0) + 1

        req_ctx = case.get("required_context")
        if not isinstance(req_ctx, list):
            print(f"[ERROR] Case index {idx} ({case_id}) required_context must be a list")
            errors += 1

        ex_ctx = case.get("excluded_context")
        if not isinstance(ex_ctx, list):
            print(f"[ERROR] Case index {idx} ({case_id}) excluded_context must be a list")
            errors += 1

        pass_crit = case.get("pass_criteria")
        if not pass_crit or not isinstance(pass_crit, str) or not pass_crit.strip():
            print(f"[ERROR] Case index {idx} ({case_id}) pass_criteria must be a non-empty string")
            errors += 1

        if mode == "DESTRUCTIVE" or gov == "BLOCKED_PENDING_AUTHORIZATION":
            destructive_coverage += 1

    print(f"\n[REPORT] Validating {total_cases} Benchmark Definitions...")

    if errors > 0:
        print(f"[FAIL] Found {errors} structural errors in definitions.")
        sys.exit(1)

    print(f"[PASS] All {total_cases} cases contain required fields and are structurally valid.")

    print("\n--- Coverage Summaries ---")
    print("Mode Coverage:")
    for m, c in mode_coverage.items():
        print(f"  - {m}: {c}")

    print("\nGovernance Coverage:")
    for g, c in governance_coverage.items():
        print(f"  - {g}: {c}")

    print(f"\nDestructive-Operation Coverage: {destructive_coverage} cases")
    print("=" * 60)

    if destructive_coverage == 0:
        print("[ERROR] No destructive-operation benchmarks found! Failing.")
        sys.exit(1)

    if total_cases != 12:
        print(f"[ERROR] Expected exactly 12 benchmark cases, found {total_cases}.")
        sys.exit(1)

    print("[SUCCESS] Benchmark definitions are structurally valid.")
    sys.exit(0)

if __name__ == "__main__":
    main()
