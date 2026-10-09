# UAI maturity and closeout

UAI-10 closes the current Universal Adaptive Integration sequence after the
UAI-9 cross-host conformance evidence. It records maturity boundaries and
current limitations. It is not a release, deployment, marketplace publication,
credential change, policy activation, or provider-routing promotion.

The executable closeout checks are in
`tests/runtime/test_uai10_maturity_closeout.py`.

| Boundary | Current canonical disposition |
| --- | --- |
| Host capability | GitHub Copilot is the only admitted observed host profile. Its Conductor capability remains `SUPPORTED_WITH_LIMITS`; Ponytail remains `SUPPORTED_VERIFIED`. |
| Copilot retest | One focused `/conductor` live retest remains required for promotion only. The unavailable Copilot surface does not block UAI-2 through UAI-10. |
| Provider/model capability | No provider/model profiles are admitted. The broker remains shadow advisory and cannot select, switch, or fall back between providers/models. |
| Transport | Integration strategy and fallback remain deterministic, non-executing, policy-allowed transport decisions. |
| Routing and workflow | Conductor remains the sole internal specialist router and AWF remains the workflow-topology owner. `CLEAR_OWNERSHIP` does not bypass Conductor; a direct single-specialist fast route is still distinct from a router bypass. |
| Projection | Canonical-source-backed projections are current with parity `PASS`; generated projections remain derived-only. |
| Unobserved hosts | Antigravity and Codex remain unknown/not admitted. No capability or authority is inferred for them. |
| Deferred work | UAI-3 implementation, automatic provider routing/fallback, learned routing promotion, concurrency widening, AR-3, AR-4, release, deployment, and marketplace work remain outside this closeout. |

The closeout therefore establishes:

- `CONDUCTOR_IS_SOLE_INTERNAL_SPECIALIST_ROUTER`;
- `CLEAR_OWNERSHIP != CONDUCTOR_BYPASS`;
- `CLEAR_OWNERSHIP MAY_ENABLE DIRECT_SINGLE_SPECIALIST_FAST_ROUTE`;
- `FAST_ROUTE != ROUTER_BYPASS`;
- `HOST != PROVIDER` and `PROVIDER != SPECIALIST`;
- `CAPABILITY != AUTHORITY`;
- `TRANSPORT != WORKFLOW` and `UAI_TRANSPORT_SELECTION != AWF_SPECIALIST_ROUTING`;
- `MODEL_SELECTION != GOVERNANCE`;
- `AWF = WORKFLOW TOPOLOGY OWNER`.
