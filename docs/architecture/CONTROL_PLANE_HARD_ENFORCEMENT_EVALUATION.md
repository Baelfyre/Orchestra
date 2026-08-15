# Control-Plane Hard-Enforcement Evaluation

Status: P8 evaluation; **no enforcement daemon, sandbox, MCP service, or policy activation is authorized or performed by this document**.

## Decision

Orchestra should first enforce a deterministic in-process **pre-execution decision contract** and keep external enforcement mechanisms behind a later, separately validated integration boundary.

The P8 runtime gate therefore accepts structured `ExecutionIntent`, `PreExecutionPolicy`, and evidence-backed host capability declarations, then emits only `ALLOW`, `STOP`, `ESCALATE_HUMAN`, or `WAIT_FOR_CAPACITY`. It does not execute the requested action.

This preserves the distinction:

- **policy decision point**: determine whether an already-authorized action is permitted under current state/evidence;
- **policy enforcement point**: physically prevent an action that is not permitted.

The control plane must be correct before authority is delegated to a stronger enforcement mechanism.

## Candidate enforcement locations

### 1. In-process wrappers

A shell/filesystem/network wrapper is the lowest-dependency path and maps directly to Orchestra's Python runtime, typed intents, exact paths, host-capability declarations, and receipts. Its weakness is coverage: it protects only actions routed through the wrapper, so bypass resistance depends on ensuring all execution paths use it.

**P8 disposition:** implement the decision contract now; do not claim complete hard enforcement yet.

### 2. Open Policy Agent (OPA)

OPA is a general-purpose policy engine designed to separate policy decision-making from enforcement and accepts structured input such as JSON. Its documentation explicitly models applications as policy-enforcement points that query OPA as a policy-decision point. OPA can run as a server or be integrated into an application, and its policies can be tested independently.

**Potential fit:** useful if Orchestra later needs a separately managed declarative policy layer shared by several hosts/services.

**Current disposition:** evaluate later; do not add an OPA runtime dependency until Orchestra's own machine policy schemas stabilize and the added operational dependency is justified.

References:
- https://www.openpolicyagent.org/docs
- https://www.openpolicyagent.org/docs/deploy
- https://www.openpolicyagent.org/docs/policy-testing

### 3. WebAssembly / WASI sandbox boundary

A WebAssembly runtime can provide a stronger execution boundary for code that can be expressed as a Wasm guest. Wasmtime documents sandboxing and WASI capability-based filesystem access, where guests receive only explicitly granted filesystem capabilities.

**Potential fit:** strong candidate for untrusted or tightly sandboxed helper execution where the workload can run inside the Wasm/WASI capability model.

**Current disposition:** not a universal replacement for host-native Git/IDE/tool operations; evaluate for selected untrusted execution workloads after control-plane migration.

References:
- https://docs.wasmtime.dev/security.html
- https://docs.wasmtime.dev/

### 4. MCP service/tool boundary

MCP tools expose schema-described executable functions to language-model clients. That makes MCP useful as a portable typed transport and as a place to put a policy-enforcing tool facade. However, the protocol describes how tools are exposed/invoked; it does not itself create Orchestra authority or prove that the underlying operation is permitted.

**Potential fit:** host-independent facade around Orchestra's already-validated machine contracts and pre-execution gate.

**Current disposition:** transport candidate for P5/P9 portability, not the source of governance authority.

Reference:
- https://modelcontextprotocol.io/specification/2025-11-25/server/tools

## Recommended sequence

1. Keep Orchestra-owned JSON schemas and deterministic validators authoritative.
2. Route proposed actions through the P8 pre-execution gate.
3. Run P9 shadow comparison and final workflow-sanity/conformance suites.
4. Identify which operations still have bypassable enforcement paths.
5. Select the smallest enforcement mechanism per operation class rather than adopting one universal daemon.
6. Activate any external enforcement mechanism only under a separately governed implementation/deployment decision.

## Non-goals

P8 does not:
- deploy OPA;
- execute Rego;
- install or activate a Wasm runtime;
- deploy an MCP server;
- intercept arbitrary OS system calls;
- authorize production or destructive actions;
- change repository rulesets or host permissions.
