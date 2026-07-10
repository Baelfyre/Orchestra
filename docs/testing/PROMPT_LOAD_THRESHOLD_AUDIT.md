# Prompt-load Threshold Audit

## Purpose

This Wave 5B audit reviews prompt-load threshold policy, validator behavior, and specialist prompt-size discipline after `v1.1.1` and the Wave 5A cross-platform CI coverage hardening merge.

This branch is audit-first. It records observed behavior and recommended follow-up work without changing thresholds, validator logic, skill instructions, runtime behavior, governance semantics, or CI workflows.

## Current Threshold Model

Prompt-load measurement is implemented by `scripts/measure_prompt_load.py`. The script reads a fixed set of repository files, counts lines, words, and characters, and estimates tokens with `characters // 4`.

Prompt-load threshold review is implemented by `scripts/check_prompt_load_thresholds.py`. The checker uses the same fixed file groups, computes the same approximate token estimate, prints a report, and always exits with status `0`.

Current checker constants:

| Check | Current value |
|---|---:|
| Group A baseline | 7,087 estimated tokens |
| Conductor baseline | 1,365 estimated tokens |
| Group A soft limit | 8,000 estimated tokens |
| Grand Total soft limit | 20,000 estimated tokens |
| Group A watch trigger | baseline + 10% |
| Conductor review trigger | baseline + 15% |

Current checker statuses:

| Status | Meaning |
|---|---|
| `[PASS]` | Metric is below the configured review trigger. |
| `[WATCH]` | Group A grew more than 10% over baseline. |
| `[REVIEW]` | Conductor grew more than 15% over baseline. |
| `[EXCEEDED]` | Group A or Grand Total exceeded its configured soft limit. |

The checker is report-only. Threshold breaches are visible in CI artifacts but do not fail local validation or CI.

## Current Coverage

The measured groups are static:

| Group | Files measured |
|---|---|
| Group A | `skills/conductor/SKILL.md`, `SKILL_INDEX.md`, `docs/routing/CONTEXT_RETRIEVAL_RULES.md`, `docs/routing/MINIMAL_PROMPT_FORMAT.md`, `docs/routing/EXECUTION_MODES_POLICY.md` |
| Group B | `ROUTING_MAP.md`, `docs/routing/ROUTER_FIRST_ARCHITECTURE.md`, `docs/testing/ROUTER_DRY_RUN_TEST_CASES.md`, `docs/testing/ROUTER_VALIDATION_BENCHMARKS.md` |
| Group C | `docs/governance/GOVERNANCE_LAYER.md` |
| Group D | `docs/performance/PROMPT_LOAD_AUDIT.md`, `docs/performance/PERFORMANCE_BASELINE.md` |

Only one source skill file is included directly: `skills/conductor/SKILL.md`.

The repository does not contain `.codex-plugin/skills`. Codex export output exists under `adapters/codex/skills` and is separately validated by `adapters/codex/validate_codex_export.py`. That validator checks exported skill structure, frontmatter shape, required export files, relative links, Conductor routing references, and tracked template parity. It does not measure exported prompt-load size.

Prompt-load threshold validation does not currently measure:

- `skills/*/SKILL.md` other than Conductor
- `adapters/codex/skills/*/SKILL.md`
- `README.md`
- `plugin.json`
- runtime-generated prompt payloads
- user prompts, session history, or downstream specialist outputs

## Findings

### Major Findings

1. **Current prompt-load metrics exceed documented soft limits.**

   Current local measurement reports:

   | Metric | Current | Limit | Status |
   |---|---:|---:|---|
   | Group A | 8,028 estimated tokens | 8,000 | `[EXCEEDED]` |
   | Grand Total | 20,916 estimated tokens | 20,000 | `[EXCEEDED]` |
   | Conductor | 2,248 estimated tokens | 1,365 baseline plus 15% review trigger | `[REVIEW]` |

   The checker reports these conditions but exits `0`, so they are advisory only.

2. **Policy coverage and checker coverage are inconsistent for Group B and Group C.**

   `docs/performance/PROMPT_LOAD_THRESHOLD_POLICY.md` defines soft limits for Group B and Group C, but `scripts/check_prompt_load_thresholds.py` does not emit Group B or Group C threshold statuses. Current measurement reports Group B at 6,147 estimated tokens and Group C at 4,411 estimated tokens, which are above the documented 6,000 and 4,000 soft limits, but the checker does not call them out.

3. **Documented baseline values no longer match current measurements.**

   `docs/performance/PROMPT_LOAD_THRESHOLD_POLICY.md` records baseline values such as Group A at approximately 7,087 estimated tokens and Grand Total at approximately 17,080 estimated tokens. Current measurement reports Group A at 8,028 estimated tokens and Grand Total at 20,916 estimated tokens. The baseline may still be historically useful, but the docs do not clearly distinguish original baseline from current observed state.

### Minor Findings

1. **Specialist prompt-size discipline is mostly unmeasured.**

   Several specialist source skill files are larger than the Conductor skill, including `skills/cloak/SKILL.md`, `skills/overseer/SKILL.md`, `skills/cipher/SKILL.md`, and `skills/the-governor/SKILL.md`. These files are not default Conductor routing context, so this is not a direct Group A failure. It is still relevant because specialist activation loads those surfaces during routed work.

2. **Codex export prompt-size parity is not thresholded.**

   Exported Codex skills under `adapters/codex/skills` are structurally validated, but their prompt-load size is not checked against source skills or any export-specific budget. Current exported skill sizes broadly track source sizes, but the threshold tooling does not report them.

3. **Checker remediation guidance is too generic for fast review.**

   The checker reports `[EXCEEDED]` and `[REVIEW]` statuses, then recommends formal review. It does not identify the largest contributing files, does not link to the policy, and does not explain whether a breach is advisory, required-review, or release-blocking.

### Cleanup Findings

1. **The expected Codex export inspection path is easy to confuse.**

   `.codex-plugin/skills` does not exist in this repository, while tracked Codex export output exists at `adapters/codex/skills`. Future audit prompts and docs should use the actual tracked export path when discussing exported Codex skills.

## Risk Assessment

| Severity | Assessment |
|---|---|
| Critical | None. The checker runs, reports current breaches, and remains intentionally report-only. No unsafe prompt loading or broken validator execution was found. |
| Major | Current soft thresholds are exceeded; Group B and Group C policy limits are not reported by the checker; baseline documentation is stale relative to current measurements. |
| Minor | Specialist and exported skill prompt sizes are not thresholded; checker remediation guidance is not specific enough for quick maintainer action. |
| Cleanup | Codex export path wording should be clarified in future docs and prompts. |

## Recommended Wave 5B Implementation Plan

1. Keep this audit PR documentation-only.
2. Update threshold documentation to distinguish original baselines from current observed measurements.
3. Decide whether Group B and Group C soft limits should be reported by `scripts/check_prompt_load_thresholds.py`.
4. Add clearer checker output that links to the policy and states that current breaches are advisory unless a future strict mode is enabled.
5. Add largest-contributor reporting to make remediation faster without changing thresholds.
6. Consider a separate specialist prompt-size report for `skills/*/SKILL.md` and `adapters/codex/skills/*/SKILL.md`.
7. Document any accepted exceptions instead of silently normalizing threshold breaches.
8. Keep current thresholds unchanged unless maintainers agree that the observed post-`v1.1.1` measurements are the new baseline.

## Non-goals

- No threshold changes in the audit PR.
- No skill rewriting.
- No validator logic changes.
- No CI changes.
- No governance semantics changes.
- No runtime behavior changes.
- No Wave 5C-F implementation work.

## Decision Needed

Before implementation, maintainers need to decide:

1. Whether to keep, lower, or re-baseline the current Group A and Grand Total thresholds.
2. Whether Group B and Group C policy limits should be enforced in checker output.
3. Whether source skills and exported Codex skills should be treated identically for prompt-size reporting.
4. Whether specialist prompt-load budgets should exist for routed specialist activation.
5. Whether prompt-load budget status should remain an advisory warning, become a strict gate, or support both modes through an explicit strict flag.
