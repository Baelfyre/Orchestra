# Changelog

## v0.7.0 - Phase 6: Manifest verification (2026-06-20)

- Added a standalone manifest verification script (`scripts/validate-manifest.ps1`).
- Implemented robust frontmatter-to-manifest consistency checks to prevent documentation drift.
- Ensured the Markdown-first `SKILL.md` frontmatter remains the absolute source of truth.
- Zero runtime plugin implementation added. Plugin schema examples strictly verified.

## v0.6.0 - Phase 5: Plugin readiness and metadata discovery (2026-06-20)

- Added `PLUGIN_READINESS.md` documenting how future LLM loaders can extract routing metadata and lazily load outputs while preserving the core Markdown-first architecture.
- Added `MANIFEST_SCHEMA.md` to establish a clean YAML-to-JSON manifest structure.
- Created an example plugin manifest (`examples/plugin-manifest.example.json`) demonstrating how the 8 skills map perfectly to standard plugin attributes.
- Updated `README.md` to highlight the non-breaking plugin readiness.
- Validated structure to enforce the permanent presence of these new metadata and example files.

## v0.5.0 - Phase 4: Live Behavior Testing (2026-06-20)

- Created a dedicated manual behavior testing framework (`tests/behavior/`) to validate Progressive Disclosure rules in live LLM environments.
- Added `BEHAVIOR_TEST_MATRIX.md` covering 8 realistic prompt scenarios (one for each major skill path).
- Added `MANUAL_TESTING_GUIDE.md` to instruct users how to verify that LLMs defer token-heavy formatting templates correctly.
- Updated structure validation scripts to require these testing documents.

## v0.4.0 - Phase 3: Routing metadata and drift prevention (2026-06-20)

- Added lightweight structured metadata (e.g. `slug`, `role`, `primary_use`, `avoid_when`) to the frontmatter of all core `SKILL.md` files to prevent drift and lay groundwork for automated plugin loading.
- Created a root-level `ROUTING_MAP.md` that maps common tasks to the correct specialist skill in a concise, scanner-friendly format.
- Merged the Conductor's legacy conflict resolution logic into `ROUTING_MAP.md` and removed the stale `ROUTING_MATRIX.md` file.
- Updated Amalgam Conductor to lazily load the routing map only when workflow coordination is unclear.
- Standardized `SKILL_INDEX.md` to precisely reflect the new structured metadata fields.


## v0.3.0 - Phase 2: Token efficiency via template extraction (2026-06-20)

- Extracted all large output format templates from core `SKILL.md` files into standalone `OUTPUT_FORMATS.md` files to drastically improve token efficiency.
- Updated the Progressive Disclosure Rule in all skills to only load formatting templates when generating final output.
- Updated structure validation scripts to require `OUTPUT_FORMATS.md` inside every skill folder.

## v0.2.0 - Structural consistency, visual identity, and cross-platform improvements (2026-06-20)

- Organized project and skill artwork under `assets/` and added it to the README and skill pages.
- Standardized skill activation, progressive disclosure, conductor integration, and output headings.
- Added MIT licensing, POSIX stale-reference validation, asset checks, and dynamic structure counts.
- Improved validation guidance, templates, and local-only documentation.

## v0.1.0 - Initial packaging (2026-06-20)

- Created the clean repository package.
- Added the eight-skill Orchestra of Amalgamation structure.
- Added IDE adapter guides and templates.
- Added validation and local-only guidance.
