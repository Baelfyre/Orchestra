# Host Update Contract

Orchestra's host update surface is a read-only planning contract. It reports host maturity, update mechanism, deterministic instructions, post-update validation, and recovery guidance. It does not itself authorize or mutate an installed host integration.

Canonical machine source:

`machine/hosts/update-contract.v1.json`

Schema:

`machine/schemas/host-update-contract.schema.json`

Planner:

`python scripts/host_update.py --host <host> --json`

## Maturity boundary

| Host | Maturity | Planner behavior | Installed-host mutation |
| --- | --- | --- | --- |
| Codex | Supported | Git fast-forward plus manual host-refresh instructions | Requires separate explicit authorization |
| Antigravity | Supported | Git fast-forward plus manual host-refresh instructions | Requires separate explicit authorization |
| Claude Code | Scaffold-only | Instruction-only continuity guidance | Not implemented by this surface |
| Cursor | Scaffold-only | Instruction-only packaging guidance | Not implemented |
| Windsurf | Scaffold-only | Instruction-only packaging guidance | Not implemented |
| VS Code / VSCodium | Scaffold-only | Instruction-only packaging guidance | Not implemented |
| JetBrains | Scaffold-only | Instruction-only packaging guidance | Not implemented |
| Zed | Scaffold-only | Instruction-only packaging guidance | Not implemented |
| Neovim | Scaffold-only | Instruction-only packaging guidance | Not implemented |

Unknown hosts fail closed.

## Status checks

The planner performs no network request. Without `--latest-version`, status is `NOT_CHECKED`. A caller that has separately obtained a trusted current release version may pass it explicitly:

```text
python scripts/host_update.py --host codex --latest-version 1.7.0 --json
```

The result is deterministic and uses only the canonical local contract plus the supplied version observation.

The existing `scripts/check_for_updates.py` remains the repository's network-backed public-release checker. It does not grant update authority.

## Git and recovery boundary

Supported Git/local plans require a clean working tree, a recorded pre-update HEAD, `git fetch origin`, and `git pull --ff-only origin <current-branch>`. Merge, rebase, force push, history rewrite, and destructive cleanup are not part of the host-update contract.

After a separately authorized repository update, the plan requires the listed canonical validations. Codex additionally validates its export surface. If fast-forward or validation fails, stop and preserve evidence. Any rollback or installed-host repair remains a separately authorized recovery action.

## Installed integrations

The planner never runs `scripts/refresh-installed-integrations.ps1`, exports skills into an installed host, reloads a plugin, reinstalls a marketplace package, publishes a release, or changes repository policy. Those actions remain outside the authority of this contract unless separately approved and supported by the active host/runtime.
