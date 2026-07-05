# OOP Runtime Core Architecture

This branch introduces `orchestra_runtime/` as the reusable runtime core for Orchestra.

Branch purpose: `feature/oop-runtime-core-adapters`

## Why this exists

The repository already had adapter-specific validation and export logic spread across `scripts/`, `adapters/codex/`, and Claude Code plugin validation files. This branch starts consolidating the shared orchestration behavior into one runtime-core-first layer so adapters stay thin and platform-specific.

## Core ownership

`orchestra_runtime/` now owns:

- runtime domain models
- manifest parsing
- skill loading
- route decisions
- governance validation
- execution flow
- audit event recording

## Adapter ownership

`CodexAdapter`, `AntigravityAdapter`, `ClaudeCodeAdapter`, `CursorAdapter`, `WindsurfAdapter`, `VSCodeAdapter`, `JetBrainsAdapter`, `ZedAdapter`, and `NeovimAdapter` translate host-specific prompts into shared runtime commands and context packages. They do not own routing or governance logic.

## Current integration points

- `scripts/helpers.py` now reuses runtime manifest and frontmatter repositories.
- `scripts/validate_manifest.py` now checks runtime registry loading in addition to manifest/frontmatter parity.
- `adapters/codex/validate_codex_export.py` now pulls skill inventory from the runtime registry.
- `scripts/validate_claude_plugin.py` now verifies Claude Code adapter command/context parity against repository metadata.

## Runtime flow

1. Adapter provides a `ContextPackage`.
2. Adapter parses a host prompt into a shared `Command`.
3. `RouterService` resolves a `RouteDecision`.
4. `GovernanceValidator` applies blocking rules for destructive and high-risk paths.
5. `RuntimeExecutor` returns an `ExecutionResult`.
6. `AuditLogger` records the execution outcome through an `IAuditSink`.

## Current packaging boundary

- Cursor, Windsurf, and VS Code now have scaffold-only packaging folders under `adapters/`.
- Their package manifests point back to the shared runtime adapter classes.
- Packaging validation checks required files, JSON manifests, and runtime-adapter references.
- Packaging does not own routing, governance, execution, manifest parsing, or audit behavior.

## Deferred work

- The runtime currently centralizes Python validation and adapter-contract behavior first.
- PowerShell installers and Markdown host guides remain in place and unchanged unless they need runtime data.
- Runtime execution still returns orchestration decisions, not full host-native execution side effects.
- Marketplace publication remains deferred for Cursor, Windsurf, and VS Code.
- JetBrains, Zed, and Neovim packaging remain out of scope for this branch.
