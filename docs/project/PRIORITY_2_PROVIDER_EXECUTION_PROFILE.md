# Priority 2 Provider Execution Profile and Requirement Gate

Status: `P2_1_IMPLEMENTATION_CANDIDATE`

Scope: bounded Priority 2 provider identity/capability representation and trusted requirement enforcement only.

This increment does not implement automatic provider routing, provider fallback, direct provider APIs, credential management, pricing optimization, model discovery, a static model catalog, release publication, deployment, policy activation, or installed-integration refresh.

## Purpose

Orchestra already separates host adapters, runtime authority/capability grants, and optional host-native specialist execution. The Codex host bridge additionally carries model selection, structured output, sandbox, network, approval, cancellation, and host-activity controls, but those execution facts were previously Codex-specific implementation details rather than a reusable typed provider contract.

P2.1 adds a fourth, explicitly non-authorizing concept:

```text
PROVIDER_EXECUTION_PROFILE = DESCRIPTIVE_EXECUTION_CAPABILITY
PROVIDER_EXECUTION_PROFILE != RUNTIME_CAPABILITY_GRANT
PROVIDER_EXECUTION_PROFILE != AUTHORITY
PROVIDER_SELECTION != AUTHORITY
MODEL_SELECTION != AUTHORITY
```

## Contracts

`orchestra_runtime/provider_execution.py` defines:

- `ProviderExecutionCapability`
- `ProviderExecutionProfile`
- `ProviderExecutionRequirement`
- `IProviderExecutionEngine`
- `ProviderSpecialistRuntimeExecutor`

Machine schemas:

- `machine/schemas/provider-execution-profile.v1.schema.json`
- `machine/schemas/provider-execution-requirement.v1.schema.json`

A profile binds:

```text
profile_version
profile_id
provider_id
model_id
capabilities
profile_digest
```

`profile_id` and `profile_digest` are deterministic over the canonical provider/model/capability payload. Capability order therefore cannot change profile identity.

The initial capability vocabulary is intentionally small and evidence-backed:

```text
STRUCTURED_OUTPUT
CANCELLATION
READ_ONLY_SANDBOX_CONTROL
NETWORK_RESTRICTION
APPROVAL_CONTROL
HOST_ACTIVITY_OBSERVATION
```

No generic token limit, price, temperature, top-p, multimodality, latency, or provider-ranking contract is introduced by P2.1.

## Trusted requirement gate

`ProviderExecutionRequirement` can constrain any combination of:

```text
required_provider_id
required_model_id
required_capabilities
```

The provider-aware runtime is explicit and host-native. Requirement and engine selection are constructor-owned trusted configuration.

Prompt text, specialist guidance, MCP client metadata, and tool arguments cannot select or override the provider profile or requirement.

Execution remains ordered as:

```text
coordination
-> routing / exact binding
-> authority
-> runtime capability
-> governance
-> lifecycle activation
-> provider profile drift check
-> trusted provider requirement match
-> host execution engine
-> receipt validation
-> lifecycle terminal result
```

A provider/model/capability mismatch fails before provider-engine invocation. Authority, runtime capability, governance, and coordination denials continue to occur before the provider gate is reached.

Provider mismatch does not fall back to another provider and does not degrade into successful route-only output.

## Compatibility

P2.1 is additive.

The following remain unchanged:

```text
RuntimeExecutor default = route-only
SpecialistRuntimeExecutor default contract = unchanged
DETERMINISTIC_TEST_ENGINE = provider-free
existing MCP builder = route-only
existing specialist MCP builder = unchanged
existing IDE/host adapters = unchanged
```

Provider-aware MCP execution uses the separate opt-in builders in `orchestra_runtime/provider_mcp_execution.py`.

## Codex mapping

`internal/codex_provider_execution.py` provides provider-aware wrappers over the existing Codex App Server engines.

Provider identity:

```text
provider_id = openai-codex
```

Model identity remains the explicit trusted model selected through the existing `CodexUserModelSelection` configuration path.

The read-only wrapper advertises the common bounded Codex capabilities plus `READ_ONLY_SANDBOX_CONTROL`. The bounded mutation-assessment wrapper advertises only the common capabilities and does not falsely claim a read-only sandbox.

The wrappers do not modify approval, network, sandbox, write-path, specialist, or command controls in the existing Codex engines.

## Evidence minimization

Provider-aware terminal evidence adds only:

```text
execution-provider:<provider_id>
model:<model_id>
provider-profile:<profile_id>
provider-profile-digest:<sha256>
```

Credentials, API keys, full host conversations, raw prompts, and file contents are not provider-profile fields and are not introduced into ordinary provider evidence by this increment.

## Current routing boundary

P2.1 does not claim a second current provider-native engine. Antigravity, Claude Code, and the other Orchestra host adapters remain distinct host-integration surfaces until separately revalidated or implemented against the provider execution contract.

Therefore:

```text
EXPLICIT_PROVIDER_REPRESENTATION = IMPLEMENTED_CANDIDATE
EXPLICIT_PROVIDER_REQUIREMENTS = IMPLEMENTED_CANDIDATE
FAIL_CLOSED_PROFILE_MATCHING = IMPLEMENTED_CANDIDATE
AUTOMATIC_MULTI_PROVIDER_ROUTING = NOT_IMPLEMENTED
AUTOMATIC_PROVIDER_FALLBACK = NOT_IMPLEMENTED
DIRECT_PROVIDER_API = NOT_IMPLEMENTED
```

A future automatic routing decision requires current evidence for at least one additional provider-native execution engine and a separately reviewed routing policy. Historical benchmark provider availability or adapter compatibility alone is insufficient.

## Compliance boundary

P2.1 does not mutate the Orchestra Compliance Registry. The Registry's existing provider vocabulary remains platform/distribution oriented and is not redefined by this runtime contract.

Any future direct provider SDK/API integration requires separate dependency, provenance, credential, security, privacy, and compliance review.

## Validation target

P2.1 focused regression coverage proves:

- deterministic profile identity and schema validity;
- duplicate/invalid capability rejection;
- exact trusted provider/model/capability requirement matching;
- mismatch before engine invocation;
- authority denial before the provider gate;
- provider profile drift detection;
- prompt/MCP metadata inability to override provider configuration;
- minimized provider evidence;
- explicit Codex user model mapping without security-policy widening;
- provider-aware MCP opt-in behavior.

Repository-wide required validation remains authoritative for merge readiness. Validation success does not create merge, release, deployment, policy, destructive, credential, or integration-refresh authority.
