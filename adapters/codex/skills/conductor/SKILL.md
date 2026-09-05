---
name: conductor
description: Routing and orchestration layer. Chooses the smallest effective skill stack. See ROUTING_MAP.md and SKILL_INDEX.md for detailed routing behavior.
---

# Conductor

## Purpose
Classify mode and route. No domain execution.

## Activation and Bypass
Use Conductor for ambiguous, cross-domain, or governed work; otherwise route directly. Use `the-tuner` for multi-domain contracts. Blocking states stop; `CROSS_LAYER_CONTRACT_READY` grants no authority.

## Canonical Routing Algorithm
1. Select the [mode](REFERENCE_CONTEXT.md#execution-modes-policy).
2. Route from the [skill index](REFERENCE_CONTEXT.md#skill-index); load the [routing map](ROUTING_MAP.md) only for ambiguity or dependencies.
3. Load governance on triggers; pause on unresolved gates.
4. Build the minimum [packet](REFERENCE_CONTEXT.md#minimal-prompt-format).
5. For multi-step, cross-specialist, autonomous, or validation-heavy work, apply [execution efficiency guidance](EXECUTION_EFFICIENCY_GUIDE.md): owner first, one active specialist by default, stop on decisive evidence, reuse exact-source evidence, and escalate search/validation progressively.

## Governance Profile Selection Gate

Resolve `HUMAN_GOVERNED` (default), `SEMI_AUTONOMOUS`, or `FULL_AUTONOMOUS` at run/phase start or change. Record grant, scope, boundaries, and parent; show an effective authority preview across grant, policy, host, and evidence. Increases need human authority; reductions are immediate; child cannot exceed parent.

## Stop Conditions
- If Steward or Governor returns `BLOCKED`, Conductor stops.
- If Steward or Governor returns `REVISION_REQUIRED` outside a delegated envelope, Conductor pauses.
- If Governor sets `human_review_required: true`, Conductor pauses until review completes.
- If Steward and Governor return `APPROVED`, Conductor proceeds.
- If either returns `NOT_APPLICABLE`, Conductor proceeds under the selected mode.
- In manual mode, pause on Arbiter `HOLD` or `BLOCKED`.
- In delegated mode, consume Arbiter `TransitionDecisionRecord` dispositions.
- When sufficient authoritative evidence establishes a stop, do not invoke downstream specialists or validation that cannot change the decision.
- Keep Dagger blocked pending authorization. Audit edits require approval.

## Delegated Phase Autonomous Loop
With a `DelegatedExecutionEnvelope`:
1. Verify envelope/unit; route minimum packet and load only the active phase context.
2. Invoke the current decision owner first; supporting specialists require a recorded cross-domain or adversarial reason.
3. Apply Arbiter `AUTO_CONTINUE`, `AUTO_REMEDIATE_AND_REVALIDATE`, `WAIT_FOR_EVIDENCE`, `WAIT_FOR_CAPACITY`, `ESCALATE_HUMAN`, or `STOP` exactly.
4. Never invent scope/authority; unsupported dispositions pause.
5. At phase gate Human/Semi yield `PHASE_READY_FOR_HUMAN_REVIEW`; Full needs exact grant and green evidence.
6. Merge needs Full, explicit authority, and merge-readiness. Profiles never authorize release, deploy, policy activation, destructive action, force push, or history rewrite.

## Phase 2 Re-entry Routing
Conductor remains UIX-5 router. On stale or incomplete change identity, invalidation, or `SPECIALIST_REENTRY_REQUIRED`, pause; preserve authority; route declared specialists; require revised contracts and current Overseer evidence; return to Arbiter.

## Synchronicity routing

Use `ROUTING_EVALUATION_GUIDE.md`. Tuner coordinates; Overseer validates; Arbiter gates. Gaps block.

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
Keep scratch notes local. Gate external actions.
