# Compatibility

The current public GitHub Release is Orchestra `v1.11.0: Adaptive Assurance and Governance Hardening`, published from lightweight tag `v1.11.0` at exact GitHub-verified signed release commit `72c2884a66bb0e0d0ff1e070e7cc1feccd968e35` with tree `e4072cff4de83efa1c1d2d495aa5c186a2469db4`. The release is non-draft, non-prerelease, immutable, and independently verified.

The `v1.11.0` tag resolves directly to the exact release commit. v1.11.0 adds governed adaptive-assurance and protected-governance hardening without changing the existing host-maturity classifications below.

The v1.11.0 release keeps scaffold-only hosts scaffold-only, does not automatically refresh installed integrations, and does not infer or admit a provider/model identity for Copilot Auto mode.

Host capability, package/version parity, validation success, and release publication remain non-authorizing and do not grant runtime, provider-selection, deployment, or policy authority.

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
