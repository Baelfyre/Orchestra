# UAI transport and fallback integration

The UAI integration strategy resolver can produce a deterministic transport
fallback chain from current, evidence-backed transport options. The chain is
read-only planning data. It does not execute a transport, switch providers, or
change the active model.

The primary strategy and every fallback must:

- be `SUPPORTED_VERIFIED` or `SUPPORTED_WITH_LIMITS`;
- satisfy the required capabilities;
- preserve authority;
- be allowed by host and provider policy;
- remain transport decisions, separate from Conductor specialist routing and
  deterministic AWF workflow topology.

If no eligible transport exists, the resolver returns
`UNSUPPORTED_FAIL_CLOSED`. A fallback transport is not a provider fallback:
`automatic_provider_fallback` remains `false`.

The policy is defined in
`machine/hosts/integration-strategy-policy.v1.json`, and the pure domain API is
`resolve_transport_fallback` in
`orchestra_runtime/domain/adaptive/integration_strategy.py`.
