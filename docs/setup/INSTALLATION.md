# Installation

Orchestra can be installed in several ways depending on your AI host or IDE:

## Current Release

`v1.1.0 Specialist Governance & Boundary Standard` builds on the `v1.0.0 Portable Runtime` baseline and focuses on documentation, governance, metadata, and specialist-definition normalization.

| Host | Install Surface | Current Status |
|---|---|---|
| Codex | Marketplace or repo-local fallback | Supported |
| Claude Code | Marketplace plugin | Supported |
| Antigravity | Native plugin install | Supported |
| Cursor | Scaffold-only packaging and workspace instructions | Supported |
| Windsurf | Scaffold-only packaging and workspace instructions | Supported |
| VS Code | Scaffold-only packaging and workspace instructions | Supported |
| VSCodium | Reuses VS Code scaffold and runtime adapter | Compatible |
| JetBrains | Scaffold-only plugin surface | Supported |
| Zed | Scaffold-only packaging and workspace instructions | Supported |
| Neovim | Scaffold-only packaging and workspace instructions | Supported |
| Local AI systems | Manual skill loading | Supported |

## 1. Antigravity Plugin Setup

If you are using the Antigravity ecosystem, install the plugin directly:

```sh
agy plugin install https://github.com/Baelfyre/Orchestra
```

## 2. Codex Plugin Setup

For most Codex users, install Orchestra through the Codex Marketplace and invoke it with `@Orchestra`. Repo-local `.agents/skills` setup is available for local testing, custom workspace setups, unsupported Codex workflows, or repos that intentionally want local skill files.

### Install in Codex through Marketplace

1. Open Codex.
2. Go to Plugins.
3. Add a marketplace or open Marketplace source settings.
4. Paste this GitHub repository URL into the Source field:

   https://github.com/Baelfyre/Orchestra

5. Add the marketplace source.
6. Restart Codex.
7. Go back to Plugins.
8. Open Personal.
9. Search for Orchestra.
10. Click Install.
11. Confirm that Orchestra appears as installed or enabled.

Use Orchestra in Codex with:

```text
@Orchestra
```

If Orchestra does not appear under Personal after adding the marketplace source, restart Codex again and check that the repository URL was entered correctly.

### Advanced: Install locally per-project

Use this path only when the target repo deliberately needs local skill files:

```sh
powershell -ExecutionPolicy Bypass -File .\scripts\refresh-installed-integrations.ps1 -Target Codex -CodexRepoPath "C:\path\to\your\project" -Force
```

Do not commit `.agents/` unless the repo intentionally shares those Codex skill files. For local-only setup, add `.agents/` to `.git/info/exclude`.

The Codex refresh path now uses a temporary staging export by default. It reads tracked repository source, exports into a temp directory outside the repo, validates the staged export, installs from that staged copy, verifies parity, and then removes the temp directory. Generated runtime output is not written into tracked export folders during a normal refresh.

## 3. Claude Code Plugin Setup

For Claude Code, you can install the Orchestra plugin directly using its marketplace.

```text
/plugin marketplace add Baelfyre/Orchestra
/plugin install orchestra@orchestra
```

To update or validate your plugin, run the following commands inside Claude Code:

```text
/plugin marketplace update
/reload-plugins
/plugin validate .
```

You can also run validation from your terminal at the repository root:

```text
claude plugin validate .
```

*Note: Claude Code plugin skills are expected to be namespaced after installation.*

## 4. Skills-only Setup (Manual)

If you prefer not to use a plugin manager or are using an unsupported environment, you can install the raw skills manually:

1. Clone the repository:
   ```sh
   git clone https://github.com/Baelfyre/Orchestra.git
   ```
2. Copy only the specific folders you need from `skills/` into the local skill or instruction location supported by your tool.
3. Keep the repository copy separate from unrelated source repositories. Follow [LOCAL_ONLY_GUIDE.md](LOCAL_ONLY_GUIDE.md) if you are deliberately using local skill files.

## 5. Scaffold-Only IDE Packaging

Cursor, Windsurf, VS Code, JetBrains, Zed, and Neovim currently ship scaffold-only packaging folders under `adapters/`. These folders do not duplicate routing, governance, execution, manifest parsing, or audit logic. They point back to the shared runtime adapters in `orchestra_runtime/`.

`VSCodium` intentionally reuses the VS Code runtime adapter and scaffold metadata.

## Refresh Installed Integrations

To manually refresh your installed skills and run validation checks, use the refresh script.

**For Antigravity:**
```sh
powershell -ExecutionPolicy Bypass -File .\scripts\refresh-installed-integrations.ps1 -Target Antigravity
```

**For Codex repo-local fallback only:**
```sh
powershell -ExecutionPolicy Bypass -File .\scripts\refresh-installed-integrations.ps1 -Target Codex -CodexRepoPath "C:\path\to\your\project"
```
*(Marketplace installation is the default Codex setup.)*

Default Codex refresh behavior:

- export to a temporary staging directory
- validate the staged export
- install staged skills into repo-local `.agents/skills`
- install staged skills into the global Codex skills directory
- compare file lists and SHA-256 hashes against the staged export
- delete the temporary staging directory after a successful refresh

Keep the staged export only when debugging:

```sh
powershell -ExecutionPolicy Bypass -File .\scripts\refresh-installed-integrations.ps1 -Target Codex -KeepTempExport
```

## Check for Updates

Orchestra update checks are notify-only. They do not silently modify installed plugin files.

Run:

```sh
python .\scripts\check_for_updates.py
```

The script reads local version metadata from the root manifest, Claude plugin manifest, and adapter package manifests where applicable, then compares it to the latest GitHub release.

If a newer release exists, use your host-specific refresh or reinstall flow to update.

## Verify

Run the structure validator (`.\scripts\validate-structure.ps1`) and confirm that normal QA routes to Overseer, normal security/privacy review routes to Cipher, and Dagger remains gated.

## Updates

> [!WARNING]
> Fully automatic updates are not recommended because plugin metadata, routing behavior, or SKILL.md frontmatter changes can break the ecosystem. Use validated updates instead.

### Safe Update Instructions (Recommended)

To safely update the ecosystem across any framework, run the included update script. This script automatically performs safety checks, fetches the latest changes, and triggers the validation suite:

```sh
powershell -ExecutionPolicy Bypass -File .\scripts\update-plugin.ps1 -DryRun
powershell -ExecutionPolicy Bypass -File .\scripts\update-plugin.ps1
```

*(You can also append `-RepoPath "C:\path"` to run it from a different directory).*

### Manual Update Instructions

If you prefer to manually handle the update sequence:

1. Ensure your working tree is clean.
2. Pull the latest changes:
   ```sh
   git pull origin main
   ```
3. Run the validation checks manually to ensure metadata and routing consistency:
   ```sh
   powershell -ExecutionPolicy Bypass -File .\scripts\validate-manifest.ps1
   powershell -ExecutionPolicy Bypass -File .\scripts\validate-structure.ps1
   ```

### Rollback Instructions

If a safe update or manual pull introduces a breaking change or validation failure, you can roll back the repository to the last known good commit:

1. Identify the previous stable commit hash using `git log`.
2. Reset the repository:
   ```sh
   git reset --hard <PREVIOUS_COMMIT_HASH>
   ```
3. Reload or restart your agent workspace (Antigravity or Codex) to revert the ecosystem behavior.
