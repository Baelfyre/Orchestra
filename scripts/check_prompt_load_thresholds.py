import os
import sys

def get_file_metrics(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            chars = len(content)
            tokens = chars // 4
            return tokens, None
    except Exception as e:
        return 0, str(e)

groups = {
    'Group A': [
        'skills/conductor/SKILL.md',
        'SKILL_INDEX.md',
        'docs/routing/CONTEXT_RETRIEVAL_RULES.md',
        'docs/routing/MINIMAL_PROMPT_FORMAT.md',
        'docs/routing/EXECUTION_MODES_POLICY.md'
    ],
    'Group B': [
        'ROUTING_MAP.md',
        'docs/routing/ROUTER_FIRST_ARCHITECTURE.md',
        'docs/testing/ROUTER_DRY_RUN_TEST_CASES.md',
        'docs/testing/ROUTER_VALIDATION_BENCHMARKS.md'
    ],
    'Group C': [
        'docs/governance/GOVERNANCE_LAYER.md'
    ],
    'Group D': [
        'docs/performance/PROMPT_LOAD_AUDIT.md',
        'docs/performance/PERFORMANCE_BASELINE.md'
    ]
}

def main():
    print("================================================================")
    print(" Prompt Load Threshold Checker (DRY RUN)")
    print("================================================================")
    
    # Baselines
    BASELINE_GROUP_A = 7087
    BASELINE_CONDUCTOR = 1365
    
    # Thresholds
    LIMIT_GROUP_A = 8000
    LIMIT_TOTAL = 20000
    WATCH_GROUP_A = BASELINE_GROUP_A * 1.10
    WATCH_CONDUCTOR = BASELINE_CONDUCTOR * 1.15
    
    current_tokens = {'Group A': 0, 'Group B': 0, 'Group C': 0, 'Group D': 0}
    conductor_tokens = 0
    
    for group_name, files in groups.items():
        for file in files:
            tokens, err = get_file_metrics(file)
            if err:
                print(f"[ERROR] Could not read {file}: {err}")
                continue
            current_tokens[group_name] += tokens
            if file == 'skills/conductor/SKILL.md':
                conductor_tokens = tokens
                
    grand_total = sum(current_tokens.values())
    
    print("\n--- Current Metrics ---")
    print(f"Group A: {current_tokens['Group A']} tokens (Limit: {LIMIT_GROUP_A})")
    print(f"Grand Total: {grand_total} tokens (Limit: {LIMIT_TOTAL})")
    print(f"Conductor: {conductor_tokens} tokens (Baseline: {BASELINE_CONDUCTOR})")
    
    print("\n--- Threshold Status ---")
    
    # Group A Check
    if current_tokens['Group A'] > LIMIT_GROUP_A:
        print(f"[EXCEEDED] Group A exceeds soft limit of {LIMIT_GROUP_A}.")
    elif current_tokens['Group A'] > WATCH_GROUP_A:
        print(f"[WATCH] Group A has grown >10% over baseline ({BASELINE_GROUP_A}).")
    else:
        print("[PASS] Group A size is healthy.")
        
    # Total Check
    if grand_total > LIMIT_TOTAL:
        print(f"[EXCEEDED] Grand Total exceeds soft limit of {LIMIT_TOTAL}.")
    else:
        print("[PASS] Grand Total size is healthy.")
        
    # Conductor Check
    if conductor_tokens > WATCH_CONDUCTOR:
        print(f"[REVIEW] Conductor skill has grown >15% over baseline ({BASELINE_CONDUCTOR}).")
    else:
        print("[PASS] Conductor size is healthy.")
        
    print("\n================================================================")
    print(" NOTE: This is a dry-run/report-only checker. Threshold breaches")
    print(" will not fail the build. A formal review is recommended if any")
    print(" [WATCH], [REVIEW], or [EXCEEDED] statuses are triggered.")
    print("================================================================\n")
    
    # Always exit 0 for dry-run
    sys.exit(0)

if __name__ == '__main__':
    main()
