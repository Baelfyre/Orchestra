# UAI Host Capability Contract

The canonical Universal Adaptive Integration host contract is [capability-contract.v1.json](../../machine/hosts/capability-contract.v1.json), validated by [host-capability-contract.v1.schema.json](../../machine/schemas/host-capability-contract.v1.schema.json).

It records host capability evidence without creating a second authority model. Each profile carries:

- a versioned capability taxonomy and host-neutral transport compatibility set;
- source repository, source commit, observation time, environment, probe, subject commit, and freshness invalidation triggers;
- explicit `SUPPORTED_VERIFIED`, `SUPPORTED_WITH_LIMITS`, `AVAILABLE_NOT_YET_VERIFIED`, `UNKNOWN`, `BLOCKED_BY_POLICY`, `VERIFIED_UNSUPPORTED_LOCALLY`, and `UNSUPPORTED` dispositions;
- authority fields fixed to false for execution, routing, specialist selection, workflow topology, provider selection, automatic provider routing, and automatic provider fallback.

Capability evidence never grants execution authority. UAI selects a compatible host transport; Conductor remains the sole internal specialist router and AWF remains the workflow-topology authority. A clear single-owner request may use a Conductor-selected direct fast route, but `CLEAR_OWNERSHIP != CONDUCTOR_BYPASS` and `FAST_ROUTE != ROUTER_BYPASS`.

Validate the canonical record with:

```text
python scripts/validate_host_capability_contract.py
```

Stale, malformed, contradictory, or authority-expanding records fail closed. Host, extension, account/organization policy, or Orchestra contract changes invalidate the recorded observation for reverification.
