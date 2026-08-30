# Priority 2 Second Provider-Native Engine Audit

Status: `P2_2A_IMPLEMENTATION_CANDIDATE`

Scope: fresh preimplementation audit and bounded implementation plan for one additional provider-native specialist execution engine after canonical P2.1.

Canonical audit baseline:

```text
ORCHESTRA_MAIN = 8798649c69e08a25c1fe20a10532dbc8c17b90ac
ORCHESTRA_TREE = 27a0d40362a2849795eda0d427606553285fc22e
P2_1 = COMPLETE_CANONICAL_VERIFIED
REGISTRY_MAIN = e5a2e1f76f8775c1bc47a6cfbefdc82375d40b79
PUBLIC_RELEASE = v1.7.0
```

## CURRENT_ARCHITECTURE

P2.1 established the descriptive, non-authorizing provider execution contract:

```text
ProviderExecutionProfile
ProviderExecutionRequirement
IProviderExecutionEngine
ProviderSpecialistRuntimeExecutor
```

The existing Codex App Server wrappers are the only canonical provider-native engine implementation at the audit baseline. Existing IDE/host adapters, including Antigravity and Claude Code, are host integration surfaces and do not become provider-native engines merely because adapter routing exists.

The default runtime and default MCP runtime remain route-only. Provider-native execution remains explicit constructor-owned trusted configuration.

## CURRENT_PROVIDER_SURFACES

### Codex

Current evidence supports a bounded provider-native Codex App Server bridge, explicit user-selected model identity, deterministic provider profile mapping, structured output, cancellation, approval control, network restriction, host-activity observation, and a separately represented read-only sandbox control for the read-only engine.

### Antigravity

Historical Orchestra C1 calibration proves that Antigravity CLI and a Gemini model completed the frozen comparative benchmark. That historical benchmark is calibration evidence, not current provider-native execution qualification.

Current Antigravity headless documentation exposes non-interactive execution, model selection, structured output, timeout, permissions, and sandbox controls. However, the documented headless default permits workspace file reads and writes, while more granular permission policy is persisted in user settings. This audit does not mutate persistent user permission settings or infer an invocation-scoped read-only workspace guarantee that has not been demonstrated.

Disposition:

```text
ANTIGRAVITY_PROVIDER_NATIVE_ENGINE = DEFERRED_PENDING_FRESH_BOUNDARY_PROOF
HISTORICAL_BENCHMARK_AVAILABILITY = INSUFFICIENT_FOR_RUNTIME_QUALIFICATION
```

### Claude Code

Current Claude Code CLI documentation exposes a narrower invocation-scoped boundary suitable for a first provider-native candidate:

```text
non-interactive print mode
explicit model selection
JSON output
JSON Schema structured output
permission mode selection
explicit built-in tool restriction
explicit tool denial patterns
safe mode / customization suppression
browser disablement
session-persistence disablement
```

The candidate can therefore expose only read-oriented built-ins (`Read`, `Glob`, `Grep`), deny MCP tools, disable browser/customizations/session persistence, require explicit model identity and schema-conforming output, and independently verify an unchanged repository before accepting a receipt.

## CONFIRMED_GAPS

At the audit baseline:

1. Orchestra has only one canonical provider-native engine family, Codex.
2. Existing Antigravity and Claude Code adapters do not implement `IProviderExecutionEngine`.
3. No automatic provider routing or fallback exists.
4. No second-provider qualification exists under the P2.1 profile contract.
5. Current evidence is insufficient to claim a provider-general OS-level read-only sandbox abstraction.
6. Current evidence is insufficient to claim cross-provider streaming host-activity observation.

## HISTORICAL_ASSUMPTIONS_INVALIDATED

The following assumptions are rejected for this increment:

```text
ADAPTER_SUPPORT == PROVIDER_NATIVE_EXECUTION
HISTORICAL_PROVIDER_BENCHMARK == CURRENT_RUNTIME_QUALIFICATION
MODEL_AVAILABILITY == EXECUTION_AUTHORITY
HOST_TOOL_RESTRICTION == OS_SANDBOX_PROOF
SECOND_ENGINE_IMPLEMENTATION == AUTOMATIC_ROUTING_AUTHORITY
```

Antigravity C1 remains useful evidence that provider availability and provider outages are real operational dimensions. It does not authorize or prove the new runtime bridge.

## COMPLIANCE_IMPACT

P2.2A does not mutate the Orchestra Compliance Registry and does not redefine the Registry's platform/distribution-oriented provider vocabulary.

The candidate uses an installed host CLI and introduces no Anthropic SDK, direct provider API, credential store, billing surface, or provider-secret persistence inside Orchestra.

No credentials, API keys, raw host conversations, or full file contents are added to ordinary provider evidence.

Any later direct provider API/SDK integration remains a separate dependency, provenance, credential, security, privacy, and compliance boundary.

## MINIMUM_IMPLEMENTATION_BOUNDARY

The selected bounded unit is:

```text
P2.2A_CLAUDE_CODE_PROVIDER_NATIVE_ENGINE
```

Implementation boundary:

1. Add a read-only Claude Code `ISpecialistExecutionEngine` bridge.
2. Require an explicit model identifier in trusted configuration.
3. Require Claude Code CLI version `>= 2.1.205` for the structured-output contract used by the bridge.
4. Restrict host tools exactly to `Read`, `Glob`, and `Grep`.
5. Deny MCP tools with an explicit disallowed-tool pattern.
6. Enable safe mode and disable browser/customization/session persistence surfaces used by this bridge.
7. Use `plan` permission mode and never use bypass-permissions mode.
8. Never configure a fallback model.
9. Bind the exact specialist source path and digest.
10. Require a clean repository before execution and exact repository-state equality after execution.
11. Require schema-conforming structured output with `non_mutating=true`.
12. Map the bridge into `IProviderExecutionEngine` with provider ID `anthropic-claude-code`.
13. Advertise only evidence-backed provider capabilities.

The provider profile intentionally advertises:

```text
APPROVAL_CONTROL
CANCELLATION
NETWORK_RESTRICTION
STRUCTURED_OUTPUT
```

It intentionally does not advertise:

```text
READ_ONLY_SANDBOX_CONTROL
HOST_ACTIVITY_OBSERVATION
```

The first omission prevents tool-surface restriction from being mislabeled as OS-level sandbox proof. The second prevents final JSON output from being mislabeled as streaming host-activity telemetry.

## TEST_STRATEGY

Deterministic qualification must prove:

- explicit model identity reaches the provider profile and invocation;
- provider profile identity changes deterministically with model identity;
- policy widening in permission mode or tool set fails during configuration;
- wrong execution mode, specialist, command, project root, or specialist digest fails before host invocation;
- dirty worktree fails before host invocation;
- CLI version below the structured-output floor fails before provider execution;
- timeout maps to a typed terminal receipt;
- nonzero host exit, malformed output, missing structured output, unsuccessful result subtype, or missing non-mutating affirmation fails closed;
- repository-state drift after host execution fails closed;
- accepted receipts contain minimized host/provider evidence and no changed paths;
- the invocation never enables bypass permissions or fallback model behavior.

Repository-wide exact-head Governance, runtime coverage, Required Analysis Compatibility, native Windows/Ubuntu/macOS, Cosmic Ray, documentation-impact, review-thread, signature, and mergeability gates remain authoritative for canonical merge readiness.

## MIGRATION_COMPATIBILITY

P2.2A is additive.

The following remain unchanged:

```text
DEFAULT_RUNTIME = ROUTE_ONLY
DEFAULT_MCP = ROUTE_ONLY
DETERMINISTIC_TEST_ENGINE = PROVIDER_FREE
CODEX_PROVIDER_ENGINE = PRESERVED
IDE_ADAPTERS = PRESERVED
STATIC_MODEL_CATALOG = ABSENT
PROMPT_DRIVEN_MODEL_SELECTION = DENIED
AUTOMATIC_PROVIDER_DISCOVERY = ABSENT
AUTOMATIC_PROVIDER_ROUTING = ABSENT
AUTOMATIC_PROVIDER_FALLBACK = ABSENT
```

The Claude Code provider engine is explicit opt-in trusted construction only.

## OUT_OF_SCOPE_ITEMS

P2.2A does not include:

- a live Claude provider effectiveness claim;
- automatic multi-provider routing;
- provider fallback or failover;
- direct Anthropic API/SDK integration;
- credential storage or mutation;
- global Claude Code settings mutation;
- installation or integration refresh;
- automatic model discovery;
- a static global model catalog;
- token-price, latency, or cost-aware routing;
- generic context-window management;
- generic temperature/top-p normalization;
- Antigravity provider-native implementation;
- Claude Code Host Update maturity graduation;
- release or tag movement;
- deployment or production mutation;
- Registry mutation or republication.

## PROTECTED_ACTIONS

This unit grants no authority for:

```text
RELEASE_OR_PUBLICATION
TAG_MOVEMENT
DEPLOYMENT
PRODUCTION_MUTATION
POLICY_ACTIVATION
RULESET_BYPASS_OR_WEAKENING
INSTALLED_INTEGRATION_REFRESH
CREDENTIAL_MUTATION
DESTRUCTIVE_CLEANUP
BRANCH_DELETION
FORCE_PUSH
HISTORY_REWRITE
```

## Audit decision

The smallest evidence-backed next unit is Claude Code provider-native bridge implementation and deterministic qualification.

```text
P2_2A_PREIMPLEMENTATION_AUDIT = COMPLETE
SELECTED_ENGINE = CLAUDE_CODE
IMPLEMENTATION_SCOPE = READ_ONLY_PROVIDER_NATIVE_BRIDGE
LIVE_PROVIDER_E2E = NOT_CLAIMED
AUTOMATIC_ROUTING = NOT_AUTHORIZED_BY_IMPLEMENTATION_SUCCESS
REGISTRY_MUTATION_REQUIRED = FALSE
```

A later routing-policy unit still requires current trustworthy evidence for at least one additional provider-native engine. P2.2A implementation alone does not satisfy that evidence threshold until the provider-native bridge itself receives separately recorded current host/provider qualification.
