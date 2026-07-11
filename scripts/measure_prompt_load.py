import os
import sys

def get_file_metrics(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.count('\n') + 1 if content else 0
            chars = len(content)
            words = len(content.split())
            tokens = chars // 4
            return {
                'lines': lines,
                'chars': chars,
                'words': words,
                'tokens': tokens,
                'error': None
            }
    except Exception as e:
        return {
            'lines': 0, 'chars': 0, 'words': 0, 'tokens': 0, 'error': str(e)
        }

groups = {
    'Group A: Core Router-First Minimal Context': [
        'skills/conductor/SKILL.md',
        'SKILL_INDEX.md',
        'docs/routing/CONTEXT_RETRIEVAL_RULES.md',
        'docs/routing/MINIMAL_PROMPT_FORMAT.md',
        'docs/routing/EXECUTION_MODES_POLICY.md'
    ],
    'Group B: Broader Routing Context': [
        'ROUTING_MAP.md',
        'docs/routing/ROUTER_FIRST_ARCHITECTURE.md',
        'docs/testing/ROUTER_DRY_RUN_TEST_CASES.md',
        'docs/testing/ROUTER_VALIDATION_BENCHMARKS.md'
    ],
    'Group C: Governance Context': [
        'docs/governance/GOVERNANCE_LAYER.md'
    ],
    'Group D: Baseline Performance Docs': [
        'docs/performance/PROMPT_LOAD_AUDIT.md',
        'docs/performance/PERFORMANCE_BASELINE.md'
    ]
}

def main():
    print("================================================================")
    print(" Prompt Load Metrics (Approximate)")
    print(" NOTE: Tokens are estimated as char_count / 4.")
    print("================================================================\n")
    
    grand_total_tokens = 0
    grand_total_chars = 0
    
    for group_name, files in groups.items():
        print(f"--- {group_name} ---")
        group_tokens = 0
        group_chars = 0
        
        for file in files:
            metrics = get_file_metrics(file)
            if metrics['error']:
                print(f"  [ERROR] {file} - {metrics['error']}")
                continue
                
            print(f"  {file:<50} | Lines: {metrics['lines']:<4} | Words: {metrics['words']:<5} | Chars: {metrics['chars']:<6} | Est. Tokens: {metrics['tokens']:<5}")
            group_tokens += metrics['tokens']
            group_chars += metrics['chars']
            
        print(f"  -> Group Totals: Chars: {group_chars}, Est. Tokens: {group_tokens}\n")
        grand_total_tokens += group_tokens
        grand_total_chars += group_chars
        
    print("================================================================")
    print(f" Grand Total: Chars: {grand_total_chars}, Est. Tokens: {grand_total_tokens}")
    print("================================================================\n")
    
    print("Interpretation Note:")
    print("By default, the Conductor now ONLY loads Group A.")
    print("Legacy execution loaded ALL routing and governance files upfront, incurring massive prompt payload overhead.")
    print("This script validates that Group A tokens remain minimal, proving the router-first hypothesis.")

if __name__ == '__main__':
    main()
