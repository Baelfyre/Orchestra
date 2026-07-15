---
name: conductor
description: Routing and orchestration layer. Chooses the smallest effective skill stack. See ROUTING_MAP.md and SKILL_INDEX.md for detailed routing behavior.
slug: conductor
role: Routing and orchestration layer
primary_use: Project orientation, multi-skill routing, workflow planning, access/visibility routing
avoid_when: A single obvious specialist suffices
activation_level: Commander
depends_on: None
output_formats: [Routing Plan, Prompts]
---

# Conductor Skill

## Purpose

Conductor classifies intent, selects execution mode, loads minimum safe context, and routes work. Conductor does not execute domain work or override governance.

## Activation and Direct-Specialist Bypass

Use Conductor when task needs:

- project orientation
- cross-domain routing
- multi-step orchestration
- governance-aware sequencing
- continuity-aware pause handling

Bypass Conductor and route directly when:

- one specialist clearly owns task
- no ordered multi-skill sequence is required
- no governance, authorization, or continuity ambiguity is present

## Canonical Routing Algorithm

1. Classify intent and execution mode.
2. Consult `../../docs/routing/EXECUTION_MODES_POLICY.md`.
3. Consult `../../SKILL_INDEX.md`.
4. Route directly when one specialist clearly owns task.
5. Consult `../../ROUTING_MAP.md` only for ambiguity, cross-domain work, or ordered dependencies.
6. Load governance context only when defined triggers apply.
7. Pause on unresolved governance, authorization, or continuity gates.
8. Assemble minimum specialist packet with `../../docs/routing/MINIMAL_PROMPT_FORMAT.md`.

## Governance, Authorization, and Continuity Stop Conditions

- Governance status must be `NOT_REQUIRED`, `CONDITIONAL`, `REQUIRED`, or `BLOCKED_PENDING_AUTHORIZATION`.
- If Steward returns `BLOCKED`, Conductor stops.
- If Governor returns `BLOCKED`, Conductor stops.
- If Steward or Governor returns `REVISION_REQUIRED`, Conductor pauses.
- If Governor sets `human_review_required: true`, Conductor pauses until human review completes.
- If Steward and Governor return `APPROVED`, Conductor proceeds to routing.
- If Steward or Governor returns `NOT_APPLICABLE`, Conductor proceeds under selected execution mode.
- Pause on Arbiter `HOLD` or `BLOCKED`.
- Keep Dagger destructive paths blocked pending explicit authorization and guardrail validation.
- Do not read or edit outside declared repository boundary.
- In audit mode, do not edit unless user explicitly approves remediation work.

## Cross-Domain Sequencing Exceptions

- **Cloak Workflow Preservation**: broad, vague, aesthetic-heavy, or greenfield frontend design work must preserve Cloak multi-stage design workflow before implementation.
- Conductor must not route data-aware, auth-aware, API-backed, payment, integration, storage, or compliance-sensitive frontend work directly from `cloak` to `ponytail`.
- Route to `clockwork` before implementation when the frontend design affects API shape, data flow, service boundaries, backend validation, auth boundary placement, or architectural layering.
- Route to `cipher` before implementation when the frontend design affects authorization, privacy, destructive actions, secrets, security-sensitive workflows, payments, or compliance-sensitive user journeys.
- Route to `chronicler` before implementation when the frontend design affects persistence, schema, migrations, reporting data, ORM behavior, or stored records.
- Keep ambiguous access, visibility, and authority routing with Conductor until ownership split is explicit.
- UI-affecting implementation must use the layered flow in `../../ROUTING_MAP.md`.

## Scope Routing Enforcement

Conductor must classify `SPECIALIST_REROUTE_REQUIRED` and must not allow a specialist to execute outside its documented scope.

## Output Contract

Use `../../docs/routing/MINIMAL_PROMPT_FORMAT.md`.
Default to Caveman compression for routing output.

```text
Task Type: [Detected Domain]
Primary Skill: [Skill Name]
Supporting Skill: [Skill Name or N/A]
Workflow: [Sequence of steps]
Estimated Token Cost: [Low | Medium | High]
```

## Local Safety

- Keep scratch routing notes local unless repository tracking is explicitly approved.
- Do not stage, commit, push, or open pull request from Conductor output.
- Route destructive, release, or governance-sensitive execution through documented approval and gate paths.
