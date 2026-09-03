# Changelog

## Post-v1.7 OR-GOV-4 Chronicler migration risk contract candidate

- Formalizes Chronicler's existing migration, locking, dialect, transaction, backfill, and zero-downtime knowledge as deterministic `MigrationRiskContract` guidance.
- Distinguishes development-only changes from production compatibility, preserves unknown production facts, and covers expand-contract, batched backfill, conditional dual read/write, engine-specific online DDL, index and constraint operations, rollback boundaries, failure recovery, observability, completion criteria, risk, and proportional human gates.
- Preserves the canonical v1 schema without converting unknown production presence to `false`; the explicit `MIGRATION_RISK_SCHEMA_GAP: UNKNOWN_PRODUCTION_STATE_NOT_REPRESENTABLE` disposition remains visible until a separately governed schema amendment exists.
- Routes accepted implementation to Ponytail and validation to Overseer while preserving Steward, Clockwork, Cipher, Conductor, and Chronicler ownership boundaries. Adds source/Codex parity and deterministic OR-GOV-4 behavior coverage.
- Does not execute migrations or production SQL, implement OR-GOV-5, start AR-3, change provider or policy behavior, deploy, release, or authorize v1.8 publication.

## Post-v1.7 OR-GOV-3 Clockwork architecture complexity and scale posture candidate

- Upgrades Clockwork (`skills/clockwork/SKILL.md`, `OUTPUT_FORMATS.md`, and dedicated `ARCHITECTURE_COMPLEXITY_AND_SCALE_POSTURE_GUIDE.md`) with architecture complexity decisions, scale-ready versus scale-provisioned posture formalization, simpler-alternative justification, and the future-scalability invariant.
- Enforces the primary invariant `FUTURE_SCALABILITY_ALONE_IS_NOT_SUFFICIENT_JUSTIFICATION`, preventing vague future-scale claims from causing premature infrastructure expansion while rejecting unsupported complexity, not growth itself.
- Formalizes `SCALE_READY` (preserving proportionate evolution paths without pre-provisioning unnecessary scale infrastructure) and `SCALE_PROVISIONED` (actively provisioning physical infrastructure based on verified capacity, performance, or isolation requirements), defaulting to `SCALE_READY` when both satisfy current accepted requirements.
- Implements mandatory simpler-alternative analysis for material complexity additions, canonical justification categorization, and decision states (`ACCEPT`, `ACCEPT_WITH_CONSTRAINTS`, `DEFER`, `REJECT`).
- Consumes upstream `ProductIntentContract` and `CapacityEnvelope` from The Steward, preserving `UNKNOWN IS VALID`, ranges without averaging, partial capacity tolerance, and cost constraints as binding architecture inputs.
- Adds Codex mirror parity (`adapters/codex/skills/clockwork/`), behavioral regression tests (`tests/behavior/test_clockwork_architecture_complexity.py`), route/registry metadata updates, and machine discovery in `README.json`.
- Does not implement Chronicler migration risk (OR-GOV-4), does not start AR-3, and does not authorize v1.8 publication.

## Post-v1.7 OR-GOV-2 The Steward product intent and capacity envelope candidate

- Upgrades The Steward (`skills/the-steward/SKILL.md`, `OUTPUT_FORMATS.md`, and dedicated `PRODUCT_INTENT_AND_CAPACITY_ENVELOPE_GUIDE.md`) with product intent governance, capacity envelope review, adaptive elicitation, and project-stage awareness.
- Decouples underlying problem statements from requested implementation mechanisms, establishing proportional challenge tiers across trivial, standard, architectural/material, and strategic scopes.
- Implements capacity envelope reasoning where unmeasured metrics are treated as valid (`UNKNOWN IS VALID`), preserving exact values and ranges without fabricated numeric precision.
- Enforces adaptive capacity elicitation using domain-sensitive prompting, avoiding universal questionnaires and redundant re-prompting for known evidence.
- Preserves specialist authority boundaries: The Steward governs business and workload assumptions, emitting upstream contracts to Clockwork, while strictly avoiding infrastructure selection or architecture implementation.
- Adds Codex mirror parity (`adapters/codex/skills/the-steward/`), behavioral regression tests (`tests/behavior/test_steward_product_intent_and_capacity.py`), and machine discovery in `README.json`.
- Does not implement Clockwork complexity engine (OR-GOV-3), does not start AR-3, and does not authorize v1.8 publication.

## Post-v1.7 OR-GOV-1 shared machine contracts and schemas candidate

- Establishes seven shared machine-readable governance contract schemas (`CapacityEnvelope`, `ProductIntentContract`, `ArchitectureComplexityDecision`, `MigrationRiskContract`, `ArchitectureGovernanceIntake`, `ArchitectureValidationContract`, and `ProjectArchitectureGovernanceProfile`) under `machine/schemas/`.
- Supports adaptive capacity value states including `EXACT`, `RANGE`, `OBSERVED`, `ESTIMATED`, `UNKNOWN`, `TO_BE_MEASURED`, and `NOT_APPLICABLE`, treating unmeasured metrics as valid rather than automatic validation failures.
- Decouples product problem statements and evidence from requested solutions in `ProductIntentContract`.
- Enforces architecture complexity justification, simpler-alternative review, scale postures (`SCALE_READY`, `SCALE_PROVISIONED`), and the invariant `FUTURE_SCALABILITY_ALONE_IS_NOT_SUFFICIENT_JUSTIFICATION`.
- Provides an engine-agnostic database migration risk contract supporting locking, compatibility, backfill, patterns (`DIRECT`, `EXPAND_CONTRACT`, `BATCHED_BACKFILL`, `DUAL_READ_WRITE`, `ONLINE_DDL`, `ENGINE_SPECIFIC`, `OTHER`), and unmeasured production telemetry.
- Establishes Conductor intake classifier surfaces and Overseer distinct validation states (`PROVEN`, `NOT_PROVEN`, `NOT_REQUIRED`, `FAILED`).
- Adds focused schema and invariant tests in `tests/runtime/test_or_gov_contracts.py` (40 passed tests) and records machine discovery in `README.json`.
- Does not implement later specialist behavior (OR-GOV-2 through OR-GOV-10), does not start AR-3, alters no runtime architecture, and does not authorize v1.8 publication.

## Post-v1.7 Scribe specialist upgrade candidate

- Expands Scribe into a Documentation, Domain Narrative, and Knowledge Traceability Specialist with `SPEC_TO_SYSTEM`, `SYSTEM_TO_DOCS`, and `RECONCILE` modes, domain narrative, bidirectional traceability, adaptive research/capstone guidance, and as-built/reconciliation templates.
- Preserves specialist authority boundaries, surfaces unsupported claims and missing evidence, and keeps external standards, institutional materials, code, data, figures, and templates subject to provenance and rights review through Conductor and The Governor.
- Updates Scribe source/Codex parity, registry/routing metadata, progressive-disclosure guides, deterministic route fixtures, and documentation indexes.
- Records exact-current prompt-load baselines for the affected routing and governance packages without changing their revision or maximum percentage thresholds.
- Keeps AR-3 unstarted, makes no provider or policy change, grants no release or deployment authority, and does not publish v1.8.

## Post-v1.7 runtime architecture AR-2 residual domain extraction closeout candidate

- Moves qualified pure-domain semantics for capability manifests, governance decision/result contracts, pre-execution intent and policy, and workflow sanity receipts into bounded inward domain packages.
- Preserves exact legacy compatibility surfaces and public object identity while leaving machine-policy evaluation, application/use-case coordination, host gates, routing/builders, DTOs, persistence, audit projection, provider, and MCP responsibilities for their later AR-3/AR-4 phases.
- Adds targeted domain, compatibility, fail-closed, and import-boundary tests plus the residual AR-2 closeout documentation and machine-index parity.
- Keeps AR-3 unstarted, makes no provider/MCP behavior change, retires no public imports, and grants no release, deployment, or policy authority.

## Post-v1.7 runtime architecture AR-2 execution lifecycle core extraction candidate

- Establishes `orchestra_runtime.domain.execution.lifecycle` as the inward-only owner of immutable lifecycle state, signal, snapshot, terminal-result, deterministic fingerprint, initialization, and transition semantics.
- Preserves exact legacy `orchestra_runtime.lifecycle` and top-level lifecycle symbol identity while retaining `LifecycleController(ILifecycleController)` plus runtime audit-event projection on the transitional legacy surface for later AR-3/AR-4 placement.
- Adds direct compatibility, transition/replay, fail-closed, controller-delegation, import-boundary regression coverage, detailed extraction documentation, and `README.json` machine-discovery parity.
- Does not alter provider/MCP behavior, runtime policy, audit-event semantics, public import compatibility, release/deployment/policy authority, or start AR-3.

## Post-v1.7 Cloak CUIR lifecycle projection reconciliation candidate

- Reconciles the current `README.json` machine projection with the verified canonical CUIR-5 controlled evaluation and CUIR-6 `ADOPT_OPTIONAL` closeout.
- Records the verified CUIR-5 commit/tree `0736517fc59f3979ec76d642bc2d8ed5c7b858b1` / `b0e5d89db6f3c9642465704ecc1ace8c3b905291` and CUIR-6 commit/tree `2f11f17742e68560d2a435bcab3f247b52d351ab` / `0f114c13d8f5f54ee5ecf1e9deb156ae6fe6e24b` while preserving phase-era candidate artifacts as historical evidence.
- Adds regression coverage ensuring the optional closeout does not become runtime expansion, mandatory full-corpus injection, automatic host injection, or new authority.
- Does not change Cloak runtime behavior, retrieval limits, provenance or licensing rules, AR state, release/deployment/provider/policy authority, or delete branches.

## Post-v1.7 runtime architecture AR-2 execution identity extraction candidate

- Establishes `orchestra_runtime.domain.execution.identity` as the inward-only owner of immutable `RunIdentity` normalization and serialization semantics.
- Preserves exact legacy `orchestra_runtime.models.RunIdentity` and top-level `orchestra_runtime.RunIdentity` object identity while routing correlation validation through the canonical execution-domain correlation contract.
- Adds direct compatibility, invariant, import-boundary regression coverage, detailed extraction documentation, and `README.json` machine-discovery parity.
- Does not move lifecycle controllers/state, audit events, execution results, capability manifests, delegation/services behavior, start AR-3/AR-4, retire public imports, or change release/deployment/policy authority.

## Post-v1.7 runtime architecture AR-2 execution correlation extraction candidate

- Establishes `orchestra_runtime.domain.execution.correlation` as the inward-only owner of deterministic RFC 9562 UUIDv7 validation while keeping clock and entropy backed correlation generation outside the domain.
- Preserves legacy `orchestra_runtime.correlation` validation symbol identity and deliberately retains `generate_correlation_id`, `_generate_correlation_id`, `time.time_ns`, `secrets.token_bytes`, and UUIDv7 construction on the transitional legacy surface.
- Adds direct compatibility and import-boundary coverage, detailed extraction documentation, and `README.json` machine-discovery parity for the execution-correlation surface.
- Does not move `RunIdentity`, lifecycle state/controllers, audit events, or execution results; start AR-3/AR-4; alter provider/MCP behavior; retire public imports; or change release/deployment/policy authority.

## Post-v1.7 runtime architecture AR-2 capability core extraction candidate

- Establishes `orchestra_runtime.domain.capabilities` as the inward-only owner of capability value objects, deterministic decision/enforcement semantics, and restrictive grant intersection.
- Preserves legacy `orchestra_runtime.capabilities` symbol identity while deliberately retaining run-bound manifests, `RunIdentity` construction, application-port inheritance, filesystem policy loading, and runtime audit-event projection on the transitional legacy surface.
- Adds direct compatibility, fail-closed evaluation/intersection, import-boundary regression coverage, detailed extraction documentation, and `README.json` machine-discovery parity.
- Does not move correlation generation/validation, start AR-3/AR-4, alter provider/MCP behavior, retire public imports, or change release/deployment/policy authority.

## Post-v1.7 runtime architecture AR-2 governance authority extraction candidate

- Establishes `orchestra_runtime.domain.governance.authority` as the inward-only owner of immutable authority entities and deterministic constraint/intersection semantics.
- Preserves legacy `orchestra_runtime.authority` symbol identity while retaining repository-policy filesystem loading, application-port inheritance, and runtime audit-event projection on the transitional legacy surface for later AR-3/AR-4 placement.
- Adds direct compatibility/import-boundary regression coverage, detailed extraction documentation, and `README.json` machine-discovery parity.
- Does not alter authority scope/evaluation behavior, provider/MCP execution, public import retirement, release/deployment/policy authority, or start AR-3.

## Post-v1.7 runtime architecture AR-2 domain context extraction candidate

- Establishes `orchestra_runtime.domain.context` as the inward-only owner of `CurrentProjectState`, `ContinuityEvent`, and deterministic `compile_context` semantics.
- Preserves legacy `orchestra_runtime.context_state` imports by re-exposing the same canonical domain symbols while deliberately retaining JSONL filesystem persistence and Markdown projection on the legacy surface for later infrastructure/presentation extraction.
- Adds direct compatibility and domain-context regression coverage plus detailed extraction documentation and `README.json` machine-discovery parity.
- Does not move communication-budget presentation dependencies, clock/entropy-backed correlation generation, provider/MCP behavior, public entrypoints, release/deployment authority, or start AR-3.

## Post-v1.7 Padayon post-restructure realignment searchability

- Adds a repository-local, searchable governance notice for the Padayon M0-M6 post-restructure source-reality reconciliation procedure and links it from the governance documentation index.
- Preserves live Orchestra source precedence, current Padayon routing, explicit drift classifications, and the verified AR-2 checkpoint as evidence only; this documentation change grants no new implementation, release, deployment, policy, provider-routing, destructive, or history-rewrite authority.

## Post-v1.7 runtime architecture AR-2 shared canonicalization extraction candidate

- Moves deterministic Git/SHA normalization, timezone normalization, canonical JSON bytes, and receipt digest ownership into the inward-only `orchestra_runtime.shared.canonicalization` surface.
- Keeps `orchestra_runtime.evidence` API-compatible by importing and re-exposing the same primitive function objects while retaining evidence-specific receipt construction in the legacy module.
- Adds equivalence and edge-case coverage for legacy exports, canonical bytes/digests, timestamps, and existing receipt constructors, and records the shared primitive surface in the machine repository index.
- Does not move context entities, persistence, application use cases, provider/MCP behavior, public entrypoints, or release/deployment authority; `domain/context` remains a later bounded AR-2 increment.

## Post-v1.7 runtime architecture AR-2 machine placement enforcement candidate

- Promotes runtime placement rules into the versioned `machine/governance/runtime-architecture-boundaries.v1.json` contract with a strict Draft 2020-12 schema and reusable standalone validator.
- Enforces new-flat-module, unknown-package-root, dependency-direction, DTO/DPO, repository-zone, compatibility-facade, repository-`internal/`, and direct domain-I/O boundaries while grandfathering only explicitly recorded migration debt.
- Wires the same validator into Governance Check and the main validate workflow, keeps pytest architecture regression coverage, and adds an agent-facing placement rule so future files must identify their bounded owner before implementation.
- Standardizes the external runtime layer name as `entrypoints/` to avoid collision with legacy `orchestra_runtime/interfaces.py`, which remains migration debt until its application-port extraction. No runtime behavior, public-import retirement, release, deployment, policy activation, provider routing/fallback, destructive action, branch deletion, force push, or history rewrite is introduced.

## Post-v1.7 runtime architecture refoundation AR-2 foundation candidate

- Creates the canonical `domain`, `application`, `infrastructure`, `bootstrap`, `shared`, and runtime-resource package boundaries plus application use-case/service/DTO/port and persistence repository/DPO/mapper/store/serialization destinations.
- Moves runtime contract error implementations to `orchestra_runtime.shared.errors` while retaining `orchestra_runtime.errors` as an identity-preserving compatibility facade for existing imports.
- Extends architecture validation so the package skeleton and compatibility facade are executable invariants; new flat runtime Python modules remain prohibited and production runtime imports from repository `internal/` remain prohibited.
- Records AR-2 in the machine repository index and architecture documentation. No runtime behavior, provider/MCP behavior, persistence semantics, public import retirement, release, deployment, policy activation, branch deletion, force push, or history rewrite is introduced.

## Post-v1.7 runtime architecture refoundation AR-0/AR-1 candidate

- Adds the validation-first Orchestra runtime architecture refoundation plan, defining bounded contexts and explicit domain, application, infrastructure, interface, composition, persistence, DTO/DPO, resource, and repository-zone ownership.
- Adds migration-aware architecture validation that freezes the current flat `orchestra_runtime` module inventory as legacy debt and rejects newly introduced flat runtime Python modules while later bounded packages are migrated incrementally.
- Adds dependency-direction checks for migrated `domain`, `application`, `infrastructure`, and `interfaces` packages, prohibits production runtime imports from repository `internal/`, and validates DTO/DPO placement intent.
- AR-0/AR-1 changes no runtime behavior or public imports. Runtime package creation and source movement begin only in separately qualified AR-2 work, with required `README.json` machine-index parity preserved in the same migration change.

## Post-v1.7 Cloak CUIR-5 controlled evaluation candidate

- Adds a deterministic representative benchmark and evaluator comparing a no-CUIR-retrieval baseline with bounded CUIR-4 progressive retrieval.
- Measures retrieval recall, provenance completeness, bounded context, authority-boundary preservation, and source-copying violation signals only; it does not claim end-to-end LLM output quality, rendered correctness, human usability preference, or production effectiveness.
- Adds regression coverage for the controlled evaluation and records the active CUIR-5 machine-discovery surfaces in `README.json`.
- A passing result may recommend only `ADOPT_OPTIONAL` for CUIR-6 consideration and grants no implementation, architecture, security, merge, release, deployment, provider-routing/fallback, production-mutation, policy, destructive, or installed-integration-refresh authority.

## Post-v1.7 Cloak CUIR-4 canonical lifecycle closeout

- Reconciles machine discovery with the verified canonical CUIR-4 integration at `67dc4a70159346cea903761373412829f7677fcf`.
- Marks CUIR-4 as `CUIR_4_CANONICAL_MERGED_VERIFIED` while preserving bounded progressive retrieval, project-native precedence, provenance/reuse classifications, and the frozen UIX-9 core guidance.
- Keeps `cuir5_started=false`; CUIR-4 canonicalization does not itself authorize CUIR-5 evaluation or any provider, release, deployment, production, policy, destructive, force-push, or history-rewrite action.

## Post-v1.7 Cloak CUIR-4 pattern intelligence integration candidate

- Integrates the canonical 16-pattern CUIR-3 catalog into Cloak through progressive disclosure instead of default full-corpus prompt injection.
- Adds a deterministic problem-class/category retrieval contract and reproducible helper capped at five normalized patterns per task.
- Preserves project-native requirements first, exact provenance, accessibility constraints, and `REFERENCE_ONLY` / `REUSE_WITH_NOTICE` / `REUSE_WITH_RIGHTS_REVIEW` distinctions.
- Adds source/Codex Cloak guide parity and deterministic runtime validation for category reachability, bounded retrieval, representative task relevance, icon-rights separation, and closed CUIR-5 authority.
- Performs no new external repository inspection, external dependency installation, source/asset copying, provider routing, release, deployment, production mutation, or policy activation.

## Post-v1.7 Cloak CUIR-3 Orchestra-native normalization candidate

- Normalized the canonical 23-record CUIR-2 static-analysis corpus into 16 evidence-bound Orchestra-native UI/reference patterns covering navigation, forms and input, selection and disclosure, status and progress, action hierarchy, data and summaries, content grouping, collections, accessibility, motion, and icon semantics.
- Added a strict normalized-pattern schema, machine knowledge catalog, human normalization record, and deterministic CUIR-3 runtime validation with complete CUIR-2 provenance accounting and no unknown or silently dropped analysis records.
- Preserved `REFERENCE_ONLY`, `REUSE_WITH_NOTICE`, and `REUSE_WITH_RIGHTS_REVIEW` classifications; kept general UI icon notice obligations separate from brand-icon rights review; rejected observed accessibility regressions instead of normalizing them.
- CUIR-3 performs no new external source inspection or revision refresh, source or asset copying, external execution, dependency installation, automatic ingestion, runtime integration, automatic pattern retrieval, provider routing or fallback, release, deployment, production mutation, or policy activation. CUIR-4 remains not started.

## Post-v1.7 Cloak CUIR-2 static pattern analysis candidate

- Added bounded static concept-level analysis across all 23 canonical CUIR-1 retained source records: 20 Nazia-99 UI references plus the three pinned Simple Icons, Tabler Icons, and Lucide icon sources.
- Recorded three bounded machine analysis batches covering concept-level UI, information-hierarchy, interaction-state, accessibility, and icon-suitability findings, with inherited provenance and reuse classifications preserved.
- Added the strict analysis schema and deterministic CUIR-2 runtime validation for source binding, batch coverage, schema conformance, and closed authority boundaries.
- CUIR-2 performs no source or asset copying, external project build, dependency installation, external execution, automatic ingestion, runtime integration, provider routing or fallback, release, deployment, production mutation, or policy activation. CUIR-3 remains not started.
## Post-v1.7 Cloak CUIR-1 corpus inventory and provenance candidate

- Added the dated CUIR-1 live-source inventory for the `Nazia-99` account, recording 144 unique public repository identities from the 2026-08-31 discovery snapshot, explicit per-repository screening dispositions, 20 retained distinct UI references, and 124 discovered sources not promoted into the retained corpus.
- Added 23 exact-revision provenance records: 20 retained `Nazia-99` UI references conservatively classified `AMBIGUOUS` and `REFERENCE_ONLY`, plus pinned Simple Icons, Tabler Icons, and Lucide icon-source records with their applicable CC0-1.0 rights-review, MIT notice, ISC notice, and Feather-derived MIT subset distinctions preserved.
- Added deterministic CUIR-1 runtime validation for snapshot identity, disposition counts, source-record schema conformance, attribution/non-copying boundaries, exact icon pins, and closed external-execution/provider-routing boundaries.
- CUIR-1 performs no external build, dependency installation, external application/script execution, repository mirroring, automatic ingestion, source/asset copying from the reference-only Nazia records, provider routing/fallback activation, or CUIR-2 pattern extraction.

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
