# Changelog

## Post-v1.6.0 Adaptive Specialist Context A2 - Candidate

- Adds opt-in, read-only adaptive specialist context after deterministic routing, trusted authority/capability evaluation, and governance validation, without changing the default `RuntimeExecutor` path.
- Compiles bounded advisory context from canonical A1 machine-local adaptive state with exact user/project/specialist/task-session scope isolation, deterministic precedence, explicit caller bounds, and inferred-candidate exclusion unless a caller supplies a confidence threshold.
- Preserves fail-closed profile/evidence integrity, deterministic fallback on missing, stale, incompatible, cross-user, or provider-failure state, and keeps governed outcome evidence advisory rather than automatically converting it into preferences.
- Adds the A2 adaptive-context machine contract/schema, architecture documentation, focused runtime regressions, and edge-case coverage for scope leakage, precedence, provider failure, canonical-route immutability, delegated-context rejection, and A3 absence.
- Keeps A2 non-authorizing and non-promoting: it cannot select another specialist, expand authority, grant capabilities, alter governance or lifecycle permissions, promote inferred patterns, add provider integration or training, rank routes/models/workers/strategies, or learn Tuner topology.
- Keeps this work on an unsigned draft source-validation lane pending a fresh exact-head validation matrix and separate signed materialization; it does not move the `v1.6.0` tag/Release, deploy, activate policy, bypass repository governance, or begin A3.

## Post-v1.6.0 Local Adaptive Memory A1 - Candidate

- Adds the bounded A1 machine-local adaptive-memory foundation with JSONL observation evidence, derived JSON profiles, explicit global-user/project/specialist/task-session scopes, and storage outside the repository working tree by default.
- Keeps adaptive state non-authorizing and disconnected from routing, authority, capability, governance, specialist-context assembly, lifecycle activation, provider behavior, training, and automatic inferred-pattern promotion; A2 and later phases remain outside this candidate.
- Adds fail-closed adaptive observation, profile, export, and store-metadata schemas plus deterministic observation/profile/export fixtures and runtime validation against JSON Schema Draft 2020-12.
- Preserves non-learnable governance/security boundaries, explicit-versus-inferred evidence semantics, hash-chained JSONL integrity, stale-profile rejection and recovery, scoped compaction/deletion, expiry pruning, structured export, and an explicit statement that forensic secure erasure is not guaranteed.
- Extends the existing runtime validation environment only with the JSON Schema validator needed by the new fixture tests; the protected-main runtime statement and branch coverage floors remain unchanged.
- Keeps this work on a draft feature PR pending exact-head validation and separate human merge authorization; it does not move the `v1.6.0` tag/Release, deploy, activate adaptive runtime behavior, bypass repository governance, or begin A2.

## v1.6.0 Integration & Developer Experience - Release Candidate

- Normalizes all 11 repository-enforced package/version surfaces to `1.6.0` without changing host maturity, runtime authority, deployment state, or the still-published `v1.5.0` tag/Release identity.
- Packages the verified post-v1.5 two-step signed-materialization optimization, preserving isolated signing evidence and a fresh complete protected-main validation matrix on the signed canonical PR.
- Packages the TrueSheet specialist knowledge enrichment with pinned Padayon/upstream provenance, MIT licensing identity, selective machine reference data, and progressive-disclosure guidance for the five approved specialist owners without vendoring or runtime dependency adoption.
- Packages hybrid context representation with JSON as canonical structured machine state and TOON only as a derived, validated, non-authoritative projection when measured context savings justify it.
- Packages the Required Analysis Compatibility workflow that runs real exact-head CodeQL before emitting the historical `Analyze (actions)` and `Analyze (python)` contexts. Issue #331 remains open; this release does not claim direct ruleset identity normalization.
- Packages governed Host Update commands with deterministic read-only planning, preserved host maturity, fail-closed unknown-host behavior, explicit recovery guidance, and no automatic installed-integration refresh.
- Packages the Adapter SDK / PRAP v1 compatibility certification surface with deterministic read-only evidence while keeping certification, host maturity, transport support, and runtime authority separate.
- Packages the repository-native Developer Portal as a discovery/indexing surface only; it is not a marketplace, registry, deployment plane, or permission source.
- Packages MCP stdio governed tool transport v1 for protocol revision `2026-07-28`, limited to `server/discover`, `tools/list`, and `tools/call`, with fresh trusted runtime composition per accepted call and no authority expansion from MCP metadata or arguments.
- Packages documentation architecture v2: a concise root README, general human documentation map, current architecture/governance entry points, `README.json` machine index v2, and deterministic documentation-impact validation that updates the correct human or machine surface instead of forcing blanket README churn.
- Adds `docs/releases/v1.6.0-integration-developer-experience-release-candidate.md` and refreshes current package/release context while keeping public publication separate from package preparation.
- Preserves Murmurs issue #316 as open with no token-savings percentage claim and preserves Adaptive Governed Orchestration issue #340 as deferred planning-only work outside v1.6.0.
- Final release readiness remains revision-bound: historical feature validation is implementation evidence only. Publication requires a fresh exact signed candidate, complete protected validation, clean merge state, expected-head Squash merge, signed canonical identity, and independent tag/Release verification.

## Post-v1.5.0 Documentation Architecture Refactor - Candidate

- Refactors the root `README.md` into a concise human landing page while preserving the existing banner, navigation style, badges, trust-boundary message, installation entry points, and release identity.
- Adds `docs/README.md` as the general human framework map plus current architecture and governance overview entry points so detailed phase documents can remain historical design evidence without acting as current machine-state authority.
- Evolves `README.json` to `orchestra.readme-machine-index.v2`, expanding AI discovery across capabilities, hosts/integrations, knowledge/provenance, continuity, release state, maturity, and current human entry points without duplicating the referenced canonical machine contracts.
- Preserves the hybrid representation rule: Markdown explains; JSON carries canonical structured machine state; JSON Schema validates; TOON remains derived, validated, and non-authoritative.
- Replaces the blanket README-impact rule with a deterministic documentation-impact contract: public identity/headline changes require `README.md`, machine-facing contract/discovery changes require `README.json`, and domain behavior changes require detailed documentation without forcing unrelated root README churn.
- Adds regression coverage for the documentation-impact contract and README machine-index v2 parity, including package-version parity, sequential scan order, required machine-contract references, and referenced-path existence.
- Keeps the current public release fixed at `v1.5.0`; no package/version surface, tag, GitHub Release, deployment, policy activation, installed-integration refresh, force push, history rewrite, branch cleanup, Murmurs token-savings claim, or Adaptive Governed Orchestration implementation is performed by this documentation unit.

## Post-v1.5.0 MCP stdio Governed Tool Transport - Candidate

- Adds the first bounded MCP integration for protocol revision `2026-07-28`, using stdio only and exposing `server/discover`, `tools/list`, and `tools/call`.
- Maps MCP tools to a deterministic intersection of an existing PRAP adapter command surface and Orchestra's trusted runtime policy; no parallel adapter registry, authority model, or permission source is introduced.
- Creates a fresh trusted runtime composition per accepted tool call and preserves existing route binding, authority, runtime-capability, governance, lifecycle, operation, and audit ordering.
- Restricts MCP tool arguments to a single `prompt` field with `additionalProperties: false`; client MCP metadata and arbitrary tool metadata cannot inject Orchestra governance validation, authority, or runtime-capability grants.
- Adds `scripts/mcp_server.py`, focused runtime regressions, and developer/Adapter SDK documentation while keeping stdout protocol-only and diagnostics on stderr.
- Keeps Streamable HTTP, resources, prompts, Tasks/extensions, deployment, policy activation, installed-integration refresh, host-maturity promotion, issue #316 closure, and token-savings claims outside this unit.
- Keeps public release `v1.5.0` fixed at `b0a56cc7af8ad78234754bcb29ed07f6ab54d920`; this is a post-release candidate and does not move or republish the release.

## Post-v1.5.0 Developer Portal - Candidate

- Adds a repository-native Developer Portal for discovery of stabilized adapter, PRAP certification, host-maturity, specialist, governance, and validation contracts without introducing a new authority layer.
- Adds a machine-readable portal catalog and JSON Schema plus deterministic tests that require referenced paths, journey references, domain-owner boundaries, and fixed release identity to remain valid.
- Provides adapter, certification, host-maturity, specialist-extension, governance, and validation contributor journeys by linking canonical surfaces rather than copying their semantics.
- Keeps PRAP v1, the Host Update contract, the specialist registry, and governance policy authoritative for their existing domains.
- Explicitly excludes marketplace listing/publication and MCP implementation; both remain separately governed later phases.
- Performs no release/tag movement, deployment, policy activation, installed-integration refresh, host-maturity promotion, destructive cleanup, branch deletion, force push, or history rewrite. Public `v1.5.0` remains fixed at `b0a56cc7af8ad78234754bcb29ed07f6ab54d920`.

## Post-v1.5.0 Adapter SDK and PRAP Compatibility Certification - Candidate

- Formalizes the existing `PRAP v1` adapter protocol as the single Adapter SDK boundary through `orchestra_runtime.protocol.sdk`; no parallel adapter abstraction is introduced.
- Adds a machine-owned read-only PRAP compatibility certification contract and evidence schema plus deterministic CLI evidence for canonical adapter targets.
- Fails closed on unknown, reserved, rejected, malformed, unsupported-version, runtime-mapping, host-mapping, or contract-drift conditions.
- Keeps compatibility certification separate from Host Update maturity: Codex and Antigravity remain `SUPPORTED`; Claude Code, Cursor, Windsurf, VS Code/VSCodium, JetBrains, Zed, and Neovim remain `SCAFFOLD_ONLY` for Host Update behavior.
- Preserves VSCodium as a compatible identity through the VS Code runtime adapter without promoting its scaffold maturity.
- Makes certification non-authorizing and non-mutating: no runtime authority or capability grant, installed-integration refresh, release/tag movement, deployment, policy activation, force push/history rewrite, branch cleanup, or host promotion is performed.
- Keeps MCP deferred to the final integration phase; future transports must map to the stabilized Adapter SDK/PRAP boundary and cannot become authority.
- Keeps public release `v1.5.0` fixed at `b0a56cc7af8ad78234754bcb29ed07f6ab54d920`.

## Post-v1.5.0 Governed Host Update Commands - Candidate

- Adds `machine/hosts/update-contract.v1.json` and its canonical JSON Schema as the machine-owned Host Update contract for Codex, Antigravity, Claude Code, Cursor, Windsurf, VS Code/VSCodium, JetBrains, Zed, and Neovim.
- Preserves the exact host maturity boundary: Codex and Antigravity are `SUPPORTED`; Claude Code, Cursor, Windsurf, VS Code/VSCodium, JetBrains, Zed, and Neovim remain `SCAFFOLD_ONLY` and instruction-only for Host Update behavior.
- Adds a deterministic read-only Host Update planner that resolves host aliases, local package/version parity, optional observed-latest status, update instructions, post-update validation, and non-destructive recovery guidance without performing network access or installed-host mutation by default.
- Keeps Git/local supported-host guidance fast-forward-only with a recorded pre-update revision, clean working tree, `git fetch origin`, `git pull --ff-only`, required post-update validation, and fail-closed handling for unknown hosts or validation failure.
- Requires separate explicit authorization before any supported-host installed-integration refresh and forbids automatic installed-integration refresh, implicit marketplace promotion, release/tag publication, deployment, policy activation, destructive cleanup, branch deletion, force push, history rewrite, ruleset bypass, or MCP implementation.
- Adds deterministic regression coverage for host-set parity, package/version parity, maturity preservation, authority non-expansion, VS Code/VSCodium alias behavior, unknown-host fail-closed behavior, status comparison, recovery safety, and rejection of an execution flag.
- Adds Host Update setup documentation and supported-host adapter guidance while keeping public release `v1.5.0` fixed at `b0a56cc7af8ad78234754bcb29ed07f6ab54d920`.

## Post-v1.5.0 Hybrid Context and Required-Check Identity Repair - Candidate

- Adds an internal hybrid context compiler that preserves canonical JSON evidence while using derived TOON only when measured size savings justify it, with compact JSON fallback for small or irregular payloads.
- Preserves full stdout/stderr evidence and SHA-256 identity behind bounded head/signal/tail summaries so large command output can be reduced for AI context without making the compact projection authoritative.
- Adds fail-closed source/projection digest verification and focused regressions for TOON selection, JSON fallback, nested command representation, source drift, projection tampering, and bounded long-log summaries.
- Repairs the stale protected-main status identity mismatch without using ruleset bypass: `.github/workflows/required-analysis-compat.yml` runs an exact-head Python CodeQL analysis with the GitHub CodeQL Action and duplicate SARIF upload disabled, then emits the required `Analyze (actions)` and `Analyze (python)` GitHub Actions contexts only after that analysis succeeds.
- Keeps GitHub default CodeQL setup unchanged and does not accept a neutral default-setup result as security success. The two historical Actions identities remain compatibility gates until direct ruleset normalization is available and do not weaken signed commits, linear history, review-thread resolution, native validation, runtime tests, governance checks, or expected-head merge protection.
- Keeps public release `v1.5.0` fixed at `b0a56cc7af8ad78234754bcb29ed07f6ab54d920`; no release/tag movement, deployment, policy activation, installed-integration refresh, destructive cleanup, force push, history rewrite, branch deletion, or MCP implementation is performed.

## Post-v1.5.0 TrueSheet Specialist Knowledge Adaptation - Candidate

- Pins the Orchestra-native machine catalog `machine/knowledge/truesheet-specialist-reference.v1.json` to canonical Padayon TrueSheet V2 reference commit `1fa5b773b04877bcbc3b85e22b6af70a0a8dd738` and upstream `lodev09/react-native-true-sheet` commit `23e119c026e2040d960725bd260e6cd4bf680b95`, with the MIT license and no-source-drift state preserved as explicit machine provenance.
- Adds progressive-disclosure TrueSheet reference guides for Cloak, Ponytail, Clockwork, Overseer, and Scribe, with byte-equivalent Codex mirrors and exact `TSF-*` feature ownership mapped back to the machine catalog.
- Keeps Conductor routing-only and The Tuner coordination-only; neither receives duplicated TrueSheet domain guidance, specialist authority is not expanded, and external `AGENTS.md` instructions do not become Orchestra governance.
- Adapts patterns through paraphrased or independently derived Orchestra-native guidance only. No TrueSheet runtime dependency, vendoring, external source-code copying, wholesale licensed-material copying, or external-test-evidence substitution is introduced.
- Adds `tests/behavior/test_truesheet_reference.py` and a canonical validation step enforcing Padayon/upstream provenance, MIT identity, exactly 18 declared feature IDs, five approved specialist mappings, source/Codex guide parity, machine-guide feature parity, and the no-Conductor/no-Tuner duplication boundary.
- Updates README parity for the new specialist knowledge surface while keeping `v1.5.0` fixed and published. No release/tag movement, deployment, policy activation, installed-integration refresh, destructive cleanup, force push, history rewrite, branch deletion, or MCP implementation is performed.

## Post-v1.5.0 Signed Materialization Optimization - Candidate

- Replaces the historical three-PR API-authored signing pattern with a two-PR transport: the unsigned source branch is reviewed directly against an isolated `materialize/**` target, then the verified GitHub-signed Squash result becomes the head of the canonical PR to `main`.
- Adds machine-owned signed-materialization transport rules to `machine/governance/policy.v1.json`, explicitly denying canonical merge-readiness, project-state promotion, release, and bypass authority to the materialization lane.
- Adds `orchestra.signed-materialization-evidence.v1`, a fail-closed validator, regression coverage, and the bounded `signed-materialization` workflow for exact source-head, target-branch, changed-path, tree, and `git diff --check` evidence.
- Scopes the full `validate`/`runtime-tests`, Mutmut, and Cosmic Ray pull-request workflows to `main`, so intermediate signing PRs no longer repeat canonical validation or mutation campaigns.
- Preserves the complete protected-main matrix on the final signed PR, including current `mergeable=true`, `mergeable_state=clean`, signed-commit, exact-head, review-thread, expected-head Squash, and independent canonical-read requirements. Materialization evidence is never reusable as canonical exact-head evidence.
- Does not change the `Protect main` ruleset, grant bypass authority, move the fixed `v1.5.0` release/tag, deploy, activate policy, refresh installed integrations, perform destructive cleanup, force push, rewrite history, delete branches, or implement MCP.

## v1.5.0 Machine-Verifiable Control Plane and Murmurs - Published 2026-08-16

- Published `Orchestra v1.5.0: Machine-Verifiable Control Plane and Murmurs` as immutable, non-draft, non-prerelease GitHub Release id `371314544` from lightweight tag `v1.5.0`, which resolves directly to exact signed canonical release commit `b0a56cc7af8ad78234754bcb29ed07f6ab54d920`.
- Completed the machine-verifiable control-plane re-foundation through `LEGACY_RETIRED`, preserving the versioned machine specialist registry, routing contract, governance policy, exact evidence/receipt stack, deterministic Arbiter Kernel, continuity/context state, persistent remediation circuit, pre-execution policy gate, and host conformance boundaries.
- Published the fail-closed merge-readiness stabilization requiring current `mergeable=true` and `mergeable_state=clean` for ordinary governed progression, with prior accepted pre-merge state carried into post-merge verification.
- Published the additive Murmurs communication budget with `NORMAL` as the default and deterministic `SILENT`, local `MURMUR`, and required `EXPLAIN` dispositions; no billing-token savings percentage is claimed without comparable host-reported counters.
- Final release evidence recorded 1,058 passing runtime tests, 98.47% statement coverage, 95.36% branch coverage, passing critical-module floors, governance, CodeQL and native-platform validation, plus complete Mutmut and Cosmic Ray campaigns.
- Added `docs/validation/V1_5_0_PUBLICATION_CLOSEOUT.md` and reconciled human/machine current-facing release, setup, roadmap, project-state, context, and handoff documentation without moving the fixed release tag or performing marketplace publication, installed-integration refresh, deployment, policy activation, destructive cleanup, branch deletion, force push, history rewrite, or MCP implementation.
- MCP was intentionally excluded from v1.5.0. Publication satisfies its sequencing prerequisite only; any MCP work requires a fresh post-release dependency/risk/value and design decision.

## Post-v1.4.0 Murmurs Communication Budget - Candidate

- Adds a machine-owned presentation policy with `NORMAL` and opt-in `MURMURS` modes plus deterministic `SILENT`, local `MURMUR`, and required `EXPLAIN` dispositions.
- Keeps human-action, authority, validation-failure, blocker, governance-stop, handoff, completion, and failure events hard-bound to explanation; malformed presentation contracts fail closed to explanation.
- Selects short non-semantic murmurs locally with deterministic SHA-256 indexing instead of asking the model to generate filler or loading the vocabulary into model context.
- Integrates presentation selection at the shared adapter boundary so supported and scaffold hosts consume the same machine policy; adapters default to normal explanation unless Murmurs is explicitly selected.
- Adds source-aware communication measurements for progress messages, model progress calls, bytes, repeated reads, elapsed communication overhead, outcome identity, and optional host-reported token counters. Token deltas are calculated only for matching host-reported counter identities; unavailable counters remain null and no percentage saving is invented.
- Adds controlled repository-simulation coverage showing routine modeled progress calls can be structurally eliminated by Murmurs while preserving outcome, validation, and governance identities; repository CI does not represent this as billing-token evidence.
- Evaluates Caveman-inspired semantic tool/log compression but does not promote lossy compaction or repeated-read stubs until original content is preserved behind an immutable retrievable reference.
- Performs no SemVer selection, release/tag publication, ruleset change/bypass, deployment, marketplace publication, installed-integration refresh, destructive cleanup, force push, history rewrite, branch deletion, or MCP implementation.

## Post-v1.4.0 Governance Stabilization - Merge-State Fail-Closed Repair

- Repairs autonomous merge readiness so `mergeable=true` is insufficient for ordinary governed progression; the current PR read must also report `mergeable_state=clean`.
- Treats missing or unknown mergeability as `WAIT_FOR_EVIDENCE` and fails closed on `blocked`, `behind`, `dirty`, `unstable`, or any other observed non-clean state.
- Carries the accepted pre-merge disposition, mergeable state, and bypass-use record into post-merge verification so API success, a signed canonical commit, or matching tree content cannot retroactively satisfy a failed pre-merge gate.
- Adds regression coverage for the PR #299 incident shape and documents a forward-only stabilization boundary under #302 without claiming a GitHub-recorded bypass event that is not independently available.
- Does not rewrite PR #299 history, change the `Protect main` ruleset, weaken validation or coverage, select a version, publish a release, deploy, refresh installed integrations, or begin Murmurs or MCP work.

## Post-v1.4.0 Control Plane Re-foundation - LEGACY_RETIRED Candidate

- Advances the separately governed migration from `CANONICAL_PROMOTION_AUTHORITY` to `LEGACY_RETIRED` without changing the published `v1.4.0` release.
- Removes the runtime's independently addressable service-level authority snapshots for default command routes, ambiguity fallback, governance-required specialist classification, governance validation-rule records, and dry-run rule identity. `SkillRegistry`, `RouterService`, `GovernanceValidator`, compatibility policy bindings, and compatibility capability grants now consume the versioned machine contracts directly.
- Replaces the stored `models.py::VALID_SPECIALISTS` snapshot with an on-demand machine-derived compatibility view so the legacy import can remain available without becoming an independent specialist-identity authority.
- Converts routing, shadow-conformance, governance, and migration-state regressions from legacy-table parity checks to direct machine-authority consumption checks, including fail-closed invalid-rule coverage.
- Marks the machine migration state `LEGACY_RETIRED` only after the adjacent `CANONICAL_PROMOTION_AUTHORITY` checkpoint became signed canonical through PR #298 at `529639beefd8fa0cc153b6e94649b487de4f7bc2`.
- This candidate does not select or publish a new SemVer, tag, or GitHub Release and does not perform marketplace publication, installed-integration refresh, deployment, production mutation, ruleset bypass, force push, history rewrite, branch deletion, or destructive cleanup.

## Post-v1.4.0 Control Plane Re-foundation P0/P1-P9 - Canonical Integration

- Consolidated the control-plane re-foundation tracked by #273 into PR #294, covering exact source and validation receipts, typed governance and deterministic Arbiter Kernel enforcement, machine specialist/routing/governance contracts, exact compliance set-equality receipts, host capability/conformance contracts, typed continuity and JSONL context state, persistent remediation circuit breakers, deterministic pre-execution policy gating, and P9 shadow conformance.
- P9 began in `SHADOW`, advanced through separately governed `ADVISORY` and `VALIDATION_AUTHORITY` checkpoints, and this candidate advances only to `CANONICAL_PROMOTION_AUTHORITY`; it does not grant legacy retirement or installed-integration mutation.
- The versioned machine specialist registry, routing contract, and governance policy now supply runtime default specialist identity, command routes and ambiguity fallback, governance-required specialist classification, governance validation rules, Arbiter transition precedence, and remediation defaults. Backward-compatible runtime names remain derived compatibility surfaces rather than independent authority.
- Release hardening persists machine-readable runtime evidence with statement and branch coverage, critical-module floors, property-based regressions, workflow-sanity coverage, bounded mutation-confidence evidence, and cross-platform validation. These measurements are confidence evidence, not proof of correctness.
- PR #294 is canonical through governed Squash merge and independent readback at signed commit `76eb96b27439700a517f75c5a921465e5c2987e6` with tree `6f98b380d984430303d630462ad4535cda483925`. This post-`v1.4.0` integration preserves `v1.4.0` as the current published release at that checkpoint and creates no new tag, version, or GitHub Release.
- Added the compact machine release-evidence index at `machine/release-evidence/control-plane-refoundation-p0-p1-p9.json`, referencing the exact final integrated candidate runtime and bounded Cosmic Ray evidence without treating coverage or mutation score as proof of correctness.
- Added typed migration-state checkpoints and regression coverage for the adjacent `SHADOW -> ADVISORY -> VALIDATION_AUTHORITY -> CANONICAL_PROMOTION_AUTHORITY` progression while preserving `LEGACY_RETIRED` as a separately governed decision.

## v1.4.0 Governance and Compliance Registry Cross-Integration - Published 2026-08-14

- Normalized the root, Claude Code, Codex, Cursor, JetBrains, Neovim, VS Code, Windsurf, and Zed package/version surfaces to `1.4.0` for the governance release candidate without changing host maturity.
- Added a deterministic runtime regression that requires all 11 live package/version surfaces to agree on `1.4.0`.
- Elevated the Compliance Registry from a local-cache integration into an explicitly documented Orchestra cross-integration across Governor, Steward, Arbiter, Conductor/The Tuner coordination, and downstream project handoffs while preserving specialist and authority boundaries.
- Added the fail-closed README Impact Gate to Governance Check: significant runtime, specialist, host-integration, governance/routing/setup/release, version, or CI/governance changes must update `README.md` in the same revision; tests and validation-evidence-only changes do not force README churn.
- Added Registry `0.1.0` release-candidate compatibility regressions covering manifest trust anchoring, install/query/project pinning, populated Philippine source/obligation identity, current freshness, and explicit `REVIEW_OVERDUE` propagation without changing Orchestra runtime behavior or publishing a Registry release.
- Added `docs/releases/v1.4.0-governance-compliance-registry-release-candidate.md` and preserved `v1.3.0` as the current public release until separately authorized `v1.4.0` tag and GitHub Release publication.
- Published and independently verified the trusted immutable Registry release `registry-v0.1.0` at canonical Registry commit `3821bcb55125b4d8864f28b6423650e6e17ac67b`, then validated Orchestra's real network sync, exact provenance, freshness, source query, project pinning, update-check, and idempotent re-sync from canonical Orchestra source baseline `b5d0790fc714f53c4561a91b158c13c625768e05`.
- Added `docs/validation/V1_4_0_RELEASE_READINESS_EVIDENCE.md`; at that readiness checkpoint, Orchestra `v1.4.0` public release/tag publication remained a separate protected transition.
- Published `Orchestra v1.4.0: Governance & Compliance Registry Cross-Integration` as GitHub Release id `370658917` from lightweight tag `v1.4.0`, which resolves directly to exact signed canonical release commit `93dd51c0fbe1b10affc58e6fadd5fb0bc2927a50`; independently verified non-draft, non-prerelease, immutable, and latest at that publication checkpoint.
- Added `docs/validation/V1_4_0_PUBLICATION_CLOSEOUT.md` and reconciled current-facing release, setup, roadmap, project-state, and handoff documentation without moving the fixed release tag or performing marketplace publication, installed-integration refresh, deployment, policy activation, destructive cleanup, branch deletion, force push, or history rewrite.

## Post-v1.3.0 Compliance Registry Local Cache - Pending

- Added an offline-first verified local client for `Baelfyre/Orchestra-Compliance-Registry` with status, verification, controlled synchronization, local bundle installation, query, project pinning, and update-check operations.
- Added candidate-before-activation, exact release-manifest identity, file-hash verification, last-known-good cache retention, safe ZIP extraction, and default anti-rollback behavior without granting registry data execution authority.
- Added progressive-disclosure Governor, Steward, and Arbiter integration for compliance applicability evidence, FR/NFR and acceptance traceability, and stale or mismatched registry-evidence invalidation.
- Added runtime contract coverage for local install/query/pin and rollback behavior; development validation also covered wrong canonical repository, content tampering, unsafe archive paths, and release-tag mismatch.
- Established the public registry foundation in the separately governed `Baelfyre/Orchestra-Compliance-Registry` repository; no trusted registry release, release/tag publication, deployment, policy activation, installed-integration refresh, destructive cleanup, branch deletion, force push, or history rewrite is performed by this work.

## v1.3.0 Specialist Intelligence - Release Preparation - Pending

- Normalized the root, Claude Code, Codex, Cursor, JetBrains, Neovim, VS Code, Windsurf, and Zed package/version surfaces to `1.3.0` for the Specialist Intelligence release candidate without changing host maturity.
- Added a deterministic runtime regression that requires all 11 live package/version surfaces to agree on `1.3.0`.
- Added the source-backed `docs/releases/v1.3.0-specialist-intelligence-release-candidate.md` preparation record covering the completed SK1-SK10 Specialist Knowledge Layer campaign and its validation baseline.
- Preserved `v1.2.0` as the current public release until a separately authorized publication gate creates `v1.3.0`; this preparation performs no tag creation, GitHub Release publication, deployment, production mutation, marketplace publication, installed-integration refresh, policy activation, destructive cleanup, branch deletion, force push, or history rewrite.

## Post-v1.2.0 Specialist Knowledge Layer - SK10 Hardening and Evaluation - Pending

- Added evidence-driven hardening guides for Weaver model/source traceability, Conductor routing evaluation, The Tuner contradiction/invalidation coordination, and Arbiter continuity/handoff evaluation.
- Added a selective JSON adversarial scenario catalog with deterministic regression coverage for routing, ownership, contradiction, re-entry, stale diagrams, handoff identity, and protected-action boundaries.
- Preserved existing orchestration and governance contracts; no routing, authority, runtime, manifest, policy, release, or deployment redesign was introduced.
- No release/tag publication, deployment/production mutation, installed-integration refresh, policy activation, destructive cleanup, branch deletion, force push, or history rewrite is performed by SK10.

## Post-v1.2.0 Specialist Knowledge Layer - SK9 The Steward and The Governor - Pending

- Deepened The Steward's requirements-traceability, acceptance-criteria, scope/change-control, and business/SDLC alignment knowledge without changing governance authority or routing.
- Deepened The Governor's authoritative-source acquisition, jurisdiction/effective-date verification, license/privacy/IP/compliance review, and human-escalation knowledge without providing legal advice or embedding legal conclusions.
- Added progressive-disclosure guides and one worked joint governance example that distinguishes verified facts, applicability questions, decisions, implementation evidence, and human-owned legal interpretation.
- Preserved specialist boundaries: The Steward owns business alignment; The Governor owns legal/compliance governance; Cipher owns technical privacy/security controls; Scribe owns documentation production; Arbiter owns transition evidence.
- Kept the campaign Markdown-primary and JSON-selective: the SK9 audit found no deterministic machine-parsing need that justified a governance JSON catalog.
- Added focused regression coverage for knowledge depth, source/Codex parity, traceability/change-control discipline, source freshness, and non-legal-advice escalation boundaries.
- No policy activation, legal publication, release/tag publication, deployment/production mutation, installed-integration refresh, destructive cleanup, branch deletion, force push, or history rewrite is performed by SK9.

## Post-v1.2.0 Specialist Knowledge Layer - SK8 Scribe - Pending

- Deepened Scribe's technical-documentation knowledge without changing routing, runtime architecture, publication state, or domain-specialist ownership.
- Added progressive-disclosure guidance for CommonMark/GitHub-Flavored Markdown, changelog and ADR conventions, API/reference documentation, versioned documentation, deprecation/sunset records, source-backed claims, and link/anchor freshness.
- Expanded documentation standards and audit checks for heading/anchor stability, fenced code and tables, source revisions, effective dates, verified commands, API examples, version selectors, redirects, and broken-link reporting.
- Added a worked source-backed API change example that separates verified current behavior, compatibility status, planned work, and release authority.
- Kept the campaign Markdown-primary and JSON-selective: the SK8 audit found no deterministic machine-parsing need that justified a Scribe JSON catalog.
- Added focused regression coverage for Scribe knowledge depth, progressive disclosure, source/Codex parity, link/claim discipline, and no-publication boundaries.
- No release/tag publication, documentation-site deployment, installed-integration refresh, policy activation, destructive cleanup, branch deletion, force push, or history rewrite is performed by SK8.

## Post-v1.2.0 Specialist Knowledge Layer - SK7 Overseer - Pending

- Deepened Overseer's validation-strategy knowledge without changing routing, runtime architecture, CI workflows, release gates, or test-code ownership.
- Added progressive-disclosure guidance for unit/integration/contract/E2E boundaries, property and mutation testing, coverage interpretation, flaky-test diagnosis, deterministic isolation, test-data management, CI/browser/device matrices, and performance acceptance.
- Expanded quality standards and testing checks with contract identity, shrinking and reproducibility, mutation-score interpretation, quarantine controls, environment matrices, percentile evidence, and privacy-safe test-data lifecycle requirements.
- Added a worked risk-based validation matrix example that separates planned evidence from executed results and preserves domain-specialist ownership.
- Kept the campaign Markdown-primary and JSON-selective: the SK7 audit found no deterministic machine-parsing need that justified an Overseer JSON catalog.
- Added focused regression coverage for Overseer knowledge depth, progressive disclosure, source/Codex parity, and evidence-state discipline.
- No CI/release-gate mutation, test execution beyond repository validation, deployment, release/tag publication, installed-integration refresh, policy activation, destructive cleanup, branch deletion, force push, or history rewrite is performed by SK7.

## Post-v1.2.0 Specialist Knowledge Layer - SK6 Chronicler - Pending

- Deepened Chronicler's persistence knowledge without changing routing, runtime architecture, schema state, or database execution authority.
- Added engine-evidence guidance for PostgreSQL, MySQL, SQL Server, and SQLite plus ORM mapping and migration-state semantics.
- Added progressive-disclosure guidance for transaction isolation, MVCC, locking, deadlock analysis, query-plan evidence, tenant isolation, and expand-contract zero-downtime migrations.
- Expanded database standards and review checks for dialect/version identity, ORM/schema parity, lock and retry behavior, tenant predicates and composite integrity, plan estimates, backfill checkpoints, and compatibility windows.
- Added a planning-only worked expand-contract migration example with bounded batches, read/write compatibility, validation, rollback boundaries, and no executable production command.
- Kept the campaign Markdown-primary and JSON-selective: the SK6 audit found no deterministic machine-parsing need that justified a Chronicler JSON catalog.
- Added focused regression coverage for Chronicler knowledge depth, progressive disclosure, source/Codex parity, and the no-execution boundary.
- No schema change, migration execution, live-data access, destructive SQL, release/tag publication, deployment/production mutation, installed-integration refresh, policy activation, destructive cleanup, branch deletion, force push, or history rewrite is performed by SK6.

## Post-v1.2.0 Specialist Knowledge Layer - SK5 Dagger - Pending

- Deepened Dagger's safe resilience knowledge without changing routing, runtime architecture, or execution authority.
- Added progressive-disclosure guidance for workload modeling, load/stress/soak interpretation, concurrency and resource pressure, bounded fault injection, recovery objectives and timelines, resilience tooling, and evidence identity.
- Expanded safety gates and the execution protocol with observable ceilings, generator health, abort controls, blast-radius checks, retry amplification, recovery windows, residual-state verification, and measurement limitations.
- Added failure-matrix and resilience-scorecard coverage for queue, connection-pool, memory, storage, retry, concurrency, generator, and post-fault recovery behavior.
- Added a planning-only bounded load/recovery example that defines an open workload model, thresholds, telemetry, recovery evidence, and cross-specialist handoffs without generating traffic.
- Preserved `scripts/dagger_guardrail.py` and its simulation-only live-execution block unchanged. Knowledge and tool examples do not grant permission to run destructive, disruptive, externally targeted, or production tests.
- Kept the campaign Markdown-primary and JSON-selective: the SK5 audit found no deterministic machine-parsing need that justified a Dagger JSON catalog.
- Added focused regression coverage for Dagger knowledge depth, source/Codex support-file parity, progressive disclosure, state/evidence separation, and safety-boundary language.
- No release/tag publication, deployment/production mutation, installed-integration refresh, policy activation, destructive cleanup, branch deletion, force push, or history rewrite is performed by SK5.

## Post-v1.2.0 Specialist Knowledge Layer - SK4 Cloak - Pending

- Deepened Cloak's frontend design knowledge without changing specialist ownership, routing authority, package version, or runtime architecture.
- Added progressive-disclosure guidance for semantic HTML, ARIA/accessibility state, keyboard and focus behavior, responsive CSS layout/overflow, forms and validation recovery, design tokens/component states, and frontend routing/component-boundary literacy.
- Expanded four previously minimal Cloak worked examples covering responsive layout, destructive dialog interaction, navigation structure, and checkout recovery.
- Kept the campaign Markdown-primary and JSON-selective: the SK4 audit found no concrete machine-parsing need that justified a new Cloak JSON catalog.
- Preserved implementation ownership with Ponytail, architecture/state ownership with Clockwork, security policy with Cipher, persistence with Chronicler, readiness gates with Overseer, and diagram/documentation ownership with Weaver/Scribe.
- Added focused regression coverage for Cloak knowledge depth and canonical/Codex support-file parity.
- No release/publication, deployment/production mutation, installed-integration refresh, policy activation, destructive cleanup, branch deletion, force push, or history rewrite is performed by SK4.
## Post-v1.2.0 Specialist Knowledge Layer - SK3 Cipher - Pending

- Expanded Cipher from general security/privacy review into deeper authentication, session, OAuth/OIDC, authorization, web/API, sensitive-business-flow, SSRF, secrets/cryptographic-misuse, framework-aware, and security-tooling interpretation guidance while preserving defensive-only specialist ownership.
- Updated standards framing around current primary references including OWASP ASVS 5.0.0, OWASP API Security Top 10 2023, MITRE CWE, OAuth 2.0 Security BCP RFC 9700, JWT BCP RFC 8725, and OpenID Connect Core without claiming automatic compliance or vulnerability proof.
- Added progressive-disclosure guides for authentication/session/OAuth, web/API controls, SAST/DAST/SCA/SBOM interpretation, and framework-aware review cues.
- Added `skills/cipher/patterns/security-control-catalog.json` as selective non-authorizing control-family metadata and extended the existing Codex selective-JSON regression to verify Clockwork and Cipher catalogs.
- Preserved source/Codex portability by regenerating tracked Codex specialist mirrors through the repository exporter.
- Preserved Cipher's defensive-only boundary: no offensive/destructive testing, implementation ownership, architecture ownership, persistence ownership, QA ownership, legal/compliance sufficiency, release approval, deployment, or production mutation is introduced by SK3.
- No release/publication, installed-integration refresh, policy activation, destructive cleanup, branch deletion, force push, or history rewrite is performed by SK3.

## Post-v1.2.0 Specialist Knowledge Layer - SK2 Clockwork - Pending

- Expanded Clockwork from OOP/layering foundations into modern application architecture review covering modular and distributed service boundaries, state and concurrency ownership, API compatibility/versioning, caching, multi-tenancy, background jobs, event-driven flows, outbox/inbox placement, and durable workflow patterns.
- Added progressive-disclosure Markdown guides for modern application architecture and event-driven/workflow reliability while preserving Clockwork as an audit-first boundary specialist rather than an implementation, persistence, security, or QA owner.
- Added `skills/clockwork/patterns/architecture-patterns.json` as selective machine-readable pattern metadata under the campaign's Markdown-primary, JSON-selective storage policy; the JSON catalog does not replace repository evidence or Markdown guidance.
- Extended the Codex exporter to copy `.json` specialist support files alongside Markdown and added regression coverage proving the Clockwork JSON catalog is valid and portable.
- Preserved source/Codex portable parity for all SK2 Clockwork support files without changing routing, manifest contracts, package version, or runtime authority semantics.
- Reconciled Clockwork output ownership so it reports downstream validation properties while Overseer retains QA strategy, test scope, validation-gate, and release-readiness ownership.
- No release/publication, deployment/production mutation, installed-integration refresh, policy activation, destructive cleanup, branch deletion, force push, or history rewrite is performed by SK2.

## Post-v1.2.0 Specialist Knowledge Layer - SK1 Ponytail - Pending

- Added an Orchestra-native Ponytail implementation knowledge layer while preserving Ponytail's established specialist ownership and upstream minimalism principles.
- Added stack discovery, implementation foundations, language/runtime references for JavaScript/TypeScript, Python, Java/JVM, Go/Rust, shell/PowerShell, and browser/web runtime work, plus build/test tooling and worked cross-specialist implementation patterns.
- Added progressive-disclosure loading so stack-specific references are loaded only after repository evidence confirms they are relevant.
- Preserved source/Codex portable parity by mirroring the Markdown support files under `adapters/codex/skills/ponytail/**` without changing exporter semantics.
- Recorded the August 12, 2026 upstream check: `Baelfyre/ponytail` remained on package `4.8.4`, upstream `DietrichGebert/ponytail` was on package `4.9.0`, and the core upstream Ponytail skill blob was unchanged between the reviewed revisions.
- Adopted Markdown-primary, JSON-selective knowledge storage for this campaign. No prose-heavy JSON knowledge files were added.
- No routing, runtime, manifest contract, package version, workflow, release, deployment, installed-integration, policy, production, force-push, history-rewrite, or branch-deletion behavior is changed by SK1.

## Post-v1.2.0 README direct-main governance reconciliation - Pending

- Preserved canonical README commit `807bda608d65cb10bf65cdf313916d9d0fd62320` after exact local content validation confirmed the intended public-facing documentation change.
- Recorded that the commit changed only `README.md`, passed the full behavior suite, passed all 541 runtime tests at 94.31% coverage, and passed strict governance with 0 errors and 0 warnings.
- Recorded the canonical commit as unsigned and the direct-main transition as outside the prescribed pull-request path.
- Applied a forward-only disposition: preserve canonical history, perform no force push or history rewrite, and do not treat the unsigned direct-main result as future precedent.
- Requires a normal exact-head validated pull request and signed Squash canonical result before this remediation is `MERGED_VERIFIED`.
- KB synchronization remains held until the Orchestra remediation is merged and independently verified.
- Performs no release, tag, deployment, marketplace graduation, installed-integration refresh, policy activation, or branch deletion.

## v1.2.0 - Published 2026-08-09

- Published the stable minor release from annotated tag `v1.2.0` at exact release commit `4f3c45f6d1e5f290aca108ddf5810c1b18f1dc76`.
- Published [Orchestra v1.2.0: Governed Orchestration](https://github.com/Baelfyre/Orchestra/releases/tag/v1.2.0) as a non-draft, non-prerelease, immutable GitHub Release.
- Preserved R7-E2, R7-F, R7-G, and R7-H evidence identities, Claude Code `SCAFFOLD_ONLY` maturity, and the repository simulation fixture as pending/empty by design.
- Performed no deployment, marketplace publication, installed-integration refresh, policy activation, force push, history rewrite, or branch deletion.

## v1.2.0 Pre-Publication History - Governed Autonomy Modes and Release-Readiness Closeout

The following entries preserve the verified candidate chronology before the separately authorized August 9, 2026 publication. They are historical release evidence, not current unpublished state.

- Reconciled the README across R7, the R7R Squash-aware governance remediation, GA-0 through GA-7, revision-bound release readiness, host maturity, and the separately authorized R8 publication boundary.
- Added source-pinned acknowledgements for Spec Kitty, OpenHero, and Strix with explicit concept-only, no-wholesale-integration, no-affiliation, and no-unsupported-reuse boundaries.
- Classified every tracked candidate path and every observed local and remote branch, preserving canonical, recovery, archive, open-PR, active-worktree, unique-commit, and release-history refs; no file or branch deletion was performed.
- Squash-merged the pre-R8 hygiene reconciliation through PR #234 as signed no-bypass canonical commit `8cca62109b10aa06abaf25fc4c9982a02160bcbf`, then refreshed the full revision-bound release-readiness matrix against that exact canonical revision.
- Completed the GA-0 architecture and overlap assessment at baseline `8163c64838d369ea5c4abf45df36f6d6504db9fd`.
- Recorded `NO_DUPLICATE_AUTHORITY_MODEL`: existing runtime authority, delegation, lifecycle, evidence, host-continuity, and Squash-aware merge contracts remain canonical.
- Authorized only an instruction-level profile/effective-action contract, deterministic fixture validation, Conductor selection behavior, and documentation parity for GA-1 through GA-7.
- At that checkpoint, preserved `v1.2.0` as `PREPARED_NOT_RELEASED`, Claude Code as `SCAFFOLD_ONLY`, and R8 as a separate human publication gate.
- Added the GA-1 through GA-7 profile, execution, selection, continuity, adversarial-validation, Codex-parity, and adoption contracts without changing `orchestra_runtime/**`.
- Squash-merged GA-0 through GA-7 through PR #232 as signed canonical commit `900f88d7a3ed480ae8b910e6ba204008a72d2784`, with exact reviewed/canonical tree equivalence, an empty content diff, green exact-head CI, and a passing rulesuite.
- Refreshed the canonical behavior, runtime-coverage, strict-governance, packaging, R7 reliability, GA, and merge-readiness evidence after the GA merge; recorded the result in `docs/validation/V1_2_0_RELEASE_READINESS_EVIDENCE.md`.
- Before R8, independently verified that the latest public release remained `v1.1.2`, no `v1.2.0` tag or GitHub Release existed, and publication remained blocked pending separate human authorization.

This changelog records release-level Orchestra history. Detailed implementation chronology remains available in Git history, merged pull requests, `DECISION_LOG.md`, `PROJECT_STATE.md`, and immutable handoff records.

## v1.2.0 Pre-Publication Release-Candidate History

This section records the final pre-publication candidate state. Repository manifests had been normalized to `1.2.0` while the latest public release was still `v1.1.2`. R7, R7R, and Governed Autonomy Modes were `MERGED_VERIFIED`, and invalidated release evidence had been refreshed. R8 later published `v1.2.0` under separate authority.

### R7 Live-Host Evidence Reconciliation - Pre-Publication History

- Reconciled accepted locally installed-host evidence for Antigravity same-host reset/resume, Codex same-host reset/resume, and Codex -> Antigravity portable handoff.
- Recorded Claude Code `SCAFFOLD_ONLY` packaging/contract compatibility without claiming active runtime continuity.
- Preserved the repository-simulation/live-evidence boundary, including the unchanged pending/empty fixture live record set and canonical validator.
- PR #230 merged the reviewed R7 content to canonical `main`; reviewed and canonical trees are equivalent, but GitHub's then-used rebase merge rewrote the reviewed commit identity and produced an unsigned canonical commit.
- The maintainer chose a forward-only disposition: preserve canonical history, perform no force push/history rewrite, and treat PR #230 as incident evidence rather than future merge precedent.
- Performed no publication, tag creation, deployment, installed-integration refresh, or policy activation.

### R7 Merge-Governance Remediation

- PR #231 aligned the autonomous merge-readiness contract with the current solo-maintainer `Protect main` ruleset and was independently verified as signed Squash commit `8163c64838d369ea5c4abf45df36f6d6504db9fd`.
- Mirror all eight current required status checks: `governance-check`, `validate`, `runtime-tests`, native Windows/Ubuntu/macOS, `Analyze (actions)`, and `Analyze (python)`.
- Replace ancestry-only post-merge verification with Squash-aware proof of exact pre-merge base, reviewed/canonical tree equivalence, empty content diff, and verified canonical commit signature.
- Preserve the existing bypass list as operational repository capability while making `BYPASS_CAPABILITY != GOVERNANCE_AUTHORIZATION` an explicit fail-closed rule.

### Added

- Delegated Phase B instruction-level autonomous progression with approved execution envelopes, six transition dispositions, checkpoints, bounded remediation, capacity handoff, current evidence requirements, and default-deny external-action authority.
- The Tuner cross-specialist coordination stack through Phases 1-4: contract assembly, missing-owner and contradiction detection, semantic invalidation, evidence continuity, typed in-memory coordination records, deterministic transitions/rejections, minimal specialist re-entry, and bounded Conductor-owned runtime integration.
- Spec Kitty-derived governed phase execution contracts: `OrchestraRuntimeEnvelope`, `OrchestraCorrelationID`, `OrchestraPhaseRetrospective`, the 15-field `ApprovedUnitPlan` extension, `OrchestraStatusProjection`, and `OrchestraWorktreeContract`.
- Cross-layer integrity audit profiles for frontend-to-backend synchronicity, backend-to-persistence integrity, and language-neutral cross-module logical flow using the existing Conductor -> Tuner -> specialist -> Overseer -> Arbiter ownership model.
- Delegated Phase C repository host-reliability contracts and deterministic adversarial fixtures covering reset/resume, active-host handoff, capacity waits, stale identity, incomplete checkpoints, scaffold-only hosts, authority expansion, and duplicate replay.
- Fail-closed autonomous merge-readiness protocol, machine-readable evaluation fixtures, and runtime regressions requiring green canonical baseline, exact-head evidence, complete successful required checks, changelog freshness, expected-head merge guards where supported, and independent post-merge verification.
- Source-backed candidate notes later promoted to stable `docs/releases/v1.2.0-governed-orchestration.md`; the former candidate path remains as a compatibility pointer for immutable historical references.

### Changed

- Reconciled Delegated Phase D against the existing trusted runtime. PR #226 concluded `NO_DUPLICATE_RUNTIME_EXTENSION_REQUIRED` for `v1.2.0`; no competing runtime model was added.
- Reconciled canonical delegated-governance state so stale Phase C/D not-started claims and false live-host promotion are rejected by executable consistency validation.
- Normalized the root, Claude Code, Codex, and scaffold adapter version surfaces to `1.2.0` without changing adapter maturity or publishing any IDE marketplace package.
- Updated README, project context/state, session handoff, roadmap, compatibility, installation, and Codex adapter documentation to distinguish release-candidate metadata from the current public release.
- Consolidated the previously fragmented post-`v1.1.2` unreleased changelog entries into this release-candidate record while preserving detailed implementation evidence in Git and pull-request history.
- Added Governed Autonomy Modes to the `v1.2.0` scope after R7 closeout and before R8 publication; affected release evidence must be refreshed after implementation.

### Clean Replay and Governance Hardening

The first autonomous finalization experiment was rolled back to the verified recovery point and preserved as audit evidence. The accepted clean replay and hardening sequence is:

- R1 / PR #223 - Spec Kitty Phase 3 and roadmap reconciliation.
- R2 / PR #224 - backend-to-persistence and cross-module logical-flow integrity.
- R3 / PR #225 - delegated Phase C repository host-reliability contract after bounded fixture remediation and a fully fresh exact-head matrix.
- R4 / PR #226 - Phase D runtime-overlap reconciliation with no duplicate runtime extension required.
- R5 / PR #227 - autonomous merge-readiness hardening.
- R5B / PR #228 - delegated-governance current-state reconciliation, merged at `fbe4532ba2083feaa7ed9fcda2988843f1237a78` and independently verified on canonical `main`.
- R6 - `v1.2.0` release-candidate metadata, public documentation, changelog, and release-note preparation.
- R7 / PR #230 - accepted live-host evidence merged; subsequent verification exposed the ancestry/signature mismatch caused by the then-used rebase merge and triggered forward-only ruleset/protocol remediation.

Historical fail-open or bypass-capable platform behavior is not successful validation precedent.

### Capability Merge Map

Key post-`v1.1.2` canonical milestones include:

- PR #190 - Delegated Phase B instruction-level progression.
- PR #191 - Phase B post-merge synchronization.
- PR #197 - The Tuner Phase 2 evidence identity and continuity.
- PR #198 - The Tuner Phase 3 typed in-memory coordination runtime.
- PR #200 - The Tuner Phase 4 scenario validation and runtime integration.
- PR #201 - Tuner Phase 4 post-merge continuity state.
- PR #208 - Spec Kitty-derived Phase 2 governed execution contracts.
- PR #210 - Spec Kitty-derived Phase 3A design and ownership package.
- PR #212 - `OrchestraStatusProjection`.
- PR #214 - `OrchestraWorktreeContract` and Phase 3 completion.
- PR #216 - frontend-to-backend synchronicity contract.
- PR #223 - clean replay roadmap/state closeout.
- PR #224 - backend-to-persistence and cross-module logical-flow profiles.
- PR #225 - Delegated Phase C repository host-reliability contract.
- PR #226 - Delegated Phase D overlap reconciliation.
- PR #227 - autonomous merge-readiness hardening.
- PR #228 - delegated-governance current-state reconciliation.
- PR #230 - R7 live installed-host evidence reconciliation.

### Compatibility and Authority Boundaries

- Codex, Claude Code, and Antigravity retain supported integration surfaces; version normalization does not by itself prove live installed-host continuity.
- Cursor, Windsurf, VS Code/VSCodium, JetBrains, Zed, and Neovim remain scaffold-only. No scaffold is graduated or marketplace-published by R6.
- Existing authority, immutable run-scoped capabilities, bounded delegation, lifecycle, coordination ownership, evidence identity, and default-deny external-action controls remain unchanged.
- Repository ruleset bypass capability is operational access only and does not itself authorize Orchestra to skip governance evidence or transitions.
- No persistent collaboration storage, SQLite, migrations, RPC, network daemon, remote worker, background agent, production deployment, or automatic policy activation is added by the release candidate.

### Evidence Boundary

Repository CI proves deterministic repository behavior for the exact candidate revision. The accepted locally installed-host records are documented separately in `docs/validation/R7_LIVE_INSTALLED_HOST_VALIDATION_EVIDENCE.md`; they do not promote Claude Code beyond `SCAFFOLD_ONLY` or change what repository-only validation can prove.

```text
REPOSITORY_SIMULATION != LIVE_HOST_EVIDENCE
LIVE_INSTALLED_HOST_VALIDATION=VERIFIED_RECONCILED_LOCALLY
```

At this pre-publication checkpoint, R7 host-derived evidence and the forward-only merge-governance remediation were verified and canonical. Governed Autonomy Modes, refreshed release verification, and separate R8 authority still remained required.

### Historical Publication Boundary

At this recorded pre-R8 checkpoint, the `v1.2.0` candidate was not yet a public release. The finalization work itself authorized no tag, GitHub Release publication, deployment, marketplace graduation, installed-host mutation, policy activation, force push, or history rewrite.

Publication subsequently required and received GA-0 through GA-7 canonical completion, refreshed release-readiness evidence, independent final verification, and separate R8 authority.

---

## v1.1.2 - Trusted Runtime Authority

Published July 14, 2026.

### Added

- Trusted runtime composition with explicit finite `ACTIVE` and `COMPATIBILITY` authority modes.
- Immutable run-scoped runtime capability manifests and fail-closed authority/capability enforcement before governance.
- Bounded in-process specialist delegation with authority and capability subset enforcement, depth limits, specialist identity checks, and explicit context minimization.
- Structured lifecycle control with deterministic terminal replay, conflict rejection, and exact state transitions.
- `RuntimeExecutor` integration with authority and capability checks before governance and adapter execution.
- Adversarial validation for initialization, escalation, provenance, binding ownership, delegation, lifecycle, execution ordering, replay, and audit-sink failure paths.
- Deterministic non-authorizing audit events.
- Four governed Artificer promotions finalized as `IMPLEMENTED` with synchronized Pattern Catalog records and preserved provenance/attribution boundaries.

### Changed

- Normalized approved plugin and scaffold-package metadata to `1.1.2` without changing scaffold maturity.
- Refreshed release, setup, compatibility, runtime, project-state, Codex, roadmap, architecture, and handoff documentation for the trusted runtime authority baseline.

See [v1.1.2 release notes](docs/releases/v1.1.2-trusted-runtime-authority.md).

---

## v1.1.1 - Post-Release Hardening

### Changed

- Hardened release-surface and startup-state validation, including Codex metadata and structured branch/version claims.
- Converted PowerShell and shell validation entrypoints into thin wrappers around canonical Python validators to reduce cross-platform drift.
- Hardened update and rollback guidance with fast-forward-only pulls, canonical post-update validation, and recovery-branch guidance.
- Fixed runtime context assembly so adapter-provided `ContextPackage` metadata is preserved and enriched rather than bypassed.

---

## v1.1.0 - Specialist Governance & Boundary Standard

### Added

- Added the shared `docs/project/SPECIALIST_AUTHORING_STANDARD.md` and normalized specialist authoring expectations.

### Changed

- Clarified governance, specialist, routing, validation, local-safety, and handoff boundaries across the public specialist set and Codex exports without changing trusted runtime behavior.
- Strengthened Cloak, Conductor, Ponytail, Clockwork, Cipher, Overseer, Chronicler, Scribe, Weaver, Governor, and Steward documentation consistency.

---

## v1.0.0 - Portable Runtime

### Release Highlights

- Added `orchestra_runtime/` as the shared runtime core for routing, manifest parsing, skill loading, governance validation, execution flow, and audit logging.
- Added `PRAP v1` as the stable Portable Runtime Adapter Protocol for host metadata, capabilities, compatibility, and validation.
- Added thin adapter support for Codex, Claude Code, Antigravity, Cursor, Windsurf, VS Code/VSCodium compatibility, JetBrains, Zed, and Neovim.
- Added scaffold-only packaging surfaces for Cursor, Windsurf, VS Code, JetBrains, Zed, and Neovim.
- Normalized release-facing documentation, compatibility guidance, and manifest metadata for the Portable Runtime baseline.

---

## Earlier Repository History

Pre-`v1.0.0` implementation detail, router-first evolution, Artificer phases, governance calibration, prompt-load work, cross-platform validation changes, and specialist foundation history remain preserved in Git history and the repository's decision, roadmap, governance, and handoff records. The changelog is intentionally release-oriented rather than a duplicate of every commit.