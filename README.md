<div align="center">
  <img src="assets/logo/orchestra-of-amalgamation.png" alt="Amalgamatic Orchestra" width="280" />
  <h1>Amalgam Conductor</h1>
  <p>An installable AI workflow plugin for routing complex software tasks through focused specialist skills.</p>
</div>

## About

Amalgam Conductor is an installable AI workflow plugin built on the Amalgamatic Orchestra framework. It routes complex software tasks through focused specialist skills while preserving token efficiency, safety gates, and evidence-based review.

The framework remains Markdown-first so the core instructions can stay reusable across tools. The plugin layer provides clean commands and skill discovery for supported plugin environments while the underlying Markdown files remain portable.

The plugin uses the existing Amalgam Conductor icon at `assets/icons/amalgam-conductor.png`. The broader framework logo remains `assets/logo/orchestra-of-amalgamation.png`.

## What this repository is

## Codex compatibility

The canonical Amalgamatic Orchestra skills remain metadata-rich. Codex may require simplified frontmatter.
Use `adapters/codex/` for Codex-compatible export and installation.
Repository-local `.agents/skills` installation is strongly recommended instead of modifying your global `.codex` directory.

## Getting Started

Amalgamatic Orchestra uses reusable Markdown instruction files to guide AI assistants through specialized project tasks while keeping responsibilities clear and separated.

The goal is to make AI-assisted project work easier to route, review, and verify. Instead of relying on one broad prompt for every task, this framework coordinates focused specialists. For example, one specialist handles UI/UX review, another handles documentation, another handles database review, and another handles QA readiness.

The main coordinating skill is **Amalgam Conductor**. It helps decide which specialist skill should be used, when multiple skills are needed, and what order they should be used in.

## What this repository is not

This repository is not a complete AI tool by itself. It does not automatically install into every IDE, chatbot, or local model environment.

It also does not include private project context, external plugins, or permission to perform risky actions. Any destructive, production-level, offensive, or pressure-testing activity must be reviewed and approved separately.

## Skills included

<table>
  <tr>
    <td align="center" width="100"><img src="assets/icons/amalgam-conductor.png" alt="Amalgam Conductor" width="80" /><br /><b><a href="skills/amalgam-conductor/SKILL.md">Amalgam Conductor</a></b></td>
    <td><b>Use for:</b> Routing, sequencing, overlap control, and token efficiency<br /><b>Not for:</b> Replacing domain specialists</td>
  </tr>
  <tr>
    <td align="center" width="100"><img src="assets/icons/cloak-meister.png" alt="Cloak Meister" width="80" /><br /><b><a href="skills/cloak-meister/SKILL.md">Cloak Meister</a></b></td>
    <td><b>Use for:</b> UI/UX, accessibility, frontend layout, dashboards, forms, responsiveness<br /><b>Not for:</b> Database or system-diagram ownership</td>
  </tr>
  <tr>
    <td align="center" width="100"><img src="assets/icons/scribe-meister.png" alt="Scribe Meister" width="80" /><br /><b><a href="skills/scribe-meister/SKILL.md">Scribe Meister</a></b></td>
    <td><b>Use for:</b> Documentation audits, reports, README files, readiness documents, technical writing<br /><b>Not for:</b> Inventing technical facts</td>
  </tr>
  <tr>
    <td align="center" width="100"><img src="assets/icons/meister-weaver.png" alt="Meister Weaver" width="80" /><br /><b><a href="skills/meister-weaver/SKILL.md">Meister Weaver</a></b></td>
    <td><b>Use for:</b> UML, use cases, ERD visuals, architecture, workflow, and process diagrams<br /><b>Not for:</b> Database semantics without a database source</td>
  </tr>
  <tr>
    <td align="center" width="100"><img src="assets/icons/meister-chronicler.png" alt="Meister Chronicler" width="80" /><br /><b><a href="skills/meister-chronicler/SKILL.md">Meister Chronicler</a></b></td>
    <td><b>Use for:</b> Schema, constraints, SQL, seeds, migrations, dictionaries, database documentation<br /><b>Not for:</b> UI review</td>
  </tr>
  <tr>
    <td align="center" width="100"><img src="assets/icons/acme-overseer.png" alt="Acme Overseer" width="80" /><br /><b><a href="skills/acme-overseer/SKILL.md">Acme Overseer</a></b></td>
    <td><b>Use for:</b> QA, tests, defects, verification, validation, regression, and release readiness<br /><b>Not for:</b> Destructive pressure testing by default</td>
  </tr>
  <tr>
    <td align="center" width="100"><img src="assets/icons/cipher-meister.png" alt="Cipher Meister" width="80" /><br /><b><a href="skills/cipher-meister/SKILL.md">Cipher Meister</a></b></td>
    <td><b>Use for:</b> Security/privacy evidence, auth, RBAC, secrets, sensitive data, dependencies, remediation<br /><b>Not for:</b> Offensive or destructive testing</td>
  </tr>
  <tr>
    <td align="center" width="100"><img src="assets/icons/hidden-dagger.png" alt="Hidden Dagger" width="80" /><br /><b><a href="skills/hidden-dagger/SKILL.md">Hidden Dagger</a></b></td>
    <td><b>Use for:</b> Approved destructive, negative, fuzz, boundary, failure-mode, guardrail, and resilience testing<br /><b>Not for:</b> Automatic, production, or unauthorized testing</td>
  </tr>
  <tr>
    <td align="center" width="100"><img src="assets/icons/clockwork-meister.png" alt="Clockwork Meister" width="80" /><br /><b><a href="skills/clockwork-meister/SKILL.md">Clockwork Meister</a></b></td>
    <td><b>Use for:</b> OOP architecture, layered architecture, system design, structural refactoring, SOLID principles<br /><b>Not for:</b> UI layouts, security boundaries, or writing documentation</td>
  </tr>
</table>

See [SKILL_INDEX.md](SKILL_INDEX.md) for the full skill index, activation level, and expected output for each skill.

## Recommended routing flow

Use this flow when deciding which skill to apply:

1. Start with **Amalgam Conductor** if the task is broad, unclear, or involves multiple types of work.
2. Route the main task to one primary specialist.
3. Add another specialist only when there is a separate required output.
4. Use **Acme Overseer** for normal QA, validation, regression, and release-readiness review.
5. Use **Cipher Meister** for normal defensive security and privacy review.
6. Use **Hidden Dagger** only when the task is explicitly authorized, scoped, isolated from production, and includes rollback, cleanup, and stop conditions.

If the task is obvious, use the correct specialist directly.

## Installation

Amalgam Conductor can be installed directly as a plugin:

```sh
agy plugin install https://github.com/Baelfyre/amalgam-conductor
```


You can also use the framework manually by copying the skill folders from `skills/` into your AI environment's instruction directory.

See [INSTALLATION.md](INSTALLATION.md) and [adapters/](adapters/README.md) for more details.

## Plugin support

Amalgam Conductor is an installable plugin layer over the Amalgamatic Orchestra framework. It provides clean top-level commands to route tasks.

Manifest consistency can be checked with:
`powershell -ExecutionPolicy Bypass -File .\scripts\validate-manifest.ps1`
## Compatibility

This repository is designed to be Markdown-first. That means the core instructions are plain Markdown files that can be adapted across different AI coding environments.

Supported or adaptable workflows may include:

- Codex-compatible local skill folders
- VS Code AI workspace instructions or prompt references
- Antigravity local skill references or adapted Markdown
- Claude Code using the supplied CLAUDE template
- Local AI systems using `SKILL.md` files through prompt context or retrieval

This repository does not guarantee automatic discovery or native integration in every IDE, model runtime, or AI assistant. Tool-specific behavior depends on the current configuration and capabilities of that environment.

See [COMPATIBILITY.md](COMPATIBILITY.md) for more details.

## Git safety

Keep experimental AI instruction files separate from unrelated repositories.

If local instruction files must live inside a project, use `.git/info/exclude` for machine-local exclusions. Use `.gitignore` only when the exclusion should apply to every clone of the repository.
