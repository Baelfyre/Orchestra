# Adapter SDK and PRAP v1 Compatibility Certification

Orchestra's Adapter SDK is a stable import surface over the existing PRAP v1 protocol. It does not replace `AdapterProtocol`, `AdapterCapabilities`, `ProtocolValidator`, or the compatibility matrix. Those existing contracts remain authoritative.

## SDK surface

Adapter authors should import the stable SDK surface from `orchestra_runtime.protocol.sdk`. The SDK currently exposes the existing PRAP protocol types plus read-only certification functions. `SDK_PROTOCOL_VERSION` remains `PRAP v1`; `SDK_SURFACE_VERSION` versions only the SDK-facing export surface.

A new adapter must still declare canonical `AdapterProtocol` metadata, use typed `AdapterCapabilities`, and pass `ProtocolValidator`. Certification does not create missing protocol metadata and does not infer compatibility from a host name.

## Read-only certification

Run one target:

```text
python scripts/certify_adapter.py --adapter codex --json
```

Run every contract-declared target:

```text
python scripts/certify_adapter.py --all --json
```

Certification reads `machine/protocol/prap-certification-contract.v1.json`, validates the runtime adapter against PRAP v1 and the existing compatibility matrix, and reads `machine/hosts/update-contract.v1.json` only to report the already-declared host maturity. Evidence conforms to `machine/schemas/prap-certification-evidence.schema.json`.

The command has no execution flag. It does not edit repository files, install or refresh a host integration, publish marketplace packages, move a release or tag, deploy, activate policy, or grant runtime authority.

## Compatibility is not host support

PRAP compatibility and Host Update maturity are separate dimensions.

- Codex and Antigravity are currently `SUPPORTED` in the Host Update contract.
- Claude Code, Cursor, Windsurf, VS Code/VSCodium, JetBrains, Zed, and Neovim remain `SCAFFOLD_ONLY` for Host Update behavior.
- A `PASS` certification means that the adapter's declared runtime metadata is compatible with PRAP v1 under the certification contract. It never promotes host maturity.
- VSCodium remains a compatibility identity that maps through the VS Code runtime adapter and VS Code scaffold maturity.
- `future`, `unknown`, unregistered identities, unsupported protocol versions, contract drift, or malformed metadata fail closed.

## Authority boundary

PRAP `AdapterCapabilities` describe adapter interface characteristics. They are not Orchestra runtime capability grants. Certification therefore emits `runtime_authority_granted=false`, `runtime_capabilities_granted=false`, `mutation_performed=false`, and `installed_integration_refresh_performed=false`.

Adapter metadata, packaging metadata, validation success, and compatibility evidence cannot expand authority. Existing trusted runtime composition and authority controls remain separate.

## MCP transport mapping

The post-v1.5 MCP candidate adds a bounded stdio transport for MCP protocol revision `2026-07-28`. It does not create a parallel adapter protocol. The MCP server selects an existing Orchestra adapter through `AdapterFactory`, projects only commands that are both exposed by that adapter and present in the current trusted runtime policy, and routes every accepted tool call through a fresh existing `RuntimeExecutor` composition.

MCP therefore remains transport rather than authority. MCP client metadata, MCP capabilities, tool names, tool arguments, discovery responses, PRAP certification, and Host Update maturity cannot grant runtime authority or runtime capability. Client-supplied tool arguments cannot inject Orchestra governance-validation metadata.

The first bounded transport exposes only `server/discover`, `tools/list`, and `tools/call` over stdio. Streamable HTTP, resources, prompts, Tasks/extensions, deployment, policy activation, and installed-integration refresh remain outside this unit. See `docs/developer/MCP_STDIO_TRANSPORT.md`.
