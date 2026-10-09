# Routing Evaluation Guide

Use this guide to test the existing router without redesigning it.

Current routing authority: Conductor classifies every request and selects every specialist, including clear single-owner work. A direct single-specialist fast route is a Conductor decision; it may reduce context loading and ceremony, but it never bypasses Conductor. `CLEAR_OWNERSHIP != CONDUCTOR_BYPASS` and `FAST_ROUTE != ROUTER_BYPASS`.

## Scenario Shape

Each scenario states request, repository/mode/authority context, material domains, expected primary owner, ordered supporting owners, governance triggers, Tuner activation or bypass, prohibited routes, expected stop/pause behavior, and evidence needed to pass.

## Adversarial Classes

Cover disguised multi-domain work, direct specialist bypass, Dagger without authorization, governance approval mistaken for execution authority, stale evidence presented as current, protected actions hidden inside ordinary work, ambiguous source of truth, and a genuinely single-owner task where Tuner must be bypassed.

## Evaluation Rules

- Conductor owns specialist selection; one specialist owns each decision or output.
- Order dependencies before implementation.
- Do not hydrate unrelated specialists.
- Domain keywords alone do not force a route; material ownership does.
- Unknown or contradictory authority fails closed.
- A correct route does not authorize the routed action.

Record expected and observed route, mismatch class, minimum contract correction, and regression identity. Prefer correcting an incomplete scenario or compact routing rule over expanding the orchestration model.

## OR-GOV-5 Architecture Governance Intake

For architecture, capacity, tenancy, persistence, product-intent, security,
or validation-sensitive requests, load
[ARCHITECTURE_GOVERNANCE_INTAKE_GUIDE.md](ARCHITECTURE_GOVERNANCE_INTAKE_GUIDE.md)
and embed the canonical `ArchitectureGovernanceIntake` in the existing
`Routing Plan` output. Classify the actual change, preserve unknown evidence,
and compose the minimum specialist route. Do not run a universal capacity
questionnaire or treat routing metadata as authority.

The OR-GOV-5 evaluation set covers product intent before architecture,
decision-specific capacity prompting, direct-route preservation, tenancy and
persistence boundaries, empirical validation claims, blocked Dagger requests,
and unresolved production presence. OR-GOV-6 dependency invalidation and
minimal re-entry remain out of scope.
