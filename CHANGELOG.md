# Changelog

This changelog tracks the repository history using git tags, merge history, and the prior documented milestone log that lived under `docs/meta/CHANGELOG.md`.

## Unreleased

### Added
- Added `orchestra_runtime/` runtime core models, services, factories, repositories, and thin Codex, Antigravity, and Claude Code adapters.
- Added runtime-core pytest coverage for skill loading, adapter contracts, and governance blocking for destructive and high-risk routes.
- Added `docs/project/OOP_RUNTIME_ARCHITECTURE.md` to document the runtime-core-first branch architecture and current integration points.
- Added Claude Code plugin compatibility files: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `docs/setup/INSTALLATION.md` with Claude Code installation instructions.
- Added validation script for Claude Code plugin: `scripts/validate_claude_plugin.py`

### Fixed
- Refactored manifest, skill, and adapter validation scripts to use the shared runtime repositories and registry instead of duplicating core loading logic.
- Fixed Claude Code marketplace source path from "." to "./" and bumped Claude plugin metadata to 1.0.1 so Claude Code can detect and refresh the plugin correctly.



- Added Cloak progressive disclosure template `bryl-minimal-design` for monochrome, typography-driven UI styling.
- Added behavior test scenario in `BEHAVIOR_TEST_MATRIX.md` to verify Cloak progressive disclosure template loading.
- Registered the new template in the Codex export validation allowlist to ensure proper structural verification.

- Added explicit Clockwork foundational OOP guidance and audit checklist coverage for encapsulation, abstraction, polymorphism, and inheritance.
- Added README open-source philosophy section clarifying Orchestra's reuse, attribution, and collaborative development stance.


### Changed

- Removed Docker-specific validation artifacts while preserving native Ubuntu/macOS cross-platform validation.
- Packaged Conductor router context docs into the Codex export and validated required backtick file references before runtime install.

### Added

- Added branch protection setup guide for configuring Orchestra required status checks on `main`.

### Added

- Added required status checks review for Orchestra branch protection and CI workflow policy.

### Added

- Added CI workflow consolidation review covering validate, Governance Check, and Cross-platform Validation workflow roles.

### Changed

- Clarified Steward context-validator negative test output so expected Release Mode blocking no longer appears as an unqualified CI error.

### Added

- Added native GitHub Actions cross-platform validation for Ubuntu and macOS.

### Changed

- Improved strict governance workflow logging so failed governance reports are printed before the job exits.

### Added

- Added Docker-based Linux validation support through `scripts/run-linux-validation.sh` and POSIX executable script handling.

- Strengthened Codex adapter export validation so governance skills, routable skills, and relative Markdown links are verified before Codex installation.

- Added Issue #56 router-first closeout note.

- Added final router-first readiness review for Issue #56 closeout.

- Added Phase 8 router-first hardening completion review.

- Added README maintainer entry points for router-first validation and observability docs.

- Cleaned router-first documentation terminology and consistency.

- Added router-first documentation cross-links for Phase 8 hardening.

- Added Phase 8A router-first integration hardening audit documentation.

- Documented the `tests/fixtures/router_benchmarks.json` schema in `ROUTER_BENCHMARK_FIXTURE_SCHEMA.md` and updated the benchmark validation runner to enforce the root shape and `schema_version`.

- Refactored `scripts/router_benchmark_runner.py` to extract hardcoded definitions into a machine-readable fixture at `tests/fixtures/router_benchmarks.json`, preserving existing validation capabilities.

- Documented CI artifact outputs in `CI_ARTIFACT_INDEX.md` to explain the reports generated during governance validation.

- Configured `governance-check.yml` CI workflow to run and publish the dry-run prompt load threshold checker report as a downloadable artifact.

- Added `scripts/check_prompt_load_thresholds.py` as a dry-run prompt load threshold checker to validate current metrics against documented soft limits without breaking CI.

- Defined `PROMPT_LOAD_THRESHOLD_POLICY.md` to establish soft limits and review triggers for context sizes in the router-first architecture, without introducing hard CI enforcement yet.

- Configured `governance-check.yml` CI workflow to run and publish `measure_prompt_load.py` output as a downloadable artifact for observability, without introducing hard prompt-size failure thresholds yet.

- Wired router benchmark validation (`scripts/router_benchmark_runner.py`) into the `governance-check.yml` CI workflow to automatically verify benchmark definitions on pull requests.

- Added structured automated router benchmark runner (`scripts/router_benchmark_runner.py`) to validate test case definitions without triggering live LLM behavior.

- Reduced `skills/conductor/SKILL.md` prompt payload by consolidating duplicate execution mode rules into canonical pointers, while preserving strict behavior conformance.

- Created `docs/performance/CONDUCTOR_LOAD_REDUCTION_PLAN.md` outlining a strategy to safely reduce `skills/conductor/SKILL.md` prompt load while preserving governance behavior and test fixtures.

- Created `scripts/measure_prompt_load.py` to calculate approximate token sizes of contextual documentation.
- Added `PROMPT_LOAD_METRICS.md` defining token estimation heuristics and context exclusion groups.

- Defined `ROUTER_VALIDATION_BENCHMARKS.md` to benchmark the efficiency, accuracy, and safety of the router-first execution model against the legacy monolithic context approach.

- Wired Execution Modes Policy (`docs/routing/EXECUTION_MODES_POLICY.md`) into Conductor.
- Replaced legacy Ideation/Prototype/Release modes with formal FAST, STANDARD, GOVERNED, AUDIT, and DESTRUCTIVE modes.

- Created `EXECUTION_MODES_POLICY.md` to formalize FAST, STANDARD, GOVERNED, AUDIT, and DESTRUCTIVE modes.
- Defined mode escalation paths, exclusions, and matrix.

- Implemented router-first execution and selective context loading policy to optimize Conductor prompt payload.
- Added `ROUTER_FIRST_ARCHITECTURE.md`, `CONTEXT_RETRIEVAL_RULES.md`, and `MINIMAL_PROMPT_FORMAT.md`.
- Synced plugin manifest, `SKILL_INDEX.md`, and skill frontmatter metadata for precise validation parity.

- Added behavior fixtures validating Conductor routing for Cloak multi-stage workflow preservation and frontend/backend alignment with Clockwork, Cipher, and Chronicler.

- Added Conductor routing rules for Cloak and backend alignment, requiring Clockwork, Cipher, and/or Chronicler before implementation when frontend work affects data, auth, APIs, persistence, security, privacy, integrations, payments, or compliance-sensitive workflows.

- Added Cloak multi-stage frontend design workflow guidance covering discovery, strategy, pattern intelligence, semantic HTML, design review, and backend alignment triggers.

- Added explicit least-privilege permissions to the Governance Check workflow.

### Changed
- Updated GitHub Actions dependencies for the governance workflow:
  - actions/checkout from v4 to v7
  - actions/setup-python from v5 to v6
  - actions/upload-artifact from v4 to v7

Changes after `v1.0.1` currently tracked in this checkout:

- Added local repository sync preflight governance check (`scripts/preflight_sync_check.py`) for new development phases and editing sessions.
- Added contributor, agent, and governance rules requiring preflight sync verification against `origin/main` before local editing begins.
- Added Codex Marketplace installation instructions to README and setup guides.
- Expanded specialist foundations for Arbiter, Clockwork, Cipher, Cloak, and Ponytail.
- Aligned Conductor routing, Codex export, and stale-reference handling, including routing arrow and encoding fixes.
- Added governance guardrails, access and visibility evidence rules, CI validation notes, and refined visual validation guidance.
- Refreshed README presentation and selective skill icons, and added Ponytail and Caveman companion links.
