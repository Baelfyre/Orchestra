# Compatibility

The current public GitHub Release is Orchestra `v1.5.0: Machine-Verifiable Control Plane and Murmurs`, published from lightweight tag `v1.5.0` at exact signed release commit `b0a56cc7af8ad78234754bcb29ed07f6ab54d920`. The release is non-draft, non-prerelease, immutable, and independently verified as latest. Publication did not graduate scaffold-only hosts or perform marketplace publication.

The `v1.5.0` tag is a lightweight `commit` ref resolving directly to the GitHub-verified signed release commit above; there is no separate tag object. Historical v1.2.0/v1.3.0 annotated-tag evidence and the v1.4.0 lightweight-tag evidence remain unchanged.

v1.5.0 preserves the existing public package, command, specialist, and host surfaces while making the machine contracts and deterministic kernel the canonical control-plane boundary at `LEGACY_RETIRED`. Murmurs is additive and opt-in with `NORMAL` as the default presentation mode. MCP is not part of v1.5.0 and remains a post-publication transport/integration candidate, not a source of authority.

Scaffold-only hosts are not full support claims. Promotion requirements and graduation order live in `docs/project/SCAFFOLD_ADAPTER_GRADUATION_CRITERIA.md`.

| Host | Runtime Adapter | Status | Notes |
|---|---|---|---|
| Codex | `codex` | Supported | Marketplace-first, with repo-local fallback. Accepted R7 same-host and cross-host continuity evidence is merged and verified. |
| Claude Code | `claude-code` | Supported packaging/integration; runtime continuity `SCAFFOLD_ONLY` | Marketplace metadata and package/contract compatibility are verified. Active runtime continuity is not claimed. |
| Antigravity | `antigravity` | Supported | Plugin install path remains host-native. Accepted R7 same-host and cross-host continuity evidence is merged and verified. |
| Cursor | `cursor` | Scaffold-only | Runtime adapter exists; packaging surface remains scaffold-only. |
| Windsurf | `windsurf` | Scaffold-only | Runtime adapter exists; packaging surface remains scaffold-only. |
| VS Code | `vscode` | Scaffold-only | Shared VS Code-family runtime adapter and packaging scaffold. |
| VSCodium | `vscode` | Scaffold-only | Reuses the VS Code-family runtime adapter and scaffold packaging path. |
| JetBrains | `jetbrains` | Scaffold-only | Runtime adapter exists; plugin surface remains scaffold-only. |
| Zed | `zed` | Scaffold-only | Runtime adapter exists; packaging surface remains scaffold-only. |
| Neovim | `neovim` | Scaffold-only | Runtime adapter exists; packaging surface remains scaffold-only. |
| Local AI systems | manual | Supported | Load selected Markdown and supporting files manually. |

Repository CI and deterministic host-reliability fixtures prove repository contracts only. They are not live installed-host evidence. Accepted R7 records are reconciled separately in `docs/validation/R7_LIVE_INSTALLED_HOST_VALIDATION_EVIDENCE.md`; the fixture remains pending/empty by design.

The repository does not guarantee automatic discovery in every IDE or model runtime. Use the adapter templates, packaging scaffolds, and runtime documentation when host behavior is uncertain.
