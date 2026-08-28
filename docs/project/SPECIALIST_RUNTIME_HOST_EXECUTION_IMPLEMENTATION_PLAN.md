# Specialist Runtime-Host Execution Implementation Plan

Status: `E1_E3_IMPLEMENTED_DETERMINISTIC_FOUNDATION_E4_E6_PENDING_HOST_EXECUTION`

Architecture: `docs/project/SPECIALIST_RUNTIME_HOST_EXECUTION_ARCHITECTURE.md`

Admission record: `machine/features/specialist-runtime-host-execution.v1.json`

Canonical design baseline:

```text
BASE_SHA  = 31d4bb31c6f839d6bee6a788f8cf77d4d5367af3
BASE_TREE = af4bb0df8afb85c84675c040551b1ed06b734767
PUBLIC_RELEASE = v1.7.0
```

The maintainer separately granted blanket authorization on 2026-08-29 for bounded E1-E3 implementation and ordinary validation/remediation. E4-E6 received separate blanket authorization for execution through Codex CLI, but those live-host stages are not executed by the E1-E3 repository phase.

## 1. Objective

Move Orchestra from the default route-only path:

```text
MCP transport
-> trusted routing
-> authority/capability/governance gates
-> route acknowledgement
```

to an optional, explicit execution path:

```text
MCP transport
-> trusted routing
-> authority/capability/governance gates
-> typed SpecialistExecutionRequest
-> explicitly configured ISpecialistExecutionEngine
-> SpecialistExecutionReceipt
-> strict receipt validation
-> existing lifecycle/audit/result path
```

while preserving route-only behavior as the default and keeping host capability independent from Orchestra authority.

## 2. Frozen invariants

```text
SPECIALIST_SELECTION != SPECIALIST_EXECUTION
SPECIALIST_EXECUTION != AUTHORITY
HOST_CAPABILITY != ORCHESTRA_AUTHORITY
HOST_APPROVAL != ORCHESTRA_AUTHORITY
MCP_TRANSPORT != EXECUTION_ENGINE
VALID_RECEIPT != MERGE_AUTHORITY
SUBSTANTIVE_OUTPUT != RELEASE_AUTHORITY
```

The E1-E3 implementation must not:

- add a direct model/provider SDK to Orchestra core;
- build on deprecated MCP Sampling;
- automatically invoke Codex, Antigravity, or another installed host;
- let MCP prompt text or client metadata select an execution engine;
- refresh an installed integration;
- change the public release identity;
- change specialist routing ownership;
- weaken authority, capability, governance, coordination, lifecycle, delegation, or audit gates;
- infer host sandbox permission from adapter metadata;
- perform a live model/provider call;
- claim substantive host-native specialist execution from deterministic fixture output.

## 3. Stage E0 - Architecture and admission

Status: `COMPLETE_VALIDATED_DESIGN_CANDIDATE`

Delivered:

- `machine/features/specialist-runtime-host-execution.v1.json`
- `docs/project/SPECIALIST_RUNTIME_HOST_EXECUTION_ARCHITECTURE.md`
- this implementation plan
- `README.json` feature discoverability entry

The original E0 source head `11a7eaa52d9ce71c3b06dd2e071f4b9273c49c1a` passed Governance, validate, Required Analysis Compatibility, Cross-platform Validation, and Cosmic Ray confidence before E1-E3 implementation began.

## 4. Stage E1 - Typed execution contract foundation

Status: `IMPLEMENTED`

Implemented surfaces:

```text
orchestra_runtime/interfaces.py
orchestra_runtime/specialist_execution.py
machine/schemas/specialist-execution-request.v1.schema.json
machine/schemas/specialist-execution-receipt.v1.schema.json
```

Implemented contract:

- `ISpecialistExecutionEngine`
- immutable `SpecialistExecutionRequest`
- immutable `SpecialistExecutionReceipt`
- deterministic request digest and request identifier
- exact run, route, command, specialist, adapter, and specialist-source identity binding
- exact authority/capability decision references
- governance status/rule binding
- trusted execution constraints
- explicit execution mode
- receipt-side engine identity, outcome, evidence, and side-effect classification

Compatibility rule remains:

```text
ENGINE_ABSENT -> CURRENT_ROUTE_ONLY_BEHAVIOR
```

No constructor omission can silently enable execution.

## 5. Stage E2 - Deterministic execution engine integration

Status: `IMPLEMENTED_AND_RUNTIME_VALIDATED`

Implementation:

- `SpecialistRuntimeExecutor` subclasses the existing `RuntimeExecutor` rather than replacing it.
- The base `RuntimeExecutor` is unchanged.
- An executor-local bound task input is carried into the existing post-activation operation boundary.
- A configured engine is invoked only after the existing coordination, exact-binding, authority, capability, governance, and lifecycle activation gates.
- Engine exceptions, malformed receipts, and request/receipt identity mismatches fail closed into existing lifecycle failure outcomes.
- `FAILED`, `CANCELLED`, and `TIMED_OUT` receipts map to the existing terminal lifecycle states.
- `DETERMINISTIC_TEST_ENGINE` rejects reported side effects.

Adversarial evidence includes:

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
DETERMINISTIC_ENGINE_SIDE_EFFECT_REJECTED
ROUTE_ONLY_DEFAULT_PRESERVED
```

Pre-parity runtime evidence from source head `da1a1c0e19914f8b0fa7048c73a93e319a197292`:

```text
TESTS_TOTAL = 1926
TESTS_PASS = 1926
TESTS_FAILURES = 0
TESTS_ERRORS = 0
STATEMENT_COVERAGE = 98.22%
BRANCH_COVERAGE = 95.09%
RUNTIME_EVIDENCE_RESULT = PASS
VALIDATE_RUN = 33203755377
```

The pull-request workflow tested merge ref `46b40fdc998a4f6142921f7688125704ea2eb1ff` and explicitly bound `source_head_sha` to `da1a1c0e19914f8b0fa7048c73a93e319a197292`.

Maximum E2 claim:

```text
DETERMINISTIC_ENGINE_E2E = VERIFIED
SUBSTANTIVE_SPECIALIST_EXECUTION_E2E = NOT_CLAIMED
```

## 6. Stage E3 - MCP optional execution wiring

Status: `IMPLEMENTED_AND_DETERMINISTIC_E2E_VALIDATED`

Implemented surface:

```text
orchestra_runtime/mcp_specialist_execution.py
```

The new explicit builders are:

```text
build_mcp_specialist_runtime_factory(...)
build_mcp_stdio_transport_with_specialist_execution(...)
```

The existing builders remain unchanged and route-only:

```text
build_mcp_runtime_factory(...)
build_mcp_stdio_transport(...)
```

Properties:

1. Engine selection is trusted constructor configuration, not MCP client input.
2. MCP prompt text cannot activate or select an engine.
3. MCP `_meta` cannot activate or select an engine.
4. Protocol revision remains `2026-07-28`.
5. The MCP surface remains `server/discover`, `tools/list`, and `tools/call`.
6. A deterministic engine can return substantive fixture output through `tools/call` after existing runtime gates.
7. A host-native bridge is still absent.

Maximum E3 claim:

```text
MCP_DETERMINISTIC_ENGINE_E2E = VERIFIED
HOST_BRIDGE_E2E = NOT_VERIFIED
SUBSTANTIVE_SPECIALIST_EXECUTION_E2E = NOT_CLAIMED
```

## 7. Stage E4 - Codex host-bridge feasibility spike

Status: `AUTHORIZED_FOR_CODEX_CLI_EXECUTION_NOT_YET_EXECUTED_IN_THIS_PHASE`

Preferred direction:

- evaluate Codex App Server as the first host integration surface;
- do not build the permanent path on deprecated MCP Sampling;
- do not default to recursive `codex exec` invocation;
- preserve Codex sandbox and approval semantics explicitly;
- keep provider credentials outside Orchestra core.

Before the first live call, freeze:

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

Mandatory blocker checks:

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

## 8. Stage E5 - Installed-host read-only Scribe E2E

Status: `AUTHORIZED_FOR_CODEX_CLI_EXECUTION_NOT_YET_VERIFIED`

Frozen first proof:

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
3. Authority, capability, and governance passed.
4. Runtime created an exact specialist execution request.
5. The Codex host bridge executed Scribe guidance against the task.
6. The bridge returned an exact matching receipt.
7. The output contains task-specific analysis beyond route acknowledgement.
8. The worktree remained unchanged.
9. No recursive MCP loop occurred.
10. Audit/result evidence contains identities without unnecessary secrets or raw prompt persistence.

Only then may the evidence state:

```text
SUBSTANTIVE_SPECIALIST_EXECUTION_E2E = VERIFIED_FOR_CODEX_READ_ONLY_SCRIBE_FIXTURE
```

The claim remains bound to the exact Codex host/version/model/configuration/specialist/task/scope evidence.

## 9. Stage E6 - Mutation-capable host execution assessment

Status: `AUTHORIZED_FOR_BOUNDED_CODEX_CLI_ASSESSMENT_NOT_YET_VERIFIED`

Read-only success is not mutation authority.

Before any mutation-capable proof, define and validate:

- exact allowed path propagation;
- prohibited path enforcement;
- shell/process capability restrictions;
- network restriction behavior;
- host approval intersection;
- Git clean/dirty-state evidence;
- post-execution validation;
- cancellation and partial-mutation recovery;
- destructive-operation exclusions;
- delegation behavior.

Do not perform destructive or high-impact mutation merely to prove capability.

## 10. Stage E7 - Promotion decision

Status: `PENDING`

Promotion is not implied by E1-E6 implementation effort.

Possible dispositions remain:

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

Evaluate the original Feature Decision Record against real host evidence, security/privacy findings, host/provider coupling, reliability, maintenance burden, reversibility, and actual value over route-only plus ordinary host skills.

## 11. Ownership

| Concern | Owner | Boundary |
| --- | --- | --- |
| Execution request/receipt shape | Clockwork | Typed engineering contract only. |
| Routing and specialist identity | Conductor | Selects route; no authority grant. |
| Authority semantics | Arbiter | Existing authority remains reduction-only and pre-execution. |
| Governance applicability | Governor | Existing governance remains pre-execution. |
| Runtime capability | Clockwork | Existing capability decision remains required. |
| Cross-specialist coordination | Tuner / coordination runtime | Engine cannot bypass coordination blockers. |
| Host bridge | Host adapter owner | Host-specific mechanics behind the stable engine interface. |
| Validation/evidence | Overseer / validators | Proves contract behavior and exact-host results. |
| Merge/release decision | Maintainer | Separately controlled. |

## 12. Stop conditions

Stop rather than broadening scope if any phase requires:

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

## 13. Current bounded state

```text
E0_DESIGN = COMPLETE
E1_TYPED_CONTRACTS = IMPLEMENTED
E2_DETERMINISTIC_ENGINE = IMPLEMENTED
E3_MCP_OPTIONAL_ENGINE_WIRING = IMPLEMENTED
ROUTE_ONLY_DEFAULT = PRESERVED
DETERMINISTIC_ENGINE_E2E = VERIFIED
MCP_DETERMINISTIC_ENGINE_E2E = VERIFIED
HOST_BRIDGE = NOT_IMPLEMENTED
HOST_BRIDGE_E2E = NOT_VERIFIED
SUBSTANTIVE_SPECIALIST_EXECUTION_E2E = NOT_CLAIMED
LIVE_MODEL_CALLS_E1_E3 = 0
PROVIDER_CALLS_E1_E3 = 0
PROMOTION = PENDING
E4_E6 = SEPARATELY_AUTHORIZED_FOR_CODEX_CLI_EXECUTION
```

Release publication, production deployment, policy activation, ruleset mutation, automatic installed-integration refresh, destructive cleanup, branch deletion, force push, and history rewrite remain outside this authorization.
