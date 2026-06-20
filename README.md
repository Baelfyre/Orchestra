<div align="center">
  <img src="assets/logo/orchestra-of-amalgamation.png" alt="Orchestra of Amalgamation" width="280" />
  <h1>Orchestra of Amalgamation</h1>
  <p>A Markdown-first suite of eight specialist AI instructions for routing, review, documentation, diagrams, databases, quality, security/privacy, and gated resilience testing.</p>
</div>

## What this repository is

The repository packages reusable instruction files and adapter guides. Amalgam Conductor selects the smallest useful specialist stack, assigns one owner per output, sequences dependent work, and marks risky actions that require approval.

## What this repository is not

- It is not a guaranteed native plugin for every AI tool.
- It does not contain project-specific instructions or private context.
- It does not grant authorization for production, destructive, or offensive testing.
- It does not bundle external plugins such as Ponytail or Caveman.

## Skills

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
    <td><b>Use for:</b> QA, tests, defects, verification, validation, regression and release readiness<br /><b>Not for:</b> Destructive pressure testing by default</td>
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

See [SKILL_INDEX.md](SKILL_INDEX.md) for activation levels and output details.

## Recommended routing flow

1. Use Amalgam Conductor when ownership or sequencing is unclear.
2. Route the primary artifact to one specialist.
3. Add another specialist only for a distinct required output.
4. Use Acme Overseer for normal quality evidence and Cipher Meister for normal security/privacy review.
5. Recommend Hidden Dagger only for an explicit or mature pre-production pressure-test need.
6. Invoke Hidden Dagger only after authorization, non-production isolation, scope, rollback, cleanup, and stop conditions are confirmed.

When the task is obvious, invoke the specialist directly.

## Installation summary

Clone or download this repository, then copy the required folders from `skills/` into the instruction or skill location supported by your AI environment. For Codex-compatible local skills, copy individual folders into your local Codex skills directory. See [INSTALLATION.md](INSTALLATION.md) and [adapters/](adapters/README.md).

## Compatibility

The guaranteed portable layer is Markdown. Codex may support direct local skill folders. VS Code AI tools, Antigravity, Claude Code, and local models may require manual context, workspace instructions, or retrieval configuration. This repository does not claim automatic discovery where it has not been configured. See [COMPATIBILITY.md](COMPATIBILITY.md).

## Git safety

Keep experimental agent files outside unrelated repositories. If local instruction files must live inside a project, use `.git/info/exclude` for machine-local exclusions. Use `.gitignore` only when the exclusion belongs to every clone. Check `git status` before staging.

## Test prompts

- Amalgam Conductor: `Use $amalgam-conductor to select the smallest skill stack for this task and explain the sequence.`
- Cloak Meister: `Use $cloak-meister to review this interface for task completion, accessibility, and responsive layout.`
- Scribe Meister: `Use $scribe-meister to audit this documentation against the supplied source files.`
- Meister Weaver: `Use $meister-weaver to review this sequence diagram against the supplied workflow.`
- Meister Chronicler: `Use $meister-chronicler to review this schema and migration for integrity and rollback risk.`
- Acme Overseer: `Use $acme-overseer to assess this test plan, regression evidence, and release readiness.`
- Cipher Meister: `Use $cipher-meister to review the supplied authentication, RBAC, secrets, and privacy evidence defensively.`
- Hidden Dagger: `Use $hidden-dagger to create a safety-gated negative-testing plan for this non-production system. Do not execute tests.`

## Validation

Run either structure validator, then the stale-reference check:

```powershell
./scripts/validate-structure.ps1
./scripts/check-stale-references.ps1
```

```sh
sh ./scripts/validate-structure.sh
sh ./scripts/check-stale-references.sh
```

See [VALIDATION.md](VALIDATION.md) for the complete checklist.

## Contributing and roadmap

Read [CONTRIBUTING.md](CONTRIBUTING.md), [ROADMAP.md](ROADMAP.md), and [CHANGELOG.md](CHANGELOG.md).

## License

Licensed under the MIT License. See [LICENSE](LICENSE).

## External plugin disclaimer

Ponytail and Caveman are external tools, are not part of this repository, and must be installed separately from their official sources if desired. This repository adopts only the general principle of concise, high-signal, low-filler review behavior.
