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
    <img src="https://img.shields.io/badge/release-v1.11.0-blue" alt="Latest release v1.11.0" />
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

## Use Orchestra in 60 seconds

You do not need to learn Orchestra's specialists, governance system, or internal assurance mechanisms before using it.

After installing Orchestra, start with:

```text
@Orchestra
```

Then describe the outcome you want and any important limits or permissions.

```text
@Orchestra

Review this repository, find the cause of the failing tests,
fix the problem, and validate the result.

You may edit files and run tests.
Do not merge anything.
```

Orchestra determines the smallest useful workflow for the task. You normally do not need to choose specialists yourself.

A useful rule of thumb is:

```text
Start with @Orchestra.
Describe the result you want.
State important limits or permissions.
Let Orchestra determine the workflow.
```

## How Orchestra works for you

```text
You describe the task
        ↓
Orchestra interprets the goal, scope, and authority
        ↓
Conductor chooses the smallest useful specialist route
        ↓
The appropriate specialists perform bounded work
        ↓
Orchestra validates the result
        ↓
Is additional human authority required?
       ↙                     ↘
     No                       Yes
      ↓                        ↓
Continue within             Stop and
approved scope              ask you
       ↘                     ↙
        Result + evidence
        + next action
```

### 1. Describe the outcome

Tell Orchestra what you want accomplished instead of trying to design the internal workflow yourself.

For example:

```text
@Orchestra

Add authentication to this application.
Keep the existing architecture where possible.
Run the relevant tests.
Prepare the changes on a branch, but do not merge.
```

For review-only work:

```text
@Orchestra

Review this pull request for architecture, security,
and test coverage. Do not modify the repository.
```

For investigation-first work:

```text
@Orchestra

Investigate why this application became slower after
the latest change. Find the root cause first.
Do not modify anything until the cause is identified.
```

### 2. Let Conductor choose the route

Conductor is Orchestra's coordinator. It decides whether a request needs one specialist, several cooperating specialists, validation only, investigation before implementation, or a human decision before work can continue.

Simple tasks should stay simple. Orchestra does not need to activate every specialist for every request.

Advanced users can invoke a specific specialist directly when they already know what they need, but new users should normally start with `@Orchestra`.

### 3. Specialists perform bounded work

Different specialists own responsibilities such as architecture, implementation, UI and UX, databases, security, testing and QA, documentation, governance, and workflow continuity.

Orchestra coordinates these responsibilities so that one part of the work does not silently invalidate another. Normal users do not need to manage these handoffs manually.

### 4. Orchestra validates important results

Completing a change is not the same as proving that the change is correct.

Depending on the task, Orchestra may check tests, static analysis, security concerns, architecture boundaries, changed files, repository state, exact branch or commit identity, and evidence from earlier stages. Validation should scale with the risk and complexity of the task.

### 5. Orchestra respects your authority

The key distinction is simple:

```text
CAN_DO != MAY_DO
TESTS_PASS != MERGE_AUTHORITY
MERGEABLE != APPROVED
TOOL_ACCESS != PERMISSION
```

Capability is not authority.

Having access to a tool does not mean Orchestra has permission to use that tool for every action. For example, Orchestra may be technically capable of creating a commit or merging a pull request, but it should only do so when the authority you provided allows it.

Passing tests also does not automatically grant permission to merge, release, deploy, change policy, or perform another protected action.

### 6. Human-controlled boundaries stay human-controlled

When Orchestra reaches a decision that requires human authority, it should stop, preserve the relevant evidence, explain what is blocking progress, and ask for the required decision.

Examples can include changing protected governance policy, granting a new exception, expanding authority beyond the approved scope, performing a protected production action, or taking an action with significant unresolved risk.

The system should not change the rule blocking its own work simply so that the work can continue.

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

## Terms you may see

Most users do not need to configure or invoke these systems directly.

| Term | Plain-language meaning |
| --- | --- |
| **Conductor** | Orchestra's primary routing and coordination layer. New users normally start with `@Orchestra` and let Conductor choose the route. |
| **Arbiter** | The specialist responsible for workflow continuity, validation state, and governed transitions when work reaches an important boundary. |
| **PRAI** | **Post-Run Assurance Invariant.** An internal assurance mechanism that checks completed work and its evidence before certain workflow transitions are accepted. |
| **ADAPT-QA / AQ** | Orchestra's adaptive assurance and quality program. AQ phases are engineering and validation stages used to strengthen Orchestra, not normal user commands. |
| **Covenant** | An internal cross-governance synthesis that reconciles independent governance evidence. It provides evidence and does not independently grant authority. |

For implementation-level details, see the [Governance reference](docs/reference/governance/README.md), [Architecture reference](docs/reference/architecture/README.md), and [Validation documentation](docs/setup/VALIDATION.md).

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

The latest published release is **[v1.11.0: Adaptive Assurance and Governance Hardening](https://github.com/Baelfyre/Orchestra/releases/tag/v1.11.0)**.

v1.11.0 strengthens Orchestra's validation and governance system. It adds deeper post-run assurance, stronger protection against autonomous policy changes, cross-governance evidence synthesis, adversarial and high-risk assurance, and clearer human approval boundaries.

These mechanisms operate behind the normal user workflow above. Most users do not need to invoke AQ phases, PRAI, or Covenant directly.

<details>
<summary>Advanced v1.11 implementation and release identity</summary>

v1.11.0 packages the complete governed post-v1.10.0 development line through AQ14, including AQ1-AQ14 Adaptive Assurance, PRAI post-run assurance, Covenant cross-governance synthesis, Protected Governance Escalation, human-only whitelist authority, tree-attested promotion assurance, deterministic release-packaging classification, and the AQ7 tenant-administration parity reference slice.

The immutable release identity is canonical commit `72c2884a66bb0e0d0ff1e070e7cc1feccd968e35`, tree `e4072cff4de83efa1c1d2d495aa5c186a2469db4`, lightweight tag `v1.11.0`, and GitHub Release `387061978`.

AQ15 remains unregistered. AR-3 through AR-9 remain separate post-v1.11 work and are not authorized by publication. The release does not grant provider, telemetry, production, deployment, whitelist, protected-policy, or CritiQual CUD10 authority.

</details>

See:

- [Changelog](CHANGELOG.md)
- [Published v1.11.0 reference](docs/reference/releases/v1.11.0.md)
- [Preserved v1.11.0 candidate qualification record](docs/releases/v1.11.0-adaptive-assurance-governance-release-candidate.md)
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
