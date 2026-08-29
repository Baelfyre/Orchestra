# Specialist Runtime-Host Execution Architecture

Status: `E1_E6_BOUNDED_CODEX_VALIDATED_E7_PENDING`

Canonical design baseline:

```text
BASE_SHA  = 31d4bb31c6f839d6bee6a788f8cf77d4d5367af3
BASE_TREE = af4bb0df8afb85c84675c040551b1ed06b734767
PUBLIC_RELEASE = v1.7.0
```

Admission record: `machine/features/specialist-runtime-host-execution.v1.json`

Implementation plan: `docs/project/SPECIALIST_RUNTIME_HOST_EXECUTION_IMPLEMENTATION_PLAN.md`

The E1-E3 deterministic foundation is implemented as an optional runtime attachment. It does not implement a live Codex or other host bridge, invoke a model/provider, refresh an installed integration, promote the feature, move the public release, or grant merge, release, deployment, policy, destructive, or other protected-action authority.

## 1. Problem and current boundary

Orchestra's default MCP path is verified through transport and routing E2E. A `tools/call` reaches the trusted runtime, resolves the exact command and specialist, evaluates authority and capability, applies governance, advances lifecycle state, and returns an `ExecutionResult`.

The default MCP runtime factory still does not configure a host-native specialist execution engine. It therefore retains route-oriented output such as:

```text
codex adapter routed 'review-docs' to 'scribe' with governance status NOT_REQUIRED
```

That proves runtime dispatch and specialist selection. It does not prove that Scribe read documents, applied Scribe guidance, used Codex host tools, or produced substantive specialist reasoning.

E1-E3 now provide the missing typed execution boundary and deterministic proof path without changing that default.

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

Effective host execution remains an intersection, never a union:

```text
EFFECTIVE_EXECUTION
  = ORCHESTRA_AUTHORITY
  INTERSECT ORCHESTRA_RUNTIME_CAPABILITY
  INTERSECT ORCHESTRA_GOVERNANCE_DISPOSITION
  INTERSECT HOST_SANDBOX_AND_APPROVAL_POLICY
  INTERSECT SPECIALIST_EXECUTION_SCOPE
```

If a host cannot represent or enforce the required restrictions, the bridge must fail closed or reduce to a safer separately authorized mode. A permissive host configuration cannot widen Orchestra authority.

## 3. Implemented design

E1-E3 implement an optional typed `ISpecialistExecutionEngine` boundary layered over the existing trusted runtime.

The default remains route-only:

```text
DEFAULT PATH
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
```

The explicit optional path is now:

```text
OPTIONAL E1-E3 PATH
Trusted RuntimeComposition
-> adapter context
-> command
-> route
-> exact binding
-> authority
-> capability
-> governance
-> lifecycle activation
-> SpecialistExecutionRequest
-> explicitly configured ISpecialistExecutionEngine
-> SpecialistExecutionReceipt
-> strict receipt validation
-> RuntimeOperationResult
-> lifecycle terminal mapping
-> ExecutionResult
```

No engine is inferred from adapter name, MCP client metadata, prompt content, provider availability, environment discovery, or installed host state.

The implementation is additive:

- existing `RuntimeExecutor` remains unchanged;
- `SpecialistRuntimeExecutor` subclasses it for explicit opt-in execution;
- existing `build_mcp_runtime_factory(...)` remains route-only;
- existing `build_mcp_stdio_transport(...)` remains route-only;
- optional execution is constructed through `orchestra_runtime/mcp_specialist_execution.py`.

## 4. Typed execution contracts

### `SpecialistExecutionRequest`

A request is created only after the existing pre-operation gates succeed.

It binds:

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

1. Run, command, adapter, and specialist identities come from trusted runtime state.
2. Skill source path resolves through the canonical `SkillRegistry`.
3. Skill source SHA-256 binds the exact specialist guidance source.
4. Authority and capability references bind the request to the decisions that allowed the exact runtime binding.
5. Task input is necessary execution input, not authority.
6. Execution constraints come from trusted runtime policy and remain reduction-only.
7. Execution mode is explicit; absence never silently enables host-native execution.

Machine contract:

`machine/schemas/specialist-execution-request.v1.schema.json`

### `SpecialistExecutionReceipt`

A receipt represents what an explicitly configured engine claims occurred. It is evidence and is validated before its output is accepted as an operation result.

It binds at least:

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

Optional host-evidence fields include host identity, sandbox identity, approval-policy identity, artifact references, changed paths, and timestamps.

Rules:

1. Request ID and digest must match exactly.
2. Run, command, adapter, specialist, engine ID, and engine version must match exactly.
3. Unknown or malformed receipt state fails closed.
4. Receipt evidence cannot create authority or retroactively authorize side effects.
5. Deterministic test-engine receipts cannot report side effects.
6. Raw credentials, secrets, and unnecessary full host transcripts are not ordinary receipt evidence.

Machine contract:

`machine/schemas/specialist-execution-receipt.v1.schema.json`

### `ISpecialistExecutionEngine`

The interface is intentionally narrower than an agent SDK:

```python
class ISpecialistExecutionEngine(ABC):
    @property
    def engine_id(self) -> str: ...

    @property
    def engine_version(self) -> str: ...

    def execute(
        self,
        request: SpecialistExecutionRequest,
    ) -> SpecialistExecutionReceipt: ...
```

It does not own routing, authority, capability evaluation, governance, coordination, lifecycle policy, delegation, merge decisions, release decisions, or host installation.

## 5. Runtime ownership and gate ordering

`SpecialistRuntimeExecutor` deliberately delegates the gate sequence to the existing `RuntimeExecutor`.

The configured engine is unreachable before:

1. coordination validation;
2. lifecycle initialization;
3. context assembly and command parsing;
4. deterministic routing;
5. exact runtime binding;
6. authority ALLOW;
7. capability ALLOW;
8. governance ALLOW/NOT_REQUIRED;
9. lifecycle activation.

Only then does the optional operation boundary create and execute a `SpecialistExecutionRequest`.

Adversarial tests prove engine invocation is absent on authority, capability, governance, and coordination denial.

## 6. Execution modes

### Route-only default

The existing runtime and MCP builders remain route-only. Successful output proves routing and gate passage only.

### `DETERMINISTIC_TEST_ENGINE`

Implemented for E1-E3 validation. It is no-network and no-provider. It proves request construction, exact receipt validation, lifecycle mapping, fail-closed behavior, and MCP result plumbing.

It is architectural evidence, not model intelligence.

### `HOST_NATIVE`

Defined but not yet implemented by a host bridge. It requires an explicitly configured bridge plus separately validated host capability, sandbox, approval, and scope evidence.

An installed Codex executable or an MCP connection does not activate this mode.

## 7. MCP integration

The protocol remains MCP `2026-07-28` with the existing stdio method surface:

```text
server/discover
tools/list
tools/call
```

E3 adds explicit optional builders:

```text
build_mcp_specialist_runtime_factory(...)
build_mcp_stdio_transport_with_specialist_execution(...)
```

Engine selection is constructor-owned trusted configuration. MCP prompt content and client `_meta` are non-authorizing and cannot select or activate an engine.

The deterministic engine has been exercised through `tools/call`, proving:

```text
MCP_DETERMINISTIC_ENGINE_E2E = VERIFIED
```

This is not host-native specialist proof.

## 8. Why MCP Sampling is not the host execution architecture

MCP `2026-07-28` deprecates Sampling for new integrations. Orchestra therefore does not build its new permanent execution path on Sampling.

MCP remains transport. Specialist execution remains behind a host-neutral runtime interface.

## 9. Why direct provider APIs are not the default core path

Putting direct model-provider calls into Orchestra core would create another agent harness with provider credentials, billing semantics, model-specific behavior, tool orchestration, network policy, and context management.

E1-E3 add no OpenAI, Google, Anthropic, or other provider SDK to the core runtime.

A materially different provider-specific engine would require its own governance, dependency, security, privacy, and authority review.

## 10. Codex bridge direction for E4

The preferred feasibility direction is a Codex host-native integration surface such as Codex App Server rather than deprecated MCP Sampling or default recursive `codex exec` invocation.

Before any live call, E4 must freeze:

```text
HOST_IDENTITY
HOST_VERSION
BRIDGE_VERSION
MODEL_IDENTITY_IF_HOST_EXPOSES_IT
SANDBOX_MODE
APPROVAL_POLICY
WORKSPACE_IDENTITY
ORCHESTRA_BASE_SHA
ORCHESTRA_ENGINE_HEAD_SHA
SPECIALIST
COMMAND
TASK_FIXTURE
EXPECTED_NON_MUTATING_OUTCOME
```

Mandatory blockers:

```text
NO_RECURSIVE_ORCHESTRA_MCP_LOOP
NO_HIDDEN_UNBOUNDED_NETWORK_REQUIREMENT
NO_PROVIDER_SECRET_IN_RUNTIME_AUDIT
NO_HOST_POLICY_WIDENING
NO_UNSCOPED_WORKSPACE_ACCESS
CANCELLATION_REPRESENTABLE
FAILURE_REPRESENTABLE
TIMEOUT_REPRESENTABLE
```

The bounded pre-E7 validation result is:

```text
CODEX_HOST_BRIDGE = VERIFIED_FOR_CODEX_APP_SERVER
CODEX_SPECIALIST_EXECUTION_E2E = VERIFIED_FOR_CURRENT_CODEX_CONFIGURATION_AND_BOUNDED_FIXTURES
```

## 11. E5 first live proof

The first installed-host proof is deliberately read-only:

```text
HOST = CODEX
COMMAND = review-docs
SPECIALIST = scribe
MODE = READ_ONLY
MUTATION_ALLOWED = FALSE
```

A successful proof must establish exact command acceptance, Scribe selection, authority/capability/governance passage, exact request creation, Codex bridge execution, exact matching receipt, task-specific substantive output, unchanged worktree, no recursion, and minimized audit evidence.

Only then may the evidence state:

```text
SUBSTANTIVE_SPECIALIST_EXECUTION_E2E = VERIFIED_FOR_CODEX_READ_ONLY_SCRIBE_FIXTURE
```

## 12. E6 mutation boundary

Read-only host proof is not mutation authority.

Any mutation-capable assessment must separately verify exact allowed/prohibited paths, process and network constraints, approval intersection, Git state evidence, post-execution validation, cancellation/partial-write recovery, destructive exclusions, and delegation behavior.

Destructive or high-impact mutation must not be performed merely to prove the bridge can mutate.

## 13. Security and privacy model

### Prompt and specialist instructions

Task text and specialist guidance may influence model behavior but cannot create authority.

### Host sandbox

The host sandbox is an independent lower-level constraint. If a bridge cannot enforce the stricter effective boundary, execution fails closed or is reduced to a safer authorized mode.

### Tool and network access

No specialist or host identity implies unrestricted shell, filesystem, process, or network access.

### Audit minimization

Audit records identities, decisions, status, reason codes, and evidence references. Raw prompts, credentials, entire host conversations, and full file contents are not persisted by default.

### Recursive execution

A host bridge must detect or prohibit recursive invocation that could create an unbounded Orchestra/Codex loop.

## 14. Failure semantics

Fail-closed conditions include:

```text
ENGINE_NOT_CONFIGURED
REQUEST_IDENTITY_MISMATCH
REQUEST_DIGEST_MISMATCH
SPECIALIST_IDENTITY_MISMATCH
COMMAND_IDENTITY_MISMATCH
RUN_IDENTITY_MISMATCH
ENGINE_IDENTITY_MISMATCH
ENGINE_VERSION_MISMATCH
MALFORMED_EXECUTION_RECEIPT
DETERMINISTIC_ENGINE_SIDE_EFFECT_REJECTED
SPECIALIST_ENGINE_EXCEPTION
HOST_CONSTRAINT_UNENFORCEABLE
HOST_EXECUTION_FAILED
HOST_EXECUTION_CANCELLED
HOST_EXECUTION_TIMED_OUT
RECURSIVE_EXECUTION_BLOCKED
```

An engine exception never degrades into a successful route acknowledgement.

Route-only remains an explicit compatibility path, not a fallback after requested host-native execution fails.

## 15. Evidence classification

Evidence levels remain separate:

```text
MCP_TRANSPORT_E2E
MCP_ROUTING_E2E
SPECIALIST_SELECTION
DETERMINISTIC_ENGINE_E2E
MCP_DETERMINISTIC_ENGINE_E2E
HOST_BRIDGE_E2E
SUBSTANTIVE_SPECIALIST_EXECUTION_E2E
PROTECTED_ACTION_VALIDATION
```

Current bounded state:

```text
MCP_TRANSPORT_E2E = VERIFIED
MCP_ROUTING_E2E = VERIFIED
SPECIALIST_SELECTION = VERIFIED
DETERMINISTIC_ENGINE_E2E = VERIFIED
MCP_DETERMINISTIC_ENGINE_E2E = VERIFIED
HOST_BRIDGE_E2E = VERIFIED_FOR_CODEX_READ_ONLY_SCRIBE_AND_BOUNDED_MUTATION_ASSESSMENT
SUBSTANTIVE_SPECIALIST_EXECUTION_E2E = VERIFIED_FOR_CURRENT_CODEX_CONFIGURATION_AND_BOUNDED_E5_FIXTURE
CODEX_MUTATION_BRIDGE_E2E = VERIFIED_FOR_EXACT_BOUNDED_E6_FIXTURE
```

## 16. Compatibility and authority boundary

- Existing `RuntimeExecutor(..., operation=None)` stays route-only.
- Existing MCP discovery and tool projection stay unchanged.
- Existing adapters remain valid.
- Host execution engines are optional trusted constructor dependencies.
- No automatic migration from route-only to host-native behavior exists.
- No installed integration is refreshed automatically.
- No direct provider SDK or MCP Sampling dependency is introduced.

E1-E3 performed zero live model/provider calls. The pre-E7 revalidation performed
three bounded E5 and three bounded E6 host trials using Codex CLI 0.150.1,
model `gpt-5.6-luna`, and explicit validation-input model selection. Exact
trial evidence is recorded in
`docs/validation/SPECIALIST_RUNTIME_HOST_EXECUTION_PRE_E7_EFFECTIVENESS_2026_08_29.md`.

E4-E6 are separately authorized for bounded execution through Codex CLI, subject to the frozen blockers and exclusions above.

Release publication, production deployment, policy activation, ruleset mutation, automatic installed-integration refresh, destructive cleanup, branch deletion, force push, and history rewrite remain separately controlled.
