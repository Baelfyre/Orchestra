import os
import json
import subprocess
import tempfile
import sys

def run_runner(fixture_path):
    runner_script = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "router_benchmark_runner.py")
    result = subprocess.run(
        [sys.executable, runner_script, fixture_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return result.returncode

def test_negative_cases():
    valid_fixture_path = os.path.join(os.path.dirname(__file__), "..", "fixtures", "router_benchmarks.json")
    
    with open(valid_fixture_path, "r", encoding="utf-8") as f:
        valid_data = json.load(f)

    # Base valid single benchmark case to reuse
    base_case = {
        "case_id": "BM-TEMP",
        "request_type": "test",
        "expected_mode": "STANDARD",
        "expected_skill_route": "ponytail",
        "required_context": ["a"],
        "excluded_context": ["b"],
        "governance_status": "NOT_REQUIRED",
        "pass_criteria": "pass"
    }
    
    # helper to generate 20 cases
    def generate_20_cases(override_case=None):
        cases = []
        for i in range(20):
            case = base_case.copy()
            case["case_id"] = f"BM-{i}"
            if i == 0 and override_case:
                case.update(override_case)
            cases.append(case)
        # Ensure at least one DESTRUCTIVE for coverage requirement
        cases[-1]["expected_mode"] = "DESTRUCTIVE"
        return cases

    # 1. Valid fixture should exit 0
    print("[TEST] Valid fixture")
    assert run_runner(valid_fixture_path) == 0, "Valid fixture failed"

    negative_cases = [
        ("missing schema_version", {"benchmarks": generate_20_cases()}),
        ("wrong schema_version", {"schema_version": "2.0", "benchmarks": generate_20_cases()}),
        ("missing benchmarks key", {"schema_version": "1.0"}),
        ("benchmarks is not a list", {"schema_version": "1.0", "benchmarks": {}}),
        ("duplicate case_id", {"schema_version": "1.0", "benchmarks": generate_20_cases({"case_id": "BM-1"})}),
        ("missing required field", {"schema_version": "1.0", "benchmarks": generate_20_cases()}),
        ("invalid expected_mode", {"schema_version": "1.0", "benchmarks": generate_20_cases({"expected_mode": "INVALID"})}),
        ("invalid governance_status", {"schema_version": "1.0", "benchmarks": generate_20_cases({"governance_status": "INVALID"})}),
        ("required_context is not a list", {"schema_version": "1.0", "benchmarks": generate_20_cases({"required_context": "string"})}),
        ("excluded_context is not a list", {"schema_version": "1.0", "benchmarks": generate_20_cases({"excluded_context": "string"})}),
        ("empty pass_criteria", {"schema_version": "1.0", "benchmarks": generate_20_cases({"pass_criteria": "   "})}),
        ("benchmark count not equal to 20", {"schema_version": "1.0", "benchmarks": generate_20_cases()[:-1]}),
    ]
    
    # Fix the missing required field test
    cases_missing_field = generate_20_cases()
    del cases_missing_field[0]["request_type"]
    negative_cases[5] = ("missing required field", {"schema_version": "1.0", "benchmarks": cases_missing_field})

    failures = 0
    with tempfile.TemporaryDirectory() as tmpdir:
        for idx, (desc, data) in enumerate(negative_cases):
            tmp_path = os.path.join(tmpdir, f"test_{idx}.json")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f)
            
            print(f"[TEST] Negative case: {desc}")
            rc = run_runner(tmp_path)
            if rc == 0:
                print(f"  [FAIL] Expected failure for '{desc}', but got exit code 0")
                failures += 1
            else:
                print(f"  [PASS] Failed correctly for '{desc}' (exit {rc})")

    if failures > 0:
        print(f"\n[SUMMARY] {failures} negative cases failed to trigger an error.")
        sys.exit(1)
        
    print("\n[SUCCESS] All negative validation tests passed.")

if __name__ == "__main__":
    test_negative_cases()
