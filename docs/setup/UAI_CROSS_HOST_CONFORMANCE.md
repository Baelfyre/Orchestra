# UAI cross-host capability conformance

UAI-9 compares the three plan-named host identities against the canonical
evidence boundary: Antigravity, Codex, and GitHub Copilot. The current source
contains fresh observed evidence for GitHub Copilot only. Antigravity and Codex
remain explicitly unadmitted and are not represented by synthetic profiles.

The executable conformance checks are in
`tests/runtime/test_uai9_cross_host_capability_conformance.py`.

| Surface | GitHub Copilot | Antigravity and Codex |
| --- | --- | --- |
| Discovery and host identity | Admitted profile with current observation evidence | Unknown/not admitted; no fabricated profile |
| Capability dispositions | Mixed: Conductor `SUPPORTED_WITH_LIMITS`, Ponytail `SUPPORTED_VERIFIED`, and other observed or unverified dimensions | Unknown |
| Transport compatibility | Host-neutral strategies; unverified or locally unsupported surfaces remain bounded | Unknown |
| Specialist ownership | Conductor remains the sole internal specialist router; Ponytail is the observed specialist surface | Unknown, so no ownership is inferred |
| Authority | All host authority grants and automatic provider flags are `false` | No host-specific authority exists |
| Validation and projection | Host/provider contracts and portable projection parity validate with `PASS` | No evidence to validate or promote |
| Permission and policy | Permission and organization/account policy dimensions remain `AVAILABLE_NOT_YET_VERIFIED` | Unknown |
| Fallback | Only deterministic, non-executing transport fallback policy applies | No fallback is selected without evidence |
| Provider/model | No provider/model profiles are admitted; shadow broker remains non-authorizing | Unknown |

This phase does not run the unavailable Copilot `/conductor` surface retest and
does not promote `SUPPORTED_WITH_LIMITS`. It also does not add hosts, providers,
models, credentials, transport implementations, automatic routing or fallback,
learned routing, concurrency, AWF topology changes, release, or deployment.

The routing boundaries remain explicit:

- `CONDUCTOR_IS_SOLE_INTERNAL_SPECIALIST_ROUTER`;
- `CLEAR_OWNERSHIP != CONDUCTOR_BYPASS`;
- `CLEAR_OWNERSHIP MAY_ENABLE DIRECT_SINGLE_SPECIALIST_FAST_ROUTE`;
- `FAST_ROUTE != ROUTER_BYPASS`;
- `UAI_TRANSPORT_SELECTION != AWF_SPECIALIST_ROUTING`;
- `AWF = WORKFLOW TOPOLOGY OWNER`.
