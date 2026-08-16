<div align="center">
  <img src="./assets/readme/orchestra-governance-banner.svg" alt="Orchestra banner showing coordinated software responsibilities" width="100%" />

  <p><strong>A portable orchestration runtime for structured AI-assisted development.</strong></p>

  <p>
    <a href="docs/setup/INSTALLATION.md">Installation</a> |
    <a href="docs/project/AUTHORITY_CAPABILITY_RUNTIME_ARCHITECTURE.md">Architecture</a> |
    <a href="docs/governance/GOVERNANCE_LAYER.md">Governance</a> |
    <a href="docs/setup/VALIDATION.md">Validation</a> |
    <a href="CHANGELOG.md">Changelog</a>
  </p>
  <p>
    <img src="https://img.shields.io/badge/package_version-v1.4.0-blue" alt="Repository package version v1.4.0" />
    <a href="https://github.com/Baelfyre/Orchestra/actions/workflows/validate.yml">
      <img src="https://github.com/Baelfyre/Orchestra/actions/workflows/validate.yml/badge.svg" alt="Repository validation status" />
    </a>
    <img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT license" />
  </p>
</div>

---

## AI can generate fast. Building well still requires structure.

AI-assisted projects rarely fail because a model cannot produce another answer. They fail when context drifts, architecture and implementation blur together, specialist assumptions conflict, unchecked output becomes the next input, evidence goes stale, decisions arrive out of order, and tool access is mistaken for permission.

Orchestra turns those scattered interactions into one coordinated workflow. It gives each responsibility a defined owner, controls when work may move forward, sends invalidated work back to the correct boundary, and preserves reviewable state across long-running tasks.

## What Orchestra Is

Orchestra is a structured, governance-driven framework for coordinating AI-assisted software work across specialist responsibilities, tools, validation stages, and human approval points.

It is not an AI model and does not replace one. The model generates or reviews work. Orchestra is the coordination layer that routes, sequences, constrains, coordinates, validates, records, and connects that work to the next responsible boundary.

The framework is designed to help developers reduce context drift, make cross-domain dependencies explicit, keep permission separate from routing and governance, and produce evidence that can be reviewed instead of inferred from generated text.

> **Core trust boundary:** governance approval, coordination readiness, validation success, and GitHub mergeability are state or evidence signals. None of them grants or expands authority.

> **Terminology:** Orchestra uses **Downstream Roles** for specialists or adapters that receive governed outputs from another canonical owner. The word **consumer** is reserved for genuine technical provider/consumer or message-consumer semantics.

## Why the Compliance Registry Matters

Compliance decisions are especially vulnerable to stale context. Laws, platform policies, licensing terms, privacy obligations, provider requirements, and effective dates can change independently of application code. If those facts are copied into prompts or project documents without provenance and freshness metadata, a previously correct assumption can quietly become the next project's bad input.

The **Orchestra Compliance Registry** is designed to prevent that failure mode. It gives Governor, Steward, and Arbiter a reusable, versioned compliance-intelligence layer whose source identity, release identity, file integrity, freshness state, and project pinning can be checked independently of the project being reviewed.

The important part is the **cross-integration**. The Registry is not a sidecar knowledge dump and it is not a new authority layer. It provides one verifiable compliance substrate that Orchestra can carry across projects and specialist handoffs while each responsibility keeps its existing owner:

- **The Governor** consumes source identity, applicability, jurisdiction/provider scope, effective dates, and freshness evidence for compliance review.
- **The Steward** maps current, Governor-qualified obligations into requirements, FR/NFR traceability, acceptance criteria, and change-control impact without becoming the legal/compliance authority.
- **Arbiter** carries the exact pinned Registry version and freshness state into continuity, evidence-freshness, transition, and release-readiness decisions so stale compliance evidence cannot silently authorize a later transition.
- **Conductor and The Tuner** can route and coordinate work that depends on those specialist-owned contracts, but Registry facts never become routing authority, execution permission, or a substitute for specialist decisions.
- **Downstream projects** can reuse the same verified compliance knowledge instead of copying conclusions into each repository, while the downstream project's own tracker and repository remain authoritative for project state and implementation evidence.

That separation is important because it lets Orchestra:

- reuse source-backed compliance knowledge across projects without duplicating legal or policy conclusions into every repository;
- distinguish **content integrity** from **distribution provenance**, so a self-consistent local bundle is not automatically treated as trusted;
- detect stale, unavailable, moved, overdue, or review-required sources instead of silently treating old evidence as current;
- pin a project to the exact registry version, release sequence, release tag, manifest SHA-256, jurisdictions, and providers used for a governed decision;
- keep compliance knowledge separate from execution authority: registry records can inform requirements and review, but they cannot authorize release, deployment, policy activation, destructive operations, or other protected actions.

Normal use is local-first: Orchestra reviews a verified active cache and uses network access only for synchronization, update checks, or authoritative-source verification when currentness cannot be established locally. A trusted network sync must come from the canonical registry's immutable GitHub Release boundary; local or air-gapped installation requires a separately verified release-manifest SHA-256 trust anchor.

See [Compliance Registry Integration](docs/governance/COMPLIANCE_REGISTRY_INTEGRATION.md) for the trust model, owner responsibilities, freshness behavior, and release boundaries.

## How Orchestra Works

Each run begins with project context and three separate choices: risk mode, progression mode, and governance profile. Those choices affect review depth and pause frequency, but they do not create permission. Orchestra composes the trusted runtime, calculates effective authority as the intersection of explicit grants and all applicable constraints, and only then lets Conductor route work. Material multi-domain work uses The Tuner to coordinate specialist-owned contracts; single-owner work bypasses that overhead.

~~~mermaid
flowchart TD
    Request["Request + Project Context"]
    Select["Select Risk Mode + Progression Mode + Governance Profile"]
    Compose["Trusted Runtime Composition"]
    Effective{"Effective Authority Intersection Allows Action?"}
    Route["Conductor Routes Smallest Responsible Stack"]
    Multi{"Material Multi-Domain Work?"}
    Tuner{"Tuner Contract Ready and Current?"}
    Specialist["Owning Specialist Execution"]
    Validate{"Current Validation + Evidence Pass?"}
    Revise["Return to Owning Boundary"]
    Arbiter{"Arbiter Transition Disposition"}
    Continue["Bounded Continuation to Next Approved Unit"]
    Remediate["In-Scope Remediation + Revalidation"]
    Wait["Checkpoint and Wait for Evidence or Capacity"]
    Escalate["Escalate Missing Intent, Scope, Policy, or Authority"]
    Stop["Stop and Preserve Safe State"]

    Request --> Select --> Compose --> Effective
    Effective -- No --> Escalate
    Effective -- Yes --> Route --> Multi
    Multi -- No --> Specialist
    Multi -- Yes --> Tuner
    Tuner -- No --> Wait
    Tuner -- Yes --> Specialist
    Specialist --> Validate
    Validate -- No --> Revise --> Specialist
    Validate -- Yes --> Arbiter
    Arbiter -- AUTO_CONTINUE --> Continue --> Route
    Arbiter -- AUTO_REMEDIATE_AND_REVALIDATE --> Remediate --> Specialist
    Arbiter -- WAIT_FOR_EVIDENCE / WAIT_FOR_CAPACITY --> Wait
    Arbiter -- ESCALATE_HUMAN --> Escalate
    Arbiter -- STOP --> Stop
~~~

Accessible summary: a request supplies project context and selects separate risk, progression, and governance-profile settings. Trusted composition and the effective-authority intersection run before Conductor routes work. Single-owner work goes directly to its specialist; material multi-domain work first requires current Tuner coordination. Validation failure returns to the owning boundary. Current evidence goes to Arbiter, which may continue or remediate inside existing authority, wait for evidence or capacity, escalate to a human, or stop safely.

## Control Plane Re-foundation Migration

The cumulative P0/P1 through P9 control-plane re-foundation is canonical through PR #294, with post-merge evidence parity through PR #295. Migration authority progresses only through the explicit sequence `SHADOW -> ADVISORY -> VALIDATION_AUTHORITY -> CANONICAL_PROMOTION_AUTHORITY -> LEGACY_RETIRED`; no stage is inferred from test success or mergeability.

The migration state in this revision is `LEGACY_RETIRED`. The versioned machine specialist registry, routing contract, and governance policy are the runtime's normative sources for specialist identity, command routing and ambiguity fallback, governance-required specialist classification, and governance validation rules. Runtime construction reads those contracts directly instead of consuming independently maintained compatibility tables. The legacy `VALID_SPECIALISTS` import remains available only as an on-demand machine-derived compatibility view. Installed integrations are not mutated by this stage, and release publication remains a separate governed transition.

Merge readiness is also machine-bound rather than inferred from a successful API call. For an ordinary protected Squash merge, the current PR read must report both `mergeable == true` and `mergeable_state == clean`. Missing or unknown mergeability waits for evidence; `blocked`, `behind`, `dirty`, `unstable`, or any other observed non-clean state blocks ordinary progression. A bypass-capable identity and a signed resulting commit do not retroactively convert a failed pre-merge gate into governed readiness. See the [Autonomous Merge Readiness Protocol](docs/governance/AUTONOMOUS_MERGE_READINESS_PROTOCOL.md).

## v1.4.0 Governance and Compliance Registry Cross-Integration

The repository/package version and current public GitHub release are both `v1.4.0`. The immutable, non-draft, non-prerelease release `Orchestra v1.4.0: Governance & Compliance Registry Cross-Integration` is published from exact signed canonical commit `93dd51c0fbe1b10affc58e6fadd5fb0bc2927a50`; tag `v1.4.0` resolves directly to that commit.

v1.4.0 packages the Compliance Registry cross-integration as an Orchestra governance capability: offline-first verified local Registry consumption, explicit integrity/provenance/freshness state, project pinning, progressive-disclosure integration across Governor, Steward, and Arbiter, and preserved routing/authority boundaries.

The Registry foundation, source/freshness pilot, deterministic packaging, and v0.1.0 release-readiness stack are canonical in `Baelfyre/Orchestra-Compliance-Registry`. The trusted `registry-v0.1.0` GitHub Release is published as non-draft, non-prerelease, and immutable at Registry commit `3821bcb55125b4d8864f28b6423650e6e17ac67b`. Orchestra completed real network-provenance validation from canonical source baseline `b5d0790fc714f53c4561a91b158c13c625768e05`, confirming the exact release identity, manifest and bundle hashes, `CURRENT` freshness, source query, project pinning, update-check behavior, and idempotent re-sync. The Orchestra package and current public GitHub release are now both `1.4.0`; publication is `PUBLISHED_VERIFIED` and does not imply marketplace publication or installed-integration refresh.

It also adds a fail-closed **README Impact Gate** to the Governance Check workflow. Changes classified as significant to Orchestra's runtime, specialist skills, host adapters/manifests, governance/routing/setup/release contracts, version surfaces, or CI/governance scripts must update `README.md` in the same revision. Tests and validation-evidence-only changes do not force documentation churn.

This documentation gate complements the existing changelog-freshness gate: significant changes must remain visible both as historical change records and as current public-facing project documentation.

See the [v1.4.0 governance upgrade release candidate](docs/releases/v1.4.0-governance-compliance-registry-release-candidate.md), the preserved [prepublication readiness evidence](docs/validation/V1_4_0_PREPUBLICATION_READINESS_EVIDENCE.md), the [final release-readiness evidence](docs/validation/V1_4_0_RELEASE_READINESS_EVIDENCE.md), and the [v1.4.0 publication closeout](docs/validation/V1_4_0_PUBLICATION_CLOSEOUT.md) for the complete trusted Registry, provenance, release-readiness, and publication evidence chain.

## v1.3.0 Specialist Intelligence

v1.3.0 deepens the knowledge available to Orchestra's existing specialists without broadening their authority or redesigning the routing and runtime architecture by default. The completed SK1 through SK10 campaign adds progressive-disclosure references, worked examples, stronger evidence discipline, selective machine-readable catalogs where deterministic parsing helps, and adversarial evaluation of routing and coordination boundaries.

- **Ponytail:** deeper stack discovery, language/runtime references, build and test tooling, implementation foundations, and worked implementation patterns.
- **Clockwork:** modular and distributed architecture, concurrency ownership, caching, API compatibility/versioning, multi-tenancy, jobs, event-driven flows, outbox/inbox placement, and durable workflow patterns.
- **Cipher:** defensive threat modeling, authentication/session/OAuth/OIDC boundaries, authorization and tenant controls, web/API security, secrets and cryptographic misuse, framework-aware review, and security-tool interpretation.
- **Cloak:** semantic HTML, ARIA, keyboard and focus behavior, responsive CSS containment, forms and validation recovery, design tokens, component states, frontend routing, and component-boundary literacy.
- **Dagger:** safe non-production workload, stress, soak, concurrency, resource-pressure, bounded fault-injection, retry-amplification, recovery-measurement, RTO/RPO, and resilience-tooling guidance while preserving simulation and authorization guardrails.
- **Chronicler:** database dialect and ORM/migration semantics, transaction isolation, MVCC, locking/deadlock analysis, tenant isolation, query-plan evidence, and expand-migrate-contract schema-change planning.
- **Overseer:** unit/integration/contract/E2E strategy, property and mutation testing, flaky-test diagnosis, deterministic isolation, coverage interpretation, CI/browser/device matrices, performance acceptance, and test-data lifecycle management.
- **Scribe:** Markdown and technical-documentation syntax, changelog/ADR conventions, API/reference documentation, versioned documentation, deprecation/sunset records, source-backed claims, and link/anchor freshness.
- **The Steward and The Governor:** stronger requirements traceability, acceptance criteria, scope/change control, authoritative-source acquisition, jurisdiction/effective-date verification, license/privacy/IP/compliance review frameworks, and explicit human-escalation boundaries.
- **Weaver, Conductor, The Tuner, and Arbiter:** adversarial hardening for model/source traceability, routing ownership, contradiction and invalidation, specialist re-entry, handoff identity, continuity, and protected-action boundaries.

The campaign uses `MARKDOWN_PRIMARY_JSON_SELECTIVE`: prose-heavy specialist knowledge remains Markdown-first, while JSON is used selectively for schemas, deterministic catalogs, fixtures, and metadata that materially benefit from structured parsing.

Stronger specialist knowledge does not create broader authority:

~~~text
specialist_knowledge_depth != authority_expansion
validation_success != authority_grant
mergeability != publication_authority
~~~

See the [v1.3.0 release candidate](docs/releases/v1.3.0-specialist-intelligence-release-candidate.md) and [v1.3.0 release-readiness evidence](docs/validation/V1_3_0_RELEASE_READINESS_EVIDENCE.md) for the completed campaign and preparation record.

## v1.2.0 Governed Runtime Baseline

v1.2.0 established the governed-runtime baseline that v1.3.0 builds on: delegated progression, specialist coordination, validation, merge-readiness, and host-continuity contracts with explicit authority boundaries.

- **Governed autonomy:** Human-Governed, Semi-Autonomous, and Full Autonomous profiles control permitted continuation and pause behavior. Effective authority remains the intersection of the selected profile, explicit grant, repository or project policy, host capability, current phase, and current evidence.
- **Delegated execution:** approved phase envelopes use six explicit Arbiter dispositions for continuation, bounded remediation, evidence waits, capacity waits, human escalation, and safe termination.
- **Multi-specialist coordination:** The Tuner participates only in material multi-domain work and requires complete, consistent, and current specialist-owned contracts before coordinated execution proceeds.
- **Cross-layer integrity validation:** reusable frontend-to-backend, backend-to-persistence, and cross-module logical-flow profiles connect findings to responsible owners, validation evidence, and governed re-entry.
- **Revision-bound validation and merge readiness:** canonical baseline health, exact-head evidence, evidence freshness, expected-head merge guards, signed Squash verification, and independent canonical reads prevent evidence from a different revision from authorizing a newer state.
- **Portable execution state:** runtime envelopes, correlation identity, phase retrospectives, approved-unit plans, status projections, and worktree contracts preserve bounded execution context and reviewable state.
- **Host-continuity evidence:** accepted Codex and Antigravity continuity evidence is distinguished from repository simulation. Claude Code remains `SCAFFOLD_ONLY` for active runtime continuity.

Implementation chronology and source provenance remain available in [Project State](PROJECT_STATE.md), the [Roadmap](docs/project/ROADMAP.md), and the stable [v1.2.0 release notes](docs/releases/v1.2.0-governed-orchestration.md).

## Governed Autonomy Profiles

- **Human-Governed:** safe default; Orchestra pauses before material Git/remote transitions and major phase progression.
- **Semi-Autonomous:** may implement, validate, commit, push, create PRs, monitor exact-head CI, and bounded-remediate when explicitly granted; stops before merge and major phase progression.
- **Full Autonomous:** may also merge and continue through later explicitly granted development phases while repository policy and exact-state evidence remain green.

Profiles are reduction-only. Effective authority is the intersection of the selected profile, explicit grant, repository/project policy, host capability, current phase, and evidence. No profile independently authorizes release, deployment, policy activation, destructive action, force push, history rewrite, or authority expansion. See [Governed Autonomy Modes](docs/governance/GOVERNED_AUTONOMY_MODES.md).

## Delegated Phase Progression

Delegated phase progression applies only when the selected autonomy profile and an explicit maintainer grant permit Orchestra to advance within a defined phase envelope. Delegation controls progression inside that envelope; it does not expand the envelope or create additional authority.

For an approved delegated phase, a maintainer authorizes the phase and its execution envelope once. Conductor may then route only internal units already allowed by that envelope. Specialists execute inside those bounds, Overseer and repository validators produce current evidence, and Arbiter emits the next transition disposition.

| Transition disposition | Meaning |
|---|---|
| `AUTO_CONTINUE` | Begin the next approved unit. |
| `AUTO_REMEDIATE_AND_REVALIDATE` | Correct a deterministic in-scope defect and rerun required checks. |
| `WAIT_FOR_EVIDENCE` | Pause until required evidence is produced. |
| `WAIT_FOR_CAPACITY` | Checkpoint safely and resume later without inventing new authority. |
| `ESCALATE_HUMAN` | Request missing intent, policy, scope, or external-action authority. |
| `STOP` | Preserve a prohibited, unsafe, or invalid state and halt. |

Validation proves conformance to an authorized envelope; it cannot create authority. Stage, commit, push, pull-request, merge, tag, release, deployment, production, infrastructure, secret, and destructive actions remain separately governed.

See the [Delegated Execution Policy](docs/governance/DELEGATED_EXECUTION_POLICY.md) and [Governance Review Flow](docs/governance/GOVERNANCE_REVIEW_FLOW.md).

## Runtime Trust Model

### Trusted composition

Every active run starts from an explicit immutable `RuntimeComposition`. `ACTIVE` mode requires trusted authority, a run-scoped capability manifest, lifecycle and delegation services, coordination services, audit integration, and finite route bindings. Missing, malformed, mismatched, or untrusted active configuration fails closed before execution.

`COMPATIBILITY` mode is also explicit and trusted. Its finite documented route bindings are derived from the versioned machine routing contract. It is not inferred when active configuration is missing, and it is never unlimited authority.

### Authority, capabilities, governance, and coordination

Authority scopes define exact targets, operations, and constraints. Run-scoped capability manifests define exact executable capabilities and allowed operations. Governance asks whether already-authorized work should proceed. Coordination asks whether specialist-owned contracts are complete, consistent, and current enough to proceed.

~~~text
governance_approval != authority_grant
governance_approval != capability_grant
coordination_ready != authority_grant
coordination_ready != capability_grant
validation_success != authority_grant
GITHUB_CAN_MERGE != GOVERNANCE_READY_TO_MERGE
REPOSITORY_SIMULATION != LIVE_HOST_EVIDENCE
~~~

### Bounded delegation

Accepted child work receives an authority subset, capability subset, bounded depth, and only explicitly allowlisted context keys. Rejected delegation creates no executable child run. Accepted child execution stays in process; Orchestra does not create remote workers or background infrastructure.

### Structured lifecycle and deterministic evidence

Runs use typed lifecycle signals and distinct waiting or terminal states. Exact replay of an accepted terminal signal is idempotent; conflicting replay is rejected. Run-linked audit events record authority, capabilities, delegation, coordination, lifecycle, and terminal outcomes without granting permission.

The control-plane re-foundation now binds exact identities, validation outcomes, specialist identity, routing defaults, governance classification, validation rules, transition precedence, and remediation defaults to versioned machine contracts. Agent prose may explain those records, but it cannot override their identities or verdicts. The migration has reached `LEGACY_RETIRED`; that retirement of duplicate runtime authority does not grant release authority, mutate installed hosts, or authorize deployment.

### Coordination state and evidence freshness

The Tuner's coordination runtime records specialist-owned contracts, dependencies, contradictions, invalidations, artifact lifecycles, evidence, and deterministic fingerprints. A supplied collaboration session that is incomplete, contradicted, stale, malformed, or otherwise not ready fails closed. Conductor remains the exclusive router, Overseer remains the validation-evidence owner, and Arbiter remains the continuation authority.

## Roles and Specialist Responsibilities

| Role | Primary responsibility | Key boundary |
|---|---|---|
| The Steward | Business alignment, requirements traceability, scope, change control, acceptance criteria | Does not decide legal or technical implementation details |
| The Governor | Legal/compliance governance, source/applicability verification, privacy-obligation, IP and licensing review | Does not provide legal advice or grant runtime authority |
| Conductor | Routing and ordered specialist handoffs | Routes work but does not implement it |
| The Tuner | Cross-specialist contract assembly, contradictions, invalidation, and re-entry recommendations | Cannot route, implement, validate itself, or grant authority |
| Clockwork | Architecture, service boundaries, distributed patterns, concurrency, API compatibility/versioning, and structural design | Does not implement |
| Cloak | UI/UX, accessibility, responsive behavior, forms, design states, and frontend interaction boundaries | Does not own backend policy |
| Chronicler | Database dialects, transactions, persistence semantics, migrations, query plans, and tenant isolation | Does not own UI or general QA |
| Ponytail | Stack-aware minimal, reversible implementation and implementation-tooling execution | Requires upstream decisions to be settled |
| Cipher | Defensive security, threat modeling, access control, sessions, secrets, privacy controls, and security-tool interpretation | No offensive testing or legal decisions |
| Overseer | QA strategy, test architecture, evidence quality, coverage interpretation, CI matrices, and release readiness | Does not write application code |
| Scribe | Source-backed technical documentation, versioned knowledge, changelog/ADR discipline, and knowledge transfer | Does not invent system behavior |
| Weaver | Mermaid and PlantUML visual models with source traceability | Does not invent architecture |
| Arbiter | Continuity, evidence freshness, transition and merge readiness | Does not override specialist-owned decisions |
| Dagger | Guarded resilience review and destructive-path simulation in explicitly authorized non-production boundaries | Simulation only unless separately authorized with guardrails |

Artificer remains a maintainer-only internal repository-evolution surface. It is not publicly routable and does not execute external code, implement its own findings, or approve its own recommendations. See the governed [Pattern Catalog](docs/internal/PATTERN_CATALOG.md).

## Supported Hosts and Maturity

Support means a validated integration surface. Scaffold-only means the repository contains a thin runtime adapter and packaging or instruction scaffold, not a published marketplace product.

| Host | Maturity | Notes |
|---|---|---|
| Codex | Supported | Marketplace-first installation with repo-local fallback; R7 same-host and cross-host continuity evidence is verified and merged. |
| Claude Code | Scaffold-only | Marketplace metadata, namespaced plugin skills, and R7-H package/contract compatibility; active runtime continuity is not claimed. |
| Antigravity | Supported | Native `agy` plugin path; R7 same-host and cross-host continuity evidence is verified and merged. |
| Cursor | Scaffold-only | Runtime adapter and packaging instructions, not marketplace-published |
| Windsurf | Scaffold-only | Runtime adapter and packaging instructions, not marketplace-published |
| VS Code / VSCodium | Scaffold-only | Shared VS Code-family adapter and scaffold |
| JetBrains | Scaffold-only | Runtime adapter and plugin scaffold, not marketplace-published |
| Zed | Scaffold-only | Runtime adapter and packaging scaffold |
| Neovim | Scaffold-only | Runtime adapter and local editor scaffold |
| Local AI systems | Manual documentation surface | Load selected Markdown and supporting files deliberately |

> **Maturity labels:** `Supported` means Orchestra has a validated integration surface for that host. `Scaffold-only` does not mean partially supported; it means repository-owned integration scaffolding exists, but Orchestra does not claim a published marketplace product or validated active-runtime continuity for that host unless the row explicitly states otherwise.

Repository CI and Phase C fixtures are not live installed-host evidence. Accepted R7 records are reconciled in [R7 live installed-host validation evidence](docs/validation/R7_LIVE_INSTALLED_HOST_VALIDATION_EVIDENCE.md); the fixture remains pending/empty by design. See [Compatibility](docs/setup/COMPATIBILITY.md).

## Installation

Use the host-native path:

- Codex: add `https://github.com/Baelfyre/Orchestra` as a Marketplace source, install Orchestra, then invoke `@Orchestra`.
- Claude Code: run `/plugin marketplace add Baelfyre/Orchestra`, then `/plugin install orchestra@orchestra`.
- Antigravity: run `agy plugin install https://github.com/Baelfyre/Orchestra`.
- Manual or scaffold-only hosts: follow the exact host boundary in the [Installation Guide](docs/setup/INSTALLATION.md).

Repository manifests identify package version `1.4.0`, and the current public GitHub release is `v1.4.0`. The completed control-plane migration does not itself publish a new version; GitHub Release publication, marketplace publication, and installed-integration refresh remain separate governed actions. See the Installation Guide for supported installation paths and host-maturity boundaries.

## Quick Start

Start by defining four things:

1. **Governance profile:** use `HUMAN_GOVERNED` unless a human explicitly grants a more autonomous profile.
2. **Authorized scope:** name the repository, branch or baseline, allowed paths, behaviors, and external actions.
3. **Hard boundaries:** state what must not happen, such as release, deployment, policy activation, destructive action, force push, or history rewrite.
4. **Terminal boundary:** say exactly where Orchestra must stop, such as an unstaged diff, validated commit, open PR, or independently verified merge.

Example:

~~~text
@Orchestra

Project: Open-source developer tool
Governance profile: HUMAN_GOVERNED
Repository: example/tool
Authorized scope: src/export/** and tests/export/**
Allowed actions: inspect, implement, and validate
Hard boundaries: no dependency change, push, merge, release, or deployment
Terminal boundary: validated unstaged diff ready for human review

Task:
Add a bounded export command without changing public APIs.
~~~

With `HUMAN_GOVERNED`, material Git and phase transitions pause for approval. `SEMI_AUTONOMOUS` may continue through explicitly granted commit, push, PR, exact-head CI, and bounded remediation, but still stops before merge and major phase progression. `FULL_AUTONOMOUS` may also merge and continue through later explicitly granted phases when every current governance gate passes. All three profiles remain inside the same explicit scope and hard boundaries.

## Validation and Evidence

Validation results are revision-specific. An older green run cannot authorize a newer head. Use repository workflow status and the canonical commands in [Validation](docs/setup/VALIDATION.md) for the exact revision being reviewed.

The validation chain covers:

- structure, manifests, Claude plugin, IDE packaging, and Codex export;
- Artificer internal, record, governance-record, and Pattern Catalog validation;
- prompt-load thresholds and budget;
- governance protocol, routing contracts, Tuner collaboration, evidence identity, and strict governance;
- the fail-closed **README Impact Gate**, which requires `README.md` in the same revision whenever significant runtime, specialist, host-integration, governance/routing/setup/release, version, or CI/governance surfaces change;
- behavior validation and runtime tests with the required coverage threshold;
- security, compatibility, licensing, version consistency, stale references, and release readiness;
- native Windows, Ubuntu, and macOS validation;
- `git diff --check` and exact authorized scope.

For autonomous or delegated merges, Orchestra additionally requires the fail-closed [Autonomous Merge Readiness Protocol](docs/governance/AUTONOMOUS_MERGE_READINESS_PROTOCOL.md): a green canonical baseline, exact-head evidence, a raw current PR state with `mergeable == true` and `mergeable_state == clean`, complete successful required checks, expected-head merge guard where supported, no governed bypass use, and independent post-merge verification.

## Release Lineage

### v1.4.0 Governance and Compliance Registry Cross-Integration

`v1.4.0` is the current published Orchestra release. It packages the verified Compliance Registry cross-integration and README Impact Gate from exact signed release commit `93dd51c0fbe1b10affc58e6fadd5fb0bc2927a50`. The GitHub Release is immutable, non-draft, and non-prerelease. Subsequent control-plane re-foundation work is post-v1.4.0 development and does not move the v1.4.0 tag.

Release preparation and publication evidence are recorded in the [v1.4.0 governance upgrade release candidate](docs/releases/v1.4.0-governance-compliance-registry-release-candidate.md), [v1.4.0 release-readiness evidence](docs/validation/V1_4_0_RELEASE_READINESS_EVIDENCE.md), and [v1.4.0 publication closeout](docs/validation/V1_4_0_PUBLICATION_CLOSEOUT.md).

### v1.3.0 Specialist Intelligence

Repository package/version surfaces are aligned at `1.3.0` for the Specialist Intelligence release. The release packages the completed SK1 through SK10 specialist-knowledge campaign while preserving Orchestra's established governance, routing, Tuner coordination, validation, Arbiter, and authority boundaries.

Package version, validation success, or mergeability does not independently establish public-release state. GitHub Release publication is a separate governed transition. See the repository's Releases page for the current publication state.

Release preparation and revision-bound evidence are recorded in the [v1.3.0 release candidate](docs/releases/v1.3.0-specialist-intelligence-release-candidate.md) and [v1.3.0 release-readiness evidence](docs/validation/V1_3_0_RELEASE_READINESS_EVIDENCE.md) for the completed campaign and preparation record.

### v1.2.0 Governed Orchestration

`v1.2.0` established the governed-orchestration baseline from annotated tag `v1.2.0` at release commit `4f3c45f6d1e5f290aca108ddf5810c1b18f1dc76`. Phase C repository reliability, accepted R7 live installed-host evidence, the signed Squash-aware R7R remediation, Phase D overlap reconciliation, R5/R5B merge-readiness hardening, Governed Autonomy Modes, pre-R8 repository hygiene, and final release readiness were completed and independently verified.

That publication did not perform deployment, marketplace graduation, installed-integration refresh, or policy activation.

See the [v1.2.0 release notes](docs/releases/v1.2.0-governed-orchestration.md). The previous v1.1.2 release remains historical release evidence.

## Honest Limitations

- Orchestra does not replace human review or engineering judgment.
- It does not guarantee correct or secure output and does not eliminate hallucinations.
- Prompt content, metadata, routes, governance approvals, coordination status, validation success, audit records, GitHub mergeability, and API success do not create authority.
- The Tuner cannot activate itself, route specialists directly, select a winning domain requirement, implement code, validate its own output, issue an Arbiter transition disposition, or perform Git, release, deployment, or external actions.
- The current coordination runtime is in-memory and does not add persistent collaboration storage, SQLite, migrations, RPC, or host-process orchestration.
- Orchestra does not create remote workers, background agents, or distributed orchestration infrastructure.
- Compatibility mode is explicit, finite, and intended for bounded existing routes.
- Cursor, Windsurf, VS Code/VSCodium, JetBrains, Zed, and Neovim remain scaffold-only.
- Repository simulation is not live installed-host evidence. Accepted R7 evidence is `MERGED_VERIFIED`; the simulated fixture remains pending/empty by design.
- Orchestra is developer tooling and a local runtime. It does not store or transmit downstream project data by default.
- Data sensitivity, privacy, retention, deletion, platform disclosure, and IP obligations depend on the downstream project and host environment.
- Release governance may require revision or block publication.
- The current public release is `v1.4.0`; post-v1.4.0 control-plane migration work is not a new release until a separately governed publication completes.

## Documentation Map

### Start here

- [Installation](docs/setup/INSTALLATION.md)
- [Compatibility](docs/setup/COMPATIBILITY.md)
- [Validation](docs/setup/VALIDATION.md)
- [Skill Index](SKILL_INDEX.md)

### Architecture and coordination

- [Runtime Architecture](docs/project/AUTHORITY_CAPABILITY_RUNTIME_ARCHITECTURE.md)
- [Authority and Capability Contracts](docs/project/AUTHORITY_CAPABILITY_CONTRACTS.md)
- [Cross-Specialist Coordination Protocol](docs/routing/CROSS_SPECIALIST_COORDINATION_PROTOCOL.md)
- [Evidence Identity and Freshness Protocol](docs/governance/EVIDENCE_IDENTITY_AND_FRESHNESS_PROTOCOL.md)
- [Portable Runtime Adapter Protocol](docs/project/PORTABLE_ADAPTER_PROTOCOL.md)
- [Roadmap](docs/project/ROADMAP.md)

### Governance

- [Governance Layer](docs/governance/GOVERNANCE_LAYER.md)
- [Governance Review Flow](docs/governance/GOVERNANCE_REVIEW_FLOW.md)
- [Delegated Execution Policy](docs/governance/DELEGATED_EXECUTION_POLICY.md)
- [Autonomous Merge Readiness Protocol](docs/governance/AUTONOMOUS_MERGE_READINESS_PROTOCOL.md)
- [Compliance Registry Integration](docs/governance/COMPLIANCE_REGISTRY_INTEGRATION.md)
- [Release Gates](docs/governance/RELEASE_GATES.md)
- [App Release Compliance Gate](docs/governance/APP_RELEASE_COMPLIANCE_GATE.md)

### Release and maintainers

- [v1.4.0 Governance Upgrade Release Candidate](docs/releases/v1.4.0-governance-compliance-registry-release-candidate.md)
- [v1.4.0 Prepublication Readiness Evidence](docs/validation/V1_4_0_PREPUBLICATION_READINESS_EVIDENCE.md)
- [v1.3.0 Release Candidate](docs/releases/v1.3.0-specialist-intelligence-release-candidate.md)
- [v1.3.0 Release Readiness Evidence](docs/validation/V1_3_0_RELEASE_READINESS_EVIDENCE.md)
- [v1.2.0 Release Notes](docs/releases/v1.2.0-governed-orchestration.md)
- [v1.1.2 Release Notes](docs/releases/v1.1.2-trusted-runtime-authority.md)
- [Contributing](docs/CONTRIBUTING.md)
- [Project State](PROJECT_STATE.md)
- [Session Handoff](SESSION_HANDOFF.md)
- [Decision Log](DECISION_LOG.md)
- [Changelog](CHANGELOG.md)

## External Pattern Governance

Orchestra uses source-pinned, static Artificer reviews to govern selected concepts observed in external open-source projects. Current governed records cover [Priivacy-ai/spec-kitty](https://github.com/Priivacy-ai/spec-kitty), [CristianOlivera1/openhero](https://github.com/CristianOlivera1/openhero), and [usestrix/strix](https://github.com/usestrix/strix).

These records distinguish static reference review, concept-only adaptation, and Orchestra-native implementation from direct reuse. They do not establish wholesale integration, source-code copying, dependency adoption, endorsement, affiliation, trademark permission, or a blanket licensing conclusion.

The authoritative incorporation record is the governed [Pattern Catalog](docs/internal/PATTERN_CATALOG.md). Source-pinned audit and decision records preserve the detailed provenance and disposition for each reviewed pattern. External source code, datasets, prompts, payloads, examples, media, assets, or documentation expression are not incorporated unless a governed record explicitly authorizes that reuse.

## Contributing, Security, and License

Contributions should preserve specialist ownership, cross-specialist contract boundaries, runtime trust boundaries, validation evidence, and scaffold maturity labels. Start with the [Contributing Guide](docs/CONTRIBUTING.md).

Report vulnerabilities privately through the process in [SECURITY.md](SECURITY.md). Do not commit secrets, credentials, personal data, client information, or private project material.

Orchestra is licensed under the [MIT License](LICENSE). Governed external-pattern records preserve applicable provenance and attribution boundaries; they do not authorize wholesale copying of external projects.