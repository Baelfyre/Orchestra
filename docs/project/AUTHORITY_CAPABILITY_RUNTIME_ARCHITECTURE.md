# Authority and Capability Runtime Architecture

Status: Phase 6B-D runtime integration and Phase 6C adversarial validation implemented and merged through PR #183. Phase 6D release preparation is complete locally under Issue #184 and pending maintainer review.

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

The current trusted runtime flow is:

```text
Trusted RuntimeComposition
-> root authority and capability-manifest validation
-> lifecycle initialization
-> Adapter ContextPackage
-> Command
-> RouterService
-> immutable route binding
-> authority evaluation
-> capability evaluation
-> GovernanceValidator
-> lifecycle activation
-> in-process operation or bounded child execution
-> structured lifecycle signal and result
-> RuntimeAuditEvent evidence
-> ExecutionResult
```

`RuntimeExecutor` requires an explicit immutable `RuntimeComposition` before adapter access. The composition carries an `ACTIVE` or `COMPATIBILITY` authority mode, run identity, root authority, capability manifest, evaluators, lifecycle controller, delegation validator, audit integration, and finite trusted route bindings. `ContextAssembler`, `RouterService`, and `GovernanceValidator` retain their existing responsibilities; governance metadata such as `governance_validated`, `destructive_validated`, and `dry_run` cannot grant authority or capabilities.

`ExecutionResult` retains its original fields and now adds verified run identity, authority and capability decision references, authority mode, lifecycle state, structured terminal result, and runtime audit-event references. `RouteDecision.governance_required` remains governance routing only.

## Implemented Boundaries

- Trusted authority and capability contracts are immutable and run-scoped.
- Active mode fails closed for missing, malformed, mismatched, or untrusted composition.
- Compatibility mode is explicit and bounded to the repository-supported command and specialist routes.
- Each run identity initializes once. Retained root and child snapshots reject repeat execution before trusted-contract revalidation or adapter access.
- Every capability grant uses the manifest provenance, and every binding with a present capability uses a grant owned by the bound specialist.
- Exact immutable bindings map routed work to an authority target and operation plus a runtime capability and operation.
- Authority and capability decisions occur before governance, and denials stop before runtime operation.
- Accepted delegation creates a bounded in-process child run; rejected delegation creates no child lifecycle or operation.
- Lifecycle state changes require structured signals. `ACTIVATE`, `WAIT`, and `RESUME` also enforce exact source states.
- Structured audit events record initialization, decisions, delegation, transitions, and terminal results without granting authority.

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

Phase 6B-D preserves this trust boundary through explicit constructor dependencies. Existing metadata and governance results remain untrusted for authority and capability grants.

## Implemented Runtime Sequence

Phase 6B-D implements this sequence:

```text
Trusted runtime configuration
-> Root authority validation
-> Immutable run identity
-> Immutable runtime capability manifest
-> Lifecycle initialization
-> Adapter context
-> Command parsing
-> Routing
-> Trusted route binding
-> Authority evaluation
-> Capability evaluation
-> Governance validation
-> Lifecycle activation
-> Operation and structured signal
-> Lifecycle terminal or waiting transition
-> Audit evidence
-> ExecutionResult
```

Authority and capability evaluation precede governance validation because governance decides whether an otherwise authorized route may proceed; it cannot make an unauthorized target, operation, or capability valid. Adapter context remains after trusted initialization so host input cannot influence root grants. Missing route bindings deny execution.

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
| Runtime implementation | Assigned specialists | Implemented through the separately authorized Phase 6B and Phase 6C batches. |

## Initialization Sequence

1. Trusted runtime composition supplies an explicit authority mode and immutable repository-owned policy.
2. Composition validation requires each grant provenance to match the manifest and each present bound capability to be owned by the bound specialist.
3. `RuntimeExecutor` rejects any retained `run_id` before root or manifest revalidation.
4. The authority evaluator validates a non-empty `AuthorityScope` and its `AuthorityProvenance`.
5. Runtime composition creates an immutable run identity.
6. The capability resolver validates grants, rejects identity collisions, calculates the effective set, and freezes a `RuntimeCapabilityManifest` owned by that run.
7. The lifecycle controller creates the run in its pre-execution state, which is retained by exact run identity through waiting or termination.
8. Initialization emits root-authority and capability-manifest audit events.
9. Missing, invalid, empty, mismatched, untrusted, or already initialized composition produces a typed initialization failure before adapter input is accepted.

## Execution Sequence

1. The adapter supplies context and the command parser creates a `Command`.
2. `RouterService` selects a route without granting authority.
3. The immutable runtime policy resolves the exact command and specialist binding; a missing binding denies execution.
4. `IAuthorityEvaluator` evaluates the bound target and operation against the immutable effective scope.
5. `ICapabilityResolver` evaluates the bound runtime capability identity and operation against the immutable manifest.
6. Any denial stops before runtime operation and emits structured evidence.
7. `GovernanceValidator` applies governance rules only after authority and capability checks pass.
8. `ILifecycleController` validates entry to active execution.
9. Execution returns a structured operation result plus typed lifecycle signal; ordinary text is output only.
10. The lifecycle controller validates the terminal or waiting transition and audit events record each decision before `ExecutionResult` is returned.

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
5. `ACTIVATE` is valid only from `INITIALIZING`, `WAIT` only from `ACTIVE`, and `RESUME` only from `WAITING`.
6. Completion, failure, cancellation, timeout, and blocking use distinct terminal signals and results.
7. An exact duplicate terminal signal is idempotent; a conflicting terminal signal is rejected and audited.
8. Invalid transitions fail deterministically without changing state.
9. Ordinary prompt, adapter, model, or tool text cannot transition lifecycle state.

## Audit Sequence

Audit records are append-only evidence derived from validated actions. Events cover root authority creation, authority decisions, capability-manifest creation, capability decisions, delegation acceptance or rejection, lifecycle transitions, terminal results, and typed initialization failures. Each event carries stable run identity, event type, decision or transition data, provenance references, and a deterministic reason code where applicable. Audit writes never change authority, capability, delegation, or lifecycle state.

## Compatibility Strategy

- Trusted runtime composition supplies a repository-owned finite root policy for existing construction paths only through the explicit compatibility helper.
- Existing adapters remain unchanged while constructor dependencies provide authority, capability, delegation, lifecycle, and audit services.
- Compatibility mode is explicit, named, and temporary; it is not inferred from missing policy.
- Active authority mode fails closed when trusted policy is missing, empty, or invalid.
- Legacy behavior is never represented as unlimited authority. The compatibility policy contains a documented finite scope and capability set.
- Existing runtime tests use the trusted composition helper, not prompt or adapter metadata.
- PRAP `AdapterCapabilities` continues to describe host integration support. Runtime execution permissions use the distinct `RuntimeCapability*` contracts.

## Failure Strategy

- Initialization failures occur before adapter context or command parsing.
- Authority, capability, and delegation denials stop before privileged action.
- Invalid lifecycle signals and transitions preserve the prior state.
- Collision, malformed configuration, and conflicting terminal-signal errors are typed and deterministic.
- All failures emit auditable evidence without exposing secrets or converting evidence into authority.
- No fail-open fallback exists for invalid or empty trusted authority.

## Phase 6B-D and Phase 6C Completion

- PR #181 and PR #183 are merged. Issues #180 and #182 are closed.
- Phase 6B-D trusted runtime composition, authority and capability enforcement order, lifecycle control, bounded delegated child execution, structured audit integration, and additive result evidence are complete and merged.
- Phase 6C adversarial validation covers trusted initialization, prompt and adapter escalation, routing and governance confusion, authority and capability attacks, delegation attacks, lifecycle attacks, execution ordering, and audit-sink failure.
- The Butler-authorized lifecycle correction rejects `RESUME` from `INITIALIZING` and `ACTIVATE` from `WAITING` with `INVALID_SIGNAL_SOURCE_STATE`; existing valid activation, waiting, resume, terminal replay, and conflict behavior remains unchanged.
- Maintainer corrections retain one lifecycle history per root or child `run_id`, require manifest-grant provenance consistency, require present bound capabilities to be owned by the bound specialist, and preserve runtime `CAPABILITY_DENIED` behavior for absent capability identifiers.
- The four promotions are `IMPLEMENTED`, and the Pattern Catalog is synchronized to those canonical records.
- Phase 6D refreshes the README and prepares target release `v1.1.2` without changing runtime behavior.
- The `v1.1.2` tag and GitHub Release remain outside this branch and require a separate post-merge publication gate.

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
