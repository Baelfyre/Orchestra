# Changelog

## Post-v1.7 Cloak CUIR-0 corpus governance candidate

- Added the bounded `CUIR-0` governance and intake contract for `CLOAK_UI_REFERENCE_CORPUS_V1`, freezing per-repository eligibility, provenance, exact source-revision pinning, reuse classifications, specialist ownership, and data-minimization rules before any broad corpus inventory or pattern extraction.
- Added machine-validatable policy and source-record schemas that fail closed: missing or ambiguous licenses permit concept-level `REFERENCE_ONLY` treatment only and cannot authorize direct source or asset reuse; account-wide license inference and automatic ingestion are prohibited.
- Added adversarial tests that reject malformed source revisions, missing non-copying provenance, invalid reuse classifications, missing `Nazia-99` attribution, authority widening, and external-execution widening.
- CUIR-0 performs no `Nazia-99` repository inventory, hard-codes no repository count, copies no external source/assets, installs no external dependencies, executes no external project code, grants no Cloak implementation authority, and does not authorize provider routing/fallback, merge, release, deployment, policy activation, integration refresh, destructive cleanup, branch deletion, force push, or history rewrite.

## Post-v1.7 Priority 2 VS Code multi-harness provider qualification candidate

- Added a bounded, non-authorizing VS Code provider-observation and qualification layer that keeps host, harness, provider source, provider, model, and authority identities separate across Local, Copilot, Claude, and Codex session paths.
- Added a frozen read-only qualification fixture, exact fixture SHA-256 binding, machine schemas, CLI validation, and adversarial runtime tests so static configuration, host-routed model evidence, provider-native harness evidence, and failed live paths cannot be conflated.
- Added a user-controlled VS Code operator protocol that requires visible harness/model/provider-source evidence and clean repository state before and after the fixture; current VS Code worktree isolation is not treated as sandbox or network-restriction proof.
- P2.2B does not control VS Code, create an AHP client, install or refresh integrations, mutate credentials/settings, call provider APIs directly, claim live provider evidence from deterministic tests, qualify the P2.2A standalone Claude CLI from a VS Code session, enable routing/fallback, mutate Registry state, release, deploy, activate policy, delete branches, force push, or rewrite history.

## Post-v1.7 Priority 2 Claude Code provider-native engine candidate

- Completed a fresh second-provider audit and selected Claude Code for the bounded P2.2A candidate because its current CLI exposes invocation-scoped model selection, structured output, tool restriction, permission mode, safe-mode/customization suppression, browser disablement, MCP denial, and session-persistence controls without requiring Orchestra to mutate persistent user permissions.
- Added a bounded read-only Claude Code specialist execution bridge that requires an explicit model, Claude Code CLI `>= 2.1.205`, exact Scribe source-digest binding, clean and unchanged repository state, `plan` permission mode, the fixed `Read`/`Glob`/`Grep` tool set, denied MCP tools, safe mode, disabled browser/session persistence, schema-conforming output, and `non_mutating=true`.
- Added the `anthropic-claude-code` provider profile wrapper while deliberately not claiming OS-level read-only sandbox control or streaming host-activity observation; deterministic adversarial tests cover policy widening, identity mismatch, version floor, timeout, malformed output, host failure, and repository-state drift.
- P2.2A is deterministic qualification only and does not claim live Claude provider E2E, automatic provider routing or fallback, direct provider APIs/SDKs, credential or global Claude settings mutation, Registry mutation, release, deployment, policy/ruleset activation, integration refresh, destructive cleanup, branch deletion, force push, or history rewrite.

## Post-v1.7 Priority 2 provider execution profile candidate

- Added a deterministic, non-authorizing provider execution profile and trusted provider/model/capability requirement gate for explicit host-native specialist execution, while preserving existing route-only and provider-free deterministic runtime paths.
- Added separate provider-aware MCP constructors and Codex App Server wrappers that map the existing explicit user-selected model configuration into `openai-codex` provider profiles without widening approval, sandbox, network, specialist, command, or mutation scope.
- Added Draft 2020-12 provider profile/requirement schemas and focused regressions for deterministic identity, fail-closed mismatch and drift handling, authority-before-provider ordering, minimized provider evidence, and prompt/MCP metadata non-override.
- P2.1 does not add automatic provider routing or fallback, direct provider SDKs/APIs, credential handling, a static model catalog, Registry mutation, release, deployment, policy activation, integration refresh, destructive operations, branch deletion, force push, or history rewrite.

## Post-v1.7 Unified Testing Mechanism Efficacy Calibration

- Added a deterministic offline 15-case baseline-versus-UTM efficacy calibration, machine-readable result, qualification record, focused regression tests, and independent read-only audit for the canonical experimental UTM candidate.
- The bounded calibration improved readiness-decision accuracy from 8/15 for the distributed-evidence proxy to 15/15 for UTM and unsafe-case detection from 4/11 to 11/11, with zero UTM false positives or false negatives in the frozen fixture corpus; all preregistered thresholds passed.
- The evidence recommendation is `ADOPT_OPTIONAL`, not mandatory/default adoption. Human operator time, live-host token cost, and live-host latency remain unmeasured; zero model/provider calls were performed, runtime integration remains disabled, and efficacy evidence grants no protected-action authority.

## Post-v1.7 Unified Testing Mechanism Experimental Candidate

- Added an `EXPERIMENT_ONLY` T0-T9 applicability and revision-bound evidence aggregation candidate that reuses existing specialist and CI validation surfaces rather than creating a second QA engine.
- Added deterministic fail-closed handling for missing, pending, failed, stale-revision, non-applicable, and malformed stage evidence while preserving `READINESS_EVIDENCE_COMPLETE != RELEASE_AUTHORITY` and all existing protected-action gates.
- Permanent promotion remains `PENDING` until the approved controlled baseline-versus-UTM efficacy campaign establishes measurable value relative to complexity and operating cost.

This root changelog is release-oriented. Detailed pre-v1.7 development chronology remains preserved byte-for-byte in [the historical changelog archive](docs/history/CHANGELOG_PRE_V1_7.md), Git history, merged pull requests, decision records, and validation evidence.

## Post-v1.7 Specialist Runtime-Host Pre-E7 Effectiveness Revalidation

- Corrected the E5 replay harness to validate current Git HEAD/tree and clean-worktree identity without coupling replay to a historical branch name, and required explicit model selection for new E5/E6 validation entrypoints.
- Revalidated the bounded Codex App Server bridge with three independent read-only E5 Scribe trials and three independent isolated E6 Ponytail mutation trials on the current validation candidate. All six trials passed with zero identity, authority, capability, governance, network, process, delegation, or out-of-scope mutation violations.
- Recorded the exact bounded evidence and preserved route-only defaults, disabled default runtime mutation, unclaimed MCP mutation E2E, `E7 = PENDING`, and `PROMOTION = PENDING`.

## Post-v1.7 Codex user-selected model configuration candidate

- Added a pre-E7 trusted configuration boundary that requires an explicit non-empty Codex model identifier instead of treating the Sol model used by E5/E6 verification as a permanent runtime default.
- Added focused runtime tests proving the selected model and optional reasoning effort are carried into the existing bounded read-only and mutation-assessment configurations without widening approval, sandbox, network, write-scope, specialist, or command controls.
- Preserved the historical E5/E6 `gpt-5.6-sol` proof identity unchanged for reproducibility. Historical tested-model identity is evidence only and does not define Orchestra's runtime default.
- This candidate does not decide E7 promotion, enable default runtime mutation, claim MCP mutation E2E, merge canonically, publish a release, deploy, activate policy, refresh integrations, or authorize destructive operations.

## Post-v1.7 Codex host bridge E5 candidate

- Added an internal, experimental Codex App Server bridge candidate behind the existing `ISpecialistExecutionEngine` boundary for the bounded E5 `review-docs` to Scribe proof. The default runtime and default MCP builders remain route-only.
- Froze the E5 host boundary to read-only sandboxing, approval policy `never`, network disabled, exact Scribe source-digest binding, recursive Orchestra MCP suppression, clean-worktree enforcement, and fail-closed handling for file changes, MCP or dynamic tool use, delegation activity, web search, approval escalation, diffs, malformed results, timeout, and repository-state drift.
- Added deterministic adversarial runtime tests plus a source-backed Scribe fixture and an internal live-proof harness for exact MCP command acceptance, Scribe routing, typed request/receipt identity, task-specific output, unchanged worktree, recursion prevention, and minimized evidence.
- E5 live installed-host verification has not yet been claimed by this candidate. E6 is authorized but not run by this change, and promotion remains pending. This candidate does not authorize canonical merge, release, deployment, policy activation, installed-integration refresh, destructive cleanup, branch deletion, force push, or history rewrite.

## Post-v1.7 deterministic specialist execution E1-E3 foundation

- Added a host-neutral `ISpecialistExecutionEngine` boundary plus immutable typed specialist execution request and receipt contracts that bind run, route, specialist source digest, task input, authority/capability decision references, governance state, trusted execution constraints, engine identity, outcome, evidence, and side-effect classification.
- Added an opt-in `SpecialistRuntimeExecutor` layered over the existing `RuntimeExecutor` so engine invocation occurs only after the established coordination, exact-binding, authority, capability, governance, and lifecycle-activation gates. The existing runtime executor remains route-only by default.
- Added strict request/receipt JSON Schemas and deterministic adversarial tests proving that authority, capability, governance, or coordination denial prevents engine invocation; mismatched or malformed receipts and engine exceptions fail closed instead of degrading to route-only success.
- Added an explicit MCP specialist-execution builder that reuses the existing MCP `2026-07-28` `server/discover`, `tools/list`, and `tools/call` surface while leaving the existing MCP builders unchanged and route-only. MCP prompt content and client metadata cannot select or activate an execution engine.
- E1-E3 use deterministic no-network test engines only. No Codex host bridge, MCP Sampling, direct provider SDK, live model/provider call, installed-integration refresh, release, deployment, policy activation, destructive cleanup, branch deletion, force push, or history rewrite is introduced or authorized by this foundation. E4-E6 live-host evidence remains separately bounded.

## Post-v1.7 Codex MCP installed-host routing revalidation and documentation parity

- Revalidated the installed Codex MCP `2026-07-28` path with Orchestra connected and 20 projected tools, then successfully dispatched `mcp__orchestra__review_docs` with `isError: false` in a bounded read-only session.
- Confirmed that Codex requires both host opt-ins: the `mcp_2026_07_28` feature and the per-server `CODEX_MCP_PROTOCOL_VERSION=2026-07-28` environment marker. Actual approval-required `tools/call` verification also requires a session policy that can request approval rather than `never`.
- Classified the successful tool result as routing E2E evidence only. The default MCP runtime does not configure a host-native specialist execution engine, so route acknowledgement proves specialist selection but does not prove substantive Scribe execution.
- Canonicalized the Codex setup, troubleshooting, routing-boundary, and installed-host evidence documentation, then realigned the OOP runtime architecture document with the current Adapter SDK / PRAP and MCP route-only runtime boundary.
- `v1.7.0` remains the immutable current public release. This post-release maintenance does not publish or move a release/tag and does not expand runtime authority, deploy, activate policy, refresh installed integrations, mutate rulesets, perform destructive cleanup, delete branches, force push, or rewrite history.

## Post-v1.7 canonical O7 and Developer Portal state reconciliation

- Reconciled the Developer Portal machine projection, schema, documentation, and regression expectations to the already-published `v1.7.0` release at commit `e5305ef3e160209a0345bd2c7843c923940e62c5`, including `authority.implements_mcp = true` and the retained bounded MCP stdio state `PUBLISHED_V1_6_STABLE_RETAINED_V1_7`.
- Reconciled O7.7 and the coupled O7 runtime-state projections from stale pending-canonicalization wording to the existing completed `CANONICAL_MERGED_VERIFIED` state while preserving the trusted Registry v0.4.0 identities and fail-closed/non-authorizing boundaries.
- Updated only the directly coupled regression tests and `README.json` machine projections needed to enforce that state. No runtime behavior, Registry cache, installed integration, policy, release, deployment, ruleset, authority, or protected-operation boundary is changed by this reconciliation.

## Post-v1.7 Codex MCP 2026 discovery compatibility

- Corrected the MCP `2026-07-28` `server/discover` result shape by adding `ttlMs: 0` and `cacheScope: "private"`, matching the modern Codex discovery contract while preventing reusable discovery caching or stale capability assumptions.
- Added a focused Codex discovery compatibility regression test and synchronized the detailed MCP transport documentation plus `README.json` machine parity.
- Codex hosts still require the `mcp_2026_07_28` feature and `CODEX_MCP_PROTOCOL_VERSION=2026-07-28` stdio-server marker; this repository change does not itself establish a successful installed-host connection.
- The fix preserves required MCP `_meta` validation and the modern stateless lifecycle. It does not add the retired `initialize` lifecycle, expand tool or runtime authority, publish a release, deploy, activate policy, refresh installed integrations, or authorize protected operations.

## Post-v1.7 O7.7 trusted Registry joint conformance

- Added an executable cross-repository O7.7 conformance gate against immutable `registry-v0.4.0`, exact release source `488c979b37dd84d8645fd8e6c288d297375c4e5b`, release-manifest SHA-256 `040d6576cf10e9f7e3a9a051792869541c1d33b7af3c665fad8eecb939c7baaa`, and bundle SHA-256 `e0457a75837d169d7bb8a7da14d8f4141d35a691952ff8f8978ef793e3cf92d3`.
- Bound joint conformance to the validated post-release Registry runtime at commit `4926a3b5f48122dd45f3c8e83a12b8d071dd5387`, tree `01be27bde90f6faa59ab74d60ba13af480c11b1d`, including trusted direct-JSON identity verification without changing the immutable v0.4.0 release.
- Verified the same privacy `EVIDENCE` query through trusted direct JSON, verified indexed gateway, and read-only MCP transport with semantic parity across records, source IDs, obligation IDs, query digest, freshness evidence, and normalized `ComplianceQueryReceipt` identity.
- Preserved Registry canonical JSON as authority, retained O1-O6 fallback and fail-closed semantic/integrity behavior, and prohibited authority expansion and model-authored integrity repair.
- The R7.9 benchmark did not establish token-efficiency benefit, so no token-efficiency claim is introduced. O7.7 conformance evidence does not itself authorize an Orchestra release, deployment, policy activation, installed-integration refresh, or any other protected action.

## Post-v1.7 O7.1-O7.6 Registry R7 direct consumption runtime

- Integrated Orchestra O7.1 through O7.6 against the canonical Registry R7.1-R7.6 stable direct surface at commit `155c21ab54f704d876ae4a0c2d995f5591f13930`, tree `ea99fce806a455c4c1e2c912277c44d3595f54d8`, without reimplementing Registry-owned query semantics in Orchestra.
- Added optional R7 capability negotiation, deterministic indexed/direct-JSON/O1-O6 fallback selection, `MINIMAL`/`SUMMARY`/`EVIDENCE`/`FULL` projection-aware consumption, and normalization into the existing `ComplianceQueryReceipt` evidence model.
- Added fail-closed semantic and result-digest integrity checks, deterministic index rejection/fallback behavior, context-budget capability gating, exact source/obligation identity preservation, and machine-readable runtime state bound to the verified Registry dependency.
- Preserved the existing O1-O6 compatibility path when optional R7 capabilities are absent; required `cap.query.v1` incompatibility remains fail closed and transport/projection choices do not expand authority.
- R7.7 MCP, Registry `v0.4.0` trusted immutable publication, trusted-release integration, measured R7.9 efficiency benchmarking, O7.7 joint conformance, release, deployment, and policy authority remain outside this runtime increment and are not claimed by it.

## Post-v1.7 O7.0 Registry consumer contract freeze

- Froze Orchestra O7.0 consumer expectations against the signed Registry R7 architecture at commit `c1910806ed3ea9147af96b1c49a9f72aef75e0f6`, tree `0c37d7bf47fc20b49b26fea156c8e180db57b4a3`, and R7 document blob `9f24a10f455a77509ec5246e6981ca2672624ca1` while retaining Registry R7 status `APPROVED_PLANNED_NOT_IMPLEMENTED`.
- Preserved required `cap.query.v1` at consumer floor `1.0.0` and froze the five future R7 optional capability IDs at Orchestra minimum `1.0.0` acceptance floors without claiming that Registry currently publishes or implements those capabilities.
- Froze indexed/local/MCP transport precedence, `MINIMAL`/`SUMMARY`/`EVIDENCE`/`FULL` projection semantics, existing `ComplianceQueryReceipt` normalization identities, fail-closed integrity dispositions, and existing Orchestra context-budget ownership.
- Added a machine-readable O7.0 contract, Draft 2020-12 schema, and deterministic runtime contract tests that reject authority expansion, capability-set drift, transport-precedence drift, and premature O7.1+ activation.
- O7.1+ runtime implementation remains blocked by `IMPLEMENTED_STABLE_REGISTRY_R7_SURFACE_REQUIRED`; no Orchestra runtime behavior, Registry source, release/tag, deployment, policy, installed integration, ruleset, or protected action is changed by O7.0.

## Post-v1.7 Prime Directive / Development Lifecycle V2 canonical closeout

- PR #592 squash merged the reviewed Prime Directive and Development Lifecycle V2 realignment tree to signed canonical `main` commit `a04dafe75fc52ecc1fedcc17a73b14b8a31f548a`, tree `854ebfb01b05226304f36d2c35420658c5c8e91f`; the reviewed tree equals the canonical tree.
- Before merge, active `Protect main` ruleset `17927422` was separately corrected under explicit ruleset-mutation authority by removing only the unintended duplicate `native-ubuntu-latest` required-status entry. Strict required-status enforcement, Squash-only merging, linear history, required signatures, pull-request requirements, and the existing bypass actors remained preserved.
- Post-merge exact-canonical validation passed: Required Analysis Compatibility `33121949316`, Governance Check `33121949333`, `validate` `33121949278`, Cross-platform Validation `33121949330`, and GitHub CodeQL push analysis `33121948441`.
- `v1.7.0` remains the immutable current public release. PR #592 is post-release canonical maintenance and did not publish or move a release/tag.
- UIX-9C V3 remains terminal negative evidence with `NO_BENEFIT_ESTABLISHED`; this closeout does not authorize another experiment or live model/provider call.

## Post-v1.7 constitutional and controlled-study closeout

- Completed UIX-9C V3 with six valid observations and three corrected valid pairs. All 39 primary governed-versus-baseline comparisons were unchanged, producing terminal `NO_BENEFIT_ESTABLISHED` with no benefit, harm, or directional model-behavior claim.
- Added Orchestra Prime Directive v1 and Feature Admission v1, separating implementation correctness from permanent capability promotion and retaining negative/inconclusive evidence as valid decision evidence.
- Added Development Lifecycle V2 candidate maturity and Feature Freeze, thin governed-autonomy lifecycle integration, risk-proportional qualification/evaluation/audit, and forward-only recovery/branch-retirement contracts without introducing a second governance, autonomy, runtime-lifecycle, Arbiter, or merge engine.
- Reconciled the historical Campaign 0-5 stack onto current post-UIX `main`, preserving current UIX/runtime work and the repository contract's unique required-check profile. During candidate construction, the live ruleset still contained a duplicate `native-ubuntu-latest` entry; that external policy drift was separately corrected before PR #592 merged and was not mutated by the source candidate itself.
- Realigned the public README, project context, governance index, and documentation map around Mission, Vision, the Prime Directive, Development Lifecycle V2, and the completed UIX null result while retaining v1.7.0 as the immutable latest published release.
- No new live model/provider call, release, deployment, policy activation, installed-integration refresh, branch deletion, destructive cleanup, force push, or history rewrite is introduced by this realignment.

## Post-v1.7 governed proof preparation

- Connected the frozen deterministic evaluator, observation validation, evidence persistence, and adjudication into the future live-proof execution path with fail-closed valid-session semantics and staged evidence finalization.
- Removed the repository-rules bypass from the Codex adapter and froze the supported `codex --ask-for-approval never exec` ordering with zero-call regression coverage.
- No live model or provider call, experimental run, external repository mutation, release, deployment, or policy activation is introduced.

- Added the UIX-9B V2 deterministic live-proof evaluator, frozen calibration cases, isolated UI fixture, machine contracts, zero-call adjudication path, and human authorization envelope.
- Corrected the UIX-9A and UIX-9B preparation runners to bind the frozen canonical SHA to `origin/main`, allowing a validated preparation candidate to run ahead on its isolated branch without changing frozen proof identities.

## v1.7.0 - Adaptive Intelligence, Portable Memory & Design Fidelity

Release tracking: [#563 - Release v1.7.0: Adaptive Intelligence, Portable Memory & Design Fidelity](https://github.com/Baelfyre/Orchestra/issues/563) (`CLOSED_COMPLETED`)

Published release: [Orchestra v1.7.0](https://github.com/Baelfyre/Orchestra/releases/tag/v1.7.0)

Release-source description: [v1.7.0 release candidate notes](docs/releases/v1.7.0-adaptive-intelligence-portable-memory-design-fidelity-release-candidate.md)

Published August 25, 2026 (UTC).

### Added

- Post-v1.6 adaptive orchestration foundations covering machine-local adaptive memory, bounded advisory specialist context, evidence-bounded shadow learning, shadow selection, and shadow topology evaluation without granting learned state execution or policy authority.
- Governed UI design-fidelity contracts and validation through the UIX-9A proof-preparation boundary, including design-source preservation, project-native component/token/asset handling, specialist integration, portability, and deterministic validation.
- Deterministic Registry adaptive-consumption and provenance/freshness improvements already canonical on the post-v1.6 main line.
- A storage-agnostic portable adaptive-memory boundary for explicitly reviewed learned candidates, supporting generic local JSON, Git-backed JSON, HTTP/API, and custom backends without coupling Orchestra to a specific external repository or service.

### Changed

- Simplified the public README so stable capabilities and current release state are primary, while detailed comparative benchmark results are linked as research/validation evidence rather than embedded as large landing-page tables.
- Portable adaptive-memory payloads exclude raw conversation, credentials, sensitive data, and local identity; backend configuration remains external to portable learned-pattern records.
- The root changelog is now release-oriented. The former detailed chronology is retained unchanged under `docs/history/CHANGELOG_PRE_V1_7.md` instead of being deleted.
- Post-release documentation parity aligns README, machine index, setup/compatibility, project continuity, MCP/PRAP, maturity, contribution, and validation guidance with the published v1.7.0 state.
- Added `requirements-dev.txt` so core local runtime-test dependencies are discoverable without reverse-engineering CI YAML.

### Research closeout

- The completed comparative program did not establish a repeatable Murmurs efficiency benefit. Murmurs is not promoted to the default execution path and is not required by specialists.
- Detailed benchmark and experiment evidence remains preserved under [`docs/benchmarking/`](docs/benchmarking/) and [`machine/benchmarking/`](machine/benchmarking/).
- Negative or inconclusive research evidence remains historical evidence and does not grant runtime authority, release permission, deployment permission, or policy activation.

### Release boundary

Orchestra v1.7.0 is published and independently verified at immutable tag/release target `e5305ef3e160209a0345bd2c7843c923940e62c5`. Post-release maintenance does not move that tag or create a new release. Deployment, production mutation, policy activation, installed-integration refresh, destructive cleanup, branch deletion, force push, and history rewrite remain separately controlled.

---

## v1.6.0 - Integration & Developer Experience

Published August 17, 2026.

- Stable Adapter SDK / PRAP v1 compatibility certification and Developer Portal.
- Governed Host Update planning and bounded MCP stdio transport.
- Hybrid context representation with JSON as canonical structured machine state and TOON as derived, validated, non-authoritative representation only when useful.
- TrueSheet specialist-reference enrichment and documentation architecture v2.
- Signed-materialization and exact-head validation improvements.

See [Orchestra v1.6.0](https://github.com/Baelfyre/Orchestra/releases/tag/v1.6.0) and the [historical detailed changelog](docs/history/CHANGELOG_PRE_V1_7.md).

## v1.5.0 - Machine-Verifiable Control Plane and Murmurs

Published August 16, 2026.

See [Orchestra v1.5.0](https://github.com/Baelfyre/Orchestra/releases/tag/v1.5.0) and the [historical detailed changelog](docs/history/CHANGELOG_PRE_V1_7.md).

## v1.4.0 - Governance and Compliance Registry Cross-Integration

Published August 14, 2026.

See [Orchestra v1.4.0](https://github.com/Baelfyre/Orchestra/releases/tag/v1.4.0) and the [historical detailed changelog](docs/history/CHANGELOG_PRE_V1_7.md).

## v1.3.0 - Specialist Intelligence

See [Orchestra v1.3.0](https://github.com/Baelfyre/Orchestra/releases/tag/v1.3.0) and the [historical detailed changelog](docs/history/CHANGELOG_PRE_V1_7.md).

## v1.2.0 - Governed Orchestration

Published August 9, 2026.

See [Orchestra v1.2.0](https://github.com/Baelfyre/Orchestra/releases/tag/v1.2.0) and the [historical detailed changelog](docs/history/CHANGELOG_PRE_V1_7.md).

## v1.1.2 - Trusted Runtime Authority

See the [historical detailed changelog](docs/history/CHANGELOG_PRE_V1_7.md) and release history for the complete record.

## v1.1.1 - Post-Release Hardening

See [the historical detailed changelog](docs/history/CHANGELOG_PRE_V1_7.md).

## v1.1.0 - Specialist Governance & Boundary Standard

See [the historical detailed changelog](docs/history/CHANGELOG_PRE_V1_7.md).

## v1.0.0 - Portable Runtime

See [Orchestra v1.0.0](https://github.com/Baelfyre/Orchestra/releases/tag/v1.0.0) and the [historical detailed changelog](docs/history/CHANGELOG_PRE_V1_7.md).

## Earlier repository history

Pre-v1.0 implementation detail and all detailed candidate chronology remain available in the [historical detailed changelog](docs/history/CHANGELOG_PRE_V1_7.md), Git history, `DECISION_LOG.md`, `PROJECT_STATE.md`, validation records, and merged pull requests.
