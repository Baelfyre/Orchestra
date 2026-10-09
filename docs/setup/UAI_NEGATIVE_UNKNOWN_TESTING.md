# UAI negative and unknown capability testing

UAI-8 exercises the fail-closed boundaries already defined by the host
capability contract, provider/model shadow broker, transport resolver, and
portable projection compiler. It is evidence work, not a new authority layer.

The executable matrix is
`tests/runtime/test_uai8_negative_unknown_capabilities.py`:

| Scenario | Expected result |
| --- | --- |
| Known host with admitted capability evidence | Current Copilot evidence validates with Conductor `SUPPORTED_WITH_LIMITS` and Ponytail `SUPPORTED_VERIFIED`. |
| Known host missing an expected surface | Provider/model advice is `UNKNOWN` with `MISSING_CAPABILITY_EVIDENCE`. |
| Unknown but capability-compatible host | Advice may be `ELIGIBLE`, but remains shadow-only and non-authorizing. |
| Host identity contradicts observed capability | Host validation emits `COPILOT_STATUS_DRIFT`. |
| Policy-disabled MCP/plugin/tools | No eligible transport produces `UNSUPPORTED_FAIL_CLOSED`. |
| Instruction-only host | `INSTRUCTION_ONLY_FALLBACK` is selectable as a bounded transport surface. |
| Supported host with unsupported provider/model | Provider/model advice is `INELIGIBLE`. |
| Unknown provider with declared but unverified capability | Advice is `UNKNOWN`. |
| Stale provider capability | Advice is `UNKNOWN` and records stale/unknown evidence. |
| Tool access without execution authority | Host and broker authority flags remain false. |
| Host/provider selection attempts to alter specialist routing | The broker rejects the authority-expanding decision. |
| Unauthorized automatic provider switching | The broker rejects automatic switching. |
| Partial installation | Unverified MCP is rejected and instruction-only transport is selected. |
| Stale generated projection | Projection parity validation fails closed. |
| Fallback governance preservation | Fallback remains transport-only, non-automatic, and provider-neutral. |

These tests do not admit new hosts, providers, models, credentials, transport
implementations, automatic fallback, learned routing, or specialist-routing
authority. In particular:

- `CONDUCTOR_IS_SOLE_INTERNAL_SPECIALIST_ROUTER` remains the routing invariant;
- `CLEAR_OWNERSHIP` can enable a direct single-specialist fast route, but does
  not bypass Conductor;
- `FAST_ROUTE` is not a router bypass;
- UAI transport selection is not AWF specialist routing;
- provider capability advice does not select, switch, or promote a provider or
  model.
