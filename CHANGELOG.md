# Changelog

This changelog tracks the repository history using git tags, merge history, and the prior documented milestone log that lived under `docs/meta/CHANGELOG.md`.

## Unreleased

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
- Cleaned local-only runtime handling for tracked `.agents/` and `.amalgam/` state.
- Added CI/CD governance planning documentation for phased advisory validation.
- Added advisory governance validation script (`scripts/governance_check.py`).
- Documented the Dagger runtime guardrail gap in governance documentation.
- Added hardened Dagger runtime guardrail validation in simulation-only mode.
- Added repeatable Dagger guardrail tests and wired them into behavior validation.
- Wired Dagger instructions to require guardrail validation and fail-closed behavior.
- Added GitHub Actions governance workflow in advisory mode.
- Confirmed the workflow is non-deployment and does not promote Dagger.
- Added a Phase 4 Arbiter governance calibration plan covering baseline, scenario expectations, severity rules, and acceptance criteria.
- Extended Arbiter guidance with a governance-effectiveness review mode and standardized advisory governance output format.
- Added behavior fixtures to validate Arbiter governance severity buckets and advisory calibration wording.
- Reclassified the accepted Phase 4 work as Phase 4A (Arbiter calibration planning) and Phase 4B (Arbiter output contract alignment) to reflect that it went beyond planning-only work.
- Documented that CI strictness remains deferred until Arbiter calibration is accepted.
- Added a Phase 5 strict governance release gate planning document covering merge gates, release gates, branch protection, signed commit policy, Arbiter review policy, and emergency bypass planning.
- Enabled Phase 6 Stage 1 strict deterministic governance gates in CI while keeping subjective Arbiter findings advisory.
- Added `scripts/governance_check.py --strict` support, strict Dagger live-execution contract checks, and a small governance-check helper self-test.
- Updated the Governance Check workflow summary and execution path for Stage 1 strict deterministic enforcement without adding deployment or release automation.
- Corrected strict forbidden-file scanning so untracked CI-generated artifacts do not fail repository-content checks, while tracked forbidden files still block Stage 1 strict CI.
- Added Phase 6.6 specialist reroute output contract to standardize wrong-specialist behavior.
- Updated 10 specialist SKILL.md files and 9 active command files with scope-enforcement routing requirements.
- Updated Conductor routing rules and routing output templates to correctly process and route `SPECIALIST_REROUTE_REQUIRED` responses.
- Updated Arbiter severity classification to flag specialist-scope misuse without reroute as a Major finding.
- Updated Python and PowerShell behavior test fixtures to cover templates, commands, Arbiter severity, and specialist self-boundary reroute contracts.
- Cleaned up stale Acme handoff references in Scribe and Dagger.
- Updated the plugin.json safety note to accurately reflect Phase 2 simulation-only guardrail restrictions.
- Applied Phase 7 `main` repository protection updates by requiring strict status checks for `governance-check`, `validate`, `Analyze (actions)`, and `Analyze (python)` on the active `Protect main` ruleset.
- Updated governance and contributor documentation to reflect pull-request-only `main` changes, required review and conversation resolution, and the still-deferred deployment and release posture.
- Added Phase 7.5 solo-maintainer bypass policy documentation to keep bypass available for recovery while preserving branch and pull-request workflow as the default path.
- Documented Dependabot auto-merge readiness as deferred and limited to a later low-risk dependency-only policy review.
- Added Phase 7.6 signed-commit readiness guidance for the solo maintainer, including current unsigned status, recommended SSH signing path, verification commands, and emergency bypass boundaries.
- Added Phase 7.6 signed-commit readiness guidance for the solo maintainer, including current unsigned status, recommended SSH signing path, verification commands, and emergency bypass boundaries.
- Added signed-commit verification test documentation for validating the SSH signing readiness workflow.
- Updated Phase 7.6 readiness guidance after a verified SSH-signed test commit on `test/signed-commit-check`, recording commit `e43202e21755b9e9e1dd6de511fa4452a93fe27d` and GitHub verification success without rewriting history or changing rulesets.

## v1.0.1 - Codex compatibility adapter (2026-06-21)

- Added Codex-compatible skill export in `adapters/codex/`.
- Simplified exported frontmatter to satisfy Codex requirements (`name` and `description` only).
- Added support for repository-local `.agents/skills` installation.
- Added adapter validation scripts.
- Canonical v1.0.0 skill files remain perfectly untouched and metadata-rich.

## v1.0.0 - Final release hardening (2026-06-20)

- Replaced all legacy references to "Orchestra of Amalgamation" with the correct "Orchestra" title.
- Replaced the vague "high-signal" term with "relevant" in the Conductor skill.
- Added `V1_READINESS_CHECKLIST.md` to formally verify all critical repository requirements before v1.0.0 tagging.
- Hardened validation scripts and documentation to guarantee zero-drift and Markdown-first architecture.

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

## v0.5.0 - Phase 4: Live behavior testing (2026-06-20)

- Created a dedicated manual behavior testing framework (`tests/behavior/`) to validate Progressive Disclosure rules in live LLM environments.
- Added `BEHAVIOR_TEST_MATRIX.md` covering 8 realistic prompt scenarios (one for each major skill path).
- Added `MANUAL_TESTING_GUIDE.md` to instruct users how to verify that LLMs defer token-heavy formatting templates correctly.
- Updated structure validation scripts to require these testing documents.

## v0.4.0 - Phase 3: Routing metadata and drift prevention (2026-06-20)

- Added lightweight structured metadata (for example `slug`, `role`, `primary_use`, and `avoid_when`) to the frontmatter of all core `SKILL.md` files to prevent drift and lay groundwork for automated plugin loading.
- Created a root-level `ROUTING_MAP.md` that maps common tasks to the correct specialist skill in a concise, scanner-friendly format.
- Merged the Conductor's legacy conflict resolution logic into `ROUTING_MAP.md` and removed the stale `ROUTING_MATRIX.md` file.
- Updated Conductor to lazily load the routing map only when workflow coordination is unclear.
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
- Added the eight-skill Orchestra structure.
- Added IDE adapter guides and templates.
- Added validation and local-only guidance.
- add negative validation tests for router benchmark fixture schema parsing
- allow runner to accept explicit fixture path argument
- added negative router benchmark fixture validation to CI pipeline
- recorded negative fixture test artifacts in CI artifact index
- added router benchmark maintenance guide with review checklists and validation procedures
- drafted router benchmark coverage expansion plan for future routing scenarios
- added priority 1 router benchmark cases BM-13 through BM-16
- added priority 2 router benchmark cases BM-17 through BM-20
- added priority 3 router benchmark cases BM-21 through BM-24
- added benchmark coverage completion review for Phase 7
