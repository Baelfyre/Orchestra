# Kontrolled Kaos Plugin Readiness

This document tracks the existing framework package surfaces under the public Kontrolled Kaos identity. The package version and host support tiers do not establish release or publication readiness.

## Status

- **Installable structure status:** Completed
  - A root `plugin.json` manifest has been added.
  - The repository layout matches installable plugin expectations.
- **Command exposure status:** Completed
  - Top-level `commands/` directory added with clean user-facing entry points (e.g. `conductor`, `review-architecture`, `resilience-check`).
  - Commands accurately map to their respective specialized skills.
  - The `resilience-check` command explicitly requires a safety gate and user approval.
- **Skill coverage status:** Completed
  - All manifest-declared skills are fully documented and integrated.
  - The current `plugin.json` skills array validates against the repository source of truth.
- **Public identity status:** Rebrand in progress
  - Canonical repository: `Baelfyre/Kaos`.
  - Public product name: `Kontrolled Kaos`.
  - `conductor` remains the existing internal routing specialist; all specialist IDs and mappings are preserved.
- **Plugin install validation status:** Completed
  - Install validation is now treated as manifest-driven and verified through repository validators instead of hardcoded historical counts.
- **Product icon status:**
  - The product icon and logo use the approved Dual K master at `assets/branding/kontrolled-kaos-dual-k-emblem.png`.
  - Specialist icons, including the Conductor icon, remain unchanged.
- **Scaffold adapter promotion policy:** Defined
  - Scaffold-only host promotion now follows `docs/project/SCAFFOLD_ADAPTER_GRADUATION_CRITERIA.md` before support or marketplace claims are raised.
- **Remaining step:** Host qualification
  - Manifest validation does not prove interactive invocation in a live host. See `docs/project/KAOS_REBRAND_DECISION.md` for the current validation boundary.

---

Kontrolled Kaos is intentionally designed as a **Markdown-first** framework. By keeping skill instructions, progressive disclosure rules, and routing metadata in standard markdown format, it remains universally readable by any AI assistant capable of file reading (e.g., Claude Code, Cursor, Antigravity) without requiring a proprietary runtime plugin.

However, as agentic platforms evolve, automated skill discovery and deterministic loading become valuable. This document outlines how plugin loaders should interact with Kontrolled Kaos without breaking its fundamental architecture.

## How Loaders Should Discover Skills
- A loader should scan the `skills/` directory for folders containing a `SKILL.md` file.
- The root `SKILL_INDEX.md` and `ROUTING_MAP.md` serve as the source of truth for the available skills.

## Reading Metadata
- Every `SKILL.md` contains a YAML frontmatter block.
- Loaders should parse this block (which includes `slug`, `role`, `primary_use`, `avoid_when`, `activation_level`, `depends_on`, and `output_formats`) to build an internal routing index.
- This metadata allows an agent to decide which skill to load before ever reading the `SKILL.md` body.
- **Note:** Future plugin loaders should treat any generated or verified manifest JSON as discovery hints only. They are not a replacement for reading the authoritative Markdown skill files when performing actual work.
- For the repository-local authoring contract around specialist frontmatter, boundaries, handoffs, and safety rules, see [Specialist Authoring Standard](SPECIALIST_AUTHORING_STANDARD.md).

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
