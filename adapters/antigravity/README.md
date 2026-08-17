# Antigravity Adapter

Antigravity usage depends on the local skill or plugin support available in the installed environment. This adapter does not claim automatic marketplace discovery or installed-host mutation.

## Host update planning

Antigravity is a supported Host Update maturity target. Generate the deterministic read-only plan with:

```text
python scripts/host_update.py --host antigravity --json
```

The plan may describe the existing fast-forward repository update and post-update validation path, but it never reloads, refreshes, or reinstalls the active Antigravity integration. Installed-host mutation requires separate explicit authorization. See `docs/setup/HOST_UPDATES.md`.

See [install-guide.md](install-guide.md) and [agent-instructions.template.md](agent-instructions.template.md).
