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

## Codex host compatibility

Current Codex MCP `2026-07-28` stdio support is opt-in at both the Codex client and the individual stdio-server configuration. A Codex host must satisfy both conditions:

1. enable the Codex feature `mcp_2026_07_28`; and
2. launch the Orchestra stdio server with `CODEX_MCP_PROTOCOL_VERSION=2026-07-28` in the server environment.

Both are required. Enabling only one of them is not a complete Codex configuration for Orchestra's modern-only MCP transport.

### Recommended Windows / PowerShell setup

From a PowerShell terminal, enable the modern Codex feature:

```powershell
codex features enable mcp_2026_07_28
```

If an older Orchestra MCP registration already exists, remove it before recreating the registration so the per-server protocol marker cannot remain stale:

```powershell
codex mcp remove orchestra
```

Register Orchestra with the required `2026-07-28` server environment marker:

```powershell
codex mcp add orchestra `
  --env CODEX_MCP_PROTOCOL_VERSION=2026-07-28 `
  -- python "D:\Dev\Repositories\+Orchestra\scripts\mcp_server.py" --adapter codex
```

Replace `D:\Dev\Repositories\+Orchestra` with the actual local Orchestra checkout path.

Verify the client feature and the server registration:

```powershell
codex features list | Select-String "mcp_2026_07_28"
codex mcp get orchestra --json
```

The verification must show the feature enabled and the stdio environment containing:

```text
CODEX_MCP_PROTOCOL_VERSION=2026-07-28
```

After changing either setting, fully exit the current Codex session and start a new one. MCP startup state is session-bound and an existing session must not be used as evidence that a changed registration has been loaded.

Inside the fresh Codex session, run:

```text
/mcp
```

A healthy installed-host result shows Orchestra connected with its projected tools. A result such as `orchestra: failed (0 tools)` is not a successful installation.

### Why both Codex opt-ins matter

If the Codex feature is disabled or the stdio protocol marker is absent, Codex can select its legacy MCP initialization lifecycle. Orchestra intentionally does not implement that retired lifecycle, so a mismatched client can receive a fail-closed error such as:

```text
Request _meta is required
```

The remedy is to align the Codex host with MCP `2026-07-28`. Do not weaken Orchestra's `_meta` validation and do not add a legacy authority path merely to accommodate a host configured for the wrong lifecycle.

For persistent Codex use, the feature can also remain enabled in the user's Codex configuration under `[features]` as `mcp_2026_07_28 = true`. This is a host compatibility setting only. It does not authorize Orchestra tool execution, governance approval, deployment, installed-integration refresh, or any protected action.

## Verify an actual `tools/call`

`/mcp` proving that Orchestra is connected establishes startup, discovery, and tool projection. It does not by itself prove that Codex successfully dispatched an Orchestra MCP tool call.

For a bounded interactive smoke test, use a read-only Codex session with an approval policy that can ask for permission if Codex classifies the MCP call as approval-required:

```powershell
codex --sandbox read-only --ask-for-approval on-request
```

Then inspect:

```text
/status
/mcp
```

A harmless smoke request is:

```text
Invoke the Orchestra MCP review-docs tool against README.md.
Read-only inspection only.
Do not modify files, stage, commit, push, create branches or pull requests,
merge, release, deploy, activate policy, refresh integrations, or perform
destructive actions.
Clearly report the MCP tool name and returned result.
```

If Codex asks for approval for that bounded MCP call, approve only the read-only request. In the 2026-08-28 installed-host revalidation, the same call was initially blocked when the effective approval policy was `never`; switching the verification session to `on-request` allowed the approval-required MCP call to dispatch without granting write access.

The successful installed-host revalidation called `mcp__orchestra__review_docs`, returned `isError: false`, and left the Orchestra worktree clean. See `docs/validation/CODEX_MCP_2026_HOST_REVALIDATION_2026_08_28.md` for the evidence record and troubleshooting sequence.

## Current protocol model

MCP `2026-07-28` uses a stateless request model. Orchestra does not implement the retired `initialize` / `initialized` handshake or MCP protocol sessions in this transport. Requests must declare `io.modelcontextprotocol/protocolVersion` in `_meta`; unsupported versions fail with the MCP unsupported-protocol-version error.

`server/discover` advertises only the protocol revision and tools capability implemented by this bounded server. Its discovery result includes `ttlMs: 0` and `cacheScope: "private"`, satisfying the MCP 2026 discovery result contract while preventing reusable discovery caching or stale capability assumptions. These cache hints are transport metadata only and do not grant runtime authority. `tools/list` returns a deterministic projection of commands that are both exposed by the selected existing adapter and present in the current trusted runtime policy. Tool definitions accept one field only, `prompt`, with `additionalProperties: false`.

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

## Current specialist execution boundary

The default MCP runtime is intentionally route-oriented at the specialist boundary.

`tools/call` does execute Orchestra's deterministic runtime path: exact command selection, trusted binding, authority evaluation, runtime-capability checks, governance, lifecycle handling, configured runtime operation, and audit. `McpToolTransport` then returns the resulting `ExecutionResult.output`.

The default MCP factory does **not** configure a host-native specialist execution engine. `RuntimeExecutor` therefore falls back to its default runtime operation, which returns the completed orchestration decision and route-oriented output. For a documentation route, a successful result can look like:

```text
codex adapter routed 'review-docs' to 'scribe' with governance status NOT_REQUIRED
```

That response means the MCP transport and Orchestra runtime successfully selected and routed the command to the Scribe ownership boundary. It does **not** mean that Scribe performed a substantive README audit.

This behavior is consistent with the current repository contract:

- `orchestra_runtime/mcp_transport.py` returns `ExecutionResult.output` from the runtime tool call;
- `orchestra_runtime/services.py` provides the route-oriented `_default_operation` when no specialist execution operation is supplied;
- `docs/project/OOP_RUNTIME_ARCHITECTURE.md` states that runtime execution currently returns orchestration decisions rather than full host-native execution side effects;
- `tests/runtime/test_mcp_transport.py` asserts exact command and specialist routing output rather than substantive specialist findings; and
- specialist workflows such as Scribe remain host/agent instructions under `commands/` and `skills/`, not Python specialist engines invoked by the default MCP factory.

Use the status terms precisely:

```text
MCP_TRANSPORT_E2E = VERIFIED
MCP_ROUTING_E2E = VERIFIED
SPECIALIST_SELECTION = VERIFIED
SPECIALIST_NATIVE_EXECUTION = NOT_IMPLEMENTED_IN_DEFAULT_MCP_RUNTIME
SUBSTANTIVE_SPECIALIST_OUTPUT = NOT_CLAIMED
```

Making an MCP tool return full Scribe, Cipher, Cloak, or other specialist work would be a separately designed executable-specialist/runtime-host capability. It is not required to classify the current MCP transport as healthy.

## stdio safety

The server reads one UTF-8 JSON-RPC message per input line and writes one compact JSON-RPC response per output line. Protocol output is written to stdout only. Internal diagnostics use stderr so logging cannot corrupt MCP framing.

Unknown tools and malformed tool arguments are protocol-level errors. Existing Orchestra runtime denials are returned as tool execution errors without changing their authority meaning.

## Troubleshooting Codex

| Symptom | Likely meaning | Response |
| --- | --- | --- |
| `Request _meta is required` | Codex selected the legacy lifecycle or one of the two modern opt-ins is missing. | Enable `mcp_2026_07_28`, set `CODEX_MCP_PROTOCOL_VERSION=2026-07-28`, then restart Codex. |
| `expect initialized result ... CallToolResult` | Codex reached the modern path but is talking to an Orchestra revision with the older discovery result shape. | Update Orchestra to a revision containing the `ttlMs: 0` / `cacheScope: "private"` discovery compatibility fix. |
| `orchestra: failed (0 tools)` | Startup/handshake failed before usable tool projection. | Recheck feature flag, server env marker, server path, and fresh-session restart. |
| Orchestra connected with projected tools | Startup, discovery, and tool projection succeeded. | Run one bounded `tools/call` smoke test for invocation evidence. |
| MCP call requires approval while policy is `never` | Codex cannot prompt for that approval-required call. | Use a bounded interactive `read-only` + `on-request` verification session. |
| Tool returns `adapter routed ... to ...` | Current default runtime completed deterministic routing. | Treat as expected route-only behavior, not substantive specialist execution. |
| `SEC_E_NO_CREDENTIALS` from Git remote/preflight | Local Windows Git/Schannel cannot prove remote freshness. | Classify separately from MCP; do not treat it as an MCP transport failure. |

## Validation expectations

The focused runtime tests cover:

- current protocol discovery;
- Codex-compatible discovery cache-hint shape;
- deterministic tool ordering and runtime-policy projection;
- exact-command routing independent of prompt triggers;
- a fresh trusted runtime per tool call;
- protocol-version and reserved `_meta` validation;
- unknown tools and malformed argument fail-closed behavior;
- rejection of client-supplied governance metadata;
- existing governed-route blocking;
- runtime-contract failure translation;
- parse/internal-error handling and stdout/stderr separation.

Installed-host validation should distinguish three layers instead of collapsing them into one claim:

```text
MCP_STARTUP_AND_DISCOVERY
MCP_TOOLS_CALL_AND_ROUTING
SUBSTANTIVE_SPECIALIST_EXECUTION
```

The first two are verified for Codex by the 2026-08-28 revalidation record. The third is outside the current default MCP runtime contract.

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
- provide a default host-native executable specialist engine;
- claim that route acknowledgement is substantive specialist output;
- deploy anything;
- activate policy;
- refresh installed integrations;
- change host maturity;
- close Murmurs issue #316;
- claim token savings.
