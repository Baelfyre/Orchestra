# Specialist Runtime-Host Execution Architecture

Status: `DESIGN_ADMITTED_NO_RUNTIME_INTEGRATION`

Canonical design baseline:

```text
BASE_SHA  = 31d4bb31c6f839d6bee6a788f8cf77d4d5367af3
BASE_TREE = af4bb0df8afb85c84675c040551b1ed06b734767
PUBLIC_RELEASE = v1.7.0
```

Admission record: `machine/features/specialist-runtime-host-execution.v1.json`

This document defines a proposed execution boundary only. It does not implement a specialist engine, invoke a model/provider, refresh an installed integration, change MCP behavior, promote a host, or grant runtime, merge, release, deployment, policy, destructive, or other protected-action authority.

## 1. Problem

Orchestra's current MCP path is verified through transport and routing E2E. A `tools/call` reaches the trusted runtime, resolves the exact command and specialist, evaluates authority and capability, applies governance, advances lifecycle state, and returns an `ExecutionResult`.

The default MCP runtime factory does not configure a substantive specialist execution engine. `RuntimeExecutor` therefore falls back to `_default_operation`, which returns route-oriented output such as:

```text
codex adapter routed 'review-docs' to 'scribe' with governance status NOT_REQUIRED
```

That result proves runtime dispatch and specialist selection. It does not prove that Scribe read the requested documents, applied Scribe instructions, used host tools, or produced a substantive specialist result.

The current operation hook also receives only:

```text
(adapter_name, RouteDecision, ValidationResult)
```

It does not receive the original task input, assembled context, command, selected skill identity digest, or exact authority/capability decision references. A real host execution engine should not recover those inputs from global state, process state, transport metadata, or hidden host context.

The required architectural change is therefore not "call a model after routing." It is to define a typed, auditable, non-authorizing boundary from an already-approved runtime route into an optional host execution engine.

## 2. Core invariants

```text
SPECIALIST_SELECTION != SPECIALIST_EXECUTION
SPECIALIST_EXECUTION != AUTHORITY
HOST_CAPABILITY != ORCHESTRA_AUTHORITY
HOST_APPROVAL != ORCHESTRA_AUTHORITY
ORCHESTRA_AUTHORITY != HOST_PERMISSION
MCP_TRANSPORT != EXECUTION_ENGINE
VALID_RECEIPT != MERGE_AUTHORITY
SUBSTANTIVE_OUTPUT != RELEASE_AUTHORITY
```

The effective execution boundary is an intersection, never a union:

```text
EFFECTIVE_EXECUTION
  = ORCHESTRA_AUTHORITY
  INTERSECT ORCHESTRA_RUNTIME_CAPABILITY
  INTERSECT ORCHESTRA_GOVERNANCE_DISPOSITION
  INTERSECT HOST_SANDBOX_AND_APPROVAL_POLICY
  INTERSECT SPECIALIST_EXECUTION_SCOPE
```

If a host cannot represent or enforce the required restrictions, the bridge must fail closed or reduce to a safer supported mode such as read-only execution. A permissive host configuration cannot widen Orchestra authority.

## 3. Design decision

Introduce an optional typed `ISpecialistExecutionEngine` boundary after existing authority, capability, and governance gates and before the runtime maps an operation outcome into lifecycle state.

The default runtime remains route-only unless an execution engine is explicitly supplied through trusted runtime construction.

```text
CURRENT DEFAULT
Trusted RuntimeComposition
-> adapter context
-> command
-> route
-> exact binding
-> authority
-> capability
-> governance
-> route-only RuntimeOperationResult
-> lifecycle
-> ExecutionResult

PROPOSED OPTIONAL PATH
Trusted RuntimeComposition
-> adapter context
-> command
-> route
-> exact binding
-> authority
-> capability
-> governance
-> SpecialistExecutionRequest
-> configured ISpecialistExecutionEngine
-> host bridge or deterministic engine
-> SpecialistExecutionReceipt
-> receipt validation
-> RuntimeOperationResult
-> lifecycle
-> ExecutionResult
```

No engine is inferred from adapter name, MCP client metadata, environment discovery, provider availability, or installed host state.

## 4. Why MCP Sampling is not the execution architecture

MCP protocol revision `2026-07-28` retains Sampling during a deprecation window but explicitly deprecates it for new integrations. Orchestra should not build a new permanent specialist execution architecture on a deprecated server-to-client model invocation feature.

MCP remains a transport that exposes Orchestra commands. Specialist execution is a runtime concern behind a host-neutral interface.

This also prevents the MCP transport from becoming responsible for provider credentials, model selection, model billing, host conversation state, or sandbox semantics.

## 5. Why direct provider APIs are not the default Orchestra core path

Calling a model provider directly from `orchestra_runtime` would introduce a second agent harness with provider credentials, model-specific behavior, billing semantics, tool orchestration, network policy, and context management. That duplicates responsibilities already owned by supported coding hosts.

The core architecture therefore does not require OpenAI, Google, Anthropic, or another provider SDK.

A future provider-specific execution engine could be evaluated as an optional integration, but it is not the default design and would require its own Feature Admission, dependency, security, privacy, and authority review if materially different from this host-bridge architecture.

## 6. Proposed typed contracts

### 6.1 `SpecialistExecutionRequest`

A request is created only after all current pre-operation gates succeed.

Minimum fields:

```text
request_version
request_id
request_digest
run_id
parent_run_id
correlation_id
adapter_name
command_name
specialist
project_root
skill_source_path
skill_source_digest
task_input
authority_decision_ref
capability_decision_ref
governance_status
evaluated_governance_rules
execution_constraints
execution_mode
```

Rules:

1. `run_id`, `command_name`, and `specialist` must exactly match the trusted route and runtime composition.
2. `authority_decision_ref` and `capability_decision_ref` must refer to the decisions that allowed this exact run and binding.
3. `skill_source_path` must resolve through the canonical `SkillRegistry`, not an arbitrary host-provided prompt path.
4. `skill_source_digest` binds the request to the exact specialist guidance loaded for the run.
5. `task_input` is the original task necessary for execution. It is not authority and must not be copied into runtime audit events by default.
6. `execution_constraints` are derived only from trusted runtime policy and explicit reduction-only request constraints. Host metadata cannot add authority.
7. `execution_mode` is explicit. Absence never silently enables substantive execution.

### 6.2 `SpecialistExecutionReceipt`

A receipt represents what the configured execution engine claims occurred. It is evidence and must be validated before the runtime accepts it as an operation result.

Minimum fields:

```text
receipt_version
receipt_id
request_id
request_digest
run_id
adapter_name
command_name
specialist
engine_id
engine_version
host_execution_id
status
reason_code
output
evidence_refs
side_effect_class
```

Recommended optional fields:

```text
host_identity
sandbox_identity
approval_policy_identity
artifact_refs
changed_paths
started_at
completed_at
```

Rules:

1. Request identity must match exactly.
2. Run, command, adapter, and specialist identity must match exactly.
3. Unknown or malformed terminal status fails closed.
4. Receipt evidence cannot create authority or retroactively authorize side effects.
5. `changed_paths` or artifact summaries may be evidence, but they do not replace Git or repository validation.
6. Raw secrets, credentials, full prompt text, and unnecessary host transcripts must not be persisted in the receipt.

### 6.3 `ISpecialistExecutionEngine`

Conceptual interface:

```python
class ISpecialistExecutionEngine(ABC):
    @abstractmethod
    def execute(
        self,
        request: SpecialistExecutionRequest,
    ) -> SpecialistExecutionReceipt:
        ...
```

The interface is intentionally narrower than a general agent SDK. It does not own routing, authority, capability evaluation, governance, lifecycle, delegation, coordination, or merge decisions.

## 7. Runtime ownership

### `RuntimeExecutor`

Owns:

- deciding whether the current route reached the execution boundary;
- constructing the typed request from already-known runtime state;
- invoking only the explicitly configured engine;
- validating receipt identity;
- translating a valid receipt into `RuntimeOperationResult`;
- preserving existing lifecycle and audit behavior.

Does not own:

- model/provider selection by inference;
- host authentication;
- host installation or refresh;
- host sandbox configuration;
- arbitrary provider tool registration;
- merge, release, deployment, or policy activation.

### `SkillRegistry`

Remains the source of canonical specialist identity and source path. The execution request should bind to the exact canonical skill source that produced the route.

Adapter-exported skill copies may be used by a host bridge only as verified host-compatible projections. They do not replace the canonical source identity.

### MCP transport

MCP continues to:

- validate protocol revision and request shape;
- project bounded Orchestra commands;
- prevent client-supplied governance metadata injection;
- call the configured runtime factory;
- serialize `ExecutionResult`.

MCP does not decide whether a substantive execution engine exists. A runtime factory may explicitly supply one later.

## 8. Execution modes

The architecture defines three semantic modes for planning and validation. They are not implemented by this design phase.

### `ROUTE_ONLY`

Current behavior. No model or host execution occurs. Successful output proves trusted routing and gate passage only.

### `DETERMINISTIC_TEST_ENGINE`

A no-network, no-provider deterministic engine used to validate request construction, receipt validation, lifecycle integration, failure behavior, and MCP result plumbing.

It must not be represented as model or specialist intelligence. Its purpose is architectural proof.

### `HOST_NATIVE`

An optional engine delegates the typed request to a supported host bridge and returns a receipt bound to the original request.

`HOST_NATIVE` requires separately validated host capability and explicit applicable authority. It is never selected because a host executable happens to be installed.

## 9. Host bridge requirements

A host bridge must provide all of the following before it can be considered for installed-host E2E:

1. Exact request identity preservation.
2. Exact specialist identity preservation.
3. A deterministic method for loading the intended specialist guidance.
4. Bounded task/context transfer.
5. A declared sandbox and approval-policy relationship.
6. No authority derivation from host capability or model output.
7. Fail-closed handling when required restrictions cannot be represented.
8. Structured terminal receipt identity.
9. Evidence sufficient to distinguish route success from substantive execution.
10. No secret material in ordinary runtime audit output.

## 10. Codex bridge direction

OpenAI documents the Codex App Server as the first-class integration method for embedding the Codex harness. That makes it a better future candidate for a Codex host bridge than recursive CLI invocation or deprecated MCP Sampling.

This architecture does not yet select or implement a Codex App Server bridge. A bounded spike must first prove:

- the bridge can create an isolated execution with explicit task and specialist instructions;
- the bridge can preserve the caller's intended sandbox/approval restrictions;
- the bridge can return stable execution identity and terminal output;
- the integration does not recursively call the same Orchestra MCP tool;
- the integration does not require Orchestra core to own OpenAI credentials or provider billing state;
- failure and cancellation can be represented without inventing lifecycle success.

Until that proof exists:

```text
CODEX_HOST_BRIDGE = DESIGN_CANDIDATE_ONLY
CODEX_SPECIALIST_EXECUTION_E2E = NOT_VERIFIED
```

## 11. Security model

### 11.1 Prompt and specialist instructions

Task text and specialist Markdown can influence model behavior, but they cannot create authority. The runtime must complete authority and capability evaluation before creating an execution request.

### 11.2 Host sandbox

The host sandbox is an independent lower-level constraint. Orchestra may require a stricter mode than the host default. If the bridge cannot enforce the Orchestra requirement, execution must be denied or reduced.

### 11.3 Tool and network access

A host bridge must not infer that a specialist needs unrestricted shell, filesystem, or network access. Required access must be represented through the applicable existing Orchestra authority/capability scope and host policy.

### 11.4 Audit minimization

Audit should record identities, decisions, status, reason codes, and evidence references. It should not log raw prompts, credentials, entire host conversations, or full file contents unless a separately defined evidence contract explicitly requires and protects them.

### 11.5 Recursive execution

A host bridge must detect or prohibit recursive invocation of the same Orchestra execution surface when recursion would create an unbounded agent loop.

## 12. Failure semantics

The following conditions must fail closed before lifecycle completion is recorded:

```text
ENGINE_NOT_CONFIGURED when HOST_NATIVE was explicitly required
REQUEST_IDENTITY_MISMATCH
REQUEST_DIGEST_MISMATCH
SPECIALIST_IDENTITY_MISMATCH
COMMAND_IDENTITY_MISMATCH
RUN_IDENTITY_MISMATCH
HOST_CONSTRAINT_UNENFORCEABLE
ENGINE_PROTOCOL_UNSUPPORTED
MALFORMED_EXECUTION_RECEIPT
HOST_EXECUTION_FAILED
HOST_EXECUTION_CANCELLED
HOST_EXECUTION_TIMED_OUT
RECURSIVE_EXECUTION_BLOCKED
```

An engine exception must never be converted into successful route output.

Route-only compatibility remains a separate explicit mode, not a fallback after a requested host-native execution fails.

## 13. Evidence classification

The architecture preserves separate evidence levels:

```text
MCP_TRANSPORT_E2E
MCP_ROUTING_E2E
SPECIALIST_SELECTION
DETERMINISTIC_ENGINE_E2E
HOST_BRIDGE_E2E
SUBSTANTIVE_SPECIALIST_EXECUTION_E2E
PROTECTED_ACTION_VALIDATION
```

A later installed-host test may claim `SUBSTANTIVE_SPECIALIST_EXECUTION_E2E = VERIFIED` only when the receipt and observable result prove that the selected specialist guidance was executed against the supplied task through the configured host bridge.

That claim still does not prove correctness of every specialist output or grant protected-action authority.

## 14. Compatibility strategy

- Existing `RuntimeExecutor(..., operation=None)` behavior remains route-only.
- Existing MCP discovery and tool projection remain unchanged unless a later phase explicitly changes them.
- No new MCP method is required for the first implementation.
- Existing adapters remain valid.
- Host execution engines are optional trusted constructor dependencies.
- No automatic migration from route-only to host-native behavior is allowed.
- No installed integration is refreshed automatically.

## 15. Rejected alternatives

### Build on MCP Sampling

Rejected as the permanent design because Sampling is deprecated for new integrations in MCP `2026-07-28`.

### Put provider API calls directly in `mcp_transport.py`

Rejected because transport would become provider, credential, billing, model, and agent-loop infrastructure.

### Recursively invoke `codex exec` by default

Rejected as the default architecture because nested CLI execution makes conversation identity, sandbox inheritance, approval semantics, cancellation, and recursion behavior harder to prove.

### Return specialist Markdown and assume the outer model executed it

Rejected as E2E proof. The outer agent may choose to follow text, but a text handoff alone does not produce a runtime-bound execution receipt.

### Treat host approval as Orchestra authority

Rejected. Host permission is an independent constraint and cannot expand the trusted Orchestra scope.

## 16. Phase boundary

This design phase authorizes only architecture and admission evidence.

```text
RUNTIME_CODE_CHANGED = FALSE
MCP_BEHAVIOR_CHANGED = FALSE
LIVE_MODEL_CALLS = 0
PROVIDER_CALLS = 0
INSTALLED_INTEGRATION_REFRESH = FALSE
POLICY_ACTIVATION = FALSE
RELEASE_PUBLICATION = FALSE
```

Implementation, installed-host execution, live model/provider calls, integration refresh, merge, and release remain separately gated.
