---
name: conductor
description: Routing and orchestration layer. Chooses the smallest effective skill stack. See ROUTING_MAP.md and SKILL_INDEX.md for detailed routing behavior.
---

# Conductor

## Purpose
Classify intent, select mode, load minimum safe context, route work. Conductor does not execute domain work.

## Activation and Bypass
Use Conductor for orientation, cross-domain routing, multi-step orchestration, or governance. Bypass when single specialist owns task and no ambiguity exists.

## Canonical Routing Algorithm
1. Classify via the [mode policy](REFERENCE_CONTEXT.md#execution-modes-policy).
2. Route via the [skill index](REFERENCE_CONTEXT.md#skill-index); go direct for one owner.
3. Use the [routing map](ROUTING_MAP.md) for ambiguity, cross-domain work, or dependencies.
4. Load governance only on triggers.
5. Pause on unresolved gates.
6. Build via the [packet format](REFERENCE_CONTEXT.md#minimal-prompt-format).

## Stop Conditions
- Governance status: `NOT_REQUIRED`, `CONDITIONAL`, `REQUIRED`, or `BLOCKED_PENDING_AUTHORIZATION`.
- If Steward or Governor returns `BLOCKED`, Conductor stops.
- If Steward or Governor returns `REVISION_REQUIRED` outside delegated envelope, Conductor pauses.
- If Governor sets `human_review_required: true`, Conductor pauses until human review completes.
- If Steward and Governor return `APPROVED`, Conductor proceeds to routing.
- If Steward or Governor returns `NOT_APPLICABLE`, Conductor proceeds under selected execution mode.
- In legacy manual mode, pause on Arbiter `HOLD` or `BLOCKED`.
- In delegated phase mode, consume Arbiter `TransitionDecisionRecord` dispositions (`AUTO_CONTINUE`, `AUTO_REMEDIATE_AND_REVALIDATE`, `WAIT_FOR_EVIDENCE`, `WAIT_FOR_CAPACITY`, `ESCALATE_HUMAN`, `STOP`).
- Keep Dagger paths blocked pending authorization. In audit mode, edit only with approval.

## Delegated Phase Autonomous Loop
In delegated phase under `DelegatedExecutionEnvelope`:
1. Verify valid envelope exists and current unit is in `ApprovedUnitPlan`.
2. Route minimum unit packet to specialist.
3. Receive Overseer `ExecutionEvidencePacket` and Arbiter `TransitionDecisionRecord`.
4. Consume Arbiter dispositions: `AUTO_CONTINUE` (checkpoint unit), `AUTO_REMEDIATE_AND_REVALIDATE` (route to remediation specialist), `WAIT_FOR_EVIDENCE` (pause execution), `WAIT_FOR_CAPACITY` (checkpoint state), `ESCALATE_HUMAN` (request human decision), `STOP` (halt execution).
5. Do not invent units or paths. Refuse automatic external actions unless authority flag is true.
6. Use legacy pause if disposition unsupported.
7. Run phase gate after units pass; yield `PHASE_READY_FOR_HUMAN_REVIEW`. Never auto-merge, release, or deploy.

## Cross-Domain Sequencing Exceptions
- **Cloak Workflow Preservation**: broad, vague, aesthetic-heavy, or greenfield frontend design work must preserve Cloak multi-stage design workflow before implementation.
- Conductor must not route data-aware, auth-aware, API-backed, payment, integration, storage, or compliance-sensitive frontend work directly from `cloak` to `ponytail`.
- Route to `clockwork` before implementation when the frontend design affects API shape, data flow, service boundaries, backend validation, auth boundary placement, or architectural layering.
- Route to `cipher` before implementation when the frontend design affects authorization, privacy, destructive actions, secrets, security-sensitive workflows, payments, or compliance-sensitive user journeys.
- Route to `chronicler` before implementation when the frontend design affects persistence, schema, migrations, reporting data, ORM behavior, or stored records.
- Keep ambiguous access/authority routing with Conductor until ownership is explicit. UI changes follow the routing map above.

## Scope Enforcement
Conductor must classify `SPECIALIST_REROUTE_REQUIRED` and must not allow a specialist to execute outside its documented scope.

## Output Contract
Use the minimum packet format above:
```text
Task Type: [Domain]
Primary Skill: [Skill]
Supporting Skill: [Skill or N/A]
Workflow: [Steps]
```

## Local Safety
Keep scratch notes local. Do not stage, commit, or push from Conductor output. Route through approval gates.
