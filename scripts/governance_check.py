import os
import json
import fnmatch
import subprocess
import sys


SIGNIFICANT_CHANGE_PATTERNS = [
    ".github/workflows/**",
    "scripts/**",
    "skills/**",
    "commands/**",
    "templates/**",
    "docs/governance/**",
    "docs/CONTRIBUTING.md",
    "plugin.json",
    "tests/**",
]

IGNORED_CHANGE_PATTERNS = [
    ".agents/**",
    ".amalgam/**",
    "artifacts/**",
    "__pycache__/**",
    "*.log",
    "*.tmp",
]


def run_git(repo_root, *args):
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )


def normalize_paths(paths):
    normalized = []
    for path in paths:
        cleaned = path.strip().replace("\\", "/")
        if cleaned:
            normalized.append(cleaned)
    return normalized


def get_changed_paths(repo_root, *args):
    result = run_git(repo_root, *args)
    if result.returncode != 0:
        return None
    return normalize_paths(result.stdout.splitlines())


def is_ignored_change(path):
    return any(fnmatch.fnmatch(path, pattern) for pattern in IGNORED_CHANGE_PATTERNS)


def is_significant_change(path):
    if path == "CHANGELOG.md" or is_ignored_change(path):
        return False
    return any(fnmatch.fnmatch(path, pattern) for pattern in SIGNIFICANT_CHANGE_PATTERNS)


def get_changelog_freshness(repo_root):
    if run_git(repo_root, "rev-parse", "--is-inside-work-tree").returncode != 0:
        return None, None, "Git repository context is unavailable. CHANGELOG.md freshness could not be verified."

    diff_candidates = [
        ("origin/main...HEAD", ("diff", "--name-only", "origin/main...HEAD")),
        ("HEAD~1..HEAD", ("diff", "--name-only", "HEAD~1..HEAD")),
    ]

    comparison_label = None
    committed_changes = None
    for label, args in diff_candidates:
        committed_changes = get_changed_paths(repo_root, *args)
        if committed_changes is not None:
            comparison_label = label
            break

    if committed_changes is None:
        return None, None, "Git history is unavailable. CHANGELOG.md freshness could not be verified."

    working_tree_changes = get_changed_paths(repo_root, "diff", "--name-only") or []
    staged_changes = get_changed_paths(repo_root, "diff", "--name-only", "--cached") or []

    combined_changes = []
    seen = set()
    for path in committed_changes + staged_changes + working_tree_changes:
        if path not in seen:
            seen.add(path)
            combined_changes.append(path)

    significant_changes = [path for path in combined_changes if is_significant_change(path)]
    changelog_changed = "CHANGELOG.md" in combined_changes
    return comparison_label, significant_changes, changelog_changed

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    print("========================================")
    print(" Orchestra CI/CD Governance Check (Phase 1) ")
    print(" Advisory Mode: ON (Non-blocking)")
    print("========================================\n")

    warnings = 0
    errors = 0

    # 1. Required Files Check
    print("[1] Checking required files...")
    required_files = [
        "plugin.json",
        "README.md",
        "CHANGELOG.md",
        "SECURITY.md",
        "LICENSE"
    ]
    for rf in required_files:
        path = os.path.join(repo_root, rf)
        if os.path.exists(path):
            print(f"  [PASS] {rf} exists.")
        else:
            print(f"  [WARN] Missing required file: {rf}")
            warnings += 1

    # 2. Plugin.json Validation
    print("\n[2] Validating plugin.json...")
    plugin_path = os.path.join(repo_root, "plugin.json")
    plugin_data = None
    if os.path.exists(plugin_path):
        try:
            with open(plugin_path, "r", encoding="utf-8") as f:
                plugin_data = json.load(f)
            print("  [PASS] plugin.json is valid JSON.")
        except json.JSONDecodeError as e:
            print(f"  [FAIL] plugin.json is invalid JSON: {e}")
            errors += 1
    else:
        print("  [FAIL] plugin.json not found.")
        errors += 1

    # 3. Skills Validation
    if plugin_data and "skills" in plugin_data:
        print("\n[3] Validating registered skills...")
        for skill in plugin_data.get("skills", []):
            skill_name = skill.get("name")
            if not skill_name:
                continue
            skill_file_path = os.path.join(repo_root, "skills", skill_name, "SKILL.md")
            if os.path.exists(skill_file_path):
                print(f"  [PASS] Skill validated: {skill_name}")
            else:
                print(f"  [FAIL] Missing SKILL.md for registered skill: {skill_name}")
                errors += 1

    # 4. Commands Validation
    if plugin_data and "commands" in plugin_data:
        print("\n[4] Validating registered commands...")
        for cmd in plugin_data.get("commands", []):
            cmd_path = os.path.join(repo_root, "commands", f"{cmd}.md")
            if os.path.exists(cmd_path):
                print(f"  [PASS] Command file validated: {cmd}")
            else:
                print(f"  [FAIL] Missing command file for: {cmd}")
                errors += 1

    # 5. Output Templates Check
    print("\n[5] Checking output templates...")
    templates_dir = os.path.join(repo_root, "templates")
    if os.path.exists(templates_dir) and os.listdir(templates_dir):
        print("  [PASS] Output templates directory is populated.")
    else:
        print("  [WARN] Output templates directory is missing or empty.")
        warnings += 1

    # 6. Secrets / Forbidden Files Check
    print("\n[6] Checking for forbidden files (secrets)...")
    forbidden_extensions = [".env", ".pem", ".key"]
    found_forbidden = []
    for root, dirs, files in os.walk(repo_root):
        if ".git" in root or ".agents" in root:
            continue
        for file in files:
            if any(file.endswith(ext) for ext in forbidden_extensions):
                found_forbidden.append(os.path.relpath(os.path.join(root, file), repo_root))
    
    if not found_forbidden:
        print("  [PASS] No forbidden files detected.")
    else:
        for f in found_forbidden:
            print(f"  [FAIL] Forbidden file detected: {f}")
            errors += 1

    # 7. Changelog Freshness Check
    print("\n[7] Checking changelog freshness...")
    comparison_label, freshness_state, freshness_meta = get_changelog_freshness(repo_root)
    if comparison_label is None:
        print(f"  [WARN] {freshness_meta}")
        warnings += 1
    else:
        significant_changes = freshness_state
        changelog_changed = freshness_meta
        if significant_changes and not changelog_changed:
            preview = ", ".join(significant_changes[:5])
            if len(significant_changes) > 5:
                preview += ", ..."
            print(f"  [WARN] Significant changes detected in {comparison_label}, but CHANGELOG.md was not updated.")
            print(f"  [WARN] Significant paths: {preview}")
            warnings += 1
        elif significant_changes:
            print(f"  [PASS] CHANGELOG.md updated alongside significant changes detected in {comparison_label}.")
        else:
            print(f"  [PASS] No significant changed files requiring a CHANGELOG.md update were detected in {comparison_label}.")

    print("\n========================================")
    print(f" Summary: {errors} Errors, {warnings} Warnings")
    print(" Status: ADVISORY MODE (Returning Exit Code 0)")
    print("========================================")
    
    # Phase 1: Always return 0 unless instructed otherwise
    sys.exit(0)

if __name__ == "__main__":
    main()
