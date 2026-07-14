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
    <img src="https://img.shields.io/badge/current_release-v1.1.2-blue" alt="Current public release v1.1.2" />
    <img src="https://img.shields.io/badge/runtime_tests-194_passed-brightgreen" alt="194 runtime tests passed" />
    <img src="https://img.shields.io/badge/runtime_coverage-97.72%25-brightgreen" alt="97.72 percent runtime coverage" />
    <a href="https://github.com/Baelfyre/Orchestra/actions/workflows/validate.yml">
      <img src="https://github.com/Baelfyre/Orchestra/actions/workflows/validate.yml/badge.svg" alt="Repository validation status" />
    </a>
    <img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT license" />
  </p>
</div>

---

## AI can generate fast. Building well still requires structure.

AI-assisted projects rarely fail because a model cannot produce another answer. They fail when context drifts, architecture and implementation blur together, unchecked output becomes the next input, evidence disappears, decisions arrive out of order, and tool access is mistaken for permission.

Orchestra turns those scattered interactions into one coordinated workflow. Like a conductor keeping each section on the same score, it gives every responsibility a defined place, controls when work moves forward, and sends failed work back for correction. After that opening metaphor, the mechanics are precise: trusted runtime composition, explicit routing, bounded authority, immutable capabilities, separate governance, structured lifecycle state, validation, and deterministic evidence.

## What Orchestra Is

Orchestra is a structured, standardized, and governance-driven framework for coordinating AI-assisted software work across specialist responsibilities, tools, validation stages, and human approval points.

It is not an AI model and does not replace one. The model generates or reviews work. Orchestra is the coordination layer that routes, sequences, constrains, validates, records, and connects that work to the next responsible boundary.

This structure helps students see which engineering question comes next, helps experienced developers reduce context drift and repeated prompting, and gives maintainers reviewable state and evidence across long-running tasks. It does not replace software fundamentals or engineering judgment.

## How Orchestra Works

The runtime establishes permission before it accepts host-provided context. Routing selects responsibility, but does not grant authority. Authority and capability checks run before governance. Governance may block authorized work, but cannot create a missing permission. Validation failure returns work to its owning boundary before any result is accepted.

~~~mermaid
flowchart TD
    Request["Request + Project Context"]
    Compose["Trusted Runtime Composition"]
    Context["Context + Command"]
    Route["Conductor Routes Work"]
    Authority{"Authority Allowed?"}
    Capability{"Capability Granted?"}
    Governance{"Governance Satisfied?"}
    Specialist["Specialist Execution"]
    Validate{"Validation Passed?"}
    Revise["Return to Owning Boundary"]
    Lifecycle["Structured Lifecycle Result"]
    Audit["Deterministic Audit Evidence"]
    Review["Human Review or Accepted Output"]

    Request --> Compose --> Context --> Route --> Authority
    Authority -- No --> Lifecycle
    Authority -- Yes --> Capability
    Capability -- No --> Lifecycle
    Capability -- Yes --> Governance
    Governance -- No --> Lifecycle
    Governance -- Yes --> Specialist --> Validate
    Validate -- No --> Revise --> Specialist
    Validate -- Yes --> Lifecycle --> Audit --> Review

    classDef input fill:#161616,stroke:#777,color:#fff
    classDef runtime fill:#24143a,stroke:#9d6cff,color:#f3eaff
    classDef coord fill:#332712,stroke:#d4af37,color:#fff3bd
    classDef work fill:#102a43,stroke:#58a6ff,color:#e5f2ff
    classDef pass fill:#12351f,stroke:#4ac26b,color:#e7ffed
    classDef stop fill:#3b1717,stroke:#ff6b6b,color:#ffe8e8
    class Request,Context input
    class Compose,Lifecycle runtime
    class Route,Authority,Capability,Governance coord
    class Specialist work
    class Validate,Audit,Review pass
    class Revise stop
~~~

Accessible summary: a request moves through trusted composition, context and command parsing, routing, authority, capability, governance, specialist execution, and validation. A failed validation returns to the owning boundary. Allowed, denied, blocked, failed, waiting, or completed work ends in a structured lifecycle result, deterministic audit evidence, and review.

The sequence is deliberate:

1. Project context and the request enter a trusted runtime composition.
2. Root authority, runtime capabilities, route bindings, and run identity are validated before adapter access.
3. Host context and a command are parsed, then Conductor selects the smallest effective skill stack.
4. Exact authority and capability decisions run against immutable trusted contracts.
5. Governance evaluates whether already-authorized work should proceed.
6. A specialist executes only inside the accepted boundary.
7. Validation either returns the work for correction or allows it to continue.
8. Structured lifecycle signals record waiting or a distinct terminal result.
9. Run-linked audit events record what happened without granting permission.

## One Request, Coordinated Responsibilities

Consider one request:

> Build a secure employee payroll system.

That sentence contains business, legal, architecture, data, implementation, security, validation, documentation, and continuity concerns. Orchestra does not activate every specialist automatically. Conductor selects the smallest effective stack, then sequences only the responsibilities supported by the task and project context.

| Responsibility | Example contribution | Boundary |
|---|---|---|
| The Steward | Confirms business purpose, scope, requirements, and required delivery artifacts | Does not decide legal or technical implementation details |
| The Governor | Reviews privacy, licensing, IP, and release obligations | Does not provide legal advice or grant runtime authority |
| Conductor | Chooses and sequences the required specialist work | Routes work but does not implement it |
| Clockwork | Defines application architecture and service boundaries | Does not write the implementation |
| Chronicler | Defines payroll data and persistence semantics | Does not own UI or security policy |
| Ponytail | Applies the approved implementation with minimal safe edits | Does not invent architecture or policy |
| Cipher | Reviews access control, secrets, and defensive security boundaries | Does not perform offensive testing |
| Overseer | Defines validation gates and release evidence | Does not write application code |
| Scribe | Produces source-backed documentation | Does not invent system behavior |
| Arbiter | Checks continuity, branch state, evidence, and transition readiness | Does not override Steward or Governor decisions |

If security validation detects unauthorized payroll access, work does not move directly to approval. It returns to the owning implementation boundary, the access control is corrected, validation runs again, and only passing evidence proceeds to review.

## Why Orchestra Instead of Direct Prompting?

| Direct prompting | Orchestra |
|---|---|
| One answer may mix architecture, code, testing, and assumptions | Defined specialists own distinct responsibilities |
| Context can drift across prompts, tools, and sessions | Project state, contracts, decisions, and handoffs preserve continuity |
| Tool access may be mistaken for permission | Exact authority and immutable runtime capability grants define permission |
| A route can be treated as an implicit grant | Routing selects responsibility only |
| Governance may be confused with authorization | Governance is a separate blocking layer that cannot create authority or capabilities |
| Failure may be explained without re-entering the workflow | Validation returns work to correction and revalidation |
| Completion may be inferred from generated text | Structured lifecycle signals control waiting and terminal state |
| Logs may be treated as proof of permission | Audit events record evidence but never authorize work |

Orchestra does not make output automatically correct. It makes ownership, ordering, constraints, failure, and evidence visible enough to review.

## Runtime Trust Model

### Trusted composition

Every run starts from an explicit immutable <code>RuntimeComposition</code>. <code>ACTIVE</code> mode requires trusted authority, a run-scoped capability manifest, lifecycle and delegation services, audit integration, and finite route bindings. Missing, malformed, mismatched, or untrusted active configuration fails closed before adapter context or command parsing.

<code>COMPATIBILITY</code> mode is also explicit and trusted. It uses finite repository-owned mappings for documented routes. It is not inferred when active configuration is missing, and it is never unlimited authority.

### Authority, capabilities, and governance

Authority scopes define exact targets, operations, and constraints. Run-scoped capability manifests define exact executable capabilities and allowed operations. Capability grant provenance must match manifest provenance, and a present capability must belong to the specialist binding that uses it.

The distinction is fundamental:

~~~text
governance_approval != authority_grant
governance_approval != capability_grant
governance_denial may block authorized work
authority_denial cannot be reversed by governance
capability_denial cannot be reversed by governance
~~~

Governance asks whether authorized work should proceed. It does not decide what the runtime is permitted to do in the first place.

### One-time run identity

Root and child run identities initialize once. Reusing the same identity raises <code>RUN_ALREADY_INITIALIZED</code> before trusted-contract revalidation, adapter access, parsing, routing, governance, or execution. A distinct run identity remains independently executable.

### Bounded delegation

Child work requires an accepted <code>DelegationResolution</code>. A child receives an authority subset, capability subset, bounded depth, and only explicitly allowlisted context keys. Sensitive or unavailable context requests are rejected. Rejected delegation creates no executable child run. Accepted child execution stays in process; Orchestra does not create remote agents, worker processes, or background infrastructure.

~~~mermaid
flowchart TD
    Trusted["Trusted runtime construction or repository-owned policy"]
    Parent["Parent Run<br/>Authority + Capabilities + Permitted Context Keys"]
    Bound{"Strict bounded delegation validation"}
    Child["Child Run<br/>Authority subset<br/>Capability subset<br/>Explicit Context Keys"]
    Reject["Rejected<br/>No executable child run"]
    Untrusted["Prompt text<br/>Adapter metadata<br/>Route<br/>Governance approval<br/>Audit record"]
    NoGrant["Cannot create or widen authority"]

    Trusted --> Parent --> Bound
    Bound -- Accepted --> Child
    Bound -- Rejected --> Reject
    Untrusted -.-> NoGrant
    NoGrant -.-> Bound

    classDef trusted fill:#24143a,stroke:#9d6cff,color:#f3eaff
    classDef parent fill:#102a43,stroke:#58a6ff,color:#e5f2ff
    classDef gate fill:#332712,stroke:#d4af37,color:#fff3bd
    classDef accepted fill:#12351f,stroke:#4ac26b,color:#e7ffed
    classDef rejected fill:#3b1717,stroke:#ff6b6b,color:#ffe8e8
    class Trusted trusted
    class Parent,Untrusted parent
    class Bound gate
    class Child accepted
    class Reject,NoGrant rejected
~~~

Accessible summary: trusted construction creates the parent run. Strict validation can create a narrower in-process child or reject the request without creating a child. Prompt text, adapter metadata, routing, governance approval, and audit records cannot create or widen authority.

### Structured lifecycle

A run begins in <code>INITIALIZING</code>. <code>ACTIVATE</code> is accepted only from that state. An active run may <code>WAIT</code>; only a waiting run may <code>RESUME</code>. <code>WAITING</code> is non-terminal. <code>COMPLETED</code>, <code>FAILED</code>, <code>CANCELLED</code>, <code>TIMED_OUT</code>, and <code>BLOCKED</code> remain distinct terminal outcomes. Ordinary generated text cannot transition or complete a run.

Exact replay of an accepted terminal signal is idempotent. Altered or conflicting terminal signals are rejected while the original immutable result remains intact.

### Deterministic evidence

Run-linked events record root authority creation, capability manifests, authority and capability decisions, delegation acceptance or rejection, lifecycle transitions, terminal results, and initialization failure. Audit evidence is non-authorizing. Even an audit sink failure cannot turn denied work into allowed work or replace an accepted terminal result.

## Architecture

These are ownership layers, not a shortcut around the runtime sequence:

| Layer | Responsibility | Canonical detail |
|---|---|---|
| Governance | Business alignment, compliance, privacy obligations, IP, continuity, and release gates | [Governance Layer](docs/governance/GOVERNANCE_LAYER.md) |
| Orchestration | Intent classification, routing, and ordered specialist handoffs | [Router-First Architecture](docs/routing/ROUTER_FIRST_ARCHITECTURE.md) |
| Trusted Runtime | Composition, authority, capabilities, delegation, lifecycle, execution, and audit evidence | [Runtime Architecture](docs/project/AUTHORITY_CAPABILITY_RUNTIME_ARCHITECTURE.md) |
| Specialist Execution | Focused architecture, implementation, data, security, QA, documentation, and visual work | [Skill Index](SKILL_INDEX.md) |
| Validation and Evidence | Behavior, runtime, packaging, governance, and release-readiness proof | [Validation Guide](docs/setup/VALIDATION.md) |

The [Authority and Capability Contracts](docs/project/AUTHORITY_CAPABILITY_CONTRACTS.md) define the immutable runtime rules. The [implementation plan](docs/project/AUTHORITY_CAPABILITY_IMPLEMENTATION_PLAN.md) records their phased delivery. Host integration remains separated by the [Portable Runtime Adapter Protocol](docs/project/PORTABLE_ADAPTER_PROTOCOL.md).

## Roles and Specialist Responsibilities

### Governance authorities

| Role | Use it for | Key boundary |
|---|---|---|
| The Steward | Business alignment, scope, requirements, acceptance criteria, and SDLC sufficiency | Does not own legal or technical decisions |
| The Governor | Legal, privacy-obligation, IP, licensing, and compliance governance | Identifies risks and escalation points, not legal advice |
| Arbiter | Continuity, source of truth, validation state, handoff, and merge readiness | Uses verified repository evidence |

### Orchestration and execution

| Role | Use it for | Key boundary |
|---|---|---|
| Conductor | Routing and multi-skill sequencing | Does not execute specialist work |
| Clockwork | Architecture, layering, and refactor structure | Does not implement |
| Cloak | UI, UX, accessibility, and responsive behavior | Does not own backend policy |
| Chronicler | Database and persistence semantics | Does not own UI or general QA |
| Ponytail | Minimal, reversible implementation | Requires upstream decisions to be settled |
| Cipher | Defensive security, access control, secrets, and privacy controls | No offensive testing or legal decisions |
| Overseer | QA strategy, validation gates, and release readiness | Does not write application code |
| Scribe | README, release, setup, and handoff documentation | Uses source-backed facts |
| Weaver | Mermaid and PlantUML diagrams | Does not invent architecture or relationships |

### Gated resilience

| Role | Use it for | Key boundary |
|---|---|---|
| Dagger | Guarded destructive-path simulation and resilience review | Simulation only unless separately authorized with guardrails |

### Internal repository evolution

| Role | Use it for | Key boundary |
|---|---|---|
| Artificer | Maintainer-only, static, read-only audits of selected external repositories for useful patterns, risks, provenance, and licensing considerations | Not publicly routable; does not execute external code, implement findings, approve its own recommendations, or appear in runtime and adapter exports |

Artificer is intentionally separate from Orchestra's public runtime specialist roster. Its audit records support transparent repository evolution, specialist review, provenance tracking, licensing analysis, and governed Pattern Catalog decisions.

See the [Artificer workflow](docs/internal/ARTIFICER_WORKFLOW.md), [Artificer boundaries](docs/internal/ARTIFICER_BOUNDARIES.md), and governed [Pattern Catalog](docs/internal/PATTERN_CATALOG.md).

## External Repository Reviews and Incorporated Patterns

Orchestra may inspect selected external open-source repositories through source-pinned, static Artificer audits. A repository can be audited without being incorporated, and an audit does not authorize copying or implementation.

| Source repository | Relationship to Orchestra | Current outcome |
|---|---|---|
| [`usestrix/strix`](https://github.com/usestrix/strix) | Reference source for lifecycle-gated completion, declared authority scope, run-scoped capabilities, and validated specialist delegation | Four governed reference-only patterns were independently implemented as Orchestra-native runtime contracts and released in `v1.1.2` |
| [`CristianOlivera1/openhero`](https://github.com/CristianOlivera1/openhero) | Static review covering UI orchestration, resilience, archive validation, and defensive-security observations | Audit findings were retained for reference; no OpenHero pattern has been promoted or implemented in Orchestra |

### External-source incorporation boundary

Listing a repository here does not mean that its entire codebase, data, or knowledge base was imported into Orchestra. Orchestra does not wholesale-copy external repositories.

Where incorporation occurs, it is limited to approved concepts, useful logic, reusable skills and knowledge, validation lessons, and independently written Orchestra-native components that improve the framework and its governed knowledge base.

External source code, datasets, prompts, payloads, examples, media, assets, and documentation are not incorporated unless a governed record explicitly authorizes reuse and the applicable license, attribution, security, and maintainer-review requirements are satisfied.

The authoritative incorporation record is the governed [Pattern Catalog](docs/internal/PATTERN_CATALOG.md). An Artificer audit alone does not mean that a repository, pattern, or finding has been incorporated into Orchestra.

## Supported Hosts and Maturity

Support means a validated integration surface. Scaffold-only means the repository contains a thin runtime adapter and packaging or instruction scaffold, not a published marketplace product.

| Host | Maturity | Notes |
|---|---|---|
| Codex | Supported | Marketplace-first installation with repo-local fallback |
| Claude Code | Supported | Marketplace metadata and namespaced plugin skills |
| Antigravity | Supported | Native <code>agy</code> plugin path |
| Cursor | Scaffold-only | Runtime adapter and packaging instructions, not marketplace-published |
| Windsurf | Scaffold-only | Runtime adapter and packaging instructions, not marketplace-published |
| VS Code / VSCodium | Scaffold-only | Shared VS Code-family adapter and scaffold |
| JetBrains | Scaffold-only | Runtime adapter and plugin scaffold, not marketplace-published |
| Zed | Scaffold-only | Runtime adapter and packaging scaffold |
| Neovim | Scaffold-only | Runtime adapter and local editor scaffold |
| Local AI systems | Manual documentation surface | Load selected Markdown and supporting files deliberately |

Orchestra does not claim to work everywhere. See [Compatibility](docs/setup/COMPATIBILITY.md) and the [scaffold graduation criteria](docs/project/SCAFFOLD_ADAPTER_GRADUATION_CRITERIA.md).

## Installation

Use the host-native path:

- Codex: add <code>https://github.com/Baelfyre/Orchestra</code> as a Marketplace source, install Orchestra, then invoke <code>@Orchestra</code>.
- Claude Code: run <code>/plugin marketplace add Baelfyre/Orchestra</code>, then <code>/plugin install orchestra@orchestra</code>.
- Antigravity: run <code>agy plugin install https://github.com/Baelfyre/Orchestra</code>.
- Manual or scaffold-only hosts: follow the exact host boundary in the [Installation Guide](docs/setup/INSTALLATION.md).

Repo-local Codex skill copies are an advanced fallback. Persistent project changes belong in tracked <code>skills/</code> source, not generated <code>.agents/</code> runtime copies.

## Quick Start

1. Provide the project type, purpose, release target, data sensitivity, dependencies, and constraints.
2. Describe the concrete task and acceptance criteria.
3. Let Conductor select and sequence the smallest effective specialist stack.
4. Review governance decisions and specialist outputs at their owning boundaries.
5. Run the required validation before accepting the result.
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

The first complete Phase 6D validation pass observed 194 runtime tests passing at 97.72 percent coverage. The behavior runner passed with 153 reported unittest cases and one documented skip. Strict governance reported 0 errors and 0 warnings. The validation chain covers:

- Artificer internal, record, governance-record, and Pattern Catalog validation;
- structure, manifests, Claude plugin, IDE packaging, and Codex export;
- prompt-load thresholds and budget;
- governance protocol, routing contract, and strict governance;
- behavior validation;
- runtime tests with at least 90 percent coverage;
- runtime import smoke;
- release-readiness, version, licensing, security, and compatibility review;
- link checks, <code>git diff --check</code>, and exact authorized scope.

These exact values come from the finished Issue #184 tree. The complete chain reproduced them after the evidence update; that second pass is authoritative. See [Validation](docs/setup/VALIDATION.md) for canonical commands.

## v1.1.2 Release Highlights

The published <code>v1.1.2</code> release includes:

- trusted authority and run-scoped runtime capability enforcement;
- explicit finite <code>ACTIVE</code> and <code>COMPATIBILITY</code> composition;
- bounded in-process specialist delegation;
- structured lifecycle control and same-run replay rejection;
- <code>RuntimeExecutor</code> integration with authority and capability checks before governance;
- adversarial fail-closed validation;
- deterministic non-authorizing audit evidence;
- completion of the four governed Artificer promotions;
- synchronized README, setup, compatibility, and release surfaces.

See the [v1.1.2 Trusted Runtime Authority release notes](docs/releases/v1.1.2-trusted-runtime-authority.md) and the published [`v1.1.2` GitHub Release](https://github.com/Baelfyre/Orchestra/releases/tag/v1.1.2).

## Honest Limitations

- Orchestra does not replace human review or engineering judgment.
- It does not guarantee correct or secure output and does not eliminate hallucinations.
- Prompt content, metadata, routes, governance approvals, and audit records do not grant authority.
- Governance can block work but cannot create authority or capabilities.
- Orchestra does not create remote workers, background agents, or distributed orchestration infrastructure.
- Compatibility mode is explicit, finite, and intended for bounded existing routes.
- Cursor, Windsurf, VS Code/VSCodium, JetBrains, Zed, and Neovim remain scaffold-only.
- Orchestra is developer tooling and a local runtime. It does not store or transmit downstream project data by default.
- Data sensitivity, privacy, retention, deletion, platform disclosure, and IP obligations depend on the downstream project and host environment.
- Release governance may require revision or block publication.

## Documentation Map

### Start here

- [Installation](docs/setup/INSTALLATION.md)
- [Compatibility](docs/setup/COMPATIBILITY.md)
- [Validation](docs/setup/VALIDATION.md)
- [Skill Index](SKILL_INDEX.md)

### Architecture

- [Runtime Architecture](docs/project/AUTHORITY_CAPABILITY_RUNTIME_ARCHITECTURE.md)
- [Authority and Capability Contracts](docs/project/AUTHORITY_CAPABILITY_CONTRACTS.md)
- [Portable Runtime Adapter Protocol](docs/project/PORTABLE_ADAPTER_PROTOCOL.md)
- [Roadmap](docs/project/ROADMAP.md)

### Governance

- [Governance Layer](docs/governance/GOVERNANCE_LAYER.md)
- [Governance Review Flow](docs/governance/GOVERNANCE_REVIEW_FLOW.md)
- [Release Gates](docs/governance/RELEASE_GATES.md)
- [App Release Compliance Gate](docs/governance/APP_RELEASE_COMPLIANCE_GATE.md)

### Maintainers

- [Contributing](docs/CONTRIBUTING.md)
- [Project State](PROJECT_STATE.md)
- [Decision Log](DECISION_LOG.md)
- [Changelog](CHANGELOG.md)

## Contributing, Security, and License

Contributions should preserve specialist ownership, runtime trust boundaries, validation evidence, and scaffold maturity labels. Start with the [Contributing Guide](docs/CONTRIBUTING.md).

Report vulnerabilities privately through the process in [SECURITY.md](SECURITY.md). Do not commit secrets, credentials, personal data, client information, or private project material.

Orchestra is licensed under the [MIT License](LICENSE). The four finalized Artificer promotions preserve governed conceptual provenance and Apache-2.0 attribution boundaries. They do not authorize copying external source code, prompts, payloads, examples, media, or documentation expression.
