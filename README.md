<div align="center">
  <img src="assets/logo/orchestra-of-amalgamation.png" alt="Amalgamatic Orchestra" width="280" />
  <h1>Amalgamatic Orchestra</h1>
  <p>A portable Markdown-based framework for coordinating specialized AI workflows across review, documentation, diagrams, database work, QA, security, and gated resilience testing.</p>
</div>

## About

Amalgamatic Orchestra is a portable AI workflow framework for coordinating specialist instruction files across different AI coding and review environments. It is designed to help an AI assistant route work to the right specialist, keep outputs focused, and preserve clear ownership across documentation, UI/UX, diagrams, database work, QA, security, and gated resilience testing.

The framework is Markdown-first so the core instructions can remain reusable across tools. Tool-specific adapters or plugins can be added later, but the repository does not depend on a single AI platform or plugin system.

## What this repository is

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

## Installation summary

Clone or download this repository.

```sh
git clone https://github.com/Baelfyre/Amalgamatic-Orchestra.git
cd Amalgamatic-Orchestra
```

Then copy only the skill folders you need from `skills/` into the instruction or skill location supported by your AI environment.

For Codex-compatible local skills, copy the selected skill folders into the configured local Codex skills directory.

For tools that do not support local skill folders directly, use the Markdown files as workspace instructions, prompt references, or local context.

See [INSTALLATION.md](INSTALLATION.md) and [adapters/](adapters/README.md) for more details.

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

Before staging or committing changes, always check:

```sh
git status
```

## Test prompts

Use these prompts to check whether each skill is being interpreted correctly:

- Amalgam Conductor: `Use $amalgam-conductor to select the smallest skill stack for this task and explain the sequence.`
- Cloak Meister: `Use $cloak-meister to review this interface for task completion, accessibility, and responsive layout.`
- Scribe Meister: `Use $scribe-meister to audit this documentation against the supplied source files.`
- Meister Weaver: `Use $meister-weaver to review this sequence diagram against the supplied workflow.`
- Meister Chronicler: `Use $meister-chronicler to review this schema and migration for integrity and rollback risk.`
- Acme Overseer: `Use $acme-overseer to assess this test plan, regression evidence, and release readiness.`
- Cipher Meister: `Use $cipher-meister to review the supplied authentication, RBAC, secrets, and privacy evidence defensively.`
- Hidden Dagger: `Use $hidden-dagger to create a safety-gated negative-testing plan for this non-production system. Do not execute tests.`

## Validation

Run the structure validator, then run the stale-reference check.

PowerShell:

```powershell
./scripts/validate-structure.ps1
./scripts/check-stale-references.ps1
```

Shell:

```sh
sh ./scripts/validate-structure.sh
sh ./scripts/check-stale-references.sh
```

See [VALIDATION.md](VALIDATION.md) for the complete checklist.

## Contributing and roadmap

Read the following files before proposing changes:

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [ROADMAP.md](ROADMAP.md)
- [CHANGELOG.md](CHANGELOG.md)

## License

Licensed under the MIT License. See [LICENSE](LICENSE).

## External inspiration and plugin disclaimer

[Ponytail](https://github.com/DietrichGebert/ponytail) and [Caveman](https://github.com/juliusbrussee/caveman) are external tools. They are not part of this repository and must be installed separately from their official sources if desired.

This repository is inspired only by the general idea of clear, focused, and low-filler review behavior. It does not bundle, copy, vendor, or install those external tools.
