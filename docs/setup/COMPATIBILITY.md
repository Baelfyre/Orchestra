# Compatibility

Orchestra `v1.0.0 Portable Runtime` is Markdown-first and runtime-core-first. Hosts integrate through thin adapters and, where available, scaffold packaging metadata that points back to the shared runtime.

| Host | Runtime Adapter | Status | Notes |
|---|---|---|---|
| Codex | `codex` | Supported | Marketplace-first, with repo-local fallback. |
| Claude Code | `claude-code` | Supported | Marketplace metadata included. |
| Antigravity | `antigravity` | Supported | Plugin install path remains host-native. |
| Cursor | `cursor` | Supported | Scaffold-only packaging surface. |
| Windsurf | `windsurf` | Supported | Scaffold-only packaging surface. |
| VS Code | `vscode` | Supported | Scaffold-only packaging surface. |
| VSCodium | `vscode` | Compatible | Reuses the VS Code runtime adapter and packaging scaffold. |
| JetBrains | `jetbrains` | Supported | Scaffold-only plugin surface. |
| Zed | `zed` | Supported | Scaffold-only packaging surface. |
| Neovim | `neovim` | Supported | Scaffold-only packaging surface. |
| Local AI systems | manual | Supported | Load selected Markdown and supporting files manually. |

The repository does not guarantee automatic discovery in every IDE or model runtime. Use the adapter templates, packaging scaffolds, and runtime documentation when host behavior is uncertain.
