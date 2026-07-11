# Router-First Architecture

## Purpose
To define the target execution architecture for the Orchestra ecosystem that mitigates the high token load and instruction dilution identified in the performance baseline. This architecture transitions the `conductor` from a monolithic prompt model to a dynamic, router-first execution model.

## Problem Statement
Currently, `skills/conductor/SKILL.md` loads all routing matrices, edge cases, and specialist rules upfront. In parallel, `plugin.json` and governance docs inject heavy context repeatedly. This causes high token consumption, degrades LLM precision due to context dilution, and limits scalability as new skills are introduced. 

## Design Goals
1. **Minimize Initial Prompt Load**: Conductor should start with the smallest possible intent-classifier prompt.
2. **Selective Context Retrieval**: Heavy matrices (e.g., `ROUTING_MAP.md`) and governance rules (`docs/governance/GOVERNANCE_LAYER.md`) are only fetched when strictly required.
3. **Decouple Skill Definitions**: Keep detailed skill summaries in `SKILL_INDEX.md` and keep `plugin.json` lightweight.
4. **Preserve Current Capabilities**: Achieve optimization without losing governance enforcement or routing accuracy.

## Proposed Execution Pipeline
1. **Intake Phase**: User prompt hits Conductor. Conductor loads only its core classifier prompt (not the full routing matrix).
2. **Intent & Mode Detection**: Conductor identifies the task goal and operating mode (Ideation, Prototype, Implementation, Audit, Release).
3. **Context Hydration**: Based on intent, Conductor retrieves specific supporting documents (e.g., `ROUTING_MAP.md`, `docs/governance/GOVERNANCE_LAYER.md`).
4. **Governance Escalation**: If the task hits a risk trigger, Conductor invokes `the-steward` or `the-governor`.
5. **Execution Routing**: Conductor routes the final assembled task to the executing specialist.

## Intent Classification Layer
A lightweight module within the new `conductor` prompt that categorizes the user's request. It checks:
- Is this a single-domain task or multi-skill task?
- Is the target clearly defined?
- Does it require a governance gate?

## Skill Index Lookup
Instead of embedding every skill's rule inside Conductor, Conductor will rely on `SKILL_INDEX.md` for a quick scan of capabilities. Detailed behaviors remain encapsulated within each specialist's `SKILL.md`.

## Context Retrieval Layer
A mechanism where Conductor conditionally reads:
- `ROUTING_MAP.md` only when the route is ambiguous or multi-step.
- `docs/governance/GOVERNANCE_LAYER.md` only when a formal audit or release validation is requested.

## Execution Mode Selection
Conductor will determine the operating mode early to bypass unnecessary checks:
- **Ideation / Prototype**: Bypass deep governance loading.
- **Implementation**: Load fast-path checks.
- **Audit / Release**: Load full governance contexts.

## Governance Escalation Rules
Instead of loading `skills/the-steward/SKILL.md` and `skills/the-governor/SKILL.md` by default, Conductor will only hand off to these authorities if:
- The task involves public release, PII, or high-risk components.
- The operating mode is Audit or Release.
- A continuity break is detected (escalating to `arbiter`).

## Minimal Prompt Assembly
The new `skills/conductor/SKILL.md` will be refactored to focus solely on the intake pipeline and escalation rules. The exhaustive routing examples and frontend/backend alignment rules will be relocated to `ROUTING_MAP.md`.

## Non-Goals
- Altering the fundamental behavior of executing skills (e.g., `ponytail`, `cloak`).
- Removing governance authorities (Steward, Governor, Arbiter).
- Implementing new runtime CI/CD checks (this remains instruction-level governance).

## Implementation Sequence
1. Refactor `plugin.json` descriptions to be concise.
2. Relocate routing matrix rules from `skills/conductor/SKILL.md` to `ROUTING_MAP.md`.
3. Rewrite `skills/conductor/SKILL.md` to act as the lightweight Intent Classification Layer.
4. Clean up duplicated governance context from `the-steward` and `the-governor`.

## Success Criteria
- Conductor's base `SKILL.md` is reduced by at least 50% in line count.
- `plugin.json` size is significantly reduced.
- Multi-skill tasks successfully load `ROUTING_MAP.md` dynamically.
- `git status` behavior tests pass without regression.

## Architecture Result
ROUTER_ARCHITECTURE_DEFINED

## Related Documents
- [Context Retrieval Rules](CONTEXT_RETRIEVAL_RULES.md)
- [Minimal Prompt Format](MINIMAL_PROMPT_FORMAT.md)
- [Execution Modes Policy](EXECUTION_MODES_POLICY.md)
- [Phase 8A Audit](ROUTER_FIRST_INTEGRATION_HARDENING_AUDIT.md)
