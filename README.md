<div align="center">
  <img src="./assets/readme/orchestra-governance-banner.svg" alt="Orchestra banner showing coordinated software responsibilities" width="100%" />

  <p><strong>Governed orchestration for AI-assisted software development.</strong></p>

  <p>
    <a href="docs/setup/INSTALLATION.md">Install</a> |
    <a href="docs/README.md">Documentation</a> |
    <a href="docs/developer/README.md">Developer Portal</a> |
    <a href="docs/governance/README.md">Governance</a> |
    <a href="CHANGELOG.md">Changelog</a>
  </p>

  <p>
    <img src="https://img.shields.io/badge/release-v1.9.0-blue" alt="Latest release v1.9.0" />
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

For the full capability map, see the [Documentation Map](docs/README.md).

## Quick start

### Codex

Add this repository as a Marketplace source, install Orchestra, then invoke:

```text
@Orchestra
```

### Antigravity

```sh
agy plugin install https://github.com/Baelfyre/Orchestra
```

### Other hosts

See the [Installation Guide](docs/setup/INSTALLATION.md) and [Compatibility Guide](docs/setup/COMPATIBILITY.md).

## MCP

Orchestra can expose a bounded tool surface to an MCP-compatible client while preserving the same runtime and governance boundaries.

```sh
python scripts/mcp_server.py --adapter codex
```

MCP is transport, not authority. Discovery or tool access does not grant permission to perform protected actions.

See [MCP stdio governed tool transport](docs/developer/MCP_STDIO_TRANSPORT.md).

## Current release

The latest published release is **[v1.9.0: UI Execution Fidelity](https://github.com/Baelfyre/Orchestra/releases/tag/v1.9.0)**.

v1.9.0 completes the current UI execution fidelity program while preserving explicit evidence limits where the project did not establish stronger claims. Detailed release evidence, maturity records, and historical validation remain in the documentation instead of being duplicated here.

See:

- [Changelog](CHANGELOG.md)
- [Maturity](docs/MATURITY.md)
- [Validation documentation](docs/setup/VALIDATION.md)

## Documentation

Use the README as the entry point, then go deeper only when needed:

- [Documentation Map](docs/README.md)
- [Installation](docs/setup/INSTALLATION.md)
- [Governance](docs/governance/README.md)
- [Developer Portal](docs/developer/README.md)
- [Architecture](docs/architecture/)
- [Routing and coordination](docs/routing/)
- [Validation](docs/setup/VALIDATION.md)
- [Third-party provenance](docs/THIRD_PARTY_PROVENANCE.md)

For AI systems and exact structured project state, start with [`README.json`](README.json).

## Support

If Orchestra is useful to you and you want to support its continued development:

<div align="center">
  <a href="https://buymeacoffee.com/baelfyre">
    <img src="https://img.shields.io/badge/Buy%20Me%20a%20Coffee-FFDD00?style=for-the-badge&logo=buymeacoffee&logoColor=000000" alt="Buy Me a Coffee" />
  </a>
</div>

---

**License:** [MIT](LICENSE) | **Security:** [SECURITY.md](SECURITY.md) | **Changelog:** [CHANGELOG.md](CHANGELOG.md)
