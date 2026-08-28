# MCP stdio governed tool transport

Status: shipped in v1.6.0 and retained in v1.7.0. Orchestra issue #349 is completed. Post-v1.7 E1-E3 add an optional deterministic specialist-execution builder without changing the default MCP runtime.

## Scope

Orchestra's MCP integration targets protocol revision `2026-07-28` and standard stdio transport. The bounded surface remains deliberately limited to:

- `server/discover`
- `tools/list`
- `tools/call`

Streamable HTTP, resources, prompts, Tasks/extensions, deployment, policy activation, and installed-integration refresh are outside this unit.

The default server entry point remains:

```text
python scripts/mcp_server.py --adapter codex
```

`--adapter` selects an existing Orchestra PRAP adapter identity. MCP does not add a new PRAP identity or promote host maturity.

## Codex host compatibility

Current Codex MCP `2026-07-28` stdio support is opt-in at both the Codex client and the individual stdio-server configuration. A Codex host must:

1. enable `mcp_2026_07_28`; and
2. launch Orchestra with `CODEX_MCP_PROTOCOL_VERSION=2026-07-28` in the server environment.

Both are required.

### Recommended Windows / PowerShell setup

```powershell
codex features enable mcp_2026_07_28
codex mcp remove orchestra
codex mcp add orchestra `
  --env CODEX_MCP_PROTOCOL_VERSION=2026-07-28 `
  -- python "D:\Dev\Repositories\+Orchestra\scripts\mcp_server.py" --adapter codex
```

Replace the repository path when necessary.

Verify:

```powershell
codex features list | Select-String "mcp_2026_07_28"
codex mcp get orchestra --json
```

The registration must contain:

```text
CODEX_MCP_PROTOCOL_VERSION=2026-07-28
```

After changing either setting, fully restart Codex. MCP startup state is session-bound.

Inside the fresh session:

```text
/mcp
```

A healthy installed-host result shows Orchestra connected with projected tools. `orchestra: failed (0 tools)` is not a successful installation.

### Why both Codex opt-ins matter

If the feature is disabled or the server marker is absent, Codex can select the legacy initialization lifecycle. Orchestra intentionally does not implement that retired lifecycle, so a mismatched client can receive a fail-closed error such as:

```text
Request _meta is required
```

Align the host with MCP `2026-07-28`; do not weaken Orchestra `_meta` validation or add a legacy authority path.

The Codex feature and server registration are host compatibility settings only. They do not authorize tool execution, governance approval, deployment, installed-integration refresh, or protected action.

## Verify an actual `tools/call`

`/mcp` proves startup, discovery, and tool projection. It does not by itself prove a tool invocation.

For a bounded route-only smoke test:

```powershell
codex --sandbox read-only --ask-for-approval on-request
```

Then inspect:

```text
/status
/mcp
```

A harmless request is:

```text
Invoke the Orchestra MCP review-docs tool against README.md.
Read-only inspection only.
Do not modify files, stage, commit, push, create branches or pull requests,
merge, release, deploy, activate policy, refresh integrations, or perform
destructive actions.
Clearly report the MCP tool name and returned result.
```

The 2026-08-28 installed-host revalidation successfully called `mcp__orchestra__review_docs`, returned `isError: false`, and left the worktree clean. That evidence proves installed-host routing E2E, not substantive Scribe execution. See `docs/validation/CODEX_MCP_2026_HOST_REVALIDATION_2026_08_28.md`.

## Current protocol model

MCP `2026-07-28` uses a stateless request model. Orchestra does not implement the retired `initialize` / `initialized` handshake or MCP protocol sessions in this transport.

Requests declare `io.modelcontextprotocol/protocolVersion` in `_meta`; unsupported versions fail closed.

`server/discover` advertises only the implemented protocol revision and tools capability. Its result includes `ttlMs: 0` and `cacheScope: "private"`, preventing reusable discovery caching or stale capability assumptions.

`tools/list` returns a deterministic projection of commands exposed by the selected adapter and present in trusted runtime policy. Tool definitions accept one field only, `prompt`, with `additionalProperties: false`.

## Authority boundary

MCP is transport, not authority.

A default tool call:

1. creates a fresh trusted compatibility composition and runtime executor;
2. selects the tool only when projected by both the backing adapter and runtime policy;
3. wraps the PRAP adapter with an exact-command transport view;
4. enters `RuntimeExecutor.execute` with transport-identification metadata only;
5. preserves existing exact binding, authority, capability, governance, lifecycle, operation, and audit sequencing.

MCP request `_meta` is validated for protocol compatibility but is not forwarded as runtime authority or governance metadata. Tool arguments cannot supply governance validation, destructive validation, authority grants, capability grants, engine identity, or arbitrary runtime metadata.

PRAP capabilities, MCP client identity/capabilities, tool names, arguments, discovery data, compatibility certification, host maturity, engine availability, and successful validation do not grant Orchestra authority.

## Specialist execution boundary

### Default route-only path

The existing default MCP path remains route-oriented at the specialist boundary.

`tools/call` executes exact command selection, trusted binding, authority evaluation, runtime-capability checks, governance, lifecycle handling, configured runtime operation, and audit. `McpToolTransport` returns `ExecutionResult.output`.

The default builders:

```text
build_mcp_runtime_factory(...)
build_mcp_stdio_transport(...)
```

do **not** configure a specialist execution engine.

A documentation route can therefore return:

```text
codex adapter routed 'review-docs' to 'scribe' with governance status NOT_REQUIRED
```

That proves transport, runtime dispatch, and Scribe selection. It does not mean Scribe performed a substantive documentation audit.

### Optional E1-E3 deterministic execution path

Post-v1.7 E1-E3 add a separate explicit construction surface:

```text
orchestra_runtime/mcp_specialist_execution.py
```

with:

```text
build_mcp_specialist_runtime_factory(...)
build_mcp_stdio_transport_with_specialist_execution(...)
```

These builders require a trusted `execution_engine_factory`. They do not infer an engine from adapter identity, installed host state, environment discovery, prompt text, or MCP client `_meta`.

The optional path creates an exact `SpecialistExecutionRequest` only after the existing runtime gates and accepts output only through a matching `SpecialistExecutionReceipt`.

The deterministic no-network test engine has been exercised through `tools/call`. This proves request construction, receipt identity validation, lifecycle/result mapping, fail-closed behavior, and MCP engine-output plumbing.

It does not prove Codex or another model host executed a specialist.

Use the status terms precisely:

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

The architecture is documented in:

- `docs/project/SPECIALIST_RUNTIME_HOST_EXECUTION_ARCHITECTURE.md`
- `docs/project/SPECIALIST_RUNTIME_HOST_EXECUTION_IMPLEMENTATION_PLAN.md`

## Request and receipt contracts

Machine interchange is bounded by:

```text
machine/schemas/specialist-execution-request.v1.schema.json
machine/schemas/specialist-execution-receipt.v1.schema.json
```

The request binds the exact run, command, adapter, specialist, specialist-source digest, original task input, authority/capability decision references, governance state, trusted execution constraints, and explicit execution mode.

The receipt binds request/run/route/engine identity, terminal status, output, evidence references, and side-effect classification.

A mismatched or malformed receipt fails closed. An engine exception does not fall back to successful route output.

## Client input cannot activate an engine

Engine selection is trusted runtime construction, not protocol input.

The following cannot activate, replace, or widen an engine:

- MCP prompt text;
- MCP request `_meta`;
- client identity/capabilities;
- tool arguments;
- adapter name;
- discovery data;
- host installation or executable presence.

If the default route-only builder is used, it remains route-only even when the prompt or `_meta` asks for `HOST_NATIVE` execution.

## E4-E6 Codex boundary

A host-native Codex bridge is not part of E1-E3.

E4-E6 are separately authorized for bounded execution through Codex CLI. Before any live call, the Codex phase must freeze host/version/bridge/model-if-exposed, sandbox, approval policy, workspace, Orchestra base/head, specialist, command, task fixture, and expected non-mutating outcome.

The first E5 proof is:

```text
HOST = CODEX
COMMAND = review-docs
SPECIALIST = scribe
MODE = READ_ONLY
MUTATION_ALLOWED = FALSE
```

Only exact evidence of Codex executing Scribe through the host bridge and returning a matching receipt may support:

```text
SUBSTANTIVE_SPECIALIST_EXECUTION_E2E = VERIFIED_FOR_CODEX_READ_ONLY_SCRIBE_FIXTURE
```

Read-only proof is not mutation authority. E6 must independently prove path/process/network/approval/Git-state/recovery/destructive-exclusion boundaries before mutation capability can be considered verified.

## stdio safety

The server reads one UTF-8 JSON-RPC message per input line and writes one compact response per output line. Protocol output is stdout only; internal diagnostics use stderr so logging cannot corrupt MCP framing.

Unknown tools and malformed tool arguments are protocol errors. Orchestra runtime denials are returned as tool-execution errors without changing their authority meaning.

## Troubleshooting Codex

| Symptom | Likely meaning | Response |
| --- | --- | --- |
| `Request _meta is required` | Legacy lifecycle selected or one modern opt-in is missing. | Enable `mcp_2026_07_28`, set `CODEX_MCP_PROTOCOL_VERSION=2026-07-28`, restart Codex. |
| `expect initialized result ... CallToolResult` | Modern path reached but Orchestra has the older discovery result shape. | Use a revision with `ttlMs: 0` / `cacheScope: "private"`. |
| `orchestra: failed (0 tools)` | Startup failed before usable tool projection. | Recheck feature, server marker/path, and fresh-session restart. |
| Orchestra connected with projected tools | Startup/discovery/tool projection succeeded. | Run one bounded `tools/call` for invocation evidence. |
| MCP call requires approval while policy is `never` | Codex cannot prompt for the approval-required call. | Use bounded `read-only` + `on-request` verification. |
| Default tool returns `adapter routed ... to ...` | Route-only runtime completed deterministic routing. | Do not classify as substantive specialist execution. |
| Explicit deterministic builder returns engine fixture output | E1-E3 optional engine path executed. | Treat as deterministic architecture evidence only. |
| `SEC_E_NO_CREDENTIALS` from Git preflight | Local Windows Git/Schannel remote freshness issue. | Classify separately from MCP; do not weaken MCP/governance. |

## Validation expectations

The focused runtime tests cover:

- current protocol discovery and cache-hint shape;
- deterministic tool projection/order;
- exact-command routing independent of prompt triggers;
- fresh trusted runtime per tool call;
- protocol-version and reserved `_meta` validation;
- unknown/malformed request fail-closed behavior;
- client governance-metadata rejection;
- governed-route blocking;
- runtime-contract failure translation;
- stdout/stderr separation;
- exact specialist execution request/receipt schema validation;
- no engine call before authority, capability, governance, or coordination;
- prompt/client metadata inability to select the engine;
- request/run/route/specialist/source-digest binding;
- receipt mismatch and malformed receipt fail-closed behavior;
- deterministic side-effect rejection;
- deterministic engine `tools/call` result plumbing;
- route-only default preservation.

Pre-parity E1-E3 runtime evidence at source head `da1a1c0e19914f8b0fa7048c73a93e319a197292` recorded:

```text
TESTS = 1926 / 1926 PASS
FAILURES = 0
ERRORS = 0
STATEMENT_COVERAGE = 98.22%
BRANCH_COVERAGE = 95.09%
RUNTIME_EVIDENCE = PASS
VALIDATE_RUN = 33203755377
```

Installed-host validation must distinguish:

```text
MCP_STARTUP_AND_DISCOVERY
MCP_TOOLS_CALL_AND_ROUTING
DETERMINISTIC_SPECIALIST_ENGINE
HOST_BRIDGE_EXECUTION
SUBSTANTIVE_SPECIALIST_EXECUTION
```

The first two are verified for installed Codex routing. Deterministic engine execution is verified in E1-E3. Host-bridge and substantive Codex specialist execution remain E4-E6 evidence questions.

The signed canonical PR must still pass Orchestra's complete protected-main validation matrix on its exact head. Validation and materialization evidence never create merge authority by themselves.

## Non-goals

This unit does not:

- create an MCP-specific authority model;
- replace PRAP or the Adapter SDK;
- expose resources or prompts;
- implement Tasks or Multi Round-Trip Requests;
- add Streamable HTTP or network listeners;
- add OAuth or remote authorization;
- provide a default host-native executable specialist engine;
- make deterministic fixture output a host-native execution claim;
- claim route acknowledgement is substantive specialist output;
- deploy anything;
- activate policy;
- refresh installed integrations;
- change host maturity;
- publish or move a release;
- claim token savings.
