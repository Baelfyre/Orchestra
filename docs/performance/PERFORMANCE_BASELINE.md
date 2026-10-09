# Performance Baseline

## Purpose
To record the current Orchestra prompt-load and performance risk profile before router-first optimization begins. This baseline provides metrics and qualitative token load estimates to measure future efficiency gains.

## Scope
This baseline covers the execution payload of the core Orchestra plugins, specifically the orchestrator (`conductor`), governance authorities (`the-steward`, `the-governor`), and globally loaded configuration files (`plugin.json`, `README.md`).

## Baseline Summary
The current architecture relies on a full-context loading model. Initial plugin discovery and multi-skill tasks result in very high token consumption due to redundant instructions and monolithic skill definitions. The baseline risk profile is HIGH for both token window exhaustion and instruction dilution.

## Current Prompt Load Sources
- **`plugin.json`**: High prompt load. Contains extensive descriptions for 12+ skills.
- **`README.md`**: Very High prompt load (~614 lines). Often ingested fully by IDE hosts, containing irrelevant IDE setup instructions (lines 145-422).
- **`skills/conductor/SKILL.md`**: Very High prompt load (~296 lines). Contains exhaustive routing matrices and gate rules.
- **`skills/the-steward/SKILL.md`**: High prompt load (~195 lines).
- **`skills/the-governor/SKILL.md`**: High prompt load (~240 lines).
- **`docs/governance/GOVERNANCE_LAYER.md`**: High prompt load (~228 lines).
- **`ROUTING_MAP.md`**: Medium prompt load (~76 lines).
- **`SKILL_INDEX.md`**: Low prompt load (~25 lines).

## Current Routing Behavior
- **Monolithic Activation**: Conductor loads all routing paths, fallback behaviors, and detailed specialist matrices at once (e.g., frontend/backend alignment rules).
- **Redundant Processing**: Both the `plugin.json` descriptions and the `ROUTING_MAP.md` are evaluated concurrently when making routing decisions, increasing processing overhead.

## Current Governance Load
- **Full-File Intake**: When governance is invoked, the AI must ingest the entirety of `the-steward/SKILL.md` or `the-governor/SKILL.md`, including verbose formatting templates.
- **Duplicated Base Profiles**: Both governance skills independently define the "Project Context Profile", "Risk Classification", and "Adaptive Review Path".

## Known Duplication Sources
- **Project Context & Risk Models**: Duplicated across three files (`the-steward/SKILL.md`, `the-governor/SKILL.md`, `GOVERNANCE_LAYER.md`).
- **Skill Summaries**: Duplicated across three files (`plugin.json`, `SKILL_INDEX.md`, individual `SKILL.md` frontmatter).
- **IDE Setup**: Duplicated conceptually in `README.md` while `docs/setup/INSTALLATION.md` exists as the intended source.
- **Routing Rules**: Duplicated between `skills/conductor/SKILL.md` (lines 170-242) and `ROUTING_MAP.md`.

## Baseline Risks
- **Very High Token Cost**: Multi-step workflows incur massive cumulative costs due to repeated ingestion of non-relevant directives (e.g., installation guides).
- **Latency**: Time-to-first-token is significantly delayed for simple intents due to the large context window requirement.
- **Context Collapse**: Critical project-specific instructions risk being ignored by the LLM due to the high volume of static framework instructions.

## Measurement Notes
- Token counts are assessed qualitatively (Low, Medium, High, Very High) based on line counts and instruction density.
- "High" load generally corresponds to 150-300 lines of dense prompt text.
- "Very High" load generally corresponds to >300 lines or >15KB file sizes loaded indiscriminately.

## Optimization Targets
1. **Reduce `plugin.json` Load**: Transition descriptions to 1-2 sentence slugs.
2. **Componentize `README.md`**: Remove IDE setup instructions; point to external docs.
3. **Router-First Conductor**: Reduce `conductor/SKILL.md` by moving the matrix to `ROUTING_MAP.md` (loaded on-demand).
4. **Centralize Governance Context**: Remove duplicated risk and context models from `the-steward` and `the-governor`; reference a single shared source.

## Baseline Result
BASELINE_DOCUMENTED
