# Installation

Conductor can be installed in three ways depending on your environment:

## 1. Antigravity Plugin Setup

If you are using the Antigravity ecosystem, install the plugin directly:

```sh
agy plugin install https://github.com/Baelfyre/Orchestra
```

## 2. Codex Plugin Setup

Codex compatibility is provided through `.codex-plugin/plugin.json`, `AGENTS.md`, and the shared `skills/` directory. Installation may be done by cloning the repository into the intended Codex workspace or by using Codex plugin discovery/marketplace configuration where available.

### Install in Codex through Marketplace

1. Open Codex.
2. Go to Plugins.
3. Open Marketplace.
4. Paste this GitHub repository URL into the Source field:

   https://github.com/Baelfyre/Orchestra

5. Add the marketplace source.
6. Restart Codex.
7. Go back to Plugins.
8. Open Personal.
9. Search for Orchestra.
10. Click Install.
11. Confirm that Orchestra appears as installed or enabled.

If Orchestra does not appear under Personal after adding the marketplace source, restart Codex again and check that the repository URL was entered correctly.

### Local Installation

If cloning manually:
1. Clone the repository into your global Codex plugins directory or your local workspace's `.agents/plugins` directory.
   ```sh
   git clone https://github.com/Baelfyre/Orchestra.git
   ```
2. Codex will automatically discover the `.codex-plugin/plugin.json` manifest and map the `skills/` directory into your environment.
3. The repository's `AGENTS.md` file will provide native instructions to Codex on how to interact with the ecosystem.

## 3. Skills-only Setup (Manual)

If you prefer not to use a plugin manager or are using an unsupported environment, you can install the raw skills manually:

1. Clone the repository:
   ```sh
   git clone https://github.com/Baelfyre/Orchestra.git
   ```
2. Copy only the specific folders you need from `skills/` into the local skill or instruction location supported by your tool.
3. Keep the repository copy separate from unrelated source repositories. Follow [LOCAL_ONLY_GUIDE.md](LOCAL_ONLY_GUIDE.md) if you are deliberately referencing skills repo-locally.

## Refresh Installed Integrations

To manually refresh your installed skills and run validation checks, use the refresh script.

**For Antigravity:**
```sh
powershell -ExecutionPolicy Bypass -File .\scripts\refresh-installed-integrations.ps1 -Target Antigravity
```

**For Codex (repo-local installation):**
```sh
powershell -ExecutionPolicy Bypass -File .\scripts\refresh-installed-integrations.ps1 -Target Codex -CodexRepoPath "C:\path\to\your\project"
```
*(Do not modify the global `.codex` directory by default.)*

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
