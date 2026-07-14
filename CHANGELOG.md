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

### Phase 4B Post-Merge Hardening

- **Artificer Governance Validators:** Added rigorous rejection of ancestor-directory symlinks for governance registries, records, and pattern bundles.
- **Artificer Governance Validators:** Corrected cross-platform list stability by introducing dual-key tuples `(item.name.casefold(), item.name)` in deterministic sort tie-breakers.

## v1.1.0 - Specialist Governance & Boundary Standard

Specialist Governance & Boundary Standard is a documentation-, governance-, metadata-, and specialist-definition-focused release that builds on the `v1.0.0 Portable Runtime` baseline without changing runtime behavior, routing policy, validation logic, CI workflows, Dagger live-execution behavior, or governance decision semantics.

### Added
- Added a shared `docs/project/SPECIALIST_AUTHORING_STANDARD.md` reference for future specialist authoring, with short cross-links from contributing, plugin-readiness, and manifest-schema documentation.

### Changed
- Clarified governance authority boundaries for Arbiter status vocabulary, Steward hygiene wording, and Governor/Cipher release-security ownership without changing governance semantics.
- Clarified Governance Strictness Levels as a derived scale over existing project type, operating mode, release stage, and risk classifications without changing governance semantics.
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
- Clarified Governor and Cipher skill-source authority boundaries between governance/compliance sufficiency and technical defensive security review.

## v1.1.1 - Post-Release Hardening

### Changed
- Hardened release-surface and startup-state validation by aligning Codex metadata to v1.1.0, removing the drifted example manifest, adding `.codex-plugin/plugin.json` to update consistency checks, and checking structured branch/version claims in repo memory files.
- Converted PowerShell and shell validation entrypoints into thin wrappers around canonical Python validators to prevent cross-platform validation drift.
- Hardened update and rollback guidance by requiring fast-forward-only pulls, running canonical validation after updates, and documenting recovery-branch creation before hard resets.
- Fixed runtime context assembly so adapter-provided ContextPackage metadata is preserved and enriched instead of bypassed during execution.

## v1.1.2 - Trusted Runtime Authority

This patch is prepared for maintainer review. The `v1.1.2` tag and GitHub Release remain pending a separate post-merge publication gate.

### Added
- Implemented Issue #182 Phase 6B-D trusted runtime composition and Phase 6C adversarial validation, including explicit finite authority modes, immutable route bindings, authority and capability enforcement before governance, single initialization per root or child run identity, manifest-grant provenance and binding-owner validation, structured lifecycle and terminal-result integration, bounded in-process delegated execution, deterministic audit evidence, and lifecycle source-state enforcement for `ACTIVATE`, `WAIT`, and `RESUME`. Missing capability identifiers retain runtime `CAPABILITY_DENIED` behavior.
- Implemented Issue #180 Phase 6B-C bounded delegation validation, immutable effective child resolutions, exact lifecycle control, deterministic terminal replay, conflict rejection, and structured audit-event factories.
- Implemented Issue #178 Phase 6B-A immutable runtime domain contracts, typed error taxonomy, authority/capability/delegation/lifecycle models, stable interfaces, deterministic serialization, and additive public exports.
- Implemented Phase 6B-B repository-contained trusted policy loading, fail-closed authority evaluation and intersection, immutable runtime capability manifest resolution and intersection, deterministic collision rejection, typed enforcement, and structured audit-event creation.
- Added Issue #176 Phase 6A runtime-gap and trust-boundary architecture for trusted authority, immutable per-run capabilities, bounded delegation, typed lifecycle control, and structured audit evidence.
- Added implementation-ready authority, runtime capability, delegation, lifecycle, interface, error, compatibility, and fail-closed contracts distinct from PRAP adapter support.
- Added sequenced Phase 6B through Phase 6D implementation and verification planning.

### Changed
- Finalized the four canonical authority, capability, delegation, and lifecycle promotions as `IMPLEMENTED` and manually synchronized the Pattern Catalog while preserving pinned provenance, Apache-2.0 attribution boundaries, conceptual-adaptation limits, and `automatic_promotion: false`.
- Refreshed release, setup, compatibility, runtime, project-state, Codex, roadmap, architecture, and handoff documentation for the trusted runtime authority baseline.
- Normalized approved plugin and scaffold-package version metadata to `1.1.2` without changing adapter maturity: Cursor, Windsurf, VS Code/VSCodium, JetBrains, Zed, and Neovim remain scaffold-only.

## Unreleased

### Added
- Recorded unanimous Phase 5C-B Arbiter, Governor, and Steward approval plus conditional Butler disposition for the design-only authority/capability proposal, without runtime implementation or source-expression reuse authority.
- Added four manual Phase 5D `APPROVED` promotion records with pinned Strix provenance, Apache-2.0 attribution boundaries, and `automatic_promotion: false`.
- Manually synchronized the Phase 5E Pattern Catalog with the four canonical promotion records; Catalog projection remains separate from implementation authority.
- Added the Phase 5C-A Evolution Proposal schema `1.1`, deterministic proposal lifecycle validation, focused behavior coverage, and one design-only Orchestra authority/capability proposal in `UNDER_REVIEW`, without promotion, Pattern Catalog, source-reuse, prompt-reuse, or implementation authority.
- Added Phase 4.5-A OpenHero pilot source-intake, pattern, and audit records through a pinned static read-only GitHub inspection with no decisions, proposals, promotions, or Pattern Catalog changes.
- Added Phase 5B-A governed OpenHero decision records for three approved concept-only patterns, one deferred concept-only UI pattern, and one rejected security anti-pattern, without creating proposals, promotions, Pattern Catalog entries, or implementation authority.
- Added Phase 5B-B governed Strix decision records for four approved concept-only patterns and one rejected implementation-blocked prompt-safety anti-pattern, with mandatory Apache-2.0 Governor review and no proposal, promotion, Pattern Catalog, source-reuse, or implementation authority.
- Added Phase 4.5-B Strix pilot source-intake, pattern, and audit records through a pinned static high-risk read-only GitHub inspection with no decisions, proposals, promotions, or Pattern Catalog changes.
- Added Phase 4C-B deterministic, read-only Pattern Catalog synchronization validation, canonical Catalog projection, strict governance integration, and behavior coverage without automatic Catalog writes or promotion authority.
- Added Phase 4C-A deterministic, read-only Markdown rendering for validated Artificer audit reports, with stdout-only CLI output, canonical ordering, Markdown safety, governance integration, and behavior coverage.
- Added Phase 4A Artificer governance contracts, including native JSON schemas for Individual Source Audits (`AUDIT_REPORT_SCHEMA.json`), Orchestra Evolution Proposals (`EVOLUTION_PROPOSAL_SCHEMA.json`), Governance Decisions (`GOVERNANCE_DECISION_SCHEMA.json`), and Pattern Catalog Promotion Records (`PROMOTION_RECORD_SCHEMA.json`).
- Established isolated read-only registries for Phase 4A records (`reviews/`, `decisions/`, `proposals/`, and `promotions/`).
- Documented Phase 4A read-only and no-execution boundaries in `EXTERNAL_SOURCE_INTAKE.md`, `SECURITY_BOUNDARIES.md`, and `EVIDENCE_REQUIREMENTS.md`.
- Added Phase 3 Artificer record-instance validator (`scripts/validate_artificer_records.py`) with Draft-7 schema subset validation, POSIX-safe repository path constraints, and cross-record registry bundle verification.
- Added 61 behavior tests (`tests/behavior/test_artificer_records.py`) providing a rigorous regression matrix that executes real validator instances against real schema copies for passing/failing conditions, empty examined-ranges, cross-platform paths, and strict schema configurations.
- Wired `scripts/validate_artificer_records.py` into the CI governance script and automated runner `tests/behavior/run_tests.py`.
- Added Phase 4B deterministic governance-record validation for audit reports, decisions, proposals, promotions, and cross-record integrity.
- Added Phase 4B behavior coverage and strict-governance/behavior-runner integration without external execution or Pattern Catalog mutation.

### Changed
- Completed specialist-boundary polarity enforcement in the Artificer boundary validator (`scripts/validate_artificer_internal.py`), refactoring keyword-only checks in `check_artificer_boundaries_md()` to require explicit Artificer-bound negative polarity.
- Prevented mixed-polarity bypasses by splitting sentences into clauses and detecting explicit positive permissions alongside prohibitions.
- Expanded behavior test suite (`tests/behavior/test_artificer_internal.py`) with 6 new regression tests covering positive implementation, test, evidence-decision, licensing, and adversarial-testing permissions, plus mixed-polarity assertions.
- Strengthened the Artificer boundary validator (`scripts/validate_artificer_internal.py`) by refactoring it into pure functions returning `ValidationFailure` dataclass instances, and introducing strict semantic checks requiring explicit Artificer-bound negative polarity.
- Hardened the behavior test suite (`tests/behavior/test_artificer_internal.py`) by replacing placeholder `pass` blocks, ensuring all regression tests assert specific validator failures, adding a quality gate check on test source code, and verifying the entire repository via `validate_repository()`.
- Added explicit no-self-implementation and no-self-approval contract checks and statements to `internal/artificer/ARTIFICER.md`.
- Changed startup-state validation to use stable canonical-branch semantics instead of comparing committed files with the transient checkout branch.
- Improved prompt-load reporting with Group B and Group C status output, largest-contributor reporting, clarified original versus observed baselines, focused regression coverage, and narrow repository-state alignment.

### Added
- Added the Artificer internal boundary validator (`scripts/validate_artificer_internal.py`) and behavioral test coverage (`tests/behavior/test_artificer_internal.py`) to enforce schema integrity, documentation boundaries, and ensure public non-registration.
- Added the Phase 1 Artificer internal architecture specification, source-intake schemas, evidence requirements, classification taxonomy, security boundaries, and maintainer-only evolution workflow without exposing Artificer through public commands, routing, runtime registration, or adapter exports.
- Added an App Release Compliance Gate plus reusable privacy review, data inventory, IP clearance, privacy policy, terms, and retention/deletion governance templates for app and public release workflows.

### Changed
- Added Windows coverage and runtime test execution to cross-platform CI validation.
- Integrated Release Mode governance docs so The Governor now treats app release compliance artifacts as required when applicable and returns `REVISION_REQUIRED` or `BLOCKED` when release-gate documentation is missing.
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

Issue #171 follow-up changes in this checkout:

- Added canonical governance decision protocol at `docs/governance/GOVERNANCE_DECISION_PROTOCOL.md`.
- Deduplicated shared governance rules from governance layer, Steward, and Governor skill files while preserving role-specific output fields.
- Recalibrated Conductor, `SKILL_INDEX.md`, and `ROUTING_MAP.md` to restore lightweight routing and ordered cross-domain sequencing.
- Added deterministic routing-contract, governance-protocol-consistency, and prompt-load-budget validators plus focused behavior tests.
- Added strict prompt-load baseline and recalibration audit artifacts.
- Synced Codex exports for Conductor, Steward, and Governor governance/routing canon.
