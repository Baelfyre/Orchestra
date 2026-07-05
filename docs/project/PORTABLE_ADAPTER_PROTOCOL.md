# Portable Runtime Adapter Protocol

Protocol version: `PRAP v1`

Branch purpose: `feature/portable-runtime-adapter-protocol`

## Design Philosophy

PRAP gives Orchestra one stable contract for host integrations.

- The runtime remains the single source of truth.
- Adapters remain thin translators.
- Packaging remains scaffold-only until a host-specific publication phase is intentionally started.
- Hosts integrate by declaring protocol metadata and translating local input and output into shared runtime models.

## Runtime Responsibilities

The shared runtime continues to own:

- routing
- governance validation
- execution flow
- manifest parsing
- skill loading
- audit logging

## Adapter Responsibilities

Adapters only:

- declare PRAP metadata
- expose host-compatible command triggers
- provide a `ContextPackage`
- translate host prompts into shared `Command` models
- return runtime `ExecutionResult` data back to the host

## Host Responsibilities

Hosts or packaging layers are responsible for:

- installation surfaces
- extension scaffolding
- editor or IDE configuration
- entry templates and workspace instruction files
- future marketplace submission details

## Required Metadata

Every adapter must declare:

- `adapter_id`
- `display_name`
- `runtime_adapter`
- `host_type`
- `protocol_version`
- `supports_commands`
- `supports_context`
- `supports_file_handoff`
- `supports_workspace`
- `supports_audit_trace`
- `supports_streaming`
- `supports_governance`
- `packaging_status`
- `marketplace_status`

## Protocol Flow

1. A host selects an Orchestra adapter.
2. The adapter exposes PRAP metadata and capabilities.
3. The adapter converts host input into a shared `ContextPackage` and `Command`.
4. The runtime routes, validates, executes, and audits the request.
5. The adapter returns the shared `ExecutionResult` to the host.

## Adapter Lifecycle

1. Register the adapter in `orchestra_runtime/adapters.py`.
2. Register construction aliases in `orchestra_runtime/factories.py`.
3. Add packaging metadata only if the host needs a scaffold.
4. Validate the adapter through PRAP metadata tests and packaging validation.
5. Publish host packaging later, in a separate branch, if needed.

## Versioning

- Current protocol version: `PRAP v1`
- Future versions must remain backward compatible where practical.
- New fields should be additive first.
- Breaking changes should move to a new named protocol version rather than silently mutating `PRAP v1`.

## Compatibility Guarantees

- PRAP-compatible adapters can integrate without moving runtime logic into the host.
- Runtime logic stays centralized even when multiple hosts share the same adapter family.
- `VSCodium` is treated as compatible with `VS Code` and reuses the `vscode` runtime adapter and packaging surface.
- Unknown adapters are rejected until they declare valid PRAP metadata.

## Compatibility Matrix

| Host | Runtime Adapter | Host Type | Packaging Status | Marketplace Status | PRAP Status |
|---|---|---|---|---|---|
| Codex | `codex` | AI assistant | marketplace | available | supported |
| Claude Code | `claude-code` | AI assistant | marketplace | available | supported |
| Antigravity | `antigravity` | AI assistant | plugin | available | supported |
| Cursor | `cursor` | IDE | scaffold-only | deferred | supported |
| Windsurf | `windsurf` | IDE | scaffold-only | deferred | supported |
| VS Code | `vscode` | IDE | scaffold-only | deferred | supported |
| VSCodium | `vscode` | IDE | shared VS Code scaffold | deferred | compatible |
| JetBrains | `jetbrains` | IDE | scaffold-only | deferred | supported |
| Zed | `zed` | editor | scaffold-only | deferred | supported |
| Neovim | `neovim` | editor | scaffold-only | deferred | supported |
| Future | `future` | unknown | external | n/a | reserved |
| Unknown adapters | `unknown` | unknown | unregistered | n/a | rejected |

## Future Extension Points

- formal Adapter SDK helpers
- semantic versioning policy for protocol evolution
- contributor certification checklist
- protocol compatibility badge, such as `PRAP v1 Compatible`
- optional streaming refinements for hosts that support incremental output
