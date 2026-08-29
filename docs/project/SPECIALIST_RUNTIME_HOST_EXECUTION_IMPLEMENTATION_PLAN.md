# Specialist Runtime-Host Execution Implementation Plan

Status: `E0_E7_COMPLETE_ADOPT_OPTIONAL`

Architecture: `docs/project/SPECIALIST_RUNTIME_HOST_EXECUTION_ARCHITECTURE.md`

Admission and promotion record: `machine/features/specialist-runtime-host-execution.v1.json`

Canonical design baseline:

```text
BASE_SHA  = 31d4bb31c6f839d6bee6a788f8cf77d4d5367af3
BASE_TREE = af4bb0df8afb85c84675c040551b1ed06b734767
PUBLIC_RELEASE = v1.7.0
```

## 1. Objective

Move Orchestra from the default route-only path to an optional, explicitly configured specialist execution path while preserving authority, capability, governance, lifecycle, and host-policy boundaries.

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

Route-only behavior remains the default.

## 2. Frozen invariants

```text
SPECIALIST_SELECTION != SPECIALIST_EXECUTION
SPECIALIST_EXECUTION != AUTHORITY
HOST_CAPABILITY != ORCHESTRA_AUTHORITY
HOST_APPROVAL != ORCHESTRA_AUTHORITY
ORCHESTRA_AUTHORITY != HOST_PERMISSION
MCP_TRANSPORT != EXECUTION_ENGINE
VALID_RECEIPT != MERGE_AUTHORITY
SUBSTANTIVE_OUTPUT != RELEASE_AUTHORITY
MODEL_SELECTION != EXECUTION_AUTHORITY
WRITE_SCOPE_ENFORCEMENT != FULL_READ_ISOLATION
```

## 3. E0-E3 deterministic foundation

- E0 architecture/admission: complete.
- E1 typed execution contracts: implemented.
- E2 deterministic execution engine integration: implemented and runtime validated.
- E3 optional MCP execution wiring: implemented and deterministic E2E validated.
- Existing route-only builders remain unchanged and default.
- MCP prompt text and client metadata cannot activate or select an execution engine.

## 4. E4 Codex host-bridge feasibility

Status: `VERIFIED_FOR_CODEX_APP_SERVER_BOUNDED_EXECUTION`

Codex App Server was validated as the first bounded host integration surface without introducing a direct provider SDK into Orchestra core or allowing host capability to widen Orchestra authority.

## 5. E5 installed-host read-only Scribe

Status: `VERIFIED_REPEATABLE_AND_CANONICALLY_CONFIRMED`

```text
HOST = CODEX
COMMAND = review-docs
SPECIALIST = scribe
MODE = READ_ONLY
MUTATION_ALLOWED = FALSE
```

Evidence includes 3/3 repeatability trials plus 1/1 canonical-alignment confirmation. Repository HEAD/tree and worktree preservation, exact request/receipt identity, task-specific output, approval-never, network-disabled, and recursion-prevention boundaries passed.

## 6. E6 bounded mutation assessment

Status: `VERIFIED_REPEATABLE_AND_CANONICALLY_CONFIRMED`

The Ponytail fixture was constrained to the isolated single file `mutation/target.md`. Evidence includes 3/3 repeatability trials plus 1/1 canonical-alignment confirmation with zero out-of-scope mutations, protected-file changes, skill-source changes, unexpected network activity, process execution, or delegation.

Read-only success remains distinct from mutation authority, and bounded write-scope enforcement is not claimed as full read isolation.

## 7. Model-selection correction

New validation requires explicit user/host configuration. The promoted surface does not treat the historical Sol proof model as Orchestra's runtime default.

```text
MODEL_SELECTION_SOURCE = USER_CONFIG
MODEL_SELECTION_FROM_PROMPT = DENIED
MODEL_SELECTION_FROM_TASK_TEXT = DENIED
MODEL_SELECTION_FROM_MCP_META = DENIED
MODEL_SELECTION != EXECUTION_AUTHORITY
```

Historical E5/E6 proof identities remain historical evidence and are not rewritten.

## 8. Pre-E7 effectiveness validation

Status: `PASS_CANONICALLY_REALIGNED`

```text
E5_REPEATABILITY = 3/3
E6_REPEATABILITY = 3/3
E5_CANONICAL_CONFIRMATION = 1/1
E6_CANONICAL_CONFIRMATION = 1/1
TOTAL_SUBSTANTIVE_LIVE_TRIALS = 8/8
BOUNDARY_VIOLATIONS = 0
IDENTITY_MISMATCHES = 0
OUT_OF_SCOPE_MUTATIONS = 0
```

Canonical evidence package: `docs/validation/SPECIALIST_RUNTIME_HOST_EXECUTION_PRE_E7_EFFECTIVENESS_2026_08_29.md` and PR #638.

## 9. E7 promotion decision

Status: `DECIDED_ADOPT_OPTIONAL`

Decision evidence: `docs/validation/SPECIALIST_RUNTIME_HOST_EXECUTION_E7_PROMOTION_DECISION_2026_08_30.md`.

The capability is retained as supported optional behavior because the bounded host execution path demonstrated measurable substantive execution value while preserving the tested trust boundaries. Route-only behavior remains default, default runtime mutation remains disabled, and generic MCP mutation E2E remains unclaimed.

The decision is intentionally narrower than default adoption because validation remains bound to the current Codex configuration and bounded E5/E6 fixtures.

## 10. Current bounded state

```text
E0_DESIGN = COMPLETE
E1_TYPED_CONTRACTS = COMPLETE
E2_DETERMINISTIC_ENGINE = COMPLETE
E3_MCP_OPTIONAL_ENGINE_WIRING = COMPLETE
E4_CODEX_HOST_BRIDGE = VERIFIED
E5_READ_ONLY_SCRIBE = VERIFIED_REPEATABLE_AND_CANONICALLY_CONFIRMED
E6_BOUNDED_PONYTAIL_MUTATION = VERIFIED_REPEATABLE_AND_CANONICALLY_CONFIRMED
E7_PROMOTION = ADOPT_OPTIONAL
SPECIALIST_RUNTIME_HOST_EXECUTION = SUPPORTED_OPTIONAL
ROUTE_ONLY_DEFAULT = PRESERVED
DEFAULT_RUNTIME_MUTATION = NOT_ENABLED
MCP_MUTATION_E2E = NOT_CLAIMED
PRE_E7_EFFECTIVENESS_REVALIDATION = PASS_CANONICALLY_REALIGNED
```

## 11. Closeout boundary

E7 completes the currently defined Specialist Runtime-Host Execution track. It does not automatically authorize a productization, multi-host, model-discovery, isolation-expansion, generic mutation, or MCP mutation campaign.

Any newly discovered gap that suggests implementation beyond this track must be presented to the maintainer first with its purpose, risk of deferral, and whether it is required or optional.

Release publication, production deployment, policy activation, ruleset mutation, automatic installed-integration refresh, destructive cleanup, branch deletion, force push, and history rewrite remain separately controlled.
