import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def get_tokens(relative_path: str):
    content = (ROOT / relative_path).read_text(encoding="utf-8")
    return len(content) // 4


groups = {
    "Group A": [
        "skills/conductor/SKILL.md",
        "SKILL_INDEX.md",
        "docs/routing/CONTEXT_RETRIEVAL_RULES.md",
        "docs/routing/MINIMAL_PROMPT_FORMAT.md",
        "docs/routing/EXECUTION_MODES_POLICY.md",
    ],
    "Group B": [
        "ROUTING_MAP.md",
        "docs/routing/ROUTER_FIRST_ARCHITECTURE.md",
        "docs/testing/ROUTER_DRY_RUN_TEST_CASES.md",
        "docs/testing/ROUTER_VALIDATION_BENCHMARKS.md",
    ],
    "Group C": [
        "docs/governance/GOVERNANCE_LAYER.md"
    ],
    "Group D": [
        "docs/performance/PROMPT_LOAD_AUDIT.md",
        "docs/performance/PERFORMANCE_BASELINE.md"
    ]
}


def main():
    print("================================================================")
    print(" Prompt Load Threshold Checker (DRY RUN)")
    print("================================================================")

    ORIGINAL_BASELINE_GROUP_A = 7087
    ORIGINAL_BASELINE_CONDUCTOR = 1365

    LIMIT_GROUP_A = 8000
    LIMIT_GROUP_B = 6000
    LIMIT_GROUP_C = 4000
    LIMIT_TOTAL = 20000
    WATCH_GROUP_A = ORIGINAL_BASELINE_GROUP_A * 1.10
    WATCH_CONDUCTOR = ORIGINAL_BASELINE_CONDUCTOR * 1.15

    current_tokens = {group_name: 0 for group_name in groups}
    file_tokens = {group_name: [] for group_name in groups}
    conductor_tokens = 0

    for group_name, files in groups.items():
        for relative_path in files:
            tokens = get_tokens(relative_path)
            current_tokens[group_name] += tokens
            file_tokens[group_name].append((tokens, relative_path))
            if relative_path == "skills/conductor/SKILL.md":
                conductor_tokens = tokens

    grand_total = sum(current_tokens.values())

    print("\n--- Current Metrics ---")
    print(f"Group A: {current_tokens['Group A']} tokens (Limit: {LIMIT_GROUP_A})")
    print(f"Group B: {current_tokens['Group B']} tokens (Limit: {LIMIT_GROUP_B})")
    print(f"Group C: {current_tokens['Group C']} tokens (Limit: {LIMIT_GROUP_C})")
    print(f"Group D: {current_tokens['Group D']} tokens (No threshold)")
    print(f"Grand Total: {grand_total} tokens (Limit: {LIMIT_TOTAL})")
    print(f"Conductor: {conductor_tokens} tokens (Original baseline: {ORIGINAL_BASELINE_CONDUCTOR})")

    print("\n--- Threshold Status ---")
    if current_tokens["Group A"] > LIMIT_GROUP_A:
        print(f"[EXCEEDED] Group A exceeds soft limit of {LIMIT_GROUP_A}.")
    elif current_tokens["Group A"] > WATCH_GROUP_A:
        print(f"[WATCH] Group A has grown >10% over original baseline ({ORIGINAL_BASELINE_GROUP_A}).")
    else:
        print("[PASS] Group A size is healthy.")

    for group_name, limit in (("Group B", LIMIT_GROUP_B), ("Group C", LIMIT_GROUP_C)):
        if current_tokens[group_name] > limit:
            print(f"[EXCEEDED] {group_name} exceeds soft limit of {limit}.")
        else:
            print(f"[PASS] {group_name} size is within soft limit.")

    if grand_total > LIMIT_TOTAL:
        print(f"[EXCEEDED] Grand Total exceeds soft limit of {LIMIT_TOTAL}.")
    else:
        print("[PASS] Grand Total size is healthy.")

    if conductor_tokens > WATCH_CONDUCTOR:
        print(f"[REVIEW] Conductor skill has grown >15% over original baseline ({ORIGINAL_BASELINE_CONDUCTOR}).")
    else:
        print("[PASS] Conductor size is healthy.")

    print("\n--- Largest Contributors ---")
    for group_name in groups:
        print(f"{group_name}:")
        contributors = sorted(file_tokens[group_name], reverse=True)[:3]
        for tokens, relative_path in contributors:
            print(f"  {relative_path}: {tokens} tokens")

    print("\n================================================================")
    print(" NOTE: This is an advisory/report-only checker. [WATCH], [REVIEW],")
    print(" and [EXCEEDED] statuses are not blocking validation failures.")
    print(" Threshold breaches require review, but this script exits 0.")
    print(" Policy: docs/performance/PROMPT_LOAD_THRESHOLD_POLICY.md")
    print("================================================================\n")

    sys.exit(0)


if __name__ == "__main__":
    main()
