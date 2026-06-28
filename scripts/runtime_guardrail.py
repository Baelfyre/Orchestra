import os
import sys
import argparse
import re
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import helpers

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-dir", default=helpers.get_project_root())
    parser.add_argument("--staged-only", action="store_true")
    parser.add_argument("--enabled", action="store_true")
    parser.add_argument("--enforce", action="store_true")
    args, _ = parser.parse_known_args()
    
    is_run = args.enabled or os.environ.get('ORCHESTRA_RUN_GUARDRAILS') == 'true'
    is_enforce = args.enforce or os.environ.get('ORCHESTRA_ENFORCE_GUARDRAILS') == 'true'
    
    if not is_run:
        helpers.write_color_host('WARNING', "SKIPPED: Guardrails disabled.")
        sys.exit(0)
        
    helpers.write_color_host('INFO', 'Orchestra Programmatic Guardrail: Commencing scanning...')
    if not is_enforce:
        helpers.write_color_host('INFO', 'Enforcement is disabled (warning-only mode). Warnings will not block commit.')
        
    violations = []
    files_to_scan = []
    
    if args.staged_only:
        import subprocess
        try:
            result = subprocess.run(['git', 'diff', '--name-only', '--cached'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                staged = result.stdout.strip().split('\n')
                for f in staged:
                    full_path = os.path.join(args.target_dir, f)
                    if os.path.isfile(full_path):
                        files_to_scan.append({"Path": full_path, "Relative": f})
        except Exception:
            helpers.write_color_host('WARNING', 'Git diff failed or not a git repo. Scanning target directory recursively instead.')
            
    if not files_to_scan:
        exclude_dirs = ['.git', '.amalgam', 'tests', 'brain']
        exclude_exts = ['.ico', '.png', '.jpg', '.zip', '.tar', '.gz']
        for dirpath, dirnames, filenames in os.walk(args.target_dir):
            dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
            for filename in filenames:
                if filename in ['runtime_guardrail.py', 'runtime-guardrail.ps1']:
                    continue
                ext = os.path.splitext(filename)[1].lower()
                if ext in exclude_exts:
                    continue
                full_path = os.path.join(dirpath, filename)
                relative = os.path.relpath(full_path, args.target_dir)
                files_to_scan.append({"Path": full_path, "Relative": relative})
                
    secret_patterns = {
        'AWS Access Key ID': re.compile(r'\bAKIA[0-9A-Z]{16}\b'),
        'Slack Webhook': re.compile(r'https://hooks\.slack\.com/services/T[A-Z0-9]+/B[A-Z0-9]+/[A-Za-z0-9]+'),
        'Generic API Key': re.compile(r'api[_-]?key\s*[:=]\s*["\'][A-Za-z0-9_\-+=]{16,}["\']', re.IGNORECASE),
        'Private Key Header': re.compile(r'-----BEGIN[ A-Z]+PRIVATE KEY-----')
    }
    
    copyleft_patterns = [re.compile(p, re.IGNORECASE) for p in [r'"gpl', r'"agpl', r'"lgpl', r'"copyleft']]
    pii_patterns = [re.compile(p, re.IGNORECASE) for p in [r'\bSSN\b', r'\bsocial\s+security\b', r'\bcredit\s*card\b', r'\bcard[_-]?number\b']]
    
    destructive_patterns = {
        'Force deletion': re.compile(r'\brm\s+-rf\b', re.IGNORECASE),
        'Destructive Remove-Item': re.compile(r'\bremove-item\b.*\b-force\b', re.IGNORECASE),
        'Raw Disk Formatting': re.compile(r'\bformat-volume\b|\bclear-disk\b', re.IGNORECASE)
    }
    
    unsafe_patterns = {
        'Invoke-Expression': re.compile(r'\binvoke-expression\b|\biex\b', re.IGNORECASE)
    }
    
    legacy_names = [
        'amalgam-conductor', 'cloak-meister', 'scribe-meister', 'clockwork-meister',
        'meister-chronicler', 'acme-overseer', 'hidden-dagger', 'cipher-meister', 'meister-weaver'
    ]
    
    state_path = os.path.join(args.target_dir, ".amalgam", "state.json")
    forbidden_repos = []
    if os.path.isfile(state_path):
        try:
            with open(state_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
                forbidden_repos = state.get('forbidden_repos', [])
        except Exception:
            pass
            
    for item in files_to_scan:
        rel = item['Relative'].replace('\\', '/')
        if re.search(r'runtime[_-]guardrail|VALIDATION\.md', rel):
            continue
            
        try:
            with open(item['Path'], 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            continue
            
        has_pii = False
        
        for i, line in enumerate(lines):
            for key, pattern in secret_patterns.items():
                if pattern.search(line):
                    violations.append(f"SECRET EXPOSURE ({key}) in {item['Relative']}:L{i+1} -> {line.strip()}")
                    
            if re.search(r'package\.json|dependencies|plugin\.json', rel):
                for p in copyleft_patterns:
                    if p.search(line):
                        violations.append(f"COPYLEFT LICENSE DETECTED ({line.strip()}) in {item['Relative']}:L{i+1}. Please confirm compatibility.")
                        
            for p in pii_patterns:
                if p.search(line):
                    has_pii = True
                    violations.append(f"PII SENSITIVE FIELD DETECTED ({line.strip()}) in {item['Relative']}:L{i+1}.")
                    
            for key, pattern in destructive_patterns.items():
                if pattern.search(line):
                    violations.append(f"DESTRUCTIVE OPERATION DETECTED ({key}) in {item['Relative']}:L{i+1} -> {line.strip()}")
                    
            for key, pattern in unsafe_patterns.items():
                if pattern.search(line):
                    violations.append(f"UNSAFE EXECUTION DETECTED ({key}) in {item['Relative']}:L{i+1} -> {line.strip()}")
                    
        if has_pii:
            privacy_docs = ['PrivacyPolicy.md', 'PRIVACY_POLICY.md', 'PRIVACY.md', 'docs/PRIVACY.md', 'docs/governance/PRIVACY.md']
            has_privacy_doc = any(os.path.exists(os.path.join(args.target_dir, doc)) for doc in privacy_docs)
            if not has_privacy_doc:
                violations.append(f"PRIVACY GAPS: PII fields collected in {item['Relative']} but no PRIVACY_POLICY.md file was found.")
                
        for forbidden in forbidden_repos:
            norm_forbidden = forbidden.replace('\\', '/')
            if re.search(re.escape(norm_forbidden), rel):
                violations.append(f"FORBIDDEN TARGET MUTATION in {item['Relative']}: Modifying forbidden repository area '{forbidden}'.")
                
        is_allowed_alias = re.search(r'aliases\.json|commands/|tests/|plugin\.json|\.codex-plugin/plugin\.json|scripts/refresh-installed-integrations\.ps1|README\.md|ROUTING_MAP\.md|docs/project/|DECISION_LOG\.md|SESSION_HANDOFF\.md|skills/conductor/SKILL\.md|examples/plugin-manifest\.example\.json', rel)
        if not is_allowed_alias:
            for ln in legacy_names:
                for i, line in enumerate(lines):
                    if re.search(re.escape(ln), line):
                        violations.append(f"STALE REFERENCE DETECTED (Legacy name '{ln}') in {item['Relative']}:L{i+1} -> {line.strip()}")
                        
    if violations:
        if is_enforce:
            helpers.write_color_host('ERROR', f"Guardrail scan failed with {len(violations)} safety violations:")
            for v in violations:
                helpers.write_color_host('ERROR', f" - {v}")
            print("\n\033[91m[WHAT FAILED] Repository files or changes violated Orchestra's runtime guardrails.\033[0m")
            print("\033[91m[WHY IT FAILED] Active safety checks blocked the operation due to unsafe patterns (e.g. secrets, copyleft licenses, PII leaks, destructive commands, or stale naming references).\033[0m")
            print("\033[93m[HOW TO FIX IT] Review the specific files and line numbers flagged above. Address the violations by removing sensitive strings, cleaning up commands, or replacing legacy names with clean slugs. To run locally without blocking, disable enforcement or omit the --enforce parameter.\033[0m")
            sys.exit(1)
        else:
            helpers.write_color_host('WARNING', f"Guardrail scan found {len(violations)} potential warnings (Warning-Only Mode):")
            for v in violations:
                helpers.write_color_host('WARNING', f" - {v}")
            print("\n\033[93m[WHAT FAILED] Potential safety warnings were detected by the guardrail scanner.\033[0m")
            print("\033[93m[WHY IT FAILED] Staged or changed files contain patterns that would block commits under active enforcement.\033[0m")
            print("\033[96m[HOW TO FIX IT] Address the warning details above. To enforce these rules on commits, set the environment variable: `ORCHESTRA_ENFORCE_GUARDRAILS=true` or run with the `--enforce` parameter.\033[0m")
            sys.exit(0)
            
    helpers.write_color_host('SUCCESS', 'Guardrail scan passed successfully! No safety issues found.')
    sys.exit(0)

if __name__ == "__main__":
    main()
