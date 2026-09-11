<div align="center">
  <img src="./assets/readme/orchestra-governance-banner.svg" alt="Orchestra banner showing coordinated software responsibilities" width="100%" />

  <p><strong>Governed orchestration for AI-assisted software development.</strong></p>

  <p>
    <a href="docs/setup/INSTALLATION.md">Install</a> |
    <a href="docs/reference/README.md">Documentation</a> |
    <a href="docs/developer/README.md">Developer Portal</a> |
    <a href="docs/governance/README.md">Governance</a> |
    <a href="CHANGELOG.md">Changelog</a>
  </p>

  <p>
    <img src="https://img.shields.io/badge/release-v1.10.0-blue" alt="Latest release v1.10.0" />
    <img src="https://img.shields.io/badge/candidate-v1.11.0-orange" alt="Release candidate v1.11.0" />
    <a href="https://github.com/Baelfyre/Orchestra/actions/workflows/validate.yml">
      <img src="https://github.com/Baelfyre/Orchestra/actions/workflows/validate.yml/badge.svg" alt="Repository validation status" />
    </a>
    <img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT license" />
    <a href="https://buymeacoffee.com/baelfyre">
      <img src="https://img.shields.io/badge/Buy%20Me%20a%20Coffee-FFDD00?style=flat-square&logo=buymeacoffee&logoColor=000000" alt="Buy Me a Coffee" />
    </a>
  </p>
</div>

---

## What is Orchestra?

Orchestra is a governance and orchestration framework for AI-assisted software development.

It helps an AI coding workflow behave more like a coordinated engineering process by routing work to focused specialists, keeping authority boundaries explicit, validating important transitions, and preserving enough evidence to continue safely across handoffs.

Orchestra is **not an AI model** and it does not replace your IDE, coding agent, or engineering judgment. It sits around those tools and helps coordinate how work moves from intent to implementation to validation.

## Why use it?

AI can generate code quickly, but larger projects can still suffer from:

- context drift between tasks or sessions;
- architecture, security, UI, database, and implementation decisions conflicting with each other;
- agents doing work outside the authority actually granted by the user;
- successful tests being mistaken for permission to merge, deploy, or change policy;
- repeated re-analysis because earlier evidence was not carried forward clearly.

Orchestra is designed to reduce those problems without turning every task into a large multi-agent workflow.

## How it works

```text
User request
    ↓
Authority and project context
    ↓
Conductor chooses the smallest useful route
    ↓
Specialist work
    ↓
Validation and evidence
    ↓
Arbiter / human boundary when required
    ↓
Next bounded action
```

The key distinction is simple:

```text
CAN_DO != MAY_DO
TESTS_PASS != MERGE_AUTHORITY
MERGEABLE != APPROVED
TOOL_ACCESS != PERMISSION
```

Capability is not authority.

## What Orchestra provides

| Area | What Orchestra adds |
| --- | --- |
| **Specialist routing** | Focused ownership for architecture, implementation, security, UI/UX, persistence, QA, documentation, governance, and coordination. |
| **Governed execution** | Clear separation between what a tool can do and what the user has actually authorized. |
| **Cross-specialist coordination** | Re-entry and handoff rules when a decision in one domain invalidates another. |
| **UI fidelity** | Preserves accepted design complexity, reusable project-native components, responsive intent, and validation boundaries. |
| **Validation and evidence** | Deterministic checks, exact-head evidence, cross-platform validation, and fail-closed transitions where appropriate. |
| **Continuity** | Machine-readable state, receipts, contracts, and bounded adaptive memory to reduce repeated reconstruction. |
| **Portable integration** | Adapter and MCP surfaces that allow Orchestra to work across supported AI coding hosts without transferring authority to the host. |

For the full capability map, see the [Orchestra Reference](docs/reference/README.md).

## Quick start

### Codex

Add this repository as a Marketplace source, install Orchestra, then invoke:

```text
@Orchestra
```

### Claude

#### Claude app / desktop plugin marketplace

1. Open **Customize > Plugins**.
2. Under **Personal plugins**, select **+ > Add marketplace > Add from a repository**.
3. Paste:

```text
https://github.com/Baelfyre/Orchestra
```

4. Install the **orchestra** plugin.

If your Claude client exposes plugin management under **Settings > Extensions > Plugins**, choose **Add Marketplace** there and use the same repository URL.

#### Claude Code

From a Claude Code session:

```text
/plugin marketplace add Baelfyre/Orchestra
/plugin install orchestra@orchestra
```

If Claude reports that plugin changes require a reload, run `/reload-plugins`.

### Antigravity

```sh
agy plugin install https://github.com/Baelfyre/Orchestra
```

### Other hosts

See the [Getting Started reference](docs/reference/getting-started/README.md), [Installation Guide](docs/setup/INSTALLATION.md), and [Compatibility Guide](docs/setup/COMPATIBILITY.md).

## MCP

Orchestra can expose a bounded tool surface to an MCP-compatible client while preserving the same runtime and governance boundaries.

### Codex MCP

```sh
python scripts/mcp_server.py --adapter codex
```

### Claude Code MCP

Orchestra already registers `claude-code` as a runtime adapter, so the same local stdio server can be launched with the Claude adapter:

```sh
python scripts/mcp_server.py --adapter claude-code
```

To register the local server with Claude Code, replace `<path-to-Orchestra>` with your local clone path:

```sh
claude mcp add --scope user --transport stdio orchestra -- python "<path-to-Orchestra>/scripts/mcp_server.py" --adapter claude-code
claude mcp get orchestra
```

Restart Claude Code after registration, then run:

```text
/mcp
```

The Claude MCP path is **prepared at the adapter and stdio-transport level**. The repository does not yet record an installed-host Claude MCP end-to-end proof equivalent to the existing Codex validation, so do not classify Claude MCP host execution as verified until that test is completed.

The Claude marketplace plugin also does not currently auto-register Orchestra MCP because the plugin root does not ship a `.mcp.json`; MCP registration is a separate explicit setup step.

MCP is transport, not authority. Discovery or tool access does not grant permission to perform protected actions.

See [MCP stdio governed tool transport](docs/developer/MCP_STDIO_TRANSPORT.md).

## Current release

The latest published release is **[v1.10.0: Universal Adaptive Integration](https://github.com/Baelfyre/Orchestra/releases/tag/v1.10.0)**.

v1.10.0 adds evidence-bounded Universal Adaptive Integration, deterministic transport and projection contracts, cross-host conformance, and verified GitHub Copilot `/conductor` support while preserving existing governance and authority boundaries.

Conductor remains the sole internal specialist router. Clear specialist ownership can use a lightweight direct route, but it never bypasses Conductor. Copilot Auto mode did not expose its provider/model identity, so no provider/model profile is admitted.

### v1.11.0 candidate

**v1.11.0: Adaptive Assurance and Governance Hardening** is prepared and currently in governed qualification. It packages the complete canonical post-v1.10.0 change set through AQ14, including AQ1–AQ14 Adaptive Assurance, PRAI post-run assurance, Covenant cross-governance synthesis, Protected Governance Escalation, human-only whitelist authority, tree-attested promotion assurance, and the AQ7 tenant-administration parity reference slice.

AQ15 is not a defined or registered phase. AR-3 through AR-9 remain deferred until v1.11.0 is published and reconciled. The candidate does not grant provider, telemetry, production, deployment, whitelist, protected-policy, or CritiQual CUD10 authority.

See:

- [Changelog](CHANGELOG.md)
- [Published v1.10.0 reference](docs/reference/releases/v1.10.0.md)
- [v1.11.0 candidate](docs/releases/v1.11.0-adaptive-assurance-governance-release-candidate.md)
- [v1.11.0 readiness evidence](docs/validation/V1_11_0_RELEASE_READINESS_EVIDENCE.md)
- [Maturity](docs/MATURITY.md)
- [Validation documentation](docs/setup/VALIDATION.md)

## Documentation

Use the README as the entry point, then go deeper only when needed:

- [Orchestra Reference](docs/reference/README.md)
- [Getting started](docs/reference/getting-started/README.md)
- [Governance](docs/reference/governance/README.md)
- [Developer Portal](docs/developer/README.md)
- [Architecture](docs/reference/architecture/README.md)
- [Integrations](docs/reference/integrations/README.md)
- [Specialists](docs/reference/specialists/README.md)
- [Releases](docs/reference/releases/README.md)
- [Detailed Documentation Map](docs/README.md)
- [Third-party provenance](docs/THIRD_PARTY_PROVENANCE.md)

For AI systems and exact structured project state, start with [`README.json`](README.json); for human navigation, start with the [Orchestra Reference](docs/reference/README.md).

## Support

If Orchestra is useful to you and you want to support its continued development:

<div align="center">
  <a href="https://buymeacoffee.com/baelfyre">
    <img src="https://img.shields.io/badge/Buy%20Me%20a%20Coffee-FFDD00?style=for-the-badge&logo=buymeacoffee&logoColor=000000" alt="Buy Me a Coffee" />
  </a>
</div>

---
