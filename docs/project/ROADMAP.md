# Roadmap

## Spec Kitty-Derived Orchestra Contracts

Design Status: `DESIGN_COMPLETE`
Runtime Status: `IMPLEMENTED_MERGED` | `NOT_RELEASED`

- [x] Phase 1A: Architecture Ownership and Contract Placement (`docs/project/SPEC_KITTY_DERIVED_CONTRACT_OWNERSHIP.md`).
- [x] Phase 1B: `OrchestraRuntimeEnvelope` Schema Specification (`docs/project/ORCHESTRA_RUNTIME_ENVELOPE.md`).
- [x] Phase 1C: `OrchestraCorrelationID` Format Evaluation and Protocol Specification (`docs/governance/CORRELATION_ID_PROTOCOL.md`).
- [x] Phase 1D: `OrchestraPhaseRetrospective` Protocol Specification (`docs/governance/PHASE_RETROSPECTIVE_PROTOCOL.md`).
- [x] Phase 1E: `OrchestraUnitRecord` Schema Extension Specification (`docs/project/ORCHESTRA_UNIT_RECORD_EXTENSION.md`).
- [x] Phase 1F: Cross-Document Synchronization and Final Design Roadmap (`docs/project/SPEC_KITTY_DERIVED_UPGRADE_ROADMAP.md`).
- [x] Phase 2A: Implementation baseline, compatibility matrix, migration plan, and test plan definition.
- [x] Phase 2B: `OrchestraRuntimeEnvelope` runtime model, serializer, parser, and adapter compatibility tests.
- [x] Phase 2C: UUIDv7 generator implementation, validation, and child propagation complete (cross-session restoration and durable persistence deferred).
- [x] Phase 2D: Phase retrospective model and deterministic builder complete (automatic closeout generation and durable retention deferred).
- [x] Phase 2E: `ApprovedUnitPlan` extension integration, schema validation, and contextual validator complete (automatic Steward integration, revision-history ordering, and policy amendment deferred).
- [x] Phase 2F: Consolidated behavior, governance, security, packaging, documentation, and backward-compatibility validation.
- [x] Phase 2G: Maintainer implementation review, commit authorization, post-commit validation, push authorization, remote verification, and PR #208 merge (`1e2992b94abe67a76c1e6ec0b98f8b712ae256e4`).

### Completed Phase 3 Sequence

- [x] Phase 3A: Read-only deferred-capability selection, ownership, compatibility, security, and implementation planning for `OrchestraWorktreeContract` and `OrchestraStatusProjection` (`docs/project/SPEC_KITTY_DERIVED_PHASE_3_CAPABILITY_ASSESSMENT.md`). Design accepted and merged through PR #210 (`1629eaf3cd3f156f8913f84c9229666257a3145a`).
- [x] Phase 3B: `OrchestraStatusProjection` model, JSON serializer, CLI renderer, and unit tests. Implemented and merged through PR #212 (reviewed head `2a6c7ea8db16ce73d66fae566672f3681094b0f7`, merge commit `fa1e052d82301e70a5869258c3fc6af765163353`).
- [x] Phase 3C: `OrchestraWorktreeContract` model, path confinement validator, base SHA checker, host capability integration, and unit tests. Implemented and merged through PR #214 (reviewed head `646111325e6de7c5d31915789fdc22a644125b7b`, merge commit `6bce297c7469f9c08ce41308cbb993cc863ac540`).
- [x] Phase 3D: Consolidated cross-platform, behavior, governance, security, packaging, compatibility, and exact-head validation completed for the final PR #214 revision.
- [x] Phase 3E: Maintainer immutable review, bounded remediation, commit and push authorization, remote verification, and PR #214 merge completed on August 6, 2026.

Phase 3A through Phase 3E are complete and merged. The Spec Kitty-derived capability set remains unreleased and no policy activation has occurred.

## Authority and Capability Runtime Progression

- [x] Phase 6A-A: audit current runtime gaps and define trust boundaries.
- [x] Phase 6A-B: define typed authority, runtime capability, delegation, lifecycle, audit, interface, and error contracts.
- [x] Phase 6A-C: sequence implementation ownership and verification requirements.
- [x] Phase 6B-A: add immutable core domain models, typed errors, interfaces, serialization where needed, and focused unit tests.
- [x] Phase 6B-B: add trusted root authority loading plus authority and capability enforcement.
- [x] Phase 6B-C: add bounded delegation, context minimization, and lifecycle control.
- [x] Phase 6B-D: integrate the contracts with `RuntimeExecutor`, adapters, governance separation, and auditing.
- [x] Phase 6C: run adversarial authority, capability, delegation, lifecycle, and fail-closed validation.
- [x] Phase 6D: finalize promotion lifecycle, Catalog synchronization, release readiness, and target patch preparation after implementation completes.

Phases 6B-A through 6C are complete and merged through PR #183. Phase 6D produced the published `v1.1.2` baseline after PR #185 and the separate publication gate.

## v1.2.0 Finalization

- [x] F0/R0: preserve and verify the recovery baseline after the first autonomous-run incident.
- [x] F1/R1: Spec Kitty Phase 3 and roadmap closeout through replay PR #223.
- [x] F2/R2: backend-to-persistence and cross-module logical-flow integrity through replay PR #224.
- [x] F3/R3 repository contract: delegated host-reliability protocol and deterministic repository evidence through replay PR #225.
- [x] F3/R7 live host evidence: installed Codex/Antigravity continuity and applicable cross-host verification are `VERIFIED / RECONCILED LOCALLY` in the source-controlled R7 evidence record; the repository fixture remains simulated and pending/empty by design.
- [x] F4/R4: delegated Phase D overlap reconciliation through PR #226 with `NO_DUPLICATE_RUNTIME_EXTENSION_REQUIRED` for v1.2.0.
- [x] R5: autonomous merge-readiness hardening through PR #227.
- [x] R5B: delegated-governance current-state reconciliation through PR #228.
- [x] R6 repository preparation: version surfaces, public current-state documentation, compatibility/install boundaries, changelog consolidation, and `v1.2.0` release-candidate notes prepared as `PREPARED_NOT_RELEASED`.
- [x] R7: reconcile live installed-host evidence locally; maintainer review, repository reconciliation merge, and independent post-merge verification remain pending.
- [ ] R8: create annotated `v1.2.0` tag and GitHub Release only from independently verified release state.

## Deferred and Future Work

- [ ] Add host-specific update commands after the shared notification-only update check stabilizes.
- [ ] Add host-specific update commands on top of the reproducible temp-staged runtime refresh pipeline.
- [ ] Publish an Adapter SDK with base classes, helper utilities, templates, and a reference implementation.
- [ ] Publish a contributor guide covering adapter construction, testing requirements, packaging conventions, and governance expectations.
- [ ] Add a `PRAP v1 Compatible` certification path with a validation checklist and compliance requirements.
- [ ] Publish a developer portal for adapter docs, skill authoring guidance, governance guidance, and runtime API reference.
- [ ] Package for a future supported skill marketplace.
- [ ] Expand the runtime core beyond validation and adapter contracts into more host-native execution paths.
- [ ] Publish a formal Adapter SDK and contributor guide on top of `PRAP v1`.
- [ ] Add semantic versioning policy, certification checklist, and a `PRAP v1 Compatible` badge for external adapters.
- [ ] Promote Cursor, Windsurf, and VS Code packaging scaffolds into publishable marketplace or extension distributions.
- [ ] Promote the shared VS Code-family path to cover VSCodium publication when that ecosystem path is worth supporting.
- [ ] Promote the JetBrains scaffold into an IntelliJ Platform build and distribution flow separately from the generic editor packaging branch.
- [ ] Promote Zed and Neovim scaffolds into host-native distribution or plugin flows after the editor packaging scaffolds stabilize.
- [ ] Use `docs/governance/PROJECT_CONTEXT_DECISION_PROMPT.md` before proposing any hard enforcement path for `PROJECT_CONTEXT.md`.
- [ ] Use `docs/governance/PROJECT_CONTEXT_ENFORCEMENT_POLICY.md` before making `PROJECT_CONTEXT.md` blocking for any repository class.
- [ ] Use optional project governance ruleset defaults before treating `PROJECT_CONTEXT.md` as universally strict across prototypes, school repos, sandboxes, or learning projects.
- [ ] Apply `docs/project/SCAFFOLD_ADAPTER_GRADUATION_CRITERIA.md` before promoting any scaffold-only adapter support level.
- [ ] Add an optional cross-platform CLI validator.
- [ ] Add an optional local-model retrieval index.
- [ ] Improve adapters as tool capabilities change.
- [ ] Expand fictional, project-agnostic examples.
- [ ] Publish `v1.2.0` only after R7 host-derived evidence, exact-head release verification, and the separate R8 publication gate are completed.
