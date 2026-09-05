# Adaptive Agentic Workflow Architecture (AWF)

Status: IMPLEMENTATION CANDIDATE, EXECUTION-EFFECTIVE WITHIN GRANTED AUTHORITY

Architecture baseline: Padayon PR #382, squash merge `b4b59d04ea37c4f23bb6a54e7d217bd3037eb6ab`
Orchestra source baseline: `75100c3ad0fd9a11c69f2b9b7c5172edd8841cd2`

## Purpose

AWF makes Orchestra's specialist workflow topology adaptive to the current task while preserving the existing authority model.

The governing invariant is:

```text
WORKFLOW_TOPOLOGY_CHANGE != AUTHORITY_EXPANSION
```

Conductor may change the workflow topology without a separate human approval when every selected action remains inside authority already granted by the user, project policy, specialist contracts, execution envelope, and protected-action rules.

Human escalation is triggered by the underlying protected action or authority/scope expansion, not by choosing Planning, Tool/ReAct, Reflection/Critic, Multi-Agent, specialist re-entry, or another valid topology.

## Runtime path

```text
request / goal / plan
        |
        v
TaskProfile
        |
        v
source-bound SpecialistAuthorityView
        |
        v
canonical specialist registry + OEE ExecutionBudget
        |
        v
Conductor workflow planner
        |
        v
AgenticWorkflowProfile
        |
        +--> optional CriticContract
        |
        +--> deterministic topology telemetry
```

The selector is execution-effective, but it does not execute protected actions by itself. It produces the authority-preserving specialist and pattern topology that downstream Orchestra execution uses.

## Five agentic primitives

| Pattern | AWF interpretation |
| --- | --- |
| Routing | Conductor-owned control-plane selection and topology change |
| Planning | Conditional dependency decomposition within the planning owner's domain |
| Tool/ReAct | Conditional evidence/tool/mutation loop whose ACT permissions inherit specialist mutation authority |
| Reflection/Critic | Conditional bounded evaluator with explicit domain, evidence owner, and transition authority |
| Multi-Agent | Conditional multi-specialist topology for genuinely distinct subproblems, authorities, evidence domains, or re-entry requirements |

Multi-Agent does not mean parallel by default. Orchestra's canonical OEE contract currently allows one active specialist by default, so multi-agent plans are normally sequential unless the OEE policy is separately changed.

## Authority enforcement

The machine authority view at `machine/specialists/authority-view.v1.json` is a source-bound derived view, not a new independent authority source.

Each entry records:

- source specialist path;
- exact Git blob identity;
- observable evidence classes;
- decision classes;
- mutation classes;
- exclusive control-plane flags.

The loader reconstructs each referenced specialist skill's canonical LF Git blob identity and fails closed if the view is stale. This keeps the binding stable across Linux, macOS, and Windows worktrees where checkout line endings may differ.

Exclusive authority remains:

| Capability | Owner |
| --- | --- |
| Dispatch / routing | Conductor |
| Cross-specialist coordination | The Tuner |
| General implementation | Ponytail |
| Primary QA / validation | Overseer |
| Transition disposition | Arbiter |

No specialist may self-authorize a protected action.

## TaskProfile

The TaskProfile is the deterministic input contract for topology selection. It records the current goal, execution mode, risk, authority domains, dependency depth, independent subtasks, mutation/implementation/validation requirements, transition requirements, external-state needs, protected-action state, critic request, specialist re-entry set, source identity, and any independently valid human-gate requirements.

Task complexity alone does not create a human gate.

## Conductor runtime attachment

The normal RouterService path remains unchanged when no AWF task profile is supplied.

When Conductor receives `context.metadata.agentic_task_profile`, RouterService loads the source-bound authority view and canonical OEE budget, invokes the AWF planner, and attaches the resulting workflow profile, critic contract, telemetry, and authority rule to the Conductor RouteDecision metadata.

A non-Conductor route that attempts to supply `agentic_task_profile` is rejected. This prevents a direct specialist route from using AWF metadata to bypass Conductor's exclusive dispatch authority.

The canonical Conductor skill text remains unchanged. AWF activation is attached at the runtime control-plane boundary through TaskProfile metadata and machine contracts, avoiding prompt-load growth and frozen-guidance digest drift.

## Specialist re-entry

When a prior specialist contract is invalidated, `reentry_specialists` identifies the affected owners.

The selector activates The Tuner for the re-entry coordination boundary, preserves the affected specialist authority, and returns a new topology through Conductor. The Tuner still cannot dispatch, validate itself, implement, or transition.

## Critic behavior

A Reflection/Critic node is represented by a `CriticContract` with:

- critic owner;
- evaluation domain;
- evidence owner;
- block/revision capability;
- transition capability;
- bounded iteration count.

Only Arbiter may receive `can_transition = true`.

AWF uses one critic iteration by default. Objective validation remains preferable when it can resolve the decision.

## Protected boundaries

`topology_change_requires_human_approval` is always false in an AWF workflow profile.

A separate human gate appears only when the TaskProfile says the underlying work independently requires it. For example:

```text
protected_action_required = true
protected_action_authorized = false
        ->
human_gate_required = true
reason = PROTECTED_ACTION_REQUIRES_INDEPENDENT_AUTHORITY
```

An already-authorized protected action does not receive a second approval solely because Orchestra changes topology.

## OEE integration

AWF consumes the canonical `ExecutionBudget` instead of creating a parallel efficiency controller.

It preserves:

- owner-first routing;
- current `max_parallel_specialists = 1` default;
- one specialist retry after the initial attempt;
- exact-source evidence reuse;
- stable-candidate validation escalation;
- earliest decisive evidence stopping;
- phase-local context;
- no active reasoning consumption for unchanged CI waits.

The workflow planner reports deterministic topology telemetry such as specialist count, pattern count, parallel peak, OEE parallel ceiling, human-gate state, and re-entry count. Telemetry does not expand authority.

## Relationship to legacy Adaptive A5

AWF does not promote or rewrite the historical A5 shadow topology ranker.

The existing A5 subsystem remains evidence and ranking infrastructure with its historical shadow-only semantics. Its prior closeout correctly recorded that execution-effective promotion was deferred because measurable comparative benefit was not established.

AWF is different:

- A5 asks whether pre-qualified topology candidates can be ranked from exact comparative evidence.
- AWF derives the minimum authority-safe execution topology from the current user goal, deterministic specialist ownership, dependency state, and OEE constraints.

The A5 shadow ranker does not control AWF dispatch. AWF does not claim A5 comparative benefit.

## UIEF-5 replay regression

UIEF-5 remains the historical replay fixture.

For the known upstream responsive contradiction:

```text
authority domain = UI_UX
primary owner = Cloak
implementation = false
validation = false
dependency depth = 0
        ->
required specialists = [cloak]
patterns = [ROUTING, TOOL_REACT]
concurrency = SINGLE_OWNER
human gate = false
```

This preserves the OEE-7 lesson: once Cloak owns a decision-sufficient upstream blocker, downstream specialist fan-out cannot improve the pre-implementation disposition.

## Implementation surfaces

Machine contracts:

- `machine/schemas/task-profile.v1.schema.json`
- `machine/schemas/critic-contract.v1.schema.json`
- `machine/schemas/specialist-authority-view.v1.schema.json`
- `machine/schemas/agentic-workflow-profile.v1.schema.json`
- `machine/specialists/authority-view.v1.json`
- `machine/workflows/patterns.v1.json`
- `machine/workflows/composition-invariants.v1.json`

Runtime:

- `orchestra_runtime/domain/adaptive/task_profile.py`
- `orchestra_runtime/domain/adaptive/topology_validator.py`
- `orchestra_runtime/domain/adaptive/agentic_workflow.py`
- `orchestra_runtime/application/use_cases/agentic_workflow.py`
- `orchestra_runtime/infrastructure/machine/agentic_workflow.py`

Validation:

- `tests/runtime/test_agentic_workflow.py`
- `tests/runtime/test_agentic_workflow_oee_replay.py`
- `tests/runtime/test_agentic_workflow_scenarios.py`
- `tests/fixtures/agentic-workflow/awf-scenarios.v1.json`

## Non-goals

This implementation does not:

- widen specialist authority;
- change the OEE concurrency default;
- promote A5 learned/shadow topology ranking into execution control;
- resume UIEF;
- merge or alter UIEF PR #799 or #791;
- authorize destructive production actions;
- authorize release, deployment, or policy activation.
