# Compatibility

The current public GitHub Release is Orchestra `v1.8.0: Governance Hardening, Runtime Refoundation & Traceability`, published from lightweight tag `v1.8.0` at exact GitHub-verified signed release commit `dad1f153f1be6522a8a7964258a2122a8d057596`. The release is non-draft, non-prerelease, immutable, and independently verified as latest.

The `v1.8.0` tag resolves directly to the exact release commit. v1.8.0 incorporates the complete architecture governance program OR-GOV-1 through OR-GOV-10, Scribe Specialist Upgrade (SSU), runtime architecture refoundation milestones AR-0 through AR-2, Registry O7 query optimization, and Cloak CUIR reference intelligence. Publication did not graduate scaffold-only hosts or publish those scaffold surfaces to marketplaces.

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
