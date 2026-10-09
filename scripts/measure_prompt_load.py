from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def get_file_metrics(relative_path: str):
    path = ROOT / relative_path
    content = path.read_text(encoding="utf-8")
    chars = len(content)
    return {
        "lines": content.count("\n") + 1 if content else 0,
        "words": len(content.split()),
        "chars": chars,
        "tokens": chars // 4,
    }


GROUPS = {
    "Group A: Core Router-First Minimal Context": [
        "skills/conductor/SKILL.md",
        "SKILL_INDEX.md",
        "docs/routing/CONTEXT_RETRIEVAL_RULES.md",
        "docs/routing/MINIMAL_PROMPT_FORMAT.md",
        "docs/routing/EXECUTION_MODES_POLICY.md",
    ],
    "Group B: Broader Routing Context": [
        "ROUTING_MAP.md",
        "docs/routing/ROUTER_FIRST_ARCHITECTURE.md",
        "docs/testing/ROUTER_DRY_RUN_TEST_CASES.md",
        "docs/testing/ROUTER_VALIDATION_BENCHMARKS.md",
    ],
    "Group C: Governance Context": [
        "docs/governance/GOVERNANCE_LAYER.md",
    ],
    "Group D: Baseline Performance Docs": [
        "docs/performance/PROMPT_LOAD_AUDIT.md",
        "docs/performance/PERFORMANCE_BASELINE.md",
    ],
}

PACKAGES = {
    "Conductor only": [
        "skills/conductor/SKILL.md",
    ],
    "Default routing package": [
        "skills/conductor/SKILL.md",
        "SKILL_INDEX.md",
        "docs/routing/CONTEXT_RETRIEVAL_RULES.md",
        "docs/routing/MINIMAL_PROMPT_FORMAT.md",
        "docs/routing/EXECUTION_MODES_POLICY.md",
    ],
    "Ambiguous-routing package": [
        "skills/conductor/SKILL.md",
        "SKILL_INDEX.md",
        "docs/routing/CONTEXT_RETRIEVAL_RULES.md",
        "docs/routing/MINIMAL_PROMPT_FORMAT.md",
        "docs/routing/EXECUTION_MODES_POLICY.md",
        "ROUTING_MAP.md",
    ],
    "Governance core": [
        "docs/governance/GOVERNANCE_LAYER.md",
    ],
    "Steward governance decision package": [
        "docs/governance/GOVERNANCE_LAYER.md",
        "docs/governance/GOVERNANCE_DECISION_PROTOCOL.md",
        "skills/the-steward/SKILL.md",
        "skills/the-steward/OUTPUT_FORMATS.md",
    ],
    "Governor governance decision package": [
        "docs/governance/GOVERNANCE_LAYER.md",
        "docs/governance/GOVERNANCE_DECISION_PROTOCOL.md",
        "skills/the-governor/SKILL.md",
        "skills/the-governor/OUTPUT_FORMATS.md",
    ],
    "Release governance package": [
        "docs/governance/GOVERNANCE_LAYER.md",
        "docs/governance/GOVERNANCE_DECISION_PROTOCOL.md",
        "skills/the-steward/SKILL.md",
        "skills/the-steward/OUTPUT_FORMATS.md",
        "skills/the-governor/SKILL.md",
        "skills/the-governor/OUTPUT_FORMATS.md",
    ],
}


def measure_collection(files):
    total_chars = 0
    total_tokens = 0
    for relative_path in files:
        metrics = get_file_metrics(relative_path)
        total_chars += metrics["chars"]
        total_tokens += metrics["tokens"]
    return total_chars, total_tokens


def main():
    print("================================================================")
    print(" Prompt Load Metrics (Approximate)")
    print(" NOTE: Tokens are estimated as char_count / 4.")
    print("================================================================\n")

    grand_total_tokens = 0
    grand_total_chars = 0

    for group_name, files in GROUPS.items():
        print(f"--- {group_name} ---")
        group_tokens = 0
        group_chars = 0
        for relative_path in files:
            metrics = get_file_metrics(relative_path)
            print(
                f"  {relative_path:<50} | Lines: {metrics['lines']:<4} | "
                f"Words: {metrics['words']:<5} | Chars: {metrics['chars']:<6} | "
                f"Est. Tokens: {metrics['tokens']:<5}"
            )
            group_tokens += metrics["tokens"]
            group_chars += metrics["chars"]
        print(f"  -> Group Totals: Chars: {group_chars}, Est. Tokens: {group_tokens}\n")
        grand_total_tokens += group_tokens
        grand_total_chars += group_chars

    print("================================================================")
    print(f" Grand Total: Chars: {grand_total_chars}, Est. Tokens: {grand_total_tokens}")
    print("================================================================\n")

    print("--- Issue 171 Package Measurements ---")
    for package_name, files in PACKAGES.items():
        chars, tokens = measure_collection(files)
        print(f"{package_name}: Chars={chars} Est. Tokens={tokens}")
        for relative_path in files:
            metrics = get_file_metrics(relative_path)
            print(f"  - {relative_path}: chars={metrics['chars']} tokens={metrics['tokens']}")
    print()

    print("Interpretation Note:")
    print("By default, Conductor should only need default routing package.")
    print("ROUTING_MAP.md is for ambiguity and ordered dependencies.")
    print("GOVERNANCE_DECISION_PROTOCOL.md is not for initial route classification.")


if __name__ == "__main__":
    main()
