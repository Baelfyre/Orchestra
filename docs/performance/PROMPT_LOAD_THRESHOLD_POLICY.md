# Prompt Load Threshold Policy

## Purpose
This policy defines the bounds for acceptable prompt payload sizes during the Conductor's routing phase. It establishes soft thresholds to ensure the router-first architecture remains highly performant and cost-efficient.

## Scope
This policy applies to context files loaded during the initial routing phase, specifically targeting the files measured by `scripts/measure_prompt_load.py`.

## Measurement Source
All thresholds are based on the output of `scripts/measure_prompt_load.py`, which provides a lightweight character count and an approximate token count.

## Threshold Philosophy
- The Conductor's default prompt load must remain as small as possible to ensure fast and cheap routing.
- Hard CI failure thresholds will not be introduced until baseline metrics show long-term stability and predictability.
- Exceeding a soft threshold does not fail the build, but triggers a mandatory maintainer review.

## Current Baseline
As of the initial measurement, the baseline metrics are:
- Group A (Core Router-First Minimal Context): ~7087 estimated tokens
- Group B (Broader Routing Context): ~5027 estimated tokens
- Group C (Governance Context): ~2636 estimated tokens
- Group D (Baseline Performance Docs): ~2330 estimated tokens
- Grand Total: ~17080 estimated tokens

## Soft Thresholds
Soft thresholds act as observability triggers.
- **Group A (Core Context)**: Should remain under 8,000 estimated tokens.
- **Group B (Broader Context)**: Should remain under 6,000 estimated tokens.
- **Group C (Governance Context)**: Allowed to grow as compliance rules evolve, but should remain under 4,000 estimated tokens.
- **Grand Total**: Should remain under 20,000 estimated tokens.

## Warning Thresholds
- **Group A Growth**: If Group A increases by more than 10% from the baseline, a warning is raised.
- **Conductor Growth**: If `skills/conductor/SKILL.md` grows by more than 15% from its baseline, a warning is raised.

## Review Thresholds
Maintainers must conduct a formal review if:
- A new file is added to Group A without explicit justification for why it cannot live in Group B or C.
- Any single canonical routing document becomes larger in token size than the Conductor skill itself.
- Governance-required phrases expand significantly without a corresponding test or policy justification.

## Future Hard-Fail Thresholds
Hard-fail thresholds will be introduced in a future milestone once:
1. The router-first architecture has stabilized over multiple release cycles.
2. The variance in prompt size across normal development activities is well understood.
3. A formal tokenization library replaces the current approximation script.

## Recommended Actions When Thresholds Are Exceeded
If a soft threshold is exceeded, maintainers should:
1. **Split Documents**: Move non-critical context into secondary files loaded only upon specific intent triggers.
2. **Shorten Phrasing**: Refine the documentation to be more concise without losing governance meaning.
3. **Move to Selective Retrieval**: Ensure the file is not loaded by default but instead selectively fetched via `ask_question` or `grep_search`.

## CI Artifact Usage
The `measure_prompt_load.py` script runs automatically in the `governance-check.yml` CI workflow. Its output is published as `prompt_load_metrics.txt` in the `governance-validation-report` artifact. This ensures continuous observability of prompt load metrics.

## Non-Goals
This policy does not govern user prompt sizes, session history limits, or downstream specialist output tokens. It only governs the static context injected into the Conductor's routing prompt.

## Policy Result
PROMPT_LOAD_THRESHOLD_POLICY_DEFINED
