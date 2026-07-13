# Authority and Capability Runtime Architecture

Status: Phase 6A architecture definition. Runtime implementation has not started.

## Purpose

Define the Orchestra-native runtime boundaries for trusted authority, immutable per-run capabilities, bounded specialist delegation, typed lifecycle control, and auditable denials and transitions. This document describes architecture only. The approved Artificer proposal and promotions are governance evidence, not executable configuration or implementation authority.

## Non-Goals

- Implementing runtime behavior in Phase 6A.
- Treating governance approval, routing, adapter support, or audit evidence as runtime authority.
- Reusing Strix source code, prompts, payloads, examples, media, or documentation expression.
- Changing PRAP v1 or using PRAP `AdapterCapabilities` as execution permission.
- Defining an unlimited legacy authority policy.
- Changing promotion status or the Pattern Catalog.

## Current Runtime

The current runtime flow is:

```text
Adapter
-> ContextPackage
-> Command
-> RouterService
-> GovernanceValidator
-> RuntimeExecutor
-> ExecutionResult
-> AuditLogger
```

`ContextAssembler` accepts a `ContextPackage` from an adapter and merges generic metadata defaults. `RouterService` maps a parsed `Command` to a specialist. `GovernanceValidator` evaluates the route using generic metadata flags such as `governance_validated`, `destructive_validated`, and `dry_run`. `RuntimeExecutor` coordinates these services and returns an `ExecutionResult`; `AuditLogger` records a generic execution summary.

This flow provides routing and governance checks, but it does not establish runtime authority. `RouteDecision.governance_required` describes governance routing. It does not grant target, operation, capability, delegation, or lifecycle authority.

## Current Gaps

- No trusted authority-scope model.
- No authority provenance.
- No explicit target or operation authorization.
- No per-run runtime capability manifest.
- No capability collision contract.
- No bounded delegation model.
- No child-authority intersection.
- No typed lifecycle state.
- No structured completion signal.
- No lifecycle transition validation.
- No authority-specific audit events.
- Generic metadata currently carries governance flags.
- No explicit separation between trusted configuration and prompt or adapter metadata.

## Trust Boundaries

1. Prompt text is untrusted.
2. Adapter-supplied metadata is untrusted for authority expansion.
3. Trusted authority enters through runtime construction or trusted repository configuration.
4. Prompt or adapter metadata may request less authority but cannot grant more authority.
5. Empty or invalid trusted authority prevents execution initialization.
6. Governance approval is not runtime authority.
7. Routing is not runtime authority.
8. PRAP adapter host support is not runtime capability authorization.
9. Audit evidence records decisions and outcomes but grants no authority.
10. External-source concepts and Artificer records provide no runtime authority.

The trust boundary sits between trusted runtime composition and all host-provided input. Authority and capability evaluators consume validated trusted policy plus reduction-only requests. They never infer grants from prompt text, `ContextPackage.metadata`, a route, governance status, audit evidence, or adapter capability flags.

## Phase 6A-A Finding

Current runtime behavior does not contradict the approved architecture premise. It lacks the proposed enforcement contracts, so later integration must add them through explicit dependencies without reclassifying existing metadata or governance results as authority.

## Target Runtime

The target sequence is:

```text
Trusted runtime configuration
-> Root authority validation
-> Immutable run identity
-> Immutable runtime capability manifest
-> Adapter context
-> Command parsing
-> Routing
-> Authority evaluation
-> Capability evaluation
-> Governance validation
-> Execution lifecycle
-> Structured result
-> Audit events
```

Authority and capability evaluation precede governance validation because governance decides whether an otherwise authorized route may proceed; it cannot make an unauthorized target, operation, or capability valid. Adapter context remains after trusted initialization so host input cannot influence root grants.

## Component Ownership

| Concern | Owner | Boundary |
| --- | --- | --- |
| Authority scope and provenance | Arbiter | Defines and reviews the trusted authority contract; does not execute it. |
| Runtime capability manifest | Clockwork | Defines immutable runtime capability structure and collision behavior. |
| Lifecycle state machine | Clockwork | Defines typed states, transitions, and signals. |
| Specialist delegation | Overseer | Defines validation and verification requirements for bounded delegation. |
| License and source independence | Governor | Preserves conceptual-adaptation and no-source-reuse constraints. |
| Scope and roadmap | Steward | Keeps architecture bounded, necessary, and sequenced. |
| Repository and implementation authorization | The Butler | Authorizes later implementation; canonical Artificer field remains `maintainer_decision`. |
| Routing | Conductor and `RouterService` | Selects workflow or specialist; grants no authority. |
| Runtime implementation | Assigned specialists in later phases | Implements only after separate Butler authorization. |

## Initialization Sequence

1. Trusted runtime composition loads a repository-owned root policy.
2. The authority evaluator validates a non-empty `AuthorityScope` and its `AuthorityProvenance`.
3. Runtime composition creates an immutable run identity.
4. The capability resolver validates grants, rejects identity collisions, calculates the effective set, and freezes a `RuntimeCapabilityManifest`.
5. The lifecycle controller creates the run in its pre-execution state.
6. Initialization emits root-authority and capability-manifest audit events.
7. Invalid or empty trusted policy produces a typed initialization failure before adapter input is accepted.

## Execution Sequence

1. The adapter supplies context and the command parser creates a `Command`.
2. `RouterService` selects a route without granting authority.
3. `IAuthorityEvaluator` evaluates the requested target and operation against the immutable effective scope.
4. `ICapabilityResolver` evaluates required runtime capability identities and operations against the immutable manifest.
5. Any denial stops before privileged execution and emits a structured denial event.
6. `GovernanceValidator` applies governance rules only after authority and capability checks pass.
7. `ILifecycleController` validates entry to active execution.
8. Execution returns a structured result plus typed lifecycle signal; ordinary text is output only.
9. The lifecycle controller validates the terminal or non-terminal transition and audit events record each decision.

## Delegation Sequence

1. A parent run submits a structured `DelegationRequest` naming a registered specialist, task, requested scope, requested capabilities, context allowlist, and depth.
2. `IDelegationValidator` validates parent identity, specialist registration, depth, task shape, and context exclusions.
3. Effective child authority is the intersection of requested authority and parent authority.
4. Effective child capabilities are the intersection of requested capabilities and parent capabilities.
5. Empty, broader, unknown, over-depth, or sensitive-context requests are rejected deterministically.
6. Accepted delegation creates a distinct child run identity and immutable parent-child provenance.
7. Accepted and rejected decisions emit structured audit events before child execution.

## Lifecycle Sequence

1. A run begins in the typed pre-execution state.
2. Only the lifecycle controller may apply a structured signal.
3. Allowed transitions move the run to active, waiting, or a terminal state.
4. Waiting is non-terminal and requires an explicit resume signal.
5. Completion, failure, cancellation, timeout, and blocking use distinct terminal signals and results.
6. An exact duplicate terminal signal is idempotent; a conflicting terminal signal is rejected and audited.
7. Invalid transitions fail deterministically without changing state.
8. Ordinary prompt, adapter, model, or tool text cannot transition lifecycle state.

## Audit Sequence

Audit records are append-only evidence derived from validated actions. Events cover root authority creation, authority decisions, capability-manifest creation, capability decisions, delegation acceptance or rejection, lifecycle transitions, terminal results, and typed initialization failures. Each event carries stable run identity, event type, decision or transition data, provenance references, and a deterministic reason code where applicable. Audit writes never change authority, capability, delegation, or lifecycle state.

## Compatibility Strategy

- Trusted runtime composition initially supplies a repository-owned default root policy for existing construction paths.
- Existing adapters remain unchanged while constructor dependencies introduce authority, capability, and lifecycle services.
- Compatibility mode is explicit, named, and temporary; it is not inferred from missing policy.
- Active authority mode fails closed when trusted policy is missing, empty, or invalid.
- Legacy behavior is never represented as unlimited authority. The compatibility policy contains a documented finite scope and capability set.
- Existing runtime tests that omit authority objects migrate through the trusted composition helper, not through prompt or adapter metadata.
- PRAP `AdapterCapabilities` continues to describe host integration support. Runtime execution permissions use the distinct `RuntimeCapability*` contracts.

## Failure Strategy

- Initialization failures occur before adapter context or command parsing.
- Authority, capability, and delegation denials stop before privileged action.
- Invalid lifecycle signals and transitions preserve the prior state.
- Collision, malformed configuration, and conflicting terminal-signal errors are typed and deterministic.
- All failures emit auditable evidence without exposing secrets or converting evidence into authority.
- No fail-open fallback exists for invalid or empty trusted authority.

## Rejected Alternatives

- Trusting prompt text or adapter metadata to grant authority.
- Treating `governance_validated`, `destructive_validated`, routing, or approval status as authority.
- Reusing PRAP `AdapterCapabilities` for runtime permissions.
- Using a process-global mutable capability registry.
- Copying parent scope or capabilities to a child without intersection.
- Inferring completion from ordinary text.
- Allowing a silent unlimited-policy fallback for current tests or adapters.
- Combining architecture definition with runtime implementation.

## Source Independence

This architecture is an original Orchestra contract derived from repository-local governance requirements and current runtime evidence. External-source records establish provenance and conceptual review only. No external source expression, prompt, payload, exploit, example, media, or documentation expression is reused, and no external concept supplies runtime authority.
