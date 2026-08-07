# Compatibility

The current public GitHub Release is Orchestra `v1.1.2`. Repository release-candidate metadata is normalized to `1.2.0` for R6 preparation, but `v1.2.0` is `PREPARED_NOT_RELEASED` until the separate R8 tag/GitHub Release gate completes.

Scaffold-only hosts are not full support claims. Promotion requirements and graduation order live in `docs/project/SCAFFOLD_ADAPTER_GRADUATION_CRITERIA.md`.

| Host | Runtime Adapter | Status | Notes |
|---|---|---|---|
| Codex | `codex` | Supported | Marketplace-first, with repo-local fallback. R7 live continuity evidence remains pending for the v1.2.0 publication gate. |
| Claude Code | `claude-code` | Supported packaging/integration | Marketplace metadata included. Phase C active runtime-continuity capability is not promoted beyond repository/scaffold evidence. |
| Antigravity | `antigravity` | Supported | Plugin install path remains host-native. R7 live continuity evidence remains pending for the v1.2.0 publication gate. |
| Cursor | `cursor` | Scaffold-only | Runtime adapter exists; packaging surface remains scaffold-only. |
| Windsurf | `windsurf` | Scaffold-only | Runtime adapter exists; packaging surface remains scaffold-only. |
| VS Code | `vscode` | Scaffold-only | Shared VS Code-family runtime adapter and packaging scaffold. |
| VSCodium | `vscode` | Scaffold-only | Reuses the VS Code-family runtime adapter and scaffold packaging path. |
| JetBrains | `jetbrains` | Scaffold-only | Runtime adapter exists; plugin surface remains scaffold-only. |
| Zed | `zed` | Scaffold-only | Runtime adapter exists; packaging surface remains scaffold-only. |
| Neovim | `neovim` | Scaffold-only | Runtime adapter exists; packaging surface remains scaffold-only. |
| Local AI systems | manual | Supported | Load selected Markdown and supporting files manually. |

Repository CI and deterministic host-reliability fixtures prove repository contracts only. They are not live installed-host evidence. R7 must reconcile the applicable installed Codex/Antigravity continuity evidence before `v1.2.0` publication.

The repository does not guarantee automatic discovery in every IDE or model runtime. Use the adapter templates, packaging scaffolds, and runtime documentation when host behavior is uncertain.
