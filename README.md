<div align="center">
  <img src="./assets/readme/orchestra-governance-banner.svg" alt="Orchestra governance and specialist orchestration" width="100%" />
  <p><strong>Governed orchestration for AI-assisted software development.</strong></p>
  <p><a href="docs/setup/INSTALLATION.md">Install</a> | <a href="docs/reference/README.md">Documentation</a> | <a href="docs/reference/specialists/README.md">Specialists</a> | <a href="docs/governance/README.md">Governance</a> | <a href="CHANGELOG.md">Changelog</a></p>
  <p><a href="https://github.com/Baelfyre/Orchestra/releases/tag/v1.11.0"><img src="https://img.shields.io/badge/published-v1.11.0-blue" alt="Published release v1.11.0" /></a> <a href="https://github.com/Baelfyre/Orchestra/actions/workflows/validate.yml"><img src="https://github.com/Baelfyre/Orchestra/actions/workflows/validate.yml/badge.svg" alt="Validation status" /></a> <img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT license" /></p>
</div>

## What is Orchestra?

Orchestra coordinates AI-assisted development across specialists for architecture, implementation, UI/UX, data, security, testing, documentation, and governance. It routes the task, preserves evidence, validates results, and respects human authority.

Orchestra is **not an AI model**. It works around compatible coding hosts and does not replace engineering judgment.

## Quick start

Install through the [host installation guide](docs/setup/INSTALLATION.md). Then describe the result you want and what Orchestra may do:

```text
@Orchestra

Review this repository, identify the failing tests,
fix the issue, and run relevant checks.
You may edit files and prepare a PR. Do not merge or deploy.
```

Conductor chooses the smallest useful specialist route. [Compatibility](docs/setup/COMPATIBILITY.md) and [getting started](docs/reference/getting-started/README.md) explain supported hosts.

## Capabilities

| Area | What it provides | Important limit |
| --- | --- | --- |
| **Specialist coordination** | Focused roles, bounded execution, and handoffs | Tool access never creates permission |
| **Assurance and governance** | Evidence-based validation and human-controlled boundaries | Passing tests never authorizes a merge |
| **Adaptive memory** | Local observations, opt-in read-only context, and shadow learning | No automatic authority, preference promotion, or private cloud sync |
| **Adaptive discovery** | Scoped capability-memory contracts and offline planning | Live host discovery and trusted private-memory writes are not activated |
| **JEV advisory** | Optional TypeSafe System One advisory components | Live TypeSafe/BYOK onboarding, R3-A host trust, and production wiring remain unqualified |
| **Scribe documentation** | Requirements, as-built reconstruction, drift reconciliation, and an optional six-dimension blueprint | Scribe does not approve technical decisions or impose six mandatory files |

These are **source and maturity claims**, not a guarantee that each capability is enabled in every host or in the latest published release.

## JEV and local API keys

JEV supports non-binding engineering advice when independently reviewed alternatives exist. The v1.12 offline pilot provides a repeatable 14-scenario pytest replay with explicitly labeled synthetic responses and evidence-gap recording. It makes no TypeSafe calls or actual JEV inference. The original V6 packet and source artifacts are absent, so replayed V6 findings remain **UNVERIFIED**. Live TypeSafe integration, R3-A host trust, and production wiring remain unqualified. The TypeSafe adapter and offline data-minimization components exist, but there is **no verified general-purpose end-user BYOK activation flow**. Ordinary Orchestra use needs no JEV key. Never paste credentials into prompts or tracked project files.

Read the [offline pilot instructions](docs/setup/JEV_OFFLINE_PILOT.md), [JEV local API setup and limitations](docs/setup/JEV_LOCAL_API.md), and the [decision hierarchy](docs/architecture/EVIDENCE_GATED_DECISION_HIERARCHY.md).

## Adaptive memory

**A1** maintains scoped machine-local observations. **A2** can provide opt-in, read-only context to an already-selected specialist. **A3** compares inferred tendencies in shadow mode; they cannot silently change execution. Portable memory supports backend contracts, not built-in synchronization. D3B capability memory/discovery remains offline and does not authenticate a live host.

Read [adaptive memory setup and limitations](docs/setup/ADAPTIVE_MEMORY_GUIDE.md) and [portable memory](docs/architecture/PORTABLE_ADAPTIVE_MEMORY.md).

## Scribe and the pre-development blueprint

Scribe operates in **SPEC_TO_SYSTEM**, **SYSTEM_TO_DOCS**, and **RECONCILE** modes. It can organize sources and identify documentation gaps; relevant specialists retain ownership of architecture, UI, persistence, security, validation, and governance decisions.

The six coverage areas are **product requirements, technical requirements, application flow, design brief, backend/data schema, and implementation plan**. They are *not six mandatory documents*. Reuse existing artifacts, label missing evidence, and preserve unresolved decisions.

This blueprint guidance is **merged to `main`**, but post-v1.11.0 work is not necessarily in the latest published release. Read the [blueprint guide](docs/project/PRE_DEVELOPMENT_BLUEPRINT_GUIDE.md), [Scribe skill](skills/scribe/SKILL.md), and [documentation applicability rules](docs/project/DOCUMENTATION_LIFECYCLE_APPLICABILITY.md).

## Permissions and privacy

```text
TOOL_ACCESS != USER_AUTHORIZATION
TESTS_PASS != MERGE_APPROVAL
JEV_ADVICE != EXECUTION_AUTHORITY
MEMORY_CONFIDENCE != PERMISSION
```

No model output, learned preference, documentation matrix, or installed plugin may bypass protected decisions, transmit sensitive data without proper authority, or silently change policy.

## More documentation

[Installation](docs/setup/INSTALLATION.md) · [MCP](docs/developer/MCP_STDIO_TRANSPORT.md) · [Architecture](docs/reference/architecture/README.md) · [Governance](docs/reference/governance/README.md) · [Developer portal](docs/developer/README.md) · [Detailed documentation map](docs/README.md) · [Machine index](README.json)

## Published release

The latest public release is **[v1.11.0](https://github.com/Baelfyre/Orchestra/releases/tag/v1.11.0)**. The development branch contains later work, which remains unreleased until the complete version-specific qualification and publication process is completed. See [releases](docs/reference/releases/README.md) and [changelog](CHANGELOG.md).

## Support

[Support development](https://buymeacoffee.com/baelfyre) · [MIT License](LICENSE)
