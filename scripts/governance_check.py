import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


REQUIRED_ROOT_FILES = [
    "plugin.json",
    "README.md",
    "CHANGELOG.md",
    "SECURITY.md",
    "LICENSE",
]

REQUIRED_GOVERNANCE_DOCS = [
    "AGENTS.md",
    "docs/CONTRIBUTING.md",
    "docs/governance/CI_CD_GOVERNANCE_PLAN.md",
    "docs/governance/ARBITER_CALIBRATION_PLAN.md",
    "docs/governance/DAGGER_RUNTIME_GUARDRAIL_GAP.md",
    "docs/governance/STRICT_GOVERNANCE_RELEASE_GATE_PLAN.md",
]

REQUIRED_VALIDATION_SCRIPTS = [
    "scripts/governance_check.py",
    "scripts/dagger_guardrail.py",
    "scripts/test_dagger_guardrail.py",
    "scripts/preflight_sync_check.py",
    "scripts/validate_ide_packaging.py",
    "tests/behavior/evaluate_governance.py",
    "tests/behavior/run_tests.py",
    "scripts/validate_artificer_internal.py",
    "scripts/validate_artificer_records.py",
    "scripts/validate_artificer_governance_records.py",
    "scripts/validate_artificer_pattern_catalog.py",
    "scripts/render_artificer_audit_report.py",
    "scripts/validate_prompt_load_budget.py",
    "scripts/validate_governance_protocol_consistency.py",
    "scripts/validate_routing_contract.py",
]

REPO_MEMORY_FILES = [
    "SESSION_HANDOFF.md",
    "PROJECT_STATE.md",
    "DECISION_LOG.md",
]

STRICT_VALIDATOR_SCRIPTS = [
    "scripts/validate_structure.py",
    "scripts/validate_manifest.py",
    "scripts/validate_ide_packaging.py",
    "scripts/validate_artificer_internal.py",
    "scripts/validate_artificer_records.py",
    "scripts/validate_artificer_governance_records.py",
    "scripts/validate_artificer_pattern_catalog.py",
    "scripts/validate_prompt_load_budget.py",
    "scripts/validate_governance_protocol_consistency.py",
    "scripts/validate_routing_contract.py",
]

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

FORBIDDEN_REPO_PATTERNS = [
    ".agents/**",
    ".amalgam/**",
    ".codex/**",
    "artifacts/**",
    "__pycache__/**",
    ".pytest_cache/**",
    ".mypy_cache/**",
    "*.log",
    "*.tmp",
    "*.pyc",
    "*.pyo",
]

FORBIDDEN_EXTENSIONS = [".env", ".pem", ".key"]
ALLOWED_RUNTIME_PATHS = {
    ".agents/plugins/marketplace.json",
}
PATH_EXTENSIONS = {
    ".json",
    ".md",
    ".ps1",
    ".py",
    ".sh",
    ".txt",
    ".yml",
    ".yaml",
}
REPO_PATH_PREFIXES = {
    ".agents",
    ".github",
    "adapters",
    "assets",
    "commands",
    "docs",
    "examples",
    "scripts",
    "skills",
    "templates",
    "tests",
}


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


def get_tracked_repo_files(repo_root):
    result = run_git(repo_root, "ls-files", "--cached")
    if result.returncode != 0:
        return []
    return normalize_paths(result.stdout.splitlines())


def is_ignored_change(path):
    return any(fnmatch.fnmatch(path, pattern) for pattern in IGNORED_CHANGE_PATTERNS)


def is_significant_change(path):
    if path == "CHANGELOG.md" or is_ignored_change(path):
        return False
    return any(fnmatch.fnmatch(path, pattern) for pattern in SIGNIFICANT_CHANGE_PATTERNS)


def is_forbidden_repo_path(path):
    if path in ALLOWED_RUNTIME_PATHS:
        return False
    return any(fnmatch.fnmatch(path, pattern) for pattern in FORBIDDEN_REPO_PATTERNS)


def get_exit_code(strict_mode, errors):
    if strict_mode and errors > 0:
        return 1
    return 0


def get_changelog_issue(significant_changes, changelog_changed):
    if significant_changes and not changelog_changed:
        return "Significant changes were detected without a matching CHANGELOG.md update."
    return None


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


def print_issue(level, path, reason, remediation):
    print(f"  [{level}] {path}: {reason}")
    if remediation:
        print(f"         Remediation: {remediation}")


def print_pass(path, detail):
    print(f"  [PASS] {path}: {detail}")


def record_failure(counters, path, reason, remediation):
    counters["errors"] += 1
    print_issue("FAIL", path, reason, remediation)


def record_warning(counters, path, reason, remediation):
    counters["warnings"] += 1
    print_issue("WARN", path, reason, remediation)


def run_python_script(repo_root, relative_path):
    script_path = os.path.join(repo_root, relative_path.replace("/", os.sep))
    return subprocess.run(
        [sys.executable, script_path],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )


def is_repo_relative_memory_path(path_text):
    normalized = path_text.strip().strip("`").replace("\\", "/")
    if not normalized or normalized.startswith(("http://", "https://")):
        return False
    if " " in normalized:
        return False
    if re.match(r"^[A-Za-z]:/", normalized):
        return False
    if normalized.startswith("/") or normalized in {".", ".."}:
        return False
    if any(part == ".." for part in normalized.split("/")):
        return False
    if "*" in normalized or "?" in normalized:
        return False
    suffix = Path(normalized).suffix.lower()
    if suffix in PATH_EXTENSIONS:
        return True
    first_segment = normalized.split("/", 1)[0]
    return "/" in normalized and first_segment in REPO_PATH_PREFIXES


def get_memory_path_references(line):
    references = []
    references.extend(match.group(1) for match in re.finditer(r"`([^`]+)`", line))
    references.extend(match.group(0) for match in re.finditer(r"\b[A-Za-z0-9_.-]+(?:[\\/][A-Za-z0-9_.-]+)+(?:[\\/])?", line))
    return list(dict.fromkeys(references))


def get_known_git_branches(repo_root):
    known = set()

    current_branch = get_current_git_branch(repo_root)
    if current_branch:
        norm = current_branch.strip().replace("\\", "/").rstrip("/")
        if norm and norm.lower() != "head":
            known.add(norm)

    result = run_git(repo_root, "for-each-ref", "--format=%(refname)", "refs/heads", "refs/remotes")
    if result.returncode == 0:
        for line in result.stdout.splitlines():
            ref = line.strip().replace("\\", "/").rstrip("/")
            if not ref:
                continue

            if ref.startswith("refs/pull/") or "/pull/" in ref or ref.endswith("/merge"):
                continue

            if ref.startswith("refs/heads/"):
                branch_name = ref[len("refs/heads/"):].strip()
                if branch_name and branch_name.lower() != "head":
                    known.add(branch_name)
            elif ref.startswith("refs/remotes/"):
                remote_ref = ref[len("refs/remotes/"):].strip()
                if not remote_ref or remote_ref.endswith("/HEAD") or remote_ref == "HEAD":
                    continue
                known.add(remote_ref)
                parts = remote_ref.split("/", 1)
                if len(parts) == 2 and parts[1] and parts[1].lower() != "head":
                    known.add(parts[1])

    github_head_ref = os.environ.get("GITHUB_HEAD_REF")
    if github_head_ref:
        gh_norm = github_head_ref.strip().replace("\\", "/").rstrip("/")
        if gh_norm and gh_norm.lower() != "head":
            known.add(gh_norm)

    return known


def run_repo_memory_path_check(repo_root, counters):
    print("\n[7c] Checking repo-local memory path references...")
    missing_references = []
    known_branches = get_known_git_branches(repo_root)

    for memory_file in REPO_MEMORY_FILES:
        memory_path = Path(repo_root) / memory_file
        if not memory_path.is_file():
            continue

        for line_number, line in enumerate(memory_path.read_text(encoding="utf-8").splitlines(), 1):
            for reference in get_memory_path_references(line):
                normalized = reference.strip().strip("`").replace("\\", "/").rstrip("/")
                if known_branches and normalized in known_branches:
                    continue
                if not is_repo_relative_memory_path(normalized):
                    continue
                if (Path(repo_root) / normalized).exists():
                    continue
                missing_references.append(f"{memory_file}:{line_number}: {normalized}")

    if not missing_references:
        print_pass("repo-memory", "No nonexistent repo-relative paths found in startup memory files.")
        return

    for reference in missing_references:
        record_failure(
            counters,
            reference,
            "Repo-local memory references a path that does not exist.",
            "Update or retire the stale memory entry so startup context cannot route future work to missing files.",
        )


STARTUP_STATE_FILES = [
    "PROJECT_STATE.md",
    "SESSION_HANDOFF.md",
]

CANONICAL_BRANCH_CLAIM_PATTERN = re.compile(
    r"^\s*[-*]?\s*\*{0,2}Canonical\s+Branch:?\*{0,2}\s*[:`]*\s*`?([^`\n]+?)`?\s*$",
    re.IGNORECASE,
)

BASE_BRANCH_CLAIM_PATTERN = re.compile(
    r"^\s*[-*]?\s*\*{0,2}Base\s+Branch:?\*{0,2}\s*[:`]*\s*`?([^`\n]+?)`?\s*$",
    re.IGNORECASE,
)

LEGACY_BRANCH_CLAIM_PATTERN = re.compile(
    r"^\s*[-*]?\s*\*{0,2}Current\s+Branch:?\*{0,2}\s*[:`]*\s*`?([^`\n]+?)`?\s*$",
    re.IGNORECASE,
)

STAGE_VERSION_PATTERN = re.compile(
    r"^\s*v?(\d+\.\d+\.\d+)\b",
)


def get_current_git_branch(repo_root):
    result = run_git(repo_root, "branch", "--show-current")
    if result.returncode != 0:
        return None
    branch = result.stdout.strip()
    return branch if branch else None


def get_remote_default_branch(repo_root):
    github_base = os.environ.get("GITHUB_BASE_REF")
    if github_base:
        return github_base.strip()

    result = run_git(repo_root, "symbolic-ref", "refs/remotes/origin/HEAD")
    if result.returncode == 0:
        ref = result.stdout.strip()
        if ref.startswith("refs/remotes/origin/"):
            return ref[len("refs/remotes/origin/"):]

    result = run_git(repo_root, "show-ref", "--verify", "refs/remotes/origin/main")
    if result.returncode == 0:
        return "main"

    return None


def get_plugin_version(repo_root):
    plugin_path = os.path.join(repo_root, "plugin.json")
    try:
        with open(plugin_path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return str(data.get("version", ""))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def run_startup_state_claim_check(repo_root, counters, strict_mode):
    print("\n[7d] Checking structured startup-state claims...")
    issues_found = False

    record_issue = record_failure if strict_mode else record_warning

    plugin_version = get_plugin_version(repo_root)
    remote_default = get_remote_default_branch(repo_root)

    for memory_file in STARTUP_STATE_FILES:
        memory_path = Path(repo_root) / memory_file
        if not memory_path.is_file():
            continue

        canonical_claims = []
        base_claims = []
        legacy_current_lines = []

        for line_number, line in enumerate(memory_path.read_text(encoding="utf-8").splitlines(), 1):
            legacy_match = LEGACY_BRANCH_CLAIM_PATTERN.match(line)
            if legacy_match:
                legacy_current_lines.append((line_number, legacy_match.group(1).strip()))

            canonical_match = CANONICAL_BRANCH_CLAIM_PATTERN.match(line)
            if canonical_match:
                canonical_claims.append((line_number, canonical_match.group(1).strip()))

            base_match = BASE_BRANCH_CLAIM_PATTERN.match(line)
            if base_match:
                base_claims.append((line_number, base_match.group(1).strip()))

        if legacy_current_lines:
            for line_num, val in legacy_current_lines:
                record_issue(
                    counters,
                    f"{memory_file}:{line_num}",
                    f"Legacy 'Current Branch' claim '{val}' exists in {memory_file}.",
                    "Remove the legacy 'Current Branch' field and use 'Canonical Branch' instead.",
                )
                issues_found = True

        if len(canonical_claims) == 0:
            record_issue(
                counters,
                f"{memory_file}:1",
                f"Missing required 'Canonical Branch' claim in {memory_file}.",
                "Add 'Canonical Branch: main' to the startup-state file.",
            )
            issues_found = True
        elif len(canonical_claims) > 1:
            for line_num, val in canonical_claims:
                record_issue(
                    counters,
                    f"{memory_file}:{line_num}",
                    f"Duplicate 'Canonical Branch' claim '{val}' found in {memory_file}.",
                    "Ensure exactly one 'Canonical Branch' claim exists in the startup-state file.",
                )
                issues_found = True

        if len(base_claims) == 0:
            record_issue(
                counters,
                f"{memory_file}:1",
                f"Missing required 'Base Branch' claim in {memory_file}.",
                "Add 'Base Branch: main' to the startup-state file.",
            )
            issues_found = True
        elif len(base_claims) > 1:
            for line_num, val in base_claims:
                record_issue(
                    counters,
                    f"{memory_file}:{line_num}",
                    f"Duplicate 'Base Branch' claim '{val}' found in {memory_file}.",
                    "Ensure exactly one 'Base Branch' claim exists in the startup-state file.",
                )
                issues_found = True

        if len(canonical_claims) == 1 and len(base_claims) == 1:
            canonical_val = canonical_claims[0][1]
            base_val = base_claims[0][1]
            if canonical_val != base_val:
                record_issue(
                    counters,
                    f"{memory_file}:{canonical_claims[0][0]}",
                    f"Canonical Branch '{canonical_val}' and Base Branch '{base_val}' disagree.",
                    "Update them to match (e.g., both should be 'main').",
                )
                issues_found = True

            if remote_default and canonical_val != remote_default:
                record_issue(
                    counters,
                    f"{memory_file}:{canonical_claims[0][0]}",
                    f"Canonical Branch '{canonical_val}' conflicts with detected remote default branch '{remote_default}'.",
                    "Ensure the Canonical Branch aligns with origin/HEAD.",
                )
                issues_found = True

    context_path = Path(repo_root) / "PROJECT_CONTEXT.md"
    if context_path.is_file() and plugin_version:
        in_stage_section = False
        for line_number, line in enumerate(context_path.read_text(encoding="utf-8").splitlines(), 1):
            stripped = line.strip()
            if stripped.lower().startswith("## current stage"):
                in_stage_section = True
                continue
            if in_stage_section and stripped.startswith("##"):
                in_stage_section = False
                continue
            if in_stage_section and stripped:
                match = STAGE_VERSION_PATTERN.match(stripped)
                if match:
                    claimed_version = match.group(1)
                    if claimed_version != plugin_version:
                        record_issue(
                            counters,
                            f"PROJECT_CONTEXT.md:{line_number}",
                            f"Current Stage version '{claimed_version}' does not match plugin.json version '{plugin_version}'.",
                            "Update the Current Stage field in PROJECT_CONTEXT.md to match the published release version.",
                        )
                        issues_found = True
                in_stage_section = False

    if not issues_found:
        print_pass("startup-state-claims", "Canonical branch and version claims match repository policy.")


def run_strict_validators(repo_root, counters):
    print("\n[8] Running strict metadata validators...")
    for script_path in STRICT_VALIDATOR_SCRIPTS:
        result = run_python_script(repo_root, script_path)
        if result.returncode == 0:
            print_pass(script_path, "Validator passed.")
            continue

        record_failure(
            counters,
            script_path,
            "Deterministic metadata or structure validation failed.",
            f"Run `python {script_path}` locally and resolve the reported manifest, structure, or output-format drift.",
        )
        tail = (result.stdout or result.stderr).strip()
        if tail:
            preview = tail.splitlines()[-1]
            print(f"         Validator output: {preview}")


def run_dagger_contract_check(repo_root, counters):
    print("\n[9] Checking Dagger live-execution block...")
    script_path = os.path.join(repo_root, "scripts", "dagger_guardrail.py")

    with tempfile.TemporaryDirectory(prefix="governance-dagger-check-") as temp_dir:
        pass_report = os.path.join(temp_dir, "pass-report.json")
        pass_result = subprocess.run(
            [
                sys.executable,
                script_path,
                "--action",
                "delete_file",
                "--target-path",
                "README.md",
                "--confirm",
                "--dry-run",
                "--rollback-plan",
                "restore from git",
                "--report-file",
                pass_report,
            ],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )

        fail_report = os.path.join(temp_dir, "blocked-report.json")
        blocked_result = subprocess.run(
            [
                sys.executable,
                script_path,
                "--action",
                "delete_file",
                "--target-path",
                "README.md",
                "--confirm",
                "--rollback-plan",
                "restore from git",
                "--report-file",
                fail_report,
            ],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )

        try:
            pass_payload = json.loads(Path(pass_report).read_text(encoding="utf-8"))
            blocked_payload = json.loads(Path(fail_report).read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            record_failure(
                counters,
                "scripts/dagger_guardrail.py",
                "Guardrail report could not be parsed during strict validation.",
                "Keep the guardrail JSON output stable and machine-readable.",
            )
            return

    if pass_result.returncode != 0:
        record_failure(
            counters,
            "scripts/dagger_guardrail.py",
            "Expected dry-run validation no longer passes.",
            "Restore the current simulation-only guardrail behavior for approved dry-run requests.",
        )
        return

    if blocked_result.returncode == 0:
        record_failure(
            counters,
            "scripts/dagger_guardrail.py",
            "A destructive request without --dry-run no longer fails closed.",
            "Restore the live-execution block and require --dry-run before validation passes.",
        )
        return

    if pass_payload.get("live_execution") != "blocked" or blocked_payload.get("live_execution") != "blocked":
        record_failure(
            counters,
            "scripts/dagger_guardrail.py",
            "Dagger no longer reports live execution as blocked.",
            "Keep `live_execution` set to `blocked` until a later Dagger promotion phase explicitly changes it.",
        )
        return

    print_pass("scripts/dagger_guardrail.py", "Live destructive execution remains blocked in both pass and fail paths.")


def main():
    parser = argparse.ArgumentParser(description="Validate Orchestra governance checks in advisory or strict mode.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Enable Stage 1 strict deterministic governance failures.",
    )
    args = parser.parse_args()

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    mode_label = "Stage 1 strict deterministic gates" if args.strict else "Advisory Mode: ON (Non-blocking)"

    print("========================================")
    print(" Orchestra CI/CD Governance Check ")
    print(f" {mode_label}")
    print("========================================\n")

    counters = {"warnings": 0, "errors": 0}

    print("[1] Checking required root files...")
    for relative_path in REQUIRED_ROOT_FILES:
        full_path = os.path.join(repo_root, relative_path.replace("/", os.sep))
        if os.path.exists(full_path):
            print_pass(relative_path, "File exists.")
        else:
            record_failure(
                counters,
                relative_path,
                "Required repository file is missing.",
                "Restore the file in the repository before merging.",
            )

    print("\n[2] Checking required governance documents...")
    for relative_path in REQUIRED_GOVERNANCE_DOCS:
        full_path = os.path.join(repo_root, relative_path.replace("/", os.sep))
        if os.path.exists(full_path):
            print_pass(relative_path, "Governance document exists.")
        else:
            record_failure(
                counters,
                relative_path,
                "Required governance documentation is missing.",
                "Restore the missing governance document before merging.",
            )

    print("\n[3] Checking required validation scripts...")
    for relative_path in REQUIRED_VALIDATION_SCRIPTS:
        full_path = os.path.join(repo_root, relative_path.replace("/", os.sep))
        if os.path.exists(full_path):
            print_pass(relative_path, "Validation entrypoint exists.")
        else:
            record_failure(
                counters,
                relative_path,
                "Required governance validation script is missing.",
                "Restore the missing validation script before merging.",
            )

    print("\n[4] Validating plugin.json...")
    plugin_path = os.path.join(repo_root, "plugin.json")
    plugin_data = None
    try:
        with open(plugin_path, "r", encoding="utf-8") as handle:
            plugin_data = json.load(handle)
        print_pass("plugin.json", "Valid JSON.")
    except FileNotFoundError:
        record_failure(
            counters,
            "plugin.json",
            "Manifest file is missing.",
            "Restore plugin.json before merging.",
        )
    except json.JSONDecodeError as exc:
        record_failure(
            counters,
            "plugin.json",
            f"Invalid JSON: {exc}",
            "Fix the JSON syntax and re-run validation.",
        )

    if plugin_data and "skills" in plugin_data:
        print("\n[5] Validating registered skills...")
        for skill in plugin_data.get("skills", []):
            skill_name = skill.get("name")
            if not skill_name:
                record_failure(
                    counters,
                    "plugin.json",
                    "A registered skill is missing its `name` field.",
                    "Add the missing skill name and keep manifest metadata consistent.",
                )
                continue

            skill_file_path = os.path.join(repo_root, "skills", skill_name, "SKILL.md")
            if os.path.exists(skill_file_path):
                print_pass(f"skills/{skill_name}/SKILL.md", "Registered skill file exists.")
            else:
                record_failure(
                    counters,
                    f"skills/{skill_name}/SKILL.md",
                    "Registered skill file is missing.",
                    "Restore the skill file or remove the stale manifest entry.",
                )

    if plugin_data and "commands" in plugin_data:
        print("\n[6] Validating registered commands...")
        for command_name in plugin_data.get("commands", []):
            command_path = os.path.join(repo_root, "commands", f"{command_name}.md")
            if os.path.exists(command_path):
                print_pass(f"commands/{command_name}.md", "Registered command file exists.")
            else:
                record_failure(
                    counters,
                    f"commands/{command_name}.md",
                    "Registered command file is missing.",
                    "Restore the command file or remove the stale manifest entry.",
                )

    print("\n[7] Checking forbidden committed files...")
    repo_files = get_tracked_repo_files(repo_root)
    forbidden_files = []
    for relative_path in repo_files:
        if is_forbidden_repo_path(relative_path):
            forbidden_files.append(relative_path)
            continue
        if any(relative_path.endswith(ext) for ext in FORBIDDEN_EXTENSIONS):
            forbidden_files.append(relative_path)

    if forbidden_files:
        for relative_path in forbidden_files:
            record_failure(
                counters,
                relative_path,
                "Forbidden generated artifact, runtime file, cache file, or secret-like file is present in repository content.",
                "Remove the file from version control and keep it ignored locally if it is runtime-only.",
            )
    else:
        print_pass("repository-content", "No forbidden generated artifacts, runtime folders, caches, or secret-like files detected.")

    run_repo_memory_path_check(repo_root, counters)

    run_startup_state_claim_check(repo_root, counters, args.strict)

    print("\n[7b] Checking changelog freshness...")
    comparison_label, freshness_state, freshness_meta = get_changelog_freshness(repo_root)
    if comparison_label is None:
        record_warning(
            counters,
            "CHANGELOG.md",
            freshness_meta,
            "Verify git history locally if changelog freshness needs review.",
        )
    else:
        significant_changes = freshness_state
        changelog_changed = freshness_meta
        changelog_issue = get_changelog_issue(significant_changes, changelog_changed)
        if changelog_issue:
            preview = ", ".join(significant_changes[:5])
            if len(significant_changes) > 5:
                preview += ", ..."
            record_failure(
                counters,
                "CHANGELOG.md",
                f"{changelog_issue} Comparison: {comparison_label}. Significant paths: {preview}",
                "Add a focused CHANGELOG.md entry for the significant repository changes.",
            )
        elif significant_changes:
            print_pass("CHANGELOG.md", f"Updated alongside significant changes detected in {comparison_label}.")
        else:
            print_pass("CHANGELOG.md", f"No significant changed files requiring a changelog update were detected in {comparison_label}.")

    if args.strict:
        run_strict_validators(repo_root, counters)
        run_dagger_contract_check(repo_root, counters)

    print("\n========================================")
    print(f" Summary: {counters['errors']} Errors, {counters['warnings']} Warnings")
    if args.strict:
        print(" Status: Stage 1 strict deterministic gates")
    else:
        print(" Status: ADVISORY MODE (Returning Exit Code 0)")
    print("========================================")

    sys.exit(get_exit_code(args.strict, counters["errors"]))


if __name__ == "__main__":
    main()
