# OOP Runtime Core Architecture

This document describes `orchestra_runtime/` as the reusable runtime core for Orchestra.

Historical implementation baseline: `release/v1.0.0-portable-runtime`
Current public release line: `v1.7.0`

## Why this exists

The repository originally had adapter-specific validation and export logic spread across `scripts/`, `adapters/codex/`, and Claude Code plugin validation files. The runtime core consolidates shared orchestration behavior into one runtime-core-first layer so adapters and transports stay thin and platform-specific.

## Core ownership

`orchestra_runtime/` owns:

- runtime domain models
- manifest parsing
- skill loading
- route decisions
- governance validation
- execution flow
- optional typed specialist execution attachment
- audit event recording

## Adapter ownership

`CodexAdapter`, `AntigravityAdapter`, `ClaudeCodeAdapter`, `CursorAdapter`, `WindsurfAdapter`, `VSCodeAdapter`, `JetBrainsAdapter`, `ZedAdapter`, and `NeovimAdapter` translate host-specific prompts into shared runtime commands and context packages. They do not own routing or governance logic.

## Portable protocol ownership

`orchestra_runtime/protocol/` defines the Portable Runtime Adapter Protocol (`PRAP v1`).

- adapters declare versioned metadata and capability flags through PRAP
- the protocol validator checks adapter completeness and packaging/runtime alignment
- compatibility records document supported, compatible, reserved, and rejected host states
- `VSCodium` intentionally reuses the `VSCodeAdapter` contract and packaging surface
- the stable SDK import surface is `orchestra_runtime.protocol.sdk`
- read-only PRAP compatibility certification is available through `scripts/certify_adapter.py`
- compatibility or certification evidence does not grant runtime authority, host maturity, deployment permission, policy activation, or installed-integration refresh authority

See [Adapter SDK and PRAP v1 Compatibility Certification](../setup/ADAPTER_SDK_PRAP.md).

## Current integration points

- `scripts/helpers.py` reuses runtime manifest and frontmatter repositories.
- `scripts/validate_manifest.py` checks runtime registry loading in addition to manifest/frontmatter parity.
- `adapters/codex/validate_codex_export.py` pulls skill inventory from the runtime registry.
- `scripts/validate_claude_plugin.py` verifies Claude Code adapter command/context parity against repository metadata.
- `scripts/mcp_server.py` exposes the bounded MCP stdio entry point through an existing PRAP adapter identity.
- `orchestra_runtime/mcp_transport.py` projects permitted commands as MCP tools and delegates accepted calls to a fresh trusted route-only runtime composition.
- `orchestra_runtime/specialist_execution.py` provides the optional typed `ISpecialistExecutionEngine` request/receipt boundary layered over existing runtime gates.
- `orchestra_runtime/mcp_specialist_execution.py` provides an explicit opt-in MCP builder for an injected execution engine while leaving the existing MCP builders unchanged.

## Runtime flow

Default route-only flow:

1. Adapter provides a `ContextPackage`.
2. Adapter parses a host prompt into a shared `Command`.
3. `RouterService` resolves a `RouteDecision`.
4. Exact binding, authority, capability, governance, coordination, and lifecycle checks apply before the configured runtime operation.
5. The default operation returns route-oriented output.
6. `RuntimeExecutor` returns an `ExecutionResult`.
7. `AuditLogger` records the execution outcome through an `IAuditSink`.

Optional deterministic/specialist-execution flow:

1. Trusted construction supplies `SpecialistRuntimeExecutor` with an explicit `ISpecialistExecutionEngine`.
2. The executor delegates the pre-operation gate sequence to the existing `RuntimeExecutor`.
3. After lifecycle activation, an exact `SpecialistExecutionRequest` binds run, route, specialist source digest, task input, authority/capability decision references, governance state, and trusted execution constraints.
4. The explicit engine returns a `SpecialistExecutionReceipt`.
5. Receipt run, route, specialist, command, request digest, and engine identities are validated before output is accepted.
6. Valid receipt status maps into the existing lifecycle states; malformed or mismatched receipts fail closed.
7. `ExecutionResult` remains the caller-facing result.

Routing, validation success, host capability, MCP discovery, specialist selection, execution output, and receipt success do not grant authority.

## Authority and capability architecture

The trusted-authority and runtime-capability architecture is documented separately:

- [Authority and Capability Runtime Architecture](AUTHORITY_CAPABILITY_RUNTIME_ARCHITECTURE.md)
- [Authority and Capability Contracts](AUTHORITY_CAPABILITY_CONTRACTS.md)
- [Authority and Capability Implementation Plan](AUTHORITY_CAPABILITY_IMPLEMENTATION_PLAN.md)

Current runtime behavior remains bounded by the canonical runtime, governance, and machine contracts. Governance validation, routing, PRAP host support, prompt text, adapter metadata, MCP exposure, compatibility certification, execution-engine availability, and GitHub state do not grant or expand runtime authority.

## MCP runtime boundary

The bounded MCP stdio transport targets protocol revision `2026-07-28` and exposes `server/discover`, `tools/list`, and `tools/call` through an existing PRAP adapter identity.

An accepted `tools/call` executes Orchestra's deterministic runtime path and returns `ExecutionResult.output`.

### Default path

The existing `build_mcp_runtime_factory(...)` and `build_mcp_stdio_transport(...)` remain route-only. The default MCP runtime factory does not configure a host-native executable specialist engine. When no specialist execution engine is explicitly supplied, `RuntimeExecutor` uses its default route-oriented operation.

Therefore a successful result such as:

```text
codex adapter routed 'review-docs' to 'scribe' with governance status NOT_REQUIRED
```

proves transport, runtime dispatch, and specialist route selection. It does not prove that Scribe performed a substantive documentation audit.

### Explicit deterministic execution path

E1-E3 add explicit optional builders:

```text
build_mcp_specialist_runtime_factory(...)
build_mcp_stdio_transport_with_specialist_execution(...)
```

Those builders require a trusted execution-engine factory. Prompt text and MCP client metadata cannot select or activate the engine.

The deterministic no-network test engine has been exercised through MCP `tools/call`, proving typed request construction, receipt validation, lifecycle/result plumbing, and substantive deterministic fixture output without a host/model call.

Use the current status terms precisely:

```text
MCP_TRANSPORT_E2E = VERIFIED
MCP_ROUTING_E2E = VERIFIED
SPECIALIST_SELECTION = VERIFIED
DETERMINISTIC_SPECIALIST_ENGINE_E2E = VERIFIED
MCP_DETERMINISTIC_ENGINE_E2E = VERIFIED
SPECIALIST_NATIVE_EXECUTION = NOT_IMPLEMENTED_IN_DEFAULT_MCP_RUNTIME
HOST_BRIDGE_E2E = NOT_VERIFIED
SUBSTANTIVE_SPECIALIST_OUTPUT = NOT_CLAIMED
```

Installed Codex routing E2E was revalidated on 2026-08-28. The evidence and required dual host opt-in are documented in [Codex MCP 2026 host revalidation](../validation/CODEX_MCP_2026_HOST_REVALIDATION_2026_08_28.md) and [MCP stdio governed tool transport](../developer/MCP_STDIO_TRANSPORT.md).

The E1-E3 execution architecture and Codex E4-E6 host-proof boundary are documented in [Specialist Runtime-Host Execution Architecture](SPECIALIST_RUNTIME_HOST_EXECUTION_ARCHITECTURE.md) and [Implementation Plan](SPECIALIST_RUNTIME_HOST_EXECUTION_IMPLEMENTATION_PLAN.md).

## Current packaging boundary

- Cursor, Windsurf, and VS Code have scaffold-only packaging folders under `adapters/`.
- JetBrains has a scaffold-only packaging folder under `adapters/jetbrains/`.
- Zed and Neovim have scaffold-only packaging folders under `adapters/`.
- Their package manifests point back to the shared runtime adapter classes.
- JetBrains uses `plugin.xml` plus scaffold metadata that still points back to the shared runtime adapter.
- Zed and Neovim use scaffold metadata that still points back to the shared runtime adapters.
- Packaging validation checks required files, JSON manifests, and runtime-adapter references.
- Packaging does not own routing, governance, execution, manifest parsing, or audit behavior.

## Deferred work

- The runtime centralizes Python orchestration, validation, adapter-contract, bounded transport, and deterministic typed execution behavior first.
- PowerShell installers and Markdown host guides remain separate host-facing surfaces unless they need shared runtime data.
- Runtime and MCP execution remain route-only by default.
- A default host-native executable specialist engine is not implemented in the current MCP runtime.
- Codex E4-E6 must prove a separately configured host bridge before host-native or substantive specialist E2E is claimed.
- Marketplace publication remains deferred for Cursor, Windsurf, and VS Code.
- JetBrains marketplace publication remains deferred.
- Zed and Neovim marketplace publication remain deferred.
