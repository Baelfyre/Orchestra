# Feature Admission Policy

**Contract:** `ORCHESTRA_FEATURE_ADMISSION_V1`  
**Primary record:** `FeatureDecisionRecord`  
**Machine schema:** `machine/schemas/feature-decision-record.v1.schema.json`  
**Authority class:** record completeness is `MACHINE_VALIDATED`; ownership and adoption judgments remain `HUMAN_POLICY`

## Purpose

Feature Admission prevents implementation effort, passing tests, or accumulated code from being mistaken for proof that a capability should become permanent Orchestra complexity.

The policy asks two different questions at different times:

1. **Admission:** Is this proposal justified enough to implement or investigate within a bounded scope?
2. **Promotion:** After implementation and proportional evidence, should this capability become part of Orchestra, be simplified, remain optional or experimental, be replaced by configuration, be deferred, or be rejected?

The same `FeatureDecisionRecord` follows the proposal from admission through promotion so that the original problem, ownership rationale, falsification criterion, and cost assumptions remain visible when the final decision is made.

## Required proposal questions

A full `FeatureDecisionRecord` answers all of the following:

- What problem exists, and who experiences it?
- What evidence shows the problem is real?
- Why should Orchestra own the solution?
- Does Orchestra, the host, the provider, configuration, or documentation already solve it?
- What observable improvement is expected?
- What evidence would falsify the value claim?
- What complexity, maintenance, security, privacy, policy, and cognitive cost is introduced?
- Can the feature be optional, disabled, removed, or rolled back safely?
- What happens if Orchestra does not adopt it?
- What scope, owner, and authority reference apply?

A validator can require these answers to exist and conform to the schema. It cannot manufacture the answers or decide that the evidence is persuasive.

## Initial dispositions

```text
ADMIT
EXPERIMENT_ONLY
DEFER
REJECT
```

Meaning:

- `ADMIT`: bounded implementation or evaluation may proceed under separately resolved execution authority.
- `EXPERIMENT_ONLY`: the hypothesis is worth testing, but permanent adoption is explicitly not established.
- `DEFER`: the proposal is not rejected, but current evidence, priority, ownership, dependencies, or timing do not justify proceeding.
- `REJECT`: the proposal should not proceed under the current problem statement and evidence.

Admission is not implementation authority. A record with `ADMIT` still requires the ordinary Orchestra authority chain for any state-changing work.

## Promotion dispositions

```text
ADOPT
ADOPT_SIMPLIFIED
ADOPT_OPTIONAL
REPLACE_WITH_CONFIGURATION
EXPERIMENT_ONLY
DEFER
REJECT_NO_MEASURABLE_VALUE
REJECT_COMPLEXITY_EXCEEDS_BENEFIT
```

Promotion evaluates the implemented or investigated candidate against the original problem and frozen value claim.

- `ADOPT`: evidence supports permanent inclusion as proposed.
- `ADOPT_SIMPLIFIED`: the value is supported but a smaller permanent mechanism is sufficient.
- `ADOPT_OPTIONAL`: the value is supported for bounded users or contexts but should not become a mandatory/default path.
- `REPLACE_WITH_CONFIGURATION`: the problem is real but a configuration or existing mechanism solves it without new permanent capability.
- `EXPERIMENT_ONLY`: retain as research or experimental capability; production/default promotion is not justified.
- `DEFER`: evidence or priority remains insufficient for a permanent decision.
- `REJECT_NO_MEASURABLE_VALUE`: implementation may work technically, but proportional evidence does not establish the intended benefit.
- `REJECT_COMPLEXITY_EXCEEDS_BENEFIT`: the benefit does not justify the operational, maintenance, security, privacy, policy, or cognitive cost.

## Minimal evidence

A full decision record preserves:

- problem evidence;
- Orchestra-ownership rationale;
- comparison against existing mechanisms;
- observable expected outcome;
- explicit falsification criterion;
- bounded complexity and risk estimate;
- reversibility and rollback/removal plan;
- exact source and applicable policy identity;
- accountable decision owner;
- promotion evidence when a promotion decision is made.

Negative or inconclusive evidence is retained. A no-benefit result is a valid outcome and cannot be discarded merely because implementation effort was already spent.

## Semantic separation

```text
ADMIT != promotion
ADMIT != implementation authority
ADMIT != merge authority
VALIDATED != worth adopting
ADOPT != merge authority
ADOPT != release or activation authority
ADOPT != deployment authority
FEATURE_DECISION_RECORD != execution authority
```

The record constrains decisions and preserves evidence. It does not create runtime, Git, merge, release, deployment, policy-activation, destructive-operation, integration-refresh, force-push, or history-rewrite permission.

## Machine validation versus human judgment

Machine validation may determine:

- required fields exist;
- enumerated dispositions are valid;
- source SHA and policy references are structurally valid;
- authority-denial fields remain false;
- a decided promotion carries evidence and an accountable owner;
- an initial rejection does not masquerade as a later promotion;
- the inline-rationale fast path is or is not structurally eligible.

Machine validation must not decide:

- whether a problem is important enough to solve;
- whether Orchestra should own the capability;
- whether evidence is substantively persuasive;
- whether residual complexity or risk is acceptable;
- whether a candidate should be promoted;
- whether merge, release, deployment, activation, or destructive action is authorized.

Those decisions remain with the applicable human/governance authority.

## Inline rationale fast path

A separate full `FeatureDecisionRecord` is not required for a narrow correction that does not create a new product decision. The eligible classes are:

```text
TRIVIAL_TRUTH_CORRECTION
PARITY_REFRESH
TEST_RESTORING_ACCEPTED_BEHAVIOR
BOUNDED_BUG_FIX_ACCEPTED_REQUIREMENT
```

All inline cases require a non-empty rationale. The test-restoration and bounded-bug-fix classes additionally require an existing accepted-requirement reference.

The fast path is **not eligible** when any of the following is true:

```text
NEW_CAPABILITY
GOVERNANCE_OR_POLICY_CHANGE
AUTHORITY_CHANGE_OR_EXPANSION
TRUST_BOUNDARY_CHANGE
NEW_DEPENDENCY_OR_INTEGRATION
PROTECTED_ACTION_SEMANTICS_CHANGE
PUBLIC_API_OR_COMPATIBILITY_EXPANSION
SCOPE_OR_INTENT_EXPANSION
```

When classification is uncertain, the full record is required. The fast path reduces paperwork for already-decided behavior; it cannot be used to smuggle a new feature or policy decision past admission.

## Machine fast-path disposition

For deterministic validation, an eligible narrow correction returns:

```text
INLINE_RATIONALE_ALLOWED
```

Anything else returns:

```text
FULL_RECORD_REQUIRED
```

## Record lifecycle

The record is created at proposal/admission time and remains the same logical record through promotion. Promotion may initially be `PENDING`. If the proposal is rejected at admission, promotion is `NOT_APPLICABLE`. A later decision to revive a materially different objective should create a new admission decision rather than silently rewriting the rejected record.

Campaign 1 does not introduce a candidate-maturity engine, Feature Freeze, or automated promotion. Those belong to later Development Lifecycle V2 campaigns. This policy only establishes the constitutional admission/promotion distinction and its machine-validatable record.

## Relationship to the Prime Directive

The Feature Admission policy operationalizes the Prime Directive requirement that permanent capability be justified by proportional evidence of an Orchestra-owned problem and a favorable benefit-versus-complexity/risk decision.

See `docs/governance/ORCHESTRA_PRIME_DIRECTIVE.md`.
