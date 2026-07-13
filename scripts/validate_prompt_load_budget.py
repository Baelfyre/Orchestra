import argparse
import json
import sys
from pathlib import Path


VALID_STATUSES = {"PASS", "REVISION_REQUIRED", "BLOCKED", "CONFIGURATION_ERROR"}
VALID_APPROVAL_STATES = {"BOOTSTRAP_PENDING", "APPROVED"}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Validate prompt-load budget packages.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    return parser.parse_args(argv)


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_metrics(path: Path):
    content = path.read_text(encoding="utf-8")
    chars = len(content)
    return chars, chars // 4


def measure_package(repo_root: Path, files):
    total_chars = 0
    total_tokens = 0
    for rel in files:
        path = repo_root / rel
        chars, tokens = read_metrics(path)
        total_chars += chars
        total_tokens += tokens
    return total_chars, total_tokens


def status_for(current_tokens, baseline_tokens, revision_percentage, maximum_percentage):
    if current_tokens * 100 > baseline_tokens * (100 + maximum_percentage):
        return "BLOCKED"
    if current_tokens * 100 > baseline_tokens * (100 + revision_percentage):
        return "REVISION_REQUIRED"
    return "PASS"


def validate_package_config(name, package, repo_root):
    errors = []
    required = {
        "package_name",
        "file_list",
        "approved_baseline_tokens",
        "revision_percentage",
        "maximum_percentage",
        "measurement_method",
        "approval_date",
        "approved_reference",
        "change_rationale",
        "decision_log_reference",
        "maintainer_approval",
        "baseline_change",
    }
    missing = sorted(required - package.keys())
    if missing:
        errors.append(f"{name}: missing fields {missing}")
        return errors

    if package["measurement_method"] != "utf8_chars_div_4":
        errors.append(f"{name}: unsupported measurement_method {package['measurement_method']!r}")
    if not isinstance(package["file_list"], list) or not package["file_list"]:
        errors.append(f"{name}: file_list must be non-empty list")
    else:
        for rel in package["file_list"]:
            if not isinstance(rel, str) or not rel:
                errors.append(f"{name}: invalid file_list entry {rel!r}")
                continue
            if not (repo_root / rel).is_file():
                errors.append(f"{name}: missing file {rel}")

    for field in ("approved_baseline_tokens", "revision_percentage", "maximum_percentage"):
        if not isinstance(package[field], int) or package[field] <= 0:
            errors.append(f"{name}: {field} must be positive integer")

    if isinstance(package.get("revision_percentage"), int) and isinstance(package.get("maximum_percentage"), int):
        if package["maximum_percentage"] < package["revision_percentage"]:
            errors.append(f"{name}: maximum_percentage must be >= revision_percentage")

    for field in ("approved_reference", "change_rationale", "decision_log_reference"):
        if not isinstance(package[field], str) or not package[field].strip():
            errors.append(f"{name}: {field} must be non-empty string")

    approval = package["maintainer_approval"]
    if approval not in VALID_APPROVAL_STATES:
        errors.append(f"{name}: maintainer_approval must be one of {sorted(VALID_APPROVAL_STATES)}")

    change = package["baseline_change"]
    if not isinstance(change, dict):
        errors.append(f"{name}: baseline_change must be object")
    else:
        change_required = {
            "previous_baseline_tokens",
            "new_baseline_tokens",
            "growth_percentage",
            "reason",
            "alternatives_considered",
            "maintainer_approval",
            "decision_log_reference",
        }
        missing_change = sorted(change_required - change.keys())
        if missing_change:
            errors.append(f"{name}: baseline_change missing fields {missing_change}")
        else:
            previous = change["previous_baseline_tokens"]
            new = change["new_baseline_tokens"]
            change_approval = change["maintainer_approval"]
            if not isinstance(new, int) or new <= 0:
                errors.append(f"{name}: baseline_change new_baseline_tokens must be positive integer")
            elif new != package["approved_baseline_tokens"]:
                errors.append(f"{name}: baseline_change new_baseline_tokens must equal approved_baseline_tokens")
            if change_approval not in VALID_APPROVAL_STATES:
                errors.append(f"{name}: baseline_change maintainer_approval must be one of {sorted(VALID_APPROVAL_STATES)}")
            elif change_approval != approval:
                errors.append(f"{name}: package and baseline_change maintainer_approval must match")
            for field in ("reason", "alternatives_considered", "decision_log_reference"):
                if not isinstance(change[field], str) or not change[field].strip():
                    errors.append(f"{name}: baseline_change {field} must be non-empty string")

            growth = change["growth_percentage"]
            if not isinstance(growth, (int, float)) or isinstance(growth, bool):
                errors.append(f"{name}: baseline_change growth_percentage must be number")

            if previous is None:
                if change_approval != "BOOTSTRAP_PENDING":
                    errors.append(f"{name}: null previous baseline requires BOOTSTRAP_PENDING approval")
                if "bootstrap" not in str(change["reason"]).lower():
                    errors.append(f"{name}: bootstrap baseline must state bootstrap reason")
                if growth != 0:
                    errors.append(f"{name}: bootstrap baseline growth_percentage must be 0")
            else:
                if not isinstance(previous, int) or previous <= 0:
                    errors.append(f"{name}: previous_baseline_tokens must be positive integer or null")
                elif isinstance(new, int) and new > 0:
                    expected_growth = round((new - previous) * 100 / previous, 2)
                    if growth != expected_growth:
                        errors.append(f"{name}: baseline_change growth_percentage must equal {expected_growth}")
                    if new > previous and change_approval != "APPROVED":
                        errors.append(f"{name}: baseline increase requires APPROVED maintainer approval")
                if change_approval == "BOOTSTRAP_PENDING":
                    errors.append(f"{name}: BOOTSTRAP_PENDING is allowed only when previous_baseline_tokens is null")
    return errors


def main(argv=None):
    args = parse_args(argv)
    repo_root = args.repo_root.resolve()
    baseline_path = repo_root / "docs" / "performance" / "PROMPT_LOAD_BASELINE.json"
    try:
        baseline = load_json(baseline_path)
    except FileNotFoundError:
        print("[FAIL] CONFIGURATION_ERROR: missing docs/performance/PROMPT_LOAD_BASELINE.json")
        return 2
    except json.JSONDecodeError as exc:
        print(f"[FAIL] CONFIGURATION_ERROR: invalid PROMPT_LOAD_BASELINE.json: {exc}")
        return 2

    if baseline.get("measurement_method") != "utf8_chars_div_4":
        print("[FAIL] CONFIGURATION_ERROR: top-level measurement_method must be utf8_chars_div_4")
        return 2

    packages = baseline.get("packages")
    if not isinstance(packages, dict) or not packages:
        print("[FAIL] CONFIGURATION_ERROR: packages must be non-empty object")
        return 2

    config_errors = []
    results = []
    for name, package in packages.items():
        config_errors.extend(validate_package_config(name, package, repo_root))
        if config_errors:
            continue
        chars, tokens = measure_package(repo_root, package["file_list"])
        status = status_for(tokens, package["approved_baseline_tokens"], package["revision_percentage"], package["maximum_percentage"])
        results.append((name, status, chars, tokens, package["approved_baseline_tokens"]))

    if config_errors:
        for error in config_errors:
            print(f"[FAIL] CONFIGURATION_ERROR: {error}")
        return 2

    worst = "PASS"
    exit_code = 0
    order = {"PASS": 0, "REVISION_REQUIRED": 1, "BLOCKED": 2, "CONFIGURATION_ERROR": 3}
    for name, status, chars, tokens, baseline_tokens in results:
        print(f"[{status}] {name}: chars={chars} tokens={tokens} baseline={baseline_tokens}")
        if order[status] > order[worst]:
            worst = status
    if worst in {"REVISION_REQUIRED", "BLOCKED"}:
        exit_code = 1
    print(f"[RESULT] {worst}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
