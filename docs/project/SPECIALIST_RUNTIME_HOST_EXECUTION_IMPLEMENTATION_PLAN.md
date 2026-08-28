# Specialist Runtime-Host Execution Implementation Plan

Status: `PLANNED_NOT_IMPLEMENTED`

Architecture: `docs/project/SPECIALIST_RUNTIME_HOST_EXECUTION_ARCHITECTURE.md`

Admission record: `machine/features/specialist-runtime-host-execution.v1.json`

Canonical design baseline:

```text
BASE_SHA  = 31d4bb31c6f839d6bee6a788f8cf77d4d5367af3
BASE_TREE = af4bb0df8afb85c84675c040551b1ed06b734767
```

This plan decomposes future implementation into separately reviewable stages. It does not authorize implementation, live host execution, provider/model calls, integration refresh, protected actions, merge, release, or deployment.

## 1. Objective

Move Orchestra from:

```text
MCP transport -> trusted routing -> route acknowledgement
```

to an optional path capable of:

```text
MCP transport
-> trusted routing
-> authority/capability/governance gates
-> typed specialist execution request
-> explicitly configured execution engine
-> validated execution receipt
-> existing lifecycle/audit/result path
```

while keeping route-only behavior as the default and preserving all existing authority boundaries.

## 2. Frozen non-goals

The first implementation must not:

- add direct provider SDKs to Orchestra core;
- build on deprecated MCP Sampling;
- automatically invoke Codex, Antigravity, or another host merely because it is installed;
- refresh an installed host integration;
- change public release identity;
- introduce Streamable HTTP;
- change the routing map or specialist ownership;
- weaken current authority, capability, governance, lifecycle, delegation, coordination, or audit checks;
- infer sandbox permission from adapter metadata;
- perform live model/provider calls during deterministic foundation stages;
- claim specialist execution E2E from deterministic fixture output.

## 3. Stage E0 - Architecture and admission

Status for this phase: `IN_SCOPE_NOW`

Deliverables:

- `machine/features/specialist-runtime-host-execution.v1.json`
- `docs/project/SPECIALIST_RUNTIME_HOST_EXECUTION_ARCHITECTURE.md`
- this implementation plan

Acceptance:

```text
FEATURE_ADMISSION = ADMIT_FOR_BOUNDED_DESIGN
PROMOTION = PENDING
RUNTIME_CODE_CHANGE = NONE
LIVE_MODEL_CALLS = 0
HOST_MUTATION = NONE
```

Exit condition: exact-head repository validation and maintainer merge authorization for the design artifacts.

## 4. Stage E1 - Typed execution contract foundation

Requires fresh implementation authority.

Proposed files:

```text
orchestra_runtime/models.py
orchestra_runtime/interfaces.py
orchestra_runtime/services.py
machine/schemas/specialist-execution-request.v1.schema.json
machine/schemas/specialist-execution-receipt.v1.schema.json
tests/runtime/test_specialist_execution_contract.py
```

Work:

1. Add immutable `SpecialistExecutionRequest`.
2. Add immutable `SpecialistExecutionReceipt`.
3. Add `ISpecialistExecutionEngine`.
4. Add request/receipt schema parity where machine interchange is needed.
5. Extend runtime audit event vocabulary only if necessary for request/receipt identity evidence.
6. Preserve existing `RuntimeOperationResult` as the lifecycle-facing operation result.
7. Do not yet wire a live host or provider.

Important design correction:

The execution engine must receive a typed request that contains the original task input and exact identity references. It must not use the current three-argument route-only callback as the long-term substantive execution contract.

Compatibility requirement:

```text
ENGINE_ABSENT -> CURRENT_ROUTE_ONLY_BEHAVIOR
```

No constructor omission may silently enable execution.

## 5. Stage E2 - Runtime integration with deterministic test engine

Requires fresh implementation authority after E1 is reviewed.

Proposed files:

```text
orchestra_runtime/services.py
tests/runtime/test_specialist_execution_engine.py
tests/runtime/test_specialist_execution_adversarial.py
```

Work:

1. Create the execution request only after:
   - exact runtime binding;
   - authority ALLOW;
   - capability ALLOW;
   - governance ALLOW;
   - lifecycle activation eligibility.
2. Inject a deterministic test engine from tests.
3. Validate receipt identity before accepting its output.
4. Map valid receipts to existing `RuntimeOperationResult` and lifecycle transitions.
5. Map invalid receipts and engine failures to deterministic failures.
6. Prove no engine call occurs on authority, capability, governance, coordination, or binding denial.
7. Prove prompts or host metadata cannot switch execution mode or engine identity.

Required tests include:

```text
NO_ENGINE_CALL_BEFORE_AUTHORITY
NO_ENGINE_CALL_BEFORE_CAPABILITY
NO_ENGINE_CALL_BEFORE_GOVERNANCE
NO_ENGINE_CALL_ON_COORDINATION_BLOCK
REQUEST_BINDS_EXACT_ROUTE
REQUEST_BINDS_EXACT_SKILL_DIGEST
REQUEST_BINDS_EXACT_DECISION_REFS
PROMPT_CANNOT_GRANT_EXECUTION_ENGINE
HOST_METADATA_CANNOT_GRANT_EXECUTION_ENGINE
RECEIPT_RUN_MISMATCH_FAILS_CLOSED
RECEIPT_SPECIALIST_MISMATCH_FAILS_CLOSED
RECEIPT_COMMAND_MISMATCH_FAILS_CLOSED
RECEIPT_DIGEST_MISMATCH_FAILS_CLOSED
ENGINE_EXCEPTION_IS_NOT_SUCCESS
ROUTE_ONLY_DEFAULT_PRESERVED
```

Evidence claim at E2 maximum:

```text
DETERMINISTIC_ENGINE_E2E = VERIFIED
SUBSTANTIVE_SPECIALIST_EXECUTION_E2E = NOT_CLAIMED
```

## 6. Stage E3 - MCP wiring to the optional engine

Requires fresh implementation authority.

Proposed files:

```text
orchestra_runtime/mcp_transport.py
tests/runtime/test_mcp_transport.py
tests/runtime/test_mcp_specialist_execution.py
docs/developer/MCP_STDIO_TRANSPORT.md
```

Work:

1. Allow trusted MCP runtime construction to receive an explicit engine or engine factory.
2. Keep existing `build_mcp_stdio_transport(...)` route-only unless explicitly configured.
3. Keep MCP client metadata non-authorizing.
4. Keep tool input schema bounded to task input unless a separately admitted requirement adds structured reduction-only constraints.
5. Prove the deterministic engine can flow through `tools/call` and return the engine output.
6. Preserve protocol revision `2026-07-28` and the current three-method stdio surface unless a separate protocol need is demonstrated.

Maximum E3 claim:

```text
MCP_DETERMINISTIC_ENGINE_E2E = VERIFIED
HOST_BRIDGE_E2E = NOT_VERIFIED
SUBSTANTIVE_SPECIALIST_EXECUTION_E2E = NOT_CLAIMED
```

## 7. Stage E4 - Host bridge feasibility spike

Requires separate authority because this stage can involve an installed host and live model/provider execution.

First candidate: Codex host-native bridge.

Preferred investigation direction:

- evaluate Codex App Server as the host integration surface;
- do not build the permanent path on deprecated MCP Sampling;
- do not default to recursive `codex exec` subprocess invocation;
- preserve host sandbox/approval semantics explicitly;
- keep provider credentials outside Orchestra core.

Before any live call, freeze:

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

Initial live proof should be read-only, preferably Scribe `review-docs`, because it can demonstrate substantive specialist reasoning without requiring repository mutation.

Required blocker checks:

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

If these cannot be established, E4 terminates without promotion.

## 8. Stage E5 - Installed-host read-only specialist E2E

Requires explicit live-host execution authority.

Suggested bounded proof:

```text
HOST = CODEX
COMMAND = review-docs
SPECIALIST = scribe
MODE = READ_ONLY
MUTATION_ALLOWED = FALSE
```

Success requires evidence that:

1. MCP accepted the exact command.
2. Runtime selected Scribe.
3. Authority/capability/governance all passed.
4. Runtime created an exact specialist execution request.
5. The host bridge executed the Scribe guidance against the task.
6. The bridge returned an exact matching receipt.
7. The substantive output contains task-specific analysis not present in the route acknowledgement.
8. The worktree remained unchanged.
9. No recursive MCP loop occurred.
10. Audit/result evidence contains identities but not raw secrets or unnecessary prompt content.

Only then may the evidence say:

```text
SUBSTANTIVE_SPECIALIST_EXECUTION_E2E = VERIFIED_FOR_CODEX_READ_ONLY_SCRIBE_FIXTURE
```

That claim remains host-, version-, model-, configuration-, specialist-, task-, and scope-specific until broader evidence exists.

## 9. Stage E6 - Mutation-capable host execution assessment

Not authorized by the design phase.

Mutation support is not a natural consequence of read-only E2E.

Before considering it, define and test:

- exact path scope propagation;
- prohibited path enforcement;
- shell/process capability restrictions;
- network restriction behavior;
- approval intersection;
- Git dirty-state evidence;
- post-execution validation;
- cancellation and partial-mutation recovery;
- destructive operation exclusions;
- delegation behavior.

Read-only success must not be used as mutation authority.

## 10. Stage E7 - Promotion decision

Promotion remains `PENDING` until proportional evidence exists.

Evaluate the original Feature Decision Record against:

- problem solved or not solved;
- host-neutral contract stability;
- maintenance burden of host bridges;
- security and privacy findings;
- provider/host coupling;
- installed-host reliability;
- actual value over route-only plus ordinary host skills;
- reversibility.

Possible outcomes include:

```text
ADOPT
ADOPT_SIMPLIFIED
ADOPT_OPTIONAL
REPLACE_WITH_CONFIGURATION
EXPERIMENT_ONLY
DEFER
REJECT_NO_MEASURABLE_VALUE
REJECT_COMPLEXITY_EXCEEDS_BENEFIT
```

Implementation effort does not predetermine promotion.

## 11. Proposed contract ownership

| Concern | Owner | Boundary |
| --- | --- | --- |
| Execution request/receipt shape | Clockwork | Defines typed engineering contract only. |
| Routing and specialist identity | Conductor | Selects route; no authority or execution grant. |
| Authority semantics | Arbiter | Existing authority remains reduction-only and pre-execution. |
| Governance applicability | Governor | Existing governance remains pre-execution. |
| Runtime capability | Clockwork | Existing capability decision remains required. |
| Cross-specialist coordination | Tuner / existing coordination runtime | Execution engine cannot bypass coordination blockers. |
| Host bridge | Host adapter owner | Implements host-specific mechanics behind the stable engine interface. |
| Validation/evidence | Overseer / repository validators | Proves contract behavior and exact-host results. |
| Merge/release decision | Maintainer | Remains separately gated. |

## 12. Documentation impact by stage

### E0

New design/admission docs only.

### E1-E2

Likely updates:

```text
docs/project/SPECIALIST_RUNTIME_HOST_EXECUTION_ARCHITECTURE.md
docs/project/OOP_RUNTIME_ARCHITECTURE.md
README.json if capability status becomes implemented
CHANGELOG.md after canonical implementation state changes
```

### E3-E5

Likely updates:

```text
docs/developer/MCP_STDIO_TRANSPORT.md
docs/developer/README.md
docs/validation/<host-proof>.md
README.md only if the landing-page trust model materially changes
README.json for exact current capability/evidence state
```

No documentation should claim broader host execution maturity than the evidence supports.

## 13. Stop conditions

Stop and escalate rather than broadening scope when any of the following occurs:

```text
REQUIRES_AUTHORITY_MODEL_WEAKENING
REQUIRES_GOVERNANCE_BYPASS
REQUIRES_HOST_CAPABILITY_TO_GRANT_AUTHORITY
REQUIRES_PROVIDER_SECRET_IN_CORE_CONFIG
REQUIRES_DEPRECATED_PROTOCOL_AS_PERMANENT_DEPENDENCY
REQUIRES_UNVERIFIABLE_HIDDEN_HOST_STATE
REQUIRES_AUTOMATIC_INSTALLED_INTEGRATION_REFRESH
REQUIRES_UNBOUNDED_RECURSION
REQUIRES_ROUTE_ONLY_FALLBACK_AFTER_REQUESTED_HOST_FAILURE
```

## 14. Current terminal state

At completion of the design phase:

```text
SPECIALIST_RUNTIME_HOST_EXECUTION_DESIGN = COMPLETE
FEATURE_ADMISSION = ADMIT
PROMOTION = PENDING
CANDIDATE_MATURITY = NOT_STARTED
RUNTIME_INTEGRATION = FALSE
MCP_BEHAVIOR_CHANGE = FALSE
LIVE_MODEL_CALLS = 0
PROVIDER_CALLS = 0
HOST_BRIDGE = NOT_IMPLEMENTED
SUBSTANTIVE_SPECIALIST_EXECUTION_E2E = NOT_VERIFIED
```
