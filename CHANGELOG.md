# Changelog

This changelog tracks the repository history using git tags, merge history, and the prior documented milestone log that lived under `docs/meta/CHANGELOG.md`.

## v1.0.0 - Portable Runtime

Portable Runtime is the first Orchestra release that normalizes the repository around a shared runtime core, thin adapters, and a versioned adapter protocol.

### Release Highlights
- Added `orchestra_runtime/` as the shared runtime core for routing, manifest parsing, skill loading, governance validation, execution flow, and audit logging.
- Added `PRAP v1` as the stable Portable Runtime Adapter Protocol for host metadata, capabilities, compatibility, and validation.
- Added thin adapter support for Codex, Claude Code, Antigravity, Cursor, Windsurf, VS Code, VSCodium compatibility, JetBrains, Zed, and Neovim.
- Added scaffold-only packaging surfaces for Cursor, Windsurf, VS Code, JetBrains, Zed, and Neovim.
- Normalized release-facing documentation, compatibility guidance, and manifest metadata for the `v1.0.0 Portable Runtime` baseline.

## Pre-release Build History

## Unreleased

### Added
- Added an App Release Compliance Gate plus reusable privacy review, data inventory, IP clearance, privacy policy, terms, and retention/deletion governance templates for app and public release workflows.
- Added a shared `docs/project/SPECIALIST_AUTHORING_STANDARD.md` reference for future specialist authoring, with short cross-links from contributing, plugin-readiness, and manifest-schema documentation.

### Changed
- Clarified governance authority boundaries for Arbiter status vocabulary, Steward hygiene wording, and Governor/Cipher release-security ownership without changing governance semantics.
- Clarified Governance Strictness Levels as a derived scale over existing project type, operating mode, release stage, and risk classifications without changing governance semantics.
- Integrated Release Mode governance docs so The Governor now treats app release compliance artifacts as required when applicable and returns `REVISION_REQUIRED` or `BLOCKED` when release-gate documentation is missing.
- Strengthened Cloak's documentation-only frontend review contract with artifact-evidence requirements, clearer form and validation messaging review, explicit loading/empty/error/success/retry/permission-state review, sharper frontend handoff blueprint guidance, and matching tracked Codex export parity for the updated Cloak docs.
- Normalized Conductor's skill documentation against the shared specialist authoring standard by clarifying activation conditions, supported work, scope enforcement, validation expectations, local-only safety, and direct-route versus orchestration versus reroute guidance, with matching tracked Codex export parity.
- Normalized Ponytail specialist documentation with explicit activation conditions, supported work, scope enforcement, validation expectations, local-only safety, and direct handoff boundaries for implementation-owned code changes, with matching tracked Codex export parity.
- Normalized Clockwork specialist documentation with explicit activation conditions, supported work, role boundaries, scope enforcement, validation expectations, local-only safety, and direct architecture-boundary handoff guidance, with matching tracked Codex export parity.
- Normalized Cipher specialist documentation with explicit defensive-security ownership boundaries, validation expectations, local-only safety, handoff guidance, and output-format selection while preserving its defensive-only scope.
- Normalized Overseer specialist documentation with explicit validation ownership boundaries, evidence expectations, local-only safety, expanded handoff guidance, and output-format selection while preserving its validation/readiness scope.
- Normalized Chronicler specialist documentation with explicit persistence ownership boundaries, supported work, validation expectations, output-format selection, and expanded handoff guidance while preserving its database and data-integrity scope.
- Normalized Scribe specialist documentation with explicit documentation ownership boundaries, activation conditions, validation expectations, output-format selection, and expanded handoff guidance while preserving its source-backed documentation scope.
- Normalized Weaver specialist documentation with explicit diagram ownership boundaries, activation conditions, validation expectations, output-format selection, and expanded handoff guidance while preserving its visual-modeling scope.
- Cleaned up cross-specialist consistency by aligning Scribe output-format headings and adding compact Cloak role-boundary and validation-expectation sections without changing specialist behavior.

### Changed
- Clarified optional project governance rulesets so `PROJECT_CONTEXT.md` enforcement depends on project type, risk level, and declared governance level.
- Wired `tests/runtime` into CI, enforced portable runtime coverage with `pytest-cov --cov-fail-under=90`, switched `validate.yml` to `python tests/behavior/run_tests.py`, and added runtime tests for alias loading, default-command fallback, and unresolved command-to-skill handling.

### Added
- Added root `PROJECT_CONTEXT.md` for Orchestra and wired project-context validation into governance CI.
- Added a reusable `PROJECT_CONTEXT.md` template and aligned the Python project-context validator with advisory, recommended, and strict-governed enforcement behavior.
- Added a context-sensitive `PROJECT_CONTEXT.md` enforcement policy defining advisory, recommended, and strict-governed validation modes based on project type and risk level.
- Added a Steward-led `PROJECT_CONTEXT.md` decision prompt for choosing advisory or governed project context workflows before introducing hard enforcement.
- Added scaffold adapter graduation criteria defining promotion levels, validation requirements, documentation requirements, and recommended graduation order for scaffold-only adapters.
- Added `scripts/check_for_updates.py` for notification-only release checks against the latest GitHub release using local manifest and adapter metadata.
- Added update-check metadata defaults to the root manifest, Claude plugin manifest, and scaffold adapter package metadata.
- Added runtime tests covering current-version, newer-release, invalid-version, unavailable-GitHub, and disabled-update-check behavior.
- Added a temp-staged Codex runtime refresh pipeline that exports to a temporary directory, validates staged output, installs into repo-local and global Codex runtime locations, verifies file-list and SHA-256 parity, and deletes staged output by default.
- Added reusable PowerShell directory parity helpers for recursive file-list and SHA-256 comparison across staged and installed runtime surfaces.

### Added
- Added `orchestra_runtime/protocol/` with the Portable Runtime Adapter Protocol (`PRAP v1`), including versioned adapter metadata, capabilities, compatibility records, and protocol validation.
- Added runtime protocol tests covering metadata completeness, capability validation, compatibility matrix coverage, VSCodium compatibility, and unknown adapter rejection.
- Added `docs/project/PORTABLE_ADAPTER_PROTOCOL.md` to document protocol flow, ownership boundaries, compatibility guarantees, and future extension points.
- Added scaffold-only Zed and Neovim packaging files and metadata that point to the existing `ZedAdapter` and `NeovimAdapter` runtime contracts without introducing marketplace publication.
- Added scaffold-only JetBrains packaging files and metadata that point to the existing `JetBrainsAdapter` runtime contract without introducing marketplace publication.
- Added scaffold-only packaging folders and package manifests for Cursor, Windsurf, and VS Code that point to the shared runtime adapters without introducing marketplace publication.
- Added contract-ready runtime adapters for Cursor, Windsurf, VS Code, JetBrains, Zed, and Neovim without introducing marketplace packaging.
- Added `orchestra_runtime/` runtime core models, services, factories, repositories, and thin Codex, Antigravity, and Claude Code adapters.
- Added runtime-core pytest coverage for skill loading, adapter contracts, and governance blocking for destructive and high-risk routes.
- Added `docs/project/OOP_RUNTIME_ARCHITECTURE.md` to document the runtime-core-first branch architecture and current integration points.
- Added Claude Code plugin compatibility files: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `docs/setup/INSTALLATION.md` with Claude Code installation instructions.
- Added validation script for Claude Code plugin: `scripts/validate_claude_plugin.py`

### Fixed
- Extended IDE packaging validation so runtime adapter scaffolds are checked against PRAP metadata and packaging/runtime adapter alignment.
- Added IDE packaging validation so scaffold manifests, required files, and runtime adapter references are checked centrally.
- Refactored manifest, skill, and adapter validation scripts to use the shared runtime repositories and registry instead of duplicating core loading logic.
- Fixed Claude Code marketplace source path from "." to "./" and aligned Claude plugin metadata with the release baseline so Claude Code can detect and refresh the plugin correctly.
- Fixed Codex refresh so normal installs no longer dirty tracked export folders during runtime refreshes.



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
- Clarified Governor and Cipher skill-source authority boundaries between governance/compliance sufficiency and technical defensive security review.
- Updated GitHub Actions dependencies for the governance workflow:
  - actions/checkout from v4 to v7
  - actions/setup-python from v5 to v6
  - actions/upload-artifact from v4 to v7

Additional release-prep changes included in this checkout:

- Added local repository sync preflight governance check (`scripts/preflight_sync_check.py`) for new development phases and editing sessions.
- Added contributor, agent, and governance rules requiring preflight sync verification against `origin/main` before local editing begins.
- Added Codex Marketplace installation instructions to README and setup guides.
- Expanded specialist foundations for Arbiter, Clockwork, Cipher, Cloak, and Ponytail.
- Aligned Conductor routing, Codex export, and stale-reference handling, including routing arrow and encoding fixes.
- Added governance guardrails, access and visibility evidence rules, CI validation notes, and refined visual validation guidance.
- Refreshed README presentation and selective skill icons, and added Ponytail and Caveman companion links.
