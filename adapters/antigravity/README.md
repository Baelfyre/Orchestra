# Kontrolled Kaos on Antigravity

The repository packages Antigravity metadata in `.antigravity-plugin/plugin.json` and exposes the product alias as `/kaos`. The alias reads and follows the existing `skills/conductor/SKILL.md`; it does not add a dispatcher or change authority.

Validate the package locally with `agy plugin validate . --json`. It exits successfully and discovers 15 skills. Strict mode currently exits non-zero with warnings because Antigravity ignores the repository-root `AGENTS.md`, `commands/`, and `plugin.json` in favor of its dedicated manifest. Do not duplicate those files into Antigravity rules or commands just to silence the warnings. Package validation does not prove interactive behavior in an installed session. Do not install or publish the plugin as part of repository validation.

## Host update planning

Antigravity is a supported Host Update maturity target. Generate the deterministic read-only plan with:

```text
python scripts/host_update.py --host antigravity --json
```

The plan may describe the existing fast-forward repository update and post-update validation path, but it never reloads, refreshes, or reinstalls the active Antigravity integration. Installed-host mutation requires separate explicit authorization. See `docs/setup/HOST_UPDATES.md`.

See [install-guide.md](install-guide.md) and [agent-instructions.template.md](agent-instructions.template.md).
