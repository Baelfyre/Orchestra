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
    <img src="https://img.shields.io/badge/package_version-v1.6.0-blue" alt="Repository package version v1.6.0" />
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

## Core capabilities

| Capability | What it does | Go deeper |
| --- | --- | --- |
| **Specialist orchestration** | Routes work to focused architecture, implementation, security, UI/UX, database, QA, documentation, governance, and coordination roles. | [Skills & Routing](docs/README.md#specialists-routing-and-coordination) |
| **Governed execution** | Keeps authority, capabilities, governance, human gates, and repository policy separate and explicit. | [Governance & Authority](docs/README.md#governance-and-authority) |
| **Cross-domain coordination** | Sequences specialist work, detects contradictions, and re-enters the correct owner when assumptions become stale. | [Coordination](docs/README.md#specialists-routing-and-coordination) |
| **Validation & evidence** | Uses deterministic checks, exact-head evidence, cross-platform validation, and fail-closed transition rules. | [Validation & Evidence](docs/README.md#validation-evidence-and-continuity) |
| **Portable host integration** | Supports governed adapter surfaces, PRAP compatibility, host maturity contracts, and bounded MCP transport. | [Hosts & Integrations](docs/README.md#hosts-adapters-and-integrations) |
| **Machine-readable knowledge** | Exposes structured contracts, schemas, provenance, release evidence, and an AI-first repository index. | [`README.json`](README.json) |

## Token-efficient Registry consumption

**O7 is approved and planned, not yet implemented.** It will let Orchestra consume projected/indexed Registry results through the smallest sufficient context while preserving the existing O1-O6 capability, freshness, receipt, Governor/Steward/Arbiter, and fail-closed semantics. Direct local indexed access is preferred; direct JSON remains the deterministic fallback and MCP remains an optional transport for external hosts.

See [O7 — Optimized Registry Consumption](docs/architecture/REGISTRY_QUERY_OPTIMIZATION_O7.md) for the complete architecture and phase plan.

## Research results and empirical benchmarks

Orchestra includes controlled comparative experiments so architectural or communication-efficiency ideas can be evaluated with measured evidence instead of assumed benefit.

### C1 cross-provider natural-language baseline

The completed C1 calibration ran the same frozen five-task benchmark across `DEFAULT`, `CAVEMAN`, and `MURMURS` communication arms using both the accepted Antigravity/Gemini calibration and a separately controlled Codex/GPT baseline.

| Calibration result | Antigravity | Codex |
| --- | ---: | ---: |
| Accepted runs | 30 / 30 | 30 / 30 |
| Task / validation / governance pass | 100% | 100% |
| CAVEMAN total tokens vs DEFAULT | **+2.81%** | **+18.59%** |
| MURMURS total tokens vs DEFAULT | **-0.70%** | **+0.04%** |

**Current research interpretation:** CAVEMAN's token-overhead direction replicated across the two tested provider/model stacks. The small MURMURS token-saving direction observed under Antigravity did **not** replicate under Codex, where MURMURS was effectively token-neutral. MURMURS input-token behavior remained effectively unchanged from `DEFAULT` on both stacks.

This is intentionally a calibration result, not a production-benefit claim. Absolute host-reported token totals are not treated as directly interchangeable across providers/models, and the current evidence does not establish why the MURMURS effect differs between the two host/model surfaces.

- **Full human-readable analysis:** [Codex C1 Cross-Provider Reconciliation](docs/benchmarking/CODEX_C1_CROSS_PROVIDER_RECONCILIATION.md)
- **Machine-readable result:** [`machine/benchmarking/codex-c1-cross-provider-reconciliation.v1.json`](machine/benchmarking/codex-c1-cross-provider-reconciliation.v1.json)
- **Original Antigravity calibration:** [Comparative Measurement B3](docs/benchmarking/COMPARATIVE_MEASUREMENT_B3.md)

The next research extension is C2, which will test deterministic machine-readable JSON task representation separately from this frozen natural-language baseline. C2 must not rewrite or retroactively tune C1 evidence.

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

## Install Orchestra

**Codex:** add this repository as a Marketplace source, install Orchestra, then invoke `@Orchestra`.

**Antigravity:**

```sh
agy plugin install https://github.com/Baelfyre/Orchestra
```

**Other hosts and local setups:** use the [Installation Guide](docs/setup/INSTALLATION.md) and [Compatibility Guide](docs/setup/COMPATIBILITY.md).

## Use Orchestra through MCP

**Purpose:** expose a bounded Orchestra tool surface to an MCP-compatible client while preserving the same PRAP adapter, runtime, governance, and authority boundaries.

Launch the stdio server with an existing adapter identity:

```sh
python scripts/mcp_server.py --adapter codex
```

The v1.6 transport targets MCP protocol revision `2026-07-28` and exposes only `server/discover`, `tools/list`, and `tools/call`.

**MCP is transport, not authority.** Client metadata, tool arguments, discovery, or compatibility cannot grant Orchestra runtime authority.

See [MCP stdio governed tool transport](docs/developer/MCP_STDIO_TRANSPORT.md) for framing, protocol-version handling, safety boundaries, and non-goals.

## Build or certify an adapter with the SDK / PRAP

**Purpose:** give integration authors a stable import surface and read-only compatibility certification for Orchestra's existing PRAP v1 adapter contract.

Use the stable SDK import surface:

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

## Acknowledgements & provenance

Orchestra has been built and refined with help from open-source tools, implementation references, protocol specifications, and research repositories.

A reference does **not** automatically mean Orchestra copied its source, vendors it, depends on it at runtime, or inherits authority from it. Orchestra records the relationship, reviewed revision where recoverable, license status, learned or incorporated patterns, affected surfaces, evidence, and explicit incorporation boundaries.

The provenance reconstruction includes current dependencies and references plus historically documented projects such as Strix, OpenHero, Spec-Kitty, Bryl Minimal Design, Ponytail, Caveman, TrueSheet, the MCP specification, and earlier governance/integration research. Deferred research such as Sakana AI Fugu is classified separately from already incorporated references.

- **Human-readable ledger:** [Third-Party Provenance and Acknowledgements](docs/THIRD_PARTY_PROVENANCE.md)
- **Canonical machine record:** [`machine/provenance/third-party.v1.json`](machine/provenance/third-party.v1.json)

## Explore the framework

Start with the [Documentation Map](docs/README.md) for architecture, specialists, governance, validation, hosts, MCP, knowledge, provenance, releases, and historical design records.

Developers extending Orchestra should use the [Developer Portal](docs/developer/README.md), which indexes the Adapter SDK, PRAP certification, host, specialist, governance, and validation contracts.

## Machine-readable reference

AI systems should start with [`README.json`](README.json), then follow its ordered references into `machine/` contracts and JSON Schemas. For third-party attribution and upstream influence, use [`machine/provenance/third-party.v1.json`](machine/provenance/third-party.v1.json) as the canonical semantic provenance record.

Orchestra uses a hybrid representation policy:

- **Markdown** for human explanation, rationale, examples, and specialist guidance.
- **JSON** for canonical structured machine state, contracts, indexes, receipts, provenance, and evidence.
- **JSON Schema** for deterministic validation.
- **TOON** only as a derived, validated, non-authoritative model-context projection when it provides measured context benefit.

When prose and a machine contract disagree on an exact deterministic fact, use the machine contract and treat the mismatch as documentation drift.

---

**License:** [MIT](LICENSE) | **Changelog:** [CHANGELOG.md](CHANGELOG.md) | **Security:** [SECURITY.md](SECURITY.md)