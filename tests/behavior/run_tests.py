import os
import sys
import subprocess
import uuid
import shutil
import tempfile

def main():
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    scripts = [
        {"Name": "validate_structure.py", "Path": "scripts/validate_structure.py"},
        {"Name": "validate_manifest.py", "Path": "scripts/validate_manifest.py"},
        {"Name": "validate_ide_packaging.py", "Path": "scripts/validate_ide_packaging.py"},
        {"Name": "test_governance_check.py", "Path": "scripts/test_governance_check.py"},
        {"Name": "check_stale_references.py", "Path": "scripts/check_stale_references.py"},
        {"Name": "validate_codex_export.py", "Path": "adapters/codex/validate_codex_export.py"},
        {"Name": "evaluate_governance.py", "Path": "tests/behavior/evaluate_governance.py"},
        {"Name": "runtime_guardrail.py", "Path": "scripts/runtime_guardrail.py"},
        {"Name": "test_dagger_guardrail.py", "Path": "scripts/test_dagger_guardrail.py"},
        {"Name": "test_prompt_load_thresholds.py", "Path": "tests/behavior/test_prompt_load_thresholds.py"},
        {"Name": "validate_artificer_internal.py", "Path": "scripts/validate_artificer_internal.py"},
        {"Name": "validate_artificer_records.py", "Path": "scripts/validate_artificer_records.py"},
        {"Name": "test_artificer_internal.py", "Path": "tests/behavior/test_artificer_internal.py"},
        {"Name": "test_artificer_records.py", "Path": "tests/behavior/test_artificer_records.py"}
    ]
    
    failed = False
    
    for s in scripts:
        print("========================================")
        print(f"Running {s['Name']}...")
        print("========================================")
        
        full_path = os.path.join(root, s["Path"].replace('/', os.sep))
        result = subprocess.run([sys.executable, full_path])
        
        if result.returncode != 0:
            print(f"\033[91mERROR: {s['Name']} failed with exit code {result.returncode}!\033[0m")
            failed = True
        else:
            print(f"\033[92mSUCCESS: {s['Name']} passed.\033[0m")
    
    # Regression Tests
    print("\n========================================")
    print("Running Guardrail & Lock Regression Tests...")
    print("========================================")
    
    guardrail_script = os.path.join(root, "scripts", "runtime_guardrail.py")
    lock_script = os.path.join(root, "scripts", "manage_state_lock.py")
    sys.path.insert(0, os.path.join(root, "scripts"))
    import runtime_guardrail
    
    # Test 1: Guardrail enforcement
    temp_dir = os.path.join(tempfile.gettempdir(), f"orchestra-guardrail-test-{uuid.uuid4()}")
    os.makedirs(temp_dir, exist_ok=True)
    try:
        violation_file = os.path.join(temp_dir, "mock_violation.txt")
        with open(violation_file, "w", encoding="utf-8") as f:
            f.write("legacy skill name = amalgam-conductor")
        
        enforce_result = subprocess.run([sys.executable, guardrail_script, "--target-dir", temp_dir, "--enabled", "--enforce"], capture_output=True, text=True)
        warn_result = subprocess.run([sys.executable, guardrail_script, "--target-dir", temp_dir, "--enabled"], capture_output=True, text=True)
        
        redacted_violation = runtime_guardrail.format_suppressed_guardrail_notice()
        if enforce_result.returncode != 1:
            print(f"\033[91mERROR: Guardrail did not fail on violation in enforce mode! (Exit code: {enforce_result.returncode})\033[0m")
            failed = True
        elif warn_result.returncode != 0:
            print(f"\033[91mERROR: Guardrail failed on warning-only mode! (Exit code: {warn_result.returncode})\033[0m")
            failed = True
        elif "Details suppressed" not in redacted_violation:
            print("\033[91mERROR: Guardrail formatter did not suppress details!\033[0m")
            failed = True
        else:
            print("\033[92mSUCCESS: Guardrail warning-first, enforcement, and redaction tests passed.\033[0m")
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            
    # Test 2: Project Context Validator
    context_script = os.path.join(root, "scripts", "validate_project_context.py")
    temp_dir2 = os.path.join(tempfile.gettempdir(), f"orchestra-context-test-{uuid.uuid4()}")
    os.makedirs(temp_dir2, exist_ok=True)
    try:
        missing_file = os.path.join(temp_dir2, "MISSING.md")
        strict_file = os.path.join(temp_dir2, "STRICT.md")
        with open(strict_file, "w", encoding="utf-8") as f:
            f.write("## Governance Level\nStrict-Governed\n\n## Project Name\nDemo\n")

        warn_exit = subprocess.run(
            [sys.executable, context_script, "--mode", "Implementation Mode", "--context-file", missing_file],
            capture_output=True,
            text=True
        )
        release_warn_exit = subprocess.run(
            [sys.executable, context_script, "--mode", "Release Mode", "--context-file", missing_file],
            capture_output=True,
            text=True
        )
        strict_missing_exit = subprocess.run(
            [sys.executable, context_script, "--mode", "strict-governed", "--context-file", missing_file],
            capture_output=True,
            text=True
        )
        strict_incomplete_exit = subprocess.run(
            [sys.executable, context_script, "--context-file", strict_file],
            capture_output=True,
            text=True
        )

        warn_output = f"{warn_exit.stdout}{warn_exit.stderr}"
        release_warn_output = f"{release_warn_exit.stdout}{release_warn_exit.stderr}"
        strict_missing_output = f"{strict_missing_exit.stdout}{strict_missing_exit.stderr}"
        strict_incomplete_output = f"{strict_incomplete_exit.stdout}{strict_incomplete_exit.stderr}"

        if warn_exit.returncode != 0:
            print(f"\u001b[91mERROR: Context validator failed in advisory warning mode! (Exit code: {warn_exit.returncode})\u001b[0m")
            print(warn_output)
            failed = True
        elif "Defaulting to Advisory governance" not in warn_output:
            print("\u001b[91mERROR: Context validator warning output did not confirm advisory fallback!\u001b[0m")
            print(warn_output)
            failed = True
        elif release_warn_exit.returncode != 0:
            print(f"\u001b[91mERROR: Context validator blocked Release Mode without explicit strict governance! (Exit code: {release_warn_exit.returncode})\u001b[0m")
            print(release_warn_output)
            failed = True
        elif "Proceeding for Release Mode." not in release_warn_output:
            print("\u001b[91mERROR: Context validator warning output did not preserve non-blocking Release Mode behavior!\u001b[0m")
            print(release_warn_output)
            failed = True
        elif strict_missing_exit.returncode != 1:
            print(f"\u001b[91mERROR: Context validator did not fail for missing strict-governed context! (Exit code: {strict_missing_exit.returncode})\u001b[0m")
            print(strict_missing_output)
            failed = True
        elif "Strict-Governed repositories require project context" not in strict_missing_output:
            print("\u001b[91mERROR: Context validator strict missing-file output was not specific enough!\u001b[0m")
            print(strict_missing_output)
            failed = True
        elif strict_incomplete_exit.returncode != 1:
            print(f"\u001b[91mERROR: Context validator did not fail for incomplete strict-governed context! (Exit code: {strict_incomplete_exit.returncode})\u001b[0m")
            print(strict_incomplete_output)
            failed = True
        elif "Missing required sections" not in strict_incomplete_output or "Project Purpose" not in strict_incomplete_output:
            print("\u001b[91mERROR: Context validator strict missing-section output did not list the required sections!\u001b[0m")
            print(strict_incomplete_output)
            failed = True
        else:
            print("\u001b[92mSUCCESS: Context validator advisory fallback path passed.\u001b[0m")
            print("\u001b[92mSUCCESS: Context validator non-blocking Release Mode path passed.\u001b[0m")
            print("\u001b[92mSUCCESS: Context validator strict-governed missing-file block passed.\u001b[0m")
            print("\u001b[92mSUCCESS: Context validator strict-governed missing-section block passed.\u001b[0m")
            print("\u001b[92mSUCCESS: Context validator tests passed.\u001b[0m")
    finally:
        if os.path.exists(temp_dir2):
            shutil.rmtree(temp_dir2)
            
    # Test 3: State Locking tests
    subprocess.run([sys.executable, lock_script, "--action", "Release"], stdout=subprocess.DEVNULL)
    acquire_result = subprocess.run([sys.executable, lock_script, "--action", "Acquire", "--pid", str(os.getpid())], stdout=subprocess.DEVNULL)
    check_result = subprocess.run([sys.executable, lock_script, "--action", "Check"], stdout=subprocess.DEVNULL)
    release_result = subprocess.run([sys.executable, lock_script, "--action", "Release"], stdout=subprocess.DEVNULL)
    check_result_after = subprocess.run([sys.executable, lock_script, "--action", "Check"], stdout=subprocess.DEVNULL)
    
    if acquire_result.returncode != 0:
        print("\033[91mERROR: Lock acquisition failed!\033[0m")
        failed = True
    elif check_result.returncode != 1:
        print(f"\033[91mERROR: Lock collision check did not detect active lock! (Exit code: {check_result.returncode})\033[0m")
        failed = True
    elif release_result.returncode != 0:
        print("\033[91mERROR: Lock release failed!\033[0m")
        failed = True
    elif check_result_after.returncode != 0:
        print(f"\033[91mERROR: Lock check still active after release! (Exit code: {check_result_after.returncode})\033[0m")
        failed = True
    else:
        print("\033[92mSUCCESS: Lock acquisition, collision protection, and release tests passed.\033[0m")
        
    print("\n========================================")
    if failed:
        print("\033[91mValidation suite FAILED.\033[0m")
        sys.exit(1)
    else:
        print("\033[92mValidation suite PASSED!\033[0m")
        sys.exit(0)

if __name__ == "__main__":
    main()
