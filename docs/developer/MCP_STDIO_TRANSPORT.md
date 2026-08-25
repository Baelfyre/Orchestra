# MCP stdio governed tool transport

Status: shipped in v1.6.0 and retained in v1.7.0. Orchestra issue #349 is completed.

## Scope

Orchestra's first MCP integration targets protocol revision `2026-07-28` and the standard stdio transport. The bounded surface is deliberately limited to:

- `server/discover`
- `tools/list`
- `tools/call`

Streamable HTTP, resources, prompts, Tasks/extensions, deployment, policy activation, and installed-integration refresh are outside this unit.

The server entry point is:

```text
python scripts/mcp_server.py --adapter codex
```

`--adapter` selects an existing Orchestra PRAP adapter identity. MCP does not add a new PRAP adapter identity or promote host maturity.

## Current protocol model

MCP `2026-07-28` uses a stateless request model. Orchestra does not implement the retired `initialize` / `initialized` handshake or MCP protocol sessions in this transport. Requests must declare `io.modelcontextprotocol/protocolVersion` in `_meta`; unsupported versions fail with the MCP unsupported-protocol-version error.

`server/discover` advertises only the protocol revision and tools capability implemented by this bounded server. `tools/list` returns a deterministic projection of commands that are both exposed by the selected existing adapter and present in the current trusted runtime policy. Tool definitions accept one field only, `prompt`, with `additionalProperties: false`.

## Authority boundary

MCP is transport, not authority.

A tool call:

1. creates a fresh Orchestra trusted compatibility composition and runtime executor;
2. selects the requested MCP tool only when it is currently projected by both the backing adapter and runtime policy;
3. wraps the existing PRAP adapter with an exact-command transport view;
4. enters `RuntimeExecutor.execute` with transport-identification metadata only;
5. preserves the existing binding, authority, runtime-capability, governance, lifecycle, operation, and audit sequence.

MCP request `_meta` is validated for protocol compatibility but is not forwarded as runtime authority or governance metadata. Tool arguments cannot supply `governance_validated`, `destructive_validated`, `dry_run`, authority grants, runtime capability grants, or arbitrary metadata. Routes that already require trusted governance validation therefore remain blocked unless a separately trusted Orchestra integration supplies that validation through an existing authorized boundary.

PRAP `AdapterCapabilities`, MCP client identity, MCP client capabilities, tool names, tool arguments, discovery data, compatibility certification, host maturity, and successful validation do not grant Orchestra runtime authority.

## stdio safety

The server reads one UTF-8 JSON-RPC message per input line and writes one compact JSON-RPC response per output line. Protocol output is written to stdout only. Internal diagnostics use stderr so logging cannot corrupt MCP framing.

Unknown tools and malformed tool arguments are protocol-level errors. Existing Orchestra runtime denials are returned as tool execution errors without changing their authority meaning.

## Validation expectations

The focused runtime tests cover:

- current protocol discovery;
- deterministic tool ordering and runtime-policy projection;
- exact-command routing independent of prompt triggers;
- a fresh trusted runtime per tool call;
- protocol-version and reserved `_meta` validation;
- unknown tools and malformed argument fail-closed behavior;
- rejection of client-supplied governance metadata;
- existing governed-route blocking;
- runtime-contract failure translation;
- parse/internal-error handling and stdout/stderr separation.

The signed canonical PR must still pass Orchestra's complete protected-main validation matrix on its exact head. Signed-materialization evidence is transport evidence only and is not reusable as canonical merge readiness.

## Non-goals

This unit does not:

- create an MCP-specific authority or permission model;
- replace PRAP or the Adapter SDK;
- change the Developer Portal into a hosted control plane;
- expose resources or prompts;
- implement Tasks or Multi Round-Trip Requests;
- add Streamable HTTP or network listeners;
- add OAuth or remote authorization;
- deploy anything;
- activate policy;
- refresh installed integrations;
- change host maturity;
- close Murmurs issue #316;
- claim token savings.
