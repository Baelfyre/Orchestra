# Plugin Readiness

This document tracks the readiness of the Orchestra framework for its release as the **Conductor** installable plugin.

## Status

- **Installable structure status:** Completed
  - A root `plugin.json` manifest has been added.
  - The repository layout matches installable plugin expectations.
- **Command exposure status:** Completed
  - Top-level `commands/` directory added with clean user-facing entry points (e.g. `conductor`, `review-architecture`, `resilience-check`).
  - Commands accurately map to their respective specialized skills.
  - The `resilience-check` command explicitly requires a safety gate and user approval.
- **Skill coverage status:** Completed
  - All 9 core specialist skills are fully documented and integrated.
  - Handled by `plugin.json` skills array correctly.
- **Repository rename status:** Completed
  - GitHub repo has been renamed to `Baelfyre/Orchestra`.
  - Active plugin and command identity now uses `conductor`.
  - Legacy names such as `amalgam-conductor` are compatibility aliases only.
- **Plugin install validation status:** Completed
  - `agy plugin install https://github.com/Baelfyre/Orchestra` successfully processed 9 skills and 9 commands.
- **Plugin icon status:** Completed
  - The existing Conductor icon is used as the plugin icon: `assets/icons/conductor.ico`.
  - The broader framework logo remains available at `assets/logo/orchestra.png`.
- **Remaining step:** Pending
  - Validate whether the target plugin loader displays the manifest-level icon path.

---

Orchestra is intentionally designed as a **Markdown-first** framework. By keeping skill instructions, progressive disclosure rules, and routing metadata in standard markdown format, the framework remains universally readable by any AI assistant capable of file reading (e.g., Claude Code, Cursor, Antigravity) without requiring a proprietary runtime plugin.

However, as agentic platforms evolve, automated skill discovery and deterministic loading become valuable. This document outlines how future plugin loaders should interact with the Orchestra without breaking its fundamental architecture.

## How Loaders Should Discover Skills
- A loader should scan the `skills/` directory for folders containing a `SKILL.md` file.
- The root `SKILL_INDEX.md` and `ROUTING_MAP.md` serve as the source of truth for the available skills.

## Reading Metadata
- Every `SKILL.md` contains a YAML frontmatter block.
- Loaders should parse this block (which includes `slug`, `role`, `primary_use`, `avoid_when`, `activation_level`, `depends_on`, and `output_formats`) to build an internal routing index.
- This metadata allows an agent to decide which skill to load before ever reading the `SKILL.md` body.
- **Note:** Future plugin loaders should treat any generated or verified manifest JSON as discovery hints only. They are not a replacement for reading the authoritative Markdown skill files when performing actual work.

## Using the Routing Map
- The root `ROUTING_MAP.md` is a lightweight lookup table.
- A future loader should load this file when a task overlaps multiple domains or ownership is unclear.
- The `conductor` skill uses this map as its primary source of truth for delegating complex tasks.

## Deferring Outputs (Progressive Disclosure)
- A future loader **must not** greedily load the `OUTPUT_FORMATS.md` file when initializing a skill.
- The framework is designed for token efficiency. Output formats should only be loaded at the very end of the LLM's workflow when it is ready to generate the final response or artifact.

## The Principle of Minimal Loading
- Loaders should load the smallest useful skill stack.
- Activating a skill means injecting its `SKILL.md` into context. Loading every skill simultaneously defeats the token-efficiency architecture and confuses the model.
- **Never load by default**: Examples folders (`examples/`), large supporting templates, and outputs.

## External Influences
- Note: External compression/efficiency frameworks like Ponytail and Caveman serve as conceptual inspirations for this repository's focus on brevity, but they are external tools and are **not bundled dependencies** required by this framework.
