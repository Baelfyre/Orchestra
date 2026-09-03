<div align="center">
  <img src="./assets/readme/orchestra-governance-banner.svg" alt="Orchestra banner showing coordinated software responsibilities" width="100%" />

  <p><strong>A portable governance and orchestration runtime for structured AI-assisted development.</strong></p>

  <p>
    <a href="docs/setup/INSTALLATION.md">Installation</a> |
    <a href="docs/README.md">Documentation</a> |
    <a href="docs/developer/README.md">Developer Portal</a> |
    <a href="docs/README.md#governance-and-authority">Governance</a> |
    <a href="docs/setup/VALIDATION.md">Validation</a> |
    <a href="docs/THIRD_PARTY_PROVENANCE.md">Acknowledgements</a> |
    <a href="CHANGELOG.md">Changelog</a>
  </p>
  <p>
    <img src="https://img.shields.io/badge/package_version-v1.7.0-blue" alt="Repository package version v1.7.0" />
    <a href="https://github.com/Baelfyre/Orchestra/actions/workflows/validate.yml">
      <img src="https://github.com/Baelfyre/Orchestra/actions/workflows/validate.yml/badge.svg" alt="Repository validation status" />
    </a>
    <img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT license" />
  </p>
</div>

---

## Purpose

AI can generate quickly. Reliable software development still needs ownership, constraints, evidence, and explicit authority.

**Orchestra coordinates AI-assisted development across specialist responsibilities, governance, validation, evidence, host integrations, and human approval boundaries.**

It is **not an AI model**. Models generate and review work. Orchestra determines how permitted work is routed, sequenced, constrained, validated, recorded, and handed to the next responsible boundary.

> **Core rule:** routing, tool access, compatibility, validation success, and mergeability are not authority.

## Mission and vision

**Mission:** make AI-assisted software engineering more reliable through explicit specialist ownership, bounded authority, deterministic safeguards, validation, evidence, and auditable state transitions.

**Vision:** enable the highest useful level of AI-assisted autonomy consistent with explicit human authority, deterministic safeguards, auditable evidence, and recoverable engineering state.

## Prime Directive

> Orchestra shall permit an AI-assisted action or lifecycle transition only within explicit, reduction-only authority and current applicable evidence. It shall never infer permission from capability, routing, confidence, learned state, validation success, mergeability, or prior success. A permanent capability shall be promoted only when proportional evidence shows that it solves an Orchestra-owned problem whose benefit justifies its complexity and risk without weakening these boundaries.

The practical trust boundary is intentionally strict:

```text
CAN_EDIT != MAY_EDIT
CAN_PUSH != MAY_PUSH
TESTS_PASS != MERGE_AUTHORITY
VALIDATION_SUCCESS != AUTHORITY
MCP_EXPOSURE != AUTHORITY
SELECTED_SPECIALIST != UNLIMITED_AUTHORITY
MERGEABLE != MERGE_READY
MERGE_READY != MERGE_AUTHORITY
```

See the full [Orchestra Prime Directive](docs/governance/ORCHESTRA_PRIME_DIRECTIVE.md) and [Governance Overview](docs/governance/README.md).

## Core capabilities

| Capability | What it does | Go deeper |
| --- | --- | --- |
| **Specialist orchestration** | Routes work to focused architecture, implementation, security, UI/UX, database, QA, documentation, governance, and coordination roles. | [Skills & Routing](docs/README.md#specialists-routing-and-coordination) |
| **Governed execution** | Keeps authority, capabilities, governance, human gates, and repository policy separate and explicit. | [Governance & Authority](docs/README.md#governance-and-authority) |
| **Cross-domain coordination** | Sequences specialist work, detects contradictions, and re-enters the correct owner when assumptions become stale. | [Coordination](docs/README.md#specialists-routing-and-coordination) |
| **Adaptive context and shadow learning** | Maintains bounded local evidence, advisory specialist context, and non-authorizing adaptive evaluation without allowing learned state to silently create authority. | [Adaptive Architecture](docs/README.md#adaptive-intelligence) |
| **Portable adaptive memory** | Keeps adaptive state local by default while allowing explicitly reviewed learned candidates to use a storage-agnostic user-selected backend. | [Portable Adaptive Memory](docs/architecture/PORTABLE_ADAPTIVE_MEMORY.md) |
| **UI design fidelity** | Preserves design-source evidence, project-native components, tokens, assets, accessibility requirements, specialist ownership, and deterministic validation. | [UI Design Fidelity Plan](docs/project/UI_DESIGN_FIDELITY_SYSTEM_PLAN.md) |
| **Adaptive documentation and traceability** | Extends Scribe with domain narrative, bidirectional evidence traceability, system-to-documentation reconstruction, and documentation/implementation reconciliation while preserving specialist ownership. | [Scribe Specialist Upgrade](docs/project/SCRIBE_SPECIALIST_UPGRADE_SSU.md) |
| **Product intent and capacity governance** | Extends The Steward with product intent contracts, capacity envelopes, workload assumptions, and adaptive parameter elicitation without overengineering or architecture overreach. | [Steward Intent & Capacity](skills/the-steward/PRODUCT_INTENT_AND_CAPACITY_ENVELOPE_GUIDE.md) |
| **Architecture complexity and scale posture governance** | Extends Clockwork with architecture complexity decisions, scale-ready versus scale-provisioned posture, and simpler-alternative justification without premature infrastructure expansion. | [Clockwork Complexity & Scale](skills/clockwork/ARCHITECTURE_COMPLEXITY_AND_SCALE_POSTURE_GUIDE.md) |
| **Validation and evidence** | Uses deterministic checks, exact-head evidence, cross-platform validation, and fail-closed transition rules. | [Validation & Evidence](docs/README.md#validation-evidence-and-continuity) |
| **Portable host integration** | Supports governed adapter surfaces, PRAP compatibility, host maturity contracts, and bounded MCP transport. | [Hosts & Integrations](docs/README.md#hosts-adapters-and-integrations) |
| **Machine-readable knowledge** | Exposes structured contracts, schemas, provenance, release evidence, and an AI-first repository index. | [`README.json`](README.json) |

## How Orchestra works

```text
Request / Project Context
        ↓
Governance + Authority Boundaries
        ↓
Conductor Routing
        ↓
Specialist Execution / Tuner Coordination
        ↓
Validation + Evidence
        ↓
Arbiter Transition
        ↓
Next bounded action or human gate
```

The deterministic control plane defines what is allowed. Specialists decide how to perform their owned work inside those boundaries. Validation proves outcomes; it does not grant permission.

## Development Lifecycle V2

Development-candidate maturity is kept separate from Orchestra's runtime execution lifecycle. The high-level promotion path is:

```text
Feature Admission
    ↓
Baseline + Implementation
    ↓
Candidate Declaration / Feature Freeze
    ↓
Qualification Gate Set
    ↓
Promotion Adjudication
    ↓
Merge Preparation
    ↓
Merge + Independent Verification
    ↓
Closeout + Retirement
```

This preserves an important distinction: **implemented != validated != evidence-supported != worth adopting != merge-ready != released or activated**. Greater autonomy may remove unnecessary pauses after a gate is satisfied; it does not remove the gate or create protected-action authority.

See [Feature Admission](docs/governance/FEATURE_ADMISSION_POLICY.md), [Candidate Maturity and Feature Freeze](docs/governance/CANDIDATE_MATURITY_FEATURE_FREEZE.md), and [Qualification Gates, Evaluation, and Independent Audit](docs/governance/QUALIFICATION_GATES_EVALUATION_AUDIT.md).

## Portable adaptive memory

Orchestra adaptive learning remains machine-local by default. An optional portable-memory contract can stage explicitly reviewed learned candidates for a user-selected backend without coupling the runtime to a specific repository or storage service.

Supported backend classes are generic: local JSON, Git-backed JSON, HTTP/API storage, or a custom adapter. Backend configuration and credentials remain outside portable learned-pattern payloads.

Portable memory remains advisory and non-authorizing. It cannot grant execution or policy authority, override explicit instructions, relax governance, transfer local identity, or automatically promote learned state.

See [Portable Adaptive Memory](docs/architecture/PORTABLE_ADAPTIVE_MEMORY.md).

## Current release state

The latest published release is **[v1.7.0: Adaptive Intelligence, Portable Memory & Design Fidelity](https://github.com/Baelfyre/Orchestra/releases/tag/v1.7.0)**. The immutable release resolves to canonical commit `e5305ef3e160209a0345bd2c7843c923940e62c5` with tree `7b7a0f6d5dd5376a62125ed1c6b037284e519c69` and a GitHub verified/valid signature.

v1.7.0 consolidates adaptive intelligence through bounded shadow maturity, storage-agnostic portable adaptive memory, Registry O1-O6 adaptive consumption, governed UI design fidelity through UIX-9A proof preparation, and the post-v1.6 documentation/research closeout. The `v1.7.0` tag remains fixed even when `main` receives later post-release maintenance.

The v1.7.0 release itself did not include a live UIX-9 model/provider proof. Post-release UIX-9C V3 later completed as a controlled six-observation study. Its terminal result is **`NO_BENEFIT_ESTABLISHED`**: all three corrected pairs were valid and all 39 primary governed-versus-baseline metric comparisons were unchanged, establishing neither a repeatable governed advantage nor harm under the frozen experiment.

## Research and validation archive

Detailed comparative benchmark reports are retained as research and validation evidence rather than expanded in this landing page.

The completed confirmatory program did **not** establish a repeatable efficiency benefit for Murmurs, so Murmurs is not promoted to the default execution path and is not required by specialists. Historical experiments remain preserved so the negative result is not lost or repeatedly re-tested until positive.

The completed UIX-9C V3 controlled study likewise did **not** establish a repeatable governed UIX advantage on its frozen fixture. The null result is retained as valid negative evidence and does not establish harm.

- [UIX-9C V3 post-study result](docs/validation/uix9b-live-evidence-v2/v3-poststudy-result.v2.json)
- [B-Phase Terminal Closeout Decision](docs/benchmarking/B_PHASE_CLOSEOUT_DECISION.md)
- [B-Phase Final Evidence Synthesis](docs/benchmarking/B_PHASE_FINAL_EVIDENCE_SYNTHESIS.md)
- [Codex C1 Cross-Provider Reconciliation](docs/benchmarking/CODEX_C1_CROSS_PROVIDER_RECONCILIATION.md)
- [Codex C2R1 Machine-JSON Reconciliation](docs/benchmarking/CODEX_C2R1_MACHINE_JSON_RECONCILIATION.md)
- [Benchmarking documentation archive](docs/benchmarking/)

These reports are evidence, not runtime authority or release permission.

## Install Orchestra

**Codex:** add this repository as a Marketplace source, install Orchestra, then invoke `@Orchestra`.

**Antigravity:**

```sh
agy plugin install https://github.com/Baelfyre/Orchestra
```

**Other hosts and local setups:** use the [Installation Guide](docs/setup/INSTALLATION.md) and [Compatibility Guide](docs/setup/COMPATIBILITY.md).

## Use Orchestra through MCP

Orchestra can expose a bounded tool surface to an MCP-compatible client while preserving the same PRAP adapter, runtime, governance, and authority boundaries.

Launch the stdio server with an existing adapter identity:

```sh
python scripts/mcp_server.py --adapter codex
```

The bounded MCP transport, introduced in v1.6.0 and retained in v1.7.0, targets protocol revision `2026-07-28` and exposes only `server/discover`, `tools/list`, and `tools/call`.

**MCP is transport, not authority.** Client metadata, tool arguments, discovery, or compatibility cannot grant Orchestra runtime authority.

See [MCP stdio governed tool transport](docs/developer/MCP_STDIO_TRANSPORT.md) for protocol handling, safety boundaries, and non-goals.

## Build or certify an adapter with the SDK / PRAP

Integration authors can use Orchestra's stable SDK import surface and read-only PRAP v1 compatibility certification.

```text
orchestra_runtime.protocol.sdk
```

Certify one adapter:

```sh
python scripts/certify_adapter.py --adapter codex --json
```

Or certify every contract-declared adapter:

```sh
python scripts/certify_adapter.py --all --json
```

Certification validates compatibility. It does not install integrations, promote host maturity, deploy, activate policy, or grant runtime authority.

See [Adapter SDK and PRAP v1 Compatibility Certification](docs/setup/ADAPTER_SDK_PRAP.md) for the full contract and authority boundary.

## Documentation and provenance

Start with the [Documentation Map](docs/README.md) for architecture, specialists, governance, adaptive intelligence, UI design fidelity, validation, hosts, MCP, knowledge, provenance, releases, and historical design records.

Developers extending Orchestra should use the [Developer Portal](docs/developer/README.md), which indexes the Adapter SDK, PRAP certification, host, specialist, governance, and validation contracts.

Orchestra records third-party relationships without treating a reference as automatic source adoption, runtime dependency, affiliation, or authority transfer.

- [Third-Party Provenance and Acknowledgements](docs/THIRD_PARTY_PROVENANCE.md)
- [`machine/provenance/third-party.v1.json`](machine/provenance/third-party.v1.json)

## Machine-readable reference

AI systems should start with [`README.json`](README.json), then follow its ordered references into `machine/` contracts and JSON Schemas.

Orchestra uses a hybrid representation policy:

- **Markdown** for human explanation, rationale, examples, and specialist guidance.
- **JSON** for canonical structured machine state, contracts, indexes, receipts, provenance, and evidence.
- **JSON Schema** for deterministic validation.
- **TOON** only as a derived, validated, non-authoritative model-context projection when it provides measured context benefit.

When prose and a machine contract disagree on an exact deterministic fact, use the machine contract and treat the mismatch as documentation drift.

---

**License:** [MIT](LICENSE) | **Changelog:** [CHANGELOG.md](CHANGELOG.md) | **Security:** [SECURITY.md](SECURITY.md)
