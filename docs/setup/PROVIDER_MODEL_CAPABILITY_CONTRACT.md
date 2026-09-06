# UAI Provider/Model Capability Contract

The canonical provider/model capability contract is [provider-model-capability-contract.v1.json](../../machine/providers/provider-model-capability-contract.v1.json), validated by [provider-model-capability-contract.v1.schema.json](../../machine/schemas/provider-model-capability-contract.v1.schema.json) and [validate_provider_model_capability_contract.py](../../scripts/validate_provider_model_capability_contract.py).

It defines the technical capability vocabulary needed by UAI without selecting a provider, model, host, specialist, or workflow topology. The vocabulary covers tool calling, structured output, context limits, multimodal input, host-exposed code/terminal access, sub-agents, concurrency exposure, MCP compatibility, model selection, reasoning/runtime modes, permission semantics, and provider-policy restrictions.

The current contract deliberately contains no provider/model profile. Current repository evidence does not establish a fresh provider/model capability observation that can be promoted into a canonical profile. The empty profile set is therefore an explicit evidence boundary, not an inferred absence of provider capability.

Provider/model profiles, when admitted later, require exact provider/model identity, provenance, freshness, per-capability dispositions, and authority fields fixed to false. `SUPPORTED_VERIFIED` and `SUPPORTED_WITH_LIMITS` require current evidence. Static declarations remain `AVAILABLE_NOT_YET_VERIFIED`; unknown identity remains `UNKNOWN`.

This contract does not authorize automatic provider switching, fallback, credential changes, learned-routing promotion, specialist routing, AWF topology changes, or execution. P2.1's [Provider Execution Profile](../project/PRIORITY_2_PROVIDER_EXECUTION_PROFILE.md) remains the narrower trusted execution requirement gate. A capability profile describes what may be observable; it never becomes a runtime grant.

UAI-4 resolves transport separately with the pure `resolve_integration_strategy` domain function. It considers only current supported evidence, required transport capabilities, host/provider policy, authority preservation, context cost, installation complexity, portability, and evidence quality. If no option is eligible it selects `UNSUPPORTED_FAIL_CLOSED`. The result cannot change specialist routing, AWF topology, provider/model selection, credentials, or fallback behavior.

Validate it with:

```text
python scripts/validate_provider_model_capability_contract.py
```
