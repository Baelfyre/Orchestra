<div align="center">
  <img src="./assets/readme/orchestra-governance-banner.svg" alt="Orchestra banner showing coordinated software responsibilities" width="100%" />

  <p><strong>A portable orchestration runtime for structured AI-assisted development.</strong></p>

  <p>
    <a href="docs/setup/INSTALLATION.md">Installation</a> |
    <a href="docs/README.md">Documentation</a> |
    <a href="docs/developer/README.md">Developer Portal</a> |
    <a href="docs/README.md#governance-and-authority">Governance</a> |
    <a href="docs/setup/VALIDATION.md">Validation</a> |
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

## AI can generate fast. Building well still requires structure.

Orchestra coordinates AI-assisted software work across specialist responsibilities, governance, validation, evidence, and human approval boundaries.

It is **not an AI model**. Models generate and review work. Orchestra decides how permitted work is routed, sequenced, constrained, validated, recorded, and handed to the next responsible boundary.

> **Core rule:** routing, tool access, validation success, and mergeability are not authority.

## Core capabilities

| Capability | What it does | Go deeper |
| --- | --- | --- |
| **Specialist orchestration** | Routes work to focused architecture, implementation, security, UI/UX, database, QA, documentation, governance, and coordination roles. | [Skills & Routing](docs/README.md#specialists-routing-and-coordination) |
| **Governed execution** | Keeps authority, capabilities, governance, human gates, and repository policy separate and explicit. | [Governance & Authority](docs/README.md#governance-and-authority) |
| **Cross-domain coordination** | Sequences specialist work, detects contradictions, and re-enters the correct owner when assumptions become stale. | [Coordination](docs/README.md#specialists-routing-and-coordination) |
| **Validation & evidence** | Uses deterministic checks, exact-head evidence, cross-platform validation, and fail-closed transition rules. | [Validation & Evidence](docs/README.md#validation-evidence-and-continuity) |
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

## Get started

**Codex:** add this repository as a Marketplace source, install Orchestra, then invoke `@Orchestra`.

**Antigravity:**

```sh
agy plugin install https://github.com/Baelfyre/Orchestra
```

**Other hosts and local setups:** see the [Installation Guide](docs/setup/INSTALLATION.md) and [Compatibility Guide](docs/setup/COMPATIBILITY.md).

Repository package surfaces are prepared for **v1.6.0**. The current public GitHub Release remains **v1.5.0** until the separately governed publication gate creates and verifies the `v1.6.0` tag and release.

## Explore the framework

Start with the [Documentation Map](docs/README.md) for architecture, specialists, governance, validation, hosts, MCP, knowledge, provenance, releases, and historical design records.

Developers extending Orchestra should use the [Developer Portal](docs/developer/README.md), which indexes the stabilized Adapter SDK, PRAP certification, host, specialist, governance, and validation contracts.

## Machine-readable reference

AI systems should start with [`README.json`](README.json), then follow its ordered references into `machine/` contracts and JSON Schemas.

Orchestra uses a hybrid representation policy:

- **Markdown** for human explanation, rationale, examples, and specialist guidance.
- **JSON** for canonical structured machine state, contracts, indexes, receipts, and evidence.
- **JSON Schema** for deterministic validation.
- **TOON** only as a derived, validated, non-authoritative model-context projection when it provides measured context benefit.

When prose and a machine contract disagree on an exact deterministic fact, use the machine contract and treat the mismatch as documentation drift.

---

**License:** [MIT](LICENSE) | **Changelog:** [CHANGELOG.md](CHANGELOG.md) | **Security:** [SECURITY.md](SECURITY.md)
