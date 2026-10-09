# Orchestra AR-2 Domain Extraction Closeout

Status: `AR_2_CLOSEOUT_CANDIDATE`

Phase: `AR-2 — Domain Extraction`

Canonical source baseline for this candidate: `1081ce3ba0e32b63f0ffab8380b211755f8b27f2`.

## Purpose

Complete the bounded AR-2 domain-extraction campaign without starting AR-3 application decomposition or pulling infrastructure concerns inward.

AR-2 uses the repository's strangler-compatibility strategy: pure Orchestra semantics move to bounded domain packages, while mixed legacy modules remain as compatibility and orchestration surfaces until later phases can relocate application, host, provider, persistence, transport, and entrypoint responsibilities safely.

## Canonical AR-2 domain ownership established

The full AR-2 campaign establishes inward ownership for the following qualified semantics:

- shared deterministic canonicalization primitives under `orchestra_runtime/shared/canonicalization.py`;
- context state and compilation semantics under `orchestra_runtime/domain/context/`;
- governance authority/provenance/constraint semantics under `orchestra_runtime/domain/governance/authority.py`;
- capability grant, evaluation, intersection, and manifest semantics under `orchestra_runtime/domain/capabilities/`;
- execution correlation, run identity, and lifecycle semantics under `orchestra_runtime/domain/execution/`;
- governance decision/result contracts under `orchestra_runtime/domain/governance/kernel.py`;
- pre-execution intent and policy semantics under `orchestra_runtime/domain/governance/preexecution.py`;
- workflow sanity receipt semantics under `orchestra_runtime/domain/orchestration/workflow.py`.

The domain layer depends only on deterministic standard-library primitives plus `orchestra_runtime.domain` and `orchestra_runtime.shared`.

## Residual extraction in this closeout candidate

### Capability manifest

`RuntimeCapabilityManifest` moves from `orchestra_runtime.capabilities` to `orchestra_runtime.domain.capabilities.manifest`.

The legacy module re-exports the exact same class object. Capability policy loading, resolver orchestration, filesystem-backed trusted policy loading, and runtime audit-event projection remain outside the domain.

### Governance kernel contracts

The following contracts move to `orchestra_runtime.domain.governance.kernel`:

- `GovernanceDecision`;
- `TransitionDisposition`;
- `ArbiterReasonCode`;
- `GovernanceDecisionRecord`;
- `ArbiterKernelResult`.

`orchestra_runtime.governance_kernel` re-exports the same objects while retaining `ArbiterKernelInput`, machine-policy-derived remediation defaults, transition precedence consumption, Arbiter evaluation, and fail-closed integration behavior.

The retained input/evaluator surface is deliberately not moved because its defaults and precedence are bound to repository machine policy and runtime transition orchestration rather than being isolated domain values.

### Pre-execution policy semantics

The following move to `orchestra_runtime.domain.governance.preexecution`:

- `ExecutionAction`;
- `PreExecutionConstraint`;
- `PreExecutionReason`;
- `ExecutionIntent`;
- `PreExecutionPolicy`.

The legacy module re-exports exact object identity while retaining host-capability mapping, `PreExecutionGateResult`, host evaluation, Arbiter integration, and application-level gate orchestration.

### Workflow receipt semantics

`WorkflowSanityReceipt` moves to `orchestra_runtime.domain.orchestration.workflow`.

The legacy `orchestra_runtime.workflow_contracts` module re-exports it and retains machine-route resolution plus `RouteDecision` / `ValidationResult` integration in the builder.

## Intentionally retained for later phases

The following are not unfinished AR-2 work. They are mixed or boundary-facing responsibilities whose safe destination belongs to later architecture phases:

- `CapabilityResolver`, trusted policy loading, and capability audit-event projection: AR-3 / AR-4;
- `ArbiterKernelInput`, machine policy loading, transition precedence, and Arbiter evaluation orchestration: AR-3 / AR-4;
- pre-execution host capability mapping, gate evaluation, and Arbiter integration: AR-3 / AR-4;
- workflow sanity receipt construction from machine routing and application validation records: AR-3;
- `ApprovedUnitPlan` contextual validation and its coupled runtime-envelope/application contract: AR-3, where plan/domain versus DTO/use-case placement can be split coherently rather than partially moving one stable schema surface;
- route/validation/execution result DTO-like records in `models.py`: AR-3;
- runtime audit-event projection and envelope boundary records: AR-3 / AR-4;
- MCP, provider, host, registry, Git/worktree, repository, persistence, serialization, and evidence implementations: AR-4;
- adaptive normalization: AR-5;
- resource/internal cleanup, test architecture, facade retirement, and pre-release requalification: AR-6 through AR-9.

This closeout does not reinterpret those retained concerns as domain-owned merely because some of their code is deterministic.

## Compatibility preservation

AR-2 preserves existing supported import paths. Legacy modules remain available and re-export migrated values where required. No compatibility facade is retired in AR-2.

Object-identity regression tests cover the new residual domain contracts so callers importing the legacy names continue to receive the canonical domain classes.

## Validation requirements

Before this closeout may become canonical:

1. architecture placement validation must pass;
2. existing runtime tests and targeted domain tests must pass;
3. Governance Check must pass;
4. repository `validate` must pass;
5. Required Analysis Compatibility must pass;
6. Cross-platform Validation must pass on Windows, Ubuntu, and macOS;
7. applicable CodeQL and mutation-confidence workflows must pass when triggered;
8. README machine-index parity and changelog freshness must pass;
9. the canonical post-merge revision must independently pass all applicable protected checks.

Passing validation does not create authority beyond the already approved architecture refoundation scope.

## AR-2 completion rule

AR-2 is complete only after this residual closeout becomes canonical and the resulting `main` revision independently passes the applicable post-merge qualification.

At that point:

- AR-0 is complete;
- AR-1 is complete;
- AR-2 is complete;
- AR-3 remains unstarted.

The architecture campaign may then remain paused before AR-3 while separately governed specialist work proceeds. No release, deployment, production mutation, provider routing/fallback change, policy activation, installed-integration refresh, destructive cleanup, branch deletion, force push, or history rewrite is authorized by this closeout.
