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
        {"Name": "test_dagger_guardrail.py", "Path": "scripts/test_dagger_guardrail.py"}
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
        warn_exit = subprocess.run(
            [sys.executable, context_script, "--mode", "Implementation Mode", "--context-file", missing_file],
            capture_output=True,
            text=True
        )
        err_exit = subprocess.run(
            [sys.executable, context_script, "--mode", "Release Mode", "--context-file", missing_file],
            capture_output=True,
            text=True
        )

        warn_output = f"{warn_exit.stdout}{warn_exit.stderr}"
        err_output = f"{err_exit.stdout}{err_exit.stderr}"

        if warn_exit.returncode != 0:
            print(f"[91mERROR: Context validator failed in warning mode! (Exit code: {warn_exit.returncode})[0m")
            print(warn_output)
            failed = True
        elif "This is allowed for Implementation Mode" not in warn_output:
            print("[91mERROR: Context validator warning output did not confirm Implementation Mode allowance![0m")
            print(warn_output)
            failed = True
        elif err_exit.returncode != 1:
            print(f"[91mERROR: Context validator did not fail in Release mode! (Exit code: {err_exit.returncode})[0m")
            print(err_output)
            failed = True
        elif "Cannot proceed with Release Mode without context" not in err_output:
            print("[91mERROR: Context validator error output did not confirm Release Mode block![0m")
            print(err_output)
            failed = True
        else:
            print("[92mSUCCESS: Context validator expected-warning path passed.[0m")
            print("[92mSUCCESS: Context validator expected Release Mode block passed.[0m")
            print("[92mSUCCESS: Context validator tests passed.[0m")
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
