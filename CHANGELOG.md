# Changelog

## v1.6.0 Integration & Developer Experience - Release Candidate

- Completes the v1.6 release-facing onboarding and provenance closeout: the root README now states Orchestra's purpose, gives exact MCP and Adapter SDK/PRAP quickstarts, and exposes human/machine provenance entry points; the machine provenance registry reconstructs current and historical upstream relationships with semantic context, explicit incorporation boundaries, and behavior-contract regression coverage.
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