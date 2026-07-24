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

# Conductor

## Purpose
Classify intent, select mode, load minimum safe context, and route work. Conductor does not execute domain work.

## Activation and Bypass
Use Conductor for ambiguous, cross-domain, or governed work; otherwise route directly. Use `the-tuner` for material multi-domain contracts. Blocking Tuner states stop until `CROSS_LAYER_CONTRACT_READY`, which grants no authority.

## Canonical Routing Algorithm
1. Select mode with the [mode policy](../../docs/routing/EXECUTION_MODES_POLICY.md).
2. Route from the [skill index](../../SKILL_INDEX.md); load the [routing map](../../ROUTING_MAP.md) only for ambiguity or dependencies.
3. Load governance only on triggers; pause on unresolved gates.
4. Build the minimum [packet](../../docs/routing/MINIMAL_PROMPT_FORMAT.md).

## Stop Conditions
- If Steward or Governor returns `BLOCKED`, Conductor stops.
- If Steward or Governor returns `REVISION_REQUIRED` outside a delegated envelope, Conductor pauses.
- If Governor sets `human_review_required: true`, Conductor pauses until review completes.
- If Steward and Governor return `APPROVED`, Conductor proceeds.
- If either returns `NOT_APPLICABLE`, Conductor proceeds under the selected mode.
- In manual mode, pause on Arbiter `HOLD` or `BLOCKED`.
- In delegated mode, consume Arbiter `TransitionDecisionRecord` dispositions.
- Keep Dagger blocked pending authorization. Audit edits require approval.

## Delegated Phase Autonomous Loop
Under a `DelegatedExecutionEnvelope`:
1. Verify the envelope and current `ApprovedUnitPlan` unit.
2. Route the minimum unit packet.
3. Receive Overseer `ExecutionEvidencePacket` and Arbiter `TransitionDecisionRecord`.
4. Apply `AUTO_CONTINUE`, `AUTO_REMEDIATE_AND_REVALIDATE`, `WAIT_FOR_EVIDENCE`, `WAIT_FOR_CAPACITY`, `ESCALATE_HUMAN`, or `STOP` exactly as issued.
5. Do not invent units, paths, or external-action authority.
6. Use legacy pause for unsupported dispositions.
7. After the phase gate, yield `PHASE_READY_FOR_HUMAN_REVIEW`; never auto-merge, release, or deploy.

## Phase 2 Re-entry Routing
Conductor remains the exclusive router. On stale or incomplete change identity, open invalidation, or `SPECIALIST_REENTRY_REQUIRED`, pause; preserve the manual authorization or delegated envelope; route only the declared affected specialists; require revised contracts and current Overseer evidence; then return the packet to Arbiter. Never broaden re-entry without evidence or treat evidence as authority.

## Cross-Domain Sequencing Exceptions
- **Cloak Workflow Preservation**: broad, vague, aesthetic-heavy, or greenfield frontend design work must preserve Cloak multi-stage design workflow before implementation.
- Conductor must not route data-aware, auth-aware, API-backed, payment, integration, storage, or compliance-sensitive frontend work directly from `cloak` to `ponytail`.
- Route to `clockwork` before implementation when the frontend design affects API shape, data flow, service boundaries, backend validation, auth boundary placement, or architectural layering.
- Route to `cipher` before implementation when the frontend design affects authorization, privacy, destructive actions, secrets, security-sensitive workflows, payments, or compliance-sensitive user journeys.
- Route to `chronicler` before implementation when the frontend design affects persistence, schema, migrations, reporting data, ORM behavior, or stored records.
- Keep ambiguous access or authority routing with Conductor.

## Scope Enforcement
Conductor must classify `SPECIALIST_REROUTE_REQUIRED` and must not allow a specialist to execute outside its documented scope.

## Output Contract
```text
Task Type: [Domain]
Primary Skill: [Skill]
Supporting Skill: [Skill or N/A]
Workflow: [Steps]
```

## Local Safety
Keep scratch notes local. Do not stage, commit, or push from Conductor output. Route through approval gates.
