<div align="center">
  <img src="./assets/readme/orchestra-governance-banner.svg" alt="Orchestra banner showing coordinated software responsibilities" width="100%" />

  <p><strong>A portable orchestration runtime for structured AI-assisted development.</strong></p>
  <p>From blind prompting to guided software building.</p>

  <p>
    <a href="docs/setup/INSTALLATION.md">Installation</a> |
    <a href="docs/project/AUTHORITY_CAPABILITY_RUNTIME_ARCHITECTURE.md">Architecture</a> |
    <a href="docs/governance/GOVERNANCE_LAYER.md">Governance</a> |
    <a href="docs/setup/VALIDATION.md">Validation</a> |
    <a href="CHANGELOG.md">Changelog</a>
  </p>
  <p>
    <img src="https://img.shields.io/badge/public_release-v1.1.2-blue" alt="Current public release v1.1.2" />
    <img src="https://img.shields.io/badge/release_candidate-v1.2.0-orange" alt="Repository release candidate v1.2.0" />
    <a href="https://github.com/Baelfyre/Orchestra/actions/workflows/validate.yml">
      <img src="https://github.com/Baelfyre/Orchestra/actions/workflows/validate.yml/badge.svg" alt="Repository validation status" />
    </a>
    <img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT license" />
  </p>
</div>

---

> [!IMPORTANT]
> Repository metadata is prepared for `v1.2.0`, but the latest published GitHub Release remains `v1.1.2`. The `v1.2.0` candidate is `PREPARED_NOT_RELEASED`. Accepted R7 live installed-host evidence is `VERIFIED / RECONCILED LOCALLY`, pending repository merge and independent post-merge verification; no `v1.2.0` tag, GitHub Release, deployment, marketplace graduation, or policy activation is implied.

## AI can generate fast. Building well still requires structure.

AI-assisted projects rarely fail because a model cannot produce another answer. They fail when context drifts, architecture and implementation blur together, specialist assumptions conflict, unchecked output becomes the next input, evidence goes stale, decisions arrive out of order, and tool access is mistaken for permission.

Orchestra turns those scattered interactions into one coordinated workflow. It gives each responsibility a defined owner, controls when work may move forward, sends invalidated work back to the correct boundary, and preserves reviewable state across long-running tasks.

## What Orchestra Is

Orchestra is a structured, governance-driven framework for coordinating AI-assisted software work across specialist responsibilities, tools, validation stages, and human approval points.

It is not an AI model and does not replace one. The model generates or reviews work. Orchestra is the coordination layer that routes, sequences, constrains, coordinates, validates, records, and connects that work to the next responsible boundary.

The framework is designed to help developers reduce context drift, make cross-domain dependencies explicit, keep permission separate from routing and governance, and produce evidence that can be reviewed instead of inferred from generated text.

## How Orchestra Works

The runtime establishes permission before execution. Routing selects responsibility but does not grant authority. Authority and capability checks run before governance. Governance may block already-authorized work, but cannot create missing permission. For material multi-domain work, Conductor activates The Tuner to assemble specialist-owned contracts, expose missing ownership or contradictions, and identify stale dependent evidence. Single-owner work bypasses that coordination overhead.

~~~mermaid
flowchart TD
    Request["Request + Project Context"]
    Compose["Trusted Runtime Composition"]
    Route["Conductor Routes Work"]
    Authority{"Authority Allowed?"}
    Capability{"Capability Granted?"}
    Governance{"Governance Satisfied?"}
    Multi{"Material Cross-Domain Work?"}
    Tuner{"Cross-Layer Contract Ready?"}
    Specialist["Specialist Execution"]
    Validate{"Validation Passed?"}
    Revise["Return to Owning Boundary"]
    Lifecycle["Structured Lifecycle Result"]
    Evidence["Deterministic Evidence"]
    Review["Human Review or Accepted Output"]

    Request --> Compose --> Route --> Authority
    Authority -- No --> Lifecycle
    Authority -- Yes --> Capability
    Capability -- No --> Lifecycle
    Capability -- Yes --> Governance
    Governance -- No --> Lifecycle
    Governance -- Yes --> Multi
    Multi -- No --> Specialist
    Multi -- Yes --> Tuner
    Tuner -- No --> Lifecycle
    Tuner -- Yes --> Specialist
    Specialist --> Validate
    Validate -- No --> Revise --> Specialist
    Validate -- Yes --> Lifecycle --> Evidence --> Review
~~~

Accessible summary: a request moves through trusted composition, routing, authority, capability, and governance. Single-owner work proceeds directly to its specialist. Material cross-domain work must first reach a ready coordination state. Validation failure returns work to the owning boundary. Accepted or blocked work ends in structured lifecycle state and deterministic evidence.

## v1.2.0 Release Candidate Capability Set

The candidate consolidates the substantial backward-compatible work merged after `v1.1.2`:

- **Delegated Phase B progression:** approved units, six transition dispositions, checkpoints, bounded remediation, capacity handoff, evidence freshness, and fail-closed external-action authority.
- **The Tuner Phases 1-4:** cross-specialist contract assembly, contradiction detection, semantic invalidation, minimal specialist re-entry, typed in-memory coordination, and bounded Conductor-owned runtime integration.
- **Spec Kitty-derived governed execution contracts:** `OrchestraRuntimeEnvelope`, `OrchestraCorrelationID`, `OrchestraPhaseRetrospective`, the 15-field `ApprovedUnitPlan` extension, `OrchestraStatusProjection`, and `OrchestraWorktreeContract`.
- **Cross-layer integrity auditing:** frontend-to-backend, backend-to-persistence, and language-neutral cross-module logical-flow profiles using the existing Conductor -> Tuner -> specialist -> Overseer -> Arbiter ownership model.
- **Delegated Phase C repository reliability:** deterministic repository-verifiable reset/resume, handoff, capacity, stale identity, incomplete checkpoint, authority expansion, scaffold-only host, and replay behavior.
- **Delegated Phase D reconciliation:** `NO_DUPLICATE_RUNTIME_EXTENSION_REQUIRED` for `v1.2.0`; existing trusted runtime contracts cover the material overlap.
- **Autonomous merge-readiness hardening:** green canonical baseline, exact-head evidence, complete required checks, expected-head merge guard where supported, and independent post-merge verification.
- **Current-state reconciliation:** stale Phase C/D status and false live-host promotion are rejected by executable governance consistency checks.

See [v1.2.0 release-candidate notes](docs/releases/v1.2.0-governed-orchestration-release-candidate.md).

## Delegated Phase Progression

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

`COMPATIBILITY` mode is also explicit and trusted. It uses finite repository-owned mappings for documented routes. It is not inferred when active configuration is missing, and it is never unlimited authority.

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

### Coordination state and evidence freshness

The Tuner's coordination runtime records specialist-owned contracts, dependencies, contradictions, invalidations, artifact lifecycles, evidence, and deterministic fingerprints. A supplied collaboration session that is incomplete, contradicted, stale, malformed, or otherwise not ready fails closed. Conductor remains the exclusive router, Overseer remains the validation-evidence owner, and Arbiter remains the continuation authority.

## Roles and Specialist Responsibilities

| Role | Primary responsibility | Key boundary |
|---|---|---|
| The Steward | Business alignment, scope, requirements, acceptance criteria | Does not decide legal or technical implementation details |
| The Governor | Legal, privacy-obligation, IP, licensing, compliance governance | Does not provide legal advice or grant runtime authority |
| Conductor | Routing and ordered specialist handoffs | Routes work but does not implement it |
| The Tuner | Cross-specialist contract assembly, contradictions, invalidation, re-entry recommendations | Cannot route, implement, validate itself, or grant authority |
| Clockwork | Architecture, layering, code structure | Does not implement |
| Cloak | UI/UX, accessibility, responsive behavior | Does not own backend policy |
| Chronicler | Database and persistence semantics | Does not own UI or general QA |
| Ponytail | Minimal, reversible implementation | Requires upstream decisions to be settled |
| Cipher | Defensive security, access control, secrets, privacy controls | No offensive testing or legal decisions |
| Overseer | QA strategy, validation gates, release readiness | Does not write application code |
| Scribe | Source-backed documentation and knowledge transfer | Does not invent system behavior |
| Weaver | Mermaid and PlantUML visual models | Does not invent architecture |
| Arbiter | Continuity, evidence freshness, transition and merge readiness | Does not override specialist-owned decisions |
| Dagger | Guarded destructive-path simulation and resilience review | Simulation only unless separately authorized with guardrails |

Artificer remains a maintainer-only internal repository-evolution surface. It is not publicly routable and does not execute external code, implement its own findings, or approve its own recommendations. See the governed [Pattern Catalog](docs/internal/PATTERN_CATALOG.md).

## Supported Hosts and Maturity

Support means a validated integration surface. Scaffold-only means the repository contains a thin runtime adapter and packaging or instruction scaffold, not a published marketplace product.

| Host | Maturity | Notes |
|---|---|---|
| Codex | Supported | Marketplace-first installation with repo-local fallback; R7 same-host and cross-host continuity evidence is verified locally, pending repository merge/post-merge verification. |
| Claude Code | Supported packaging/integration | Marketplace metadata and namespaced plugin skills; Phase C active runtime continuity is not inferred from packaging support. |
| Antigravity | Supported | Native `agy` plugin path; R7 same-host and cross-host continuity evidence is verified locally, pending repository merge/post-merge verification. |
| Cursor | Scaffold-only | Runtime adapter and packaging instructions, not marketplace-published |
| Windsurf | Scaffold-only | Runtime adapter and packaging instructions, not marketplace-published |
| VS Code / VSCodium | Scaffold-only | Shared VS Code-family adapter and scaffold |
| JetBrains | Scaffold-only | Runtime adapter and plugin scaffold, not marketplace-published |
| Zed | Scaffold-only | Runtime adapter and packaging scaffold |
| Neovim | Scaffold-only | Runtime adapter and local editor scaffold |
| Local AI systems | Manual documentation surface | Load selected Markdown and supporting files deliberately |

Repository CI and Phase C fixtures are not live installed-host evidence. Accepted R7 records are reconciled in [R7 live installed-host validation evidence](docs/validation/R7_LIVE_INSTALLED_HOST_VALIDATION_EVIDENCE.md); the fixture remains pending/empty by design. See [Compatibility](docs/setup/COMPATIBILITY.md).

## Installation

Use the host-native path:

- Codex: add `https://github.com/Baelfyre/Orchestra` as a Marketplace source, install Orchestra, then invoke `@Orchestra`.
- Claude Code: run `/plugin marketplace add Baelfyre/Orchestra`, then `/plugin install orchestra@orchestra`.
- Antigravity: run `agy plugin install https://github.com/Baelfyre/Orchestra`.
- Manual or scaffold-only hosts: follow the exact host boundary in the [Installation Guide](docs/setup/INSTALLATION.md).

During R6, repository manifests identify the candidate as `1.2.0`; the latest public GitHub Release remains `v1.1.2`. See the Installation Guide for the candidate/public-release distinction.

## Quick Start

1. Provide the project type, purpose, release target, data sensitivity, dependencies, and constraints.
2. Describe the concrete task and acceptance criteria.
3. Let Conductor select the smallest effective specialist stack and activate The Tuner only when material cross-domain coordination is required.
4. Review governance decisions and specialist outputs at their owning boundaries.
5. Run required validation before accepting the result.
6. Preserve project state and a concise handoff before changing session, branch, or maintainer.

Example:

~~~text
@Orchestra

Project: Open-source developer tool
Goal: Add a bounded export command
Release target: Public patch release
Data use: No end-user data
Constraints: Preserve public APIs; no new dependency

Task:
Implement the command, validate it, and leave the diff unstaged for review.
~~~

## Validation and Evidence

Validation results are revision-specific. An older green run cannot authorize a newer head. Use repository workflow status and the canonical commands in [Validation](docs/setup/VALIDATION.md) for the exact revision being reviewed.

The validation chain covers:

- structure, manifests, Claude plugin, IDE packaging, and Codex export;
- Artificer internal, record, governance-record, and Pattern Catalog validation;
- prompt-load thresholds and budget;
- governance protocol, routing contracts, Tuner collaboration, evidence identity, and strict governance;
- behavior validation and runtime tests with the required coverage threshold;
- security, compatibility, licensing, version consistency, stale references, and release readiness;
- native Windows, Ubuntu, and macOS validation;
- `git diff --check` and exact authorized scope.

For autonomous or delegated merges, Orchestra additionally requires the fail-closed [Autonomous Merge Readiness Protocol](docs/governance/AUTONOMOUS_MERGE_READINESS_PROTOCOL.md): a green canonical baseline, exact-head evidence, complete successful required checks, expected-head merge guard where supported, and independent post-merge verification.

## Release Status

### Current public release: v1.1.2

The published `v1.1.2` release established trusted runtime authority, run-scoped capabilities, bounded delegation, structured lifecycle control, `RuntimeExecutor` authority/capability ordering, adversarial fail-closed validation, deterministic non-authorizing audit evidence, and four governed Artificer promotions.

See [v1.1.2 Trusted Runtime Authority release notes](docs/releases/v1.1.2-trusted-runtime-authority.md) and the published [`v1.1.2` GitHub Release](https://github.com/Baelfyre/Orchestra/releases/tag/v1.1.2).

### Repository release candidate: v1.2.0

`v1.2.0` candidate metadata is prepared, but publication remains blocked. Phase C repository reliability is complete through PR #225; accepted R7 live installed-host evidence is verified and reconciled locally, pending repository merge and independent post-merge verification. Phase D reconciliation is complete through PR #226 with no duplicate runtime extension required. R5/R5B added merge-readiness hardening and canonical current-state reconciliation.

The candidate becomes a public release only after the R7 reconciliation is merged and independently verified, a fresh release state is verified, and the separately authorized R8 annotated-tag/GitHub-Release gate completes.

## Honest Limitations

- Orchestra does not replace human review or engineering judgment.
- It does not guarantee correct or secure output and does not eliminate hallucinations.
- Prompt content, metadata, routes, governance approvals, coordination status, validation success, audit records, GitHub mergeability, and API success do not create authority.
- The Tuner cannot activate itself, route specialists directly, select a winning domain requirement, implement code, validate its own output, issue an Arbiter transition disposition, or perform Git, release, deployment, or external actions.
- The current coordination runtime is in-memory and does not add persistent collaboration storage, SQLite, migrations, RPC, or host-process orchestration.
- Orchestra does not create remote workers, background agents, or distributed orchestration infrastructure.
- Compatibility mode is explicit, finite, and intended for bounded existing routes.
- Cursor, Windsurf, VS Code/VSCodium, JetBrains, Zed, and Neovim remain scaffold-only.
- Repository simulation is not live installed-host evidence. R7 evidence is verified and reconciled locally, while repository merge/post-merge verification and the separately authorized R8 publication gate remain required before `v1.2.0` publication.
- Orchestra is developer tooling and a local runtime. It does not store or transmit downstream project data by default.
- Data sensitivity, privacy, retention, deletion, platform disclosure, and IP obligations depend on the downstream project and host environment.
- Release governance may require revision or block publication.

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
- [Release Gates](docs/governance/RELEASE_GATES.md)
- [App Release Compliance Gate](docs/governance/APP_RELEASE_COMPLIANCE_GATE.md)

### Release and maintainers

- [v1.2.0 Release Candidate Notes](docs/releases/v1.2.0-governed-orchestration-release-candidate.md)
- [v1.1.2 Release Notes](docs/releases/v1.1.2-trusted-runtime-authority.md)
- [Contributing](docs/CONTRIBUTING.md)
- [Project State](PROJECT_STATE.md)
- [Session Handoff](SESSION_HANDOFF.md)
- [Decision Log](DECISION_LOG.md)
- [Changelog](CHANGELOG.md)

## External Pattern Governance

Orchestra may inspect selected external open-source repositories through source-pinned, static Artificer audits. An audit does not authorize copying or implementation. Where a concept is incorporated, it must pass governed provenance, licensing, security, ownership, and maintainer-review boundaries and be independently implemented as Orchestra-native work.

The authoritative incorporation record is the governed [Pattern Catalog](docs/internal/PATTERN_CATALOG.md). External source code, datasets, prompts, payloads, examples, media, assets, or documentation expression are not incorporated unless a governed record explicitly authorizes that reuse.

## Contributing, Security, and License

Contributions should preserve specialist ownership, cross-specialist contract boundaries, runtime trust boundaries, validation evidence, and scaffold maturity labels. Start with the [Contributing Guide](docs/CONTRIBUTING.md).

Report vulnerabilities privately through the process in [SECURITY.md](SECURITY.md). Do not commit secrets, credentials, personal data, client information, or private project material.

Orchestra is licensed under the [MIT License](LICENSE). Governed external-pattern records preserve applicable provenance and attribution boundaries; they do not authorize wholesale copying of external projects.
