# Orchestra Developer Portal

The Developer Portal is Orchestra's repository-native discovery surface for developers extending or integrating with the current v1.9.0 contracts. It is documentation and indexing only. It is not a hosted service, marketplace, package registry, deployment plane, policy authority, or runtime permission source.

## Start here

| Goal | Canonical surfaces |
| --- | --- |
| Understand or build an adapter | `docs/setup/ADAPTER_SDK_PRAP.md`, `machine/protocol/prap-certification-contract.v1.json`, `machine/specialists/registry.v1.json` |
| Produce PRAP compatibility evidence | `scripts/certify_adapter.py`, `machine/protocol/prap-certification-contract.v1.json`, `machine/schemas/prap-certification-evidence.schema.json` |
| Integrate through MCP stdio | `docs/developer/MCP_STDIO_TRANSPORT.md`, `docs/validation/CODEX_MCP_2026_HOST_REVALIDATION_2026_08_28.md`, `orchestra_runtime/mcp_transport.py`, `scripts/mcp_server.py` |
| Check host maturity | `machine/hosts/update-contract.v1.json`, `docs/setup/HOST_UPDATES.md` |
| Understand specialist / Downstream Role boundaries | `machine/specialists/registry.v1.json`, `docs/project/AUTHORITY_CAPABILITY_RUNTIME_ARCHITECTURE.md` |
| Review governance | `machine/governance/policy.v1.json`, `docs/governance/GOVERNANCE_LAYER.md` |
| Validate changes | `docs/setup/VALIDATION.md` |

The machine-readable index for the established portal entry points is `machine/developer-portal/catalog.v1.json`. Its schema is `machine/schemas/developer-portal-catalog.schema.json`. The bounded MCP transport is an established integration surface and does not make the portal catalog authoritative for MCP execution.

## Adapter journey

1. Read `docs/setup/ADAPTER_SDK_PRAP.md` before introducing adapter metadata.
2. Use the stable SDK import surface `orchestra_runtime.protocol.sdk`; PRAP v1 remains the protocol authority.
3. Declare adapter identity and capabilities through the existing protocol model. Do not infer compatibility from a host name.
4. Use `python scripts/certify_adapter.py --adapter <id> --json` for deterministic read-only compatibility evidence.
5. Treat certification and host maturity as separate dimensions. Certification cannot promote a scaffold host.
6. Run repository validation before proposing a governed source change.

## MCP integration journey

1. Read `docs/developer/MCP_STDIO_TRANSPORT.md` and the existing Adapter SDK/PRAP authority boundary.
2. For Codex, enable `mcp_2026_07_28` **and** register the Orchestra stdio server with `CODEX_MCP_PROTOCOL_VERSION=2026-07-28`. Both host opt-ins are required.
3. Fully restart Codex after changing either setting, then require `/mcp` to show Orchestra connected before treating discovery as verified.
4. For an installed-host invocation smoke test, use a bounded read-only session whose approval policy can permit an approval-required MCP call; the verified Codex sequence is documented in `docs/validation/CODEX_MCP_2026_HOST_REVALIDATION_2026_08_28.md`.
5. Start the bounded server with `python scripts/mcp_server.py --adapter <existing-adapter-id>` when launching it directly.
6. Treat the selected adapter as the existing PRAP/runtime identity. MCP does not register a new adapter or promote host maturity.
7. Use only the implemented `server/discover`, `tools/list`, and `tools/call` surface for protocol revision `2026-07-28`.
8. Treat MCP request metadata and tool arguments as untrusted for Orchestra authority or governance expansion.
9. Distinguish successful MCP routing from substantive specialist execution. The default MCP runtime currently returns orchestration decisions/route output and does not invoke a host-native specialist execution engine.
10. Keep Streamable HTTP, resources, prompts, Tasks/extensions, deployment, policy activation, and installed-integration refresh outside this bounded transport.

## Specialist extension journey

The machine specialist registry at `machine/specialists/registry.v1.json` owns specialist identity. The Developer Portal does not create new specialists, change ownership, or convert Downstream Roles into authority sources. Read the authority/capability/runtime architecture and governance policy before proposing a specialist extension.

Third-party discovery or publication is intentionally outside this phase. The Third-Party Specialist Marketplace remains a separately governed future phase and no listing, install, trust, reputation, package publication, or marketplace mutation behavior is implemented here.

## Governance and authority boundary

Portal links point to authoritative machine contracts where authority exists; the catalog does not duplicate or supersede those contracts. Portal discovery, documentation, validation success, certification success, packaging metadata, MCP discovery, and GitHub mergeability do not grant runtime authority or capabilities.

The Developer Portal cannot activate policy, deploy or mutate production, refresh installed integrations, move releases or tags, promote host maturity, publish marketplace content, perform destructive cleanup, or rewrite history. The separately governed MCP transport cannot turn the portal into an authority source.

## MCP transport boundary

MCP was the final integration phase in the Developer Portal sequencing model and is now an established bounded integration surface, introduced in v1.6.0 and retained in v1.7.0. It maps protocol revision `2026-07-28` to Orchestra's existing trusted Adapter SDK/PRAP/runtime boundary, projects only currently permitted runtime-bound commands, and delegates accepted calls to a fresh trusted runtime composition.

Installed Codex routing E2E was revalidated on 2026-08-28: modern discovery, 20-tool projection, and an actual `tools/call` through `mcp__orchestra__review_docs` succeeded with `isError: false` and left the worktree clean. The returned route acknowledgement is expected under the current default runtime and is not evidence of substantive Scribe execution.

MCP remains transport, not authority. The current unit does not add Streamable HTTP, resources, prompts, Tasks/extensions, deployment, policy activation, installed-integration refresh, host-maturity promotion, default host-native specialist execution, or token-savings claims. See `docs/developer/MCP_STDIO_TRANSPORT.md`.

## Public release boundary

The current public release is immutable `v1.9.0` at signed canonical commit `7129a690b041bddbf8b58f41db0c4a680317fda1`. GitHub Release `RE_kwDOS_4UtM4W2pDC` and lightweight tag `v1.9.0` independently resolve to that exact identity.

The v1.10.0 candidate adds the verified UAI host-capability and Conductor routing reconciliation surfaces without changing specialist ownership or granting provider/model selection authority. It is prepared but unpublished; provider/model identity for the Copilot Auto-mode evidence remains unresolved.
