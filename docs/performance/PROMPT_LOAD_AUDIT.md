# Prompt Load Audit

## Purpose
To audit the current Orchestra repository structure and identify performance bottlenecks caused by broad or always-loaded context. This document outlines duplicated instructions, high-token sections, and opportunities for selective, router-first context loading.

## Scope
This audit targets `plugin.json`, governance documentation (`docs/governance/GOVERNANCE_LAYER.md`), core routing docs (`ROUTING_MAP.md`, `SKILL_INDEX.md`), the `README.md`, and primary skills (`conductor`, `the-steward`, `the-governor`).

## Repository Areas Reviewed
- `plugin.json`
- `README.md`
- `AGENTS.md`
- `ROUTING_MAP.md`
- `SKILL_INDEX.md`
- `docs/governance/GOVERNANCE_LAYER.md`
- `skills/conductor/SKILL.md`
- `skills/the-steward/SKILL.md`
- `skills/the-governor/SKILL.md`

## Current Execution Model
Currently, context loading relies heavily on full-file inclusion. AI hosts typically load `plugin.json` (which contains large descriptions for every skill) on every invocation. When users invoke governance or orchestration tools, entire skill manifests (like `conductor`, `the-steward`, `the-governor`) are loaded, each containing 200 to 300 lines of prompt text, leading to massive upfront token ingestion regardless of the task's complexity.

## Always-Loaded or Broadly Loaded Context
- `plugin.json`: Contains long descriptions and output formats for every skill, loaded universally by the plugin system.
- `skills/conductor/SKILL.md`: 296 lines of dense routing rules, gates, and matrices loaded whenever orchestration is invoked.
- `README.md`: Often ingested in its entirety (614 lines) by AI hosts for repository context, despite a large portion being IDE-specific installation guides.

## Duplicated or Overlapping Instructions
1. **Project Context Profile**: The exact same block detailing `Project Type`, `Release Stage`, and `Risk Level` is duplicated across `skills/the-steward/SKILL.md`, `skills/the-governor/SKILL.md`, and `docs/governance/GOVERNANCE_LAYER.md`.
2. **Risk Classification**: The `LOW` / `MEDIUM` / `HIGH` risk table is repeated identically in Steward, Governor, and the Governance Layer doc.
3. **Adaptive Review Path**: Steps 1-5 for adaptive reviews are identical in both Steward and Governor skill definitions.
4. **Separation of Concerns**: The explanation of which layer owns which domain is restated in Steward, Governor, and the Governance Layer doc.
5. **Skill Descriptions**: The descriptions in `plugin.json` duplicate the text found in `SKILL_INDEX.md` and the frontmatter of individual `SKILL.md` files.

## High-Token Sections
- **IDE Installation Guides**: `README.md` lines 145-422 provide setup instructions for Antigravity, Codex, VS Code, and IntelliJ. This is unnecessary for runtime task execution.
- **Task Type Detection & Routing Matrix**: `skills/conductor/SKILL.md` lines 170-242 define an exhaustive routing matrix. This largely duplicates the purpose of `ROUTING_MAP.md`.
- **Output Format Templates**: `the-steward/SKILL.md` and `the-governor/SKILL.md` contain large markdown templates for both compact and expanded output formats.

## Performance Risks
- **Context Window Exhaustion**: Repeated and duplicated rules consume token limits quickly during long sessions.
- **Instruction Dilution**: LLMs may become confused by identical but slightly varied rules across multiple files, degrading precision.
- **Latency & Cost**: Increased time-to-first-token (TTFT) and higher inference costs due to loading irrelevant context (like installation instructions) during routine development tasks.

## Candidate Context Categories
To enable selective loading, context can be segmented into:
1. **Core Orchestration**: Lightweight intent classification and operating mode selection (Always loaded for Conductor).
2. **Specialized Routing**: The routing matrix (Loaded only if intent is unclear or multi-skill).
3. **Governance Definitions**: Risk classification and project context profiling (Loaded only when `Mode = Audit/Release` or risk requires it).
4. **Environment Context**: Installation and setup instructions (Loaded only explicitly for onboarding or troubleshooting).

## Candidate Routing Opportunities
- **Extract Governance Context**: Move the "Project Context Profile", "Risk Classification", and "Adaptive Review Path" into a shared configuration file or limit them to `GOVERNANCE_LAYER.md`, referencing them rather than embedding them in `the-steward` and `the-governor`.
- **Offload Routing Matrix**: Remove the "Task Type Detection & Routing Matrix" from `skills/conductor/SKILL.md` and instruct Conductor to read `ROUTING_MAP.md` only when the route isn't obvious.
- **Streamline README.md**: Move the IDE installation guides entirely out of `README.md` and point to `docs/setup/INSTALLATION.md`.
- **Trim plugin.json**: Reduce descriptions in `plugin.json` to 1-2 sentence summaries, deferring to `SKILL.md` or `SKILL_INDEX.md` for full details.

## Recommended Next Step
Refactor the Conductor skill to implement a "Router-First" model where it initially loads a minimal intent-classifier prompt, and then dynamically reads `ROUTING_MAP.md` or `GOVERNANCE_LAYER.md` based on the detected operating mode.

## Audit Result
AUDIT_ONLY_COMPLETE
