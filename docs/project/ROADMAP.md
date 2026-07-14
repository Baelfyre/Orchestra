# Roadmap

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

Phases 6B-A through 6C are complete and merged through PR #183. Phase 6D is complete locally under Issue #184 after promotion, Catalog, documentation, version, two-pass validation, and exact-scope gates. The prepared branch still requires maintainer review, merge, and separate publication authorization.

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
- [ ] Publish the `v1.1.2` tag and GitHub Release only after the Phase 6D branch merges and a separate publication gate is authorized.
