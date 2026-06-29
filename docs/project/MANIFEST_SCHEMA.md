# Future Plugin Manifest Schema

> [!WARNING]
> This is a **proposed schema for future plugin readiness**, not an active plugin manifest requirement. Orchestra is currently a Markdown-first framework that does not use or require a runtime plugin loader.

If and when a plugin loader is developed for the Orchestra, it should extract the existing `SKILL.md` frontmatters to compile a central manifest.

## Proposed JSON Schema Structure

A future loader might generate a JSON file (e.g., `plugin-manifest.json`) using the following fields:

- `name`: Human-readable name of the skill.
- `description`: Legacy compatibility description of the skill.
- `slug`: Unique identifier for the skill (e.g., `cloak`).
- `role`: The job description or title of the skill.
- `primary_use`: The core tasks the skill excels at.
- `avoid_when`: Conditions under which the skill should not be loaded.
- `activation_level`: The rank of the skill (e.g., `Commander`, `Specialist`, `Gated`).
- `depends_on`: Other skills required to function (e.g., `dagger` depends on `conductor`).
- `output_formats`: Array of supported formats (e.g., `[Compact, Full]`).
- `skill_path`: The relative path to the `SKILL.md` file.
- `icon_path`: The relative path to the skill's visual icon.

By maintaining this structured YAML metadata directly inside the `SKILL.md` files, the repository ensures zero drift between the human-readable Markdown documentation and any future machine-readable JSON manifests.

## Manifest verification

- The YAML frontmatter in each `SKILL.md` is the **absolute source of truth**.
- The `examples/plugin-manifest.example.json` file must match the frontmatter exactly.
- The `scripts/validate-manifest.ps1` script explicitly verifies the example JSON manifest against the live skill metadata, preventing documentation drift.
