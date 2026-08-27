# Qualification Gates, Evaluation, and Independent Audit

**Contract:** `ORCHESTRA_QUALIFICATION_GATES_EVALUATION_AUDIT_V1`
**Machine record:** `QualificationGatePlan`
**Machine schema:** `machine/schemas/qualification-gate-plan.v1.schema.json`
**Authority class:** gate applicability, evidence completeness, evaluation protocol shape, and audit requirements are machine-validatable; adoption, merge, live-call, release, deployment, policy-activation, destructive, and branch-deletion authority remain separately governed

## Purpose

Campaign 4 defines the risk-proportional qualification layer between `FROZEN_CANDIDATE` and the human-owned promotion/acceptance decision.

It answers four questions without creating another workflow engine:

1. Which qualification gates apply to this exact frozen candidate?
2. Why is any gate legitimately `NOT_APPLICABLE`?
3. What evaluation mode is sufficient to test the claimed benefit or risk?
4. Is an independent read-only audit required before promotion?

```text
GATE_APPLICABILITY != AUTHORITY
VALIDATION_SUCCESS != FEATURE_VALUE
QUALIFIED != ACCEPTED
QUALIFIED != MERGE_READY
AUDIT_PASS != MERGE_AUTHORITY
EXPERIMENT_PLAN != LIVE_CALL_AUTHORITY
```

The record is bound to the exact frozen candidate identity. A source, tree, base, acceptance, policy, or scope identity change makes qualification evidence stale for the replacement candidate.

## Qualification gate families

The canonical qualification families are:

```text
ENGINEERING_VALIDATION
REGRESSION_COMPATIBILITY
SECURITY_GOVERNANCE
CONTROLLED_EVALUATION
INDEPENDENT_AUDIT
```

Each gate is either:

- `REQUIRED`, with status `PENDING | PASS | FAIL`; or
- `NOT_APPLICABLE`, with a non-empty justification and status `NOT_APPLICABLE`.

A missing justification is not equivalent to N/A. Unknown or contradictory applicability fails closed.

### Engineering validation

`ENGINEERING_VALIDATION` is required for every candidate, including documentation/truth corrections. Its depth is proportional to the change, but a candidate never qualifies with no engineering evidence at all.

### Regression and compatibility

`REGRESSION_COMPATIBILITY` is required when the candidate changes runtime behavior, public contracts, dependencies/integrations, capability behavior, trust boundaries, adaptive behavior promoted into use, or release/recovery automation.

A trivial truth correction may justify N/A only when it genuinely changes none of those surfaces.

### Security and governance

`SECURITY_GOVERNANCE` is required when the candidate changes or introduces any of:

- security or governance behavior;
- trust boundaries;
- dependencies or external integrations;
- adaptive-intelligence promotion;
- release/recovery automation;
- destructive automation.

This gate validates the applicable security/governance evidence. It does not create policy authority.

### Controlled evaluation

`CONTROLLED_EVALUATION` is required when the evaluation disposition is:

```text
ADVERSARIAL_VALIDATION_REQUIRED
SIMULATION_REQUIRED
EXPERIMENT_REQUIRED
```

Adaptive-intelligence promotion must use controlled evaluation; deterministic correctness alone is not sufficient evidence of real-world benefit.

Deterministic validation may be sufficient for changes whose behavior and benefit can be established without adversarial, simulated, or experimental evidence.

### Independent audit

The independent audit begins read-only and evaluates the frozen candidate, frozen scope/acceptance, current evidence, failure behavior, portability, duplication, security/governance implications, documentation truth, and complexity.

It is mandatory for:

- governance or security policy changes;
- material trust-boundary changes;
- adaptive-intelligence promotion;
- release/recovery automation;
- destructive automation.

It is conditional for bounded fixes and capability changes when risk or policy warrants a second opinion. It is normally unnecessary for a genuine trivial truth correction.

The first pass is always read-only. A blocker returns to the owning specialist for bounded remediation; any source remediation creates a new candidate identity and invalidates the prior exact-head qualification evidence.

## Evaluation disposition

Every frozen candidate records one evaluation disposition:

```text
DETERMINISTIC_VALIDATION_SUFFICIENT
ADVERSARIAL_VALIDATION_REQUIRED
SIMULATION_REQUIRED
EXPERIMENT_REQUIRED
NOT_APPLICABLE
```

`NOT_APPLICABLE` requires justification. It is not a shortcut around evidence.

### Controlled experiment requirements

When `EXPERIMENT_REQUIRED`, the plan must be preregistered before the experiment starts and freeze at least:

- research question and hypothesis;
- provider/model/revision identity;
- task/fixture identity;
- validator/evaluator identity;
- metrics;
- endpoint identity;
- order/balancing policy;
- retry policy;
- resource ceiling;
- stop conditions;
- state-isolation method.

The machine contract also requires:

```text
ALL_ATTEMPTS_RETAINED = true
OUTCOME_BASED_RETRY_PROHIBITED = true
SELECTIVE_EXCLUSION_PROHIBITED = true
POST_START_METRIC_CHANGE_PROHIBITED = true
NEGATIVE_INCONCLUSIVE_PRESERVED = true
```

An experiment protocol does not authorize model/provider calls. Live-call authority remains a separate explicit grant and must respect the frozen protocol ceilings.

## Independent-audit blockers

The following are blockers when established by current evidence:

- violation of a Prime Directive invariant or accepted requirement;
- exploitable security/governance bypass;
- missing, stale, contradictory, unverifiable, or non-reproducible required evidence;
- public-contract regression;
- frozen-scope exceedance;
- recovery, data, or authority-integrity risk;
- invalid benefit/experiment methodology.

The following are ordinarily non-blocking unless they reveal a governing requirement failure:

- style preference;
- speculative optimization;
- optional enhancement;
- broader redesign suggestion.

## Qualification aggregation

The machine record derives one qualification disposition:

```text
QUALIFICATION_PENDING
QUALIFIED
BLOCKED
```

Rules:

```text
any REQUIRED gate == FAIL
    -> BLOCKED

all REQUIRED gates == PASS
    -> QUALIFIED

otherwise
    -> QUALIFICATION_PENDING
```

`QUALIFIED` means that the applicable evidence obligations for the frozen candidate are satisfied. It does not decide whether Orchestra should permanently adopt the feature.

The lifecycle ordering is therefore:

```text
FROZEN_CANDIDATE
    -> qualification gates
    -> QUALIFIED
    -> human-owned promotion/adoption decision
    -> ACCEPTED
```

A candidate cannot become `ACCEPTED` merely because tests are green. The promotion decision remains governed by Feature Admission and the Prime Directive.

## Relationship to Candidate Maturity and autonomy

Campaign 2's `gate_applicability_ref` and `evaluation_disposition_ref` now refer to this Campaign 4 qualification record or its evidence projection.

Campaign 3's autonomy integration may remove redundant human pauses around evidence collection, monitoring, and recording, but it must not remove any gate marked `REQUIRED` and must not make the promotion/adoption decision.

```text
MORE_AUTONOMY = FEWER_UNNECESSARY_PAUSES
MORE_AUTONOMY != FEWER_REQUIRED_GATES
```

## Explicit exclusions

Campaign 4 does not add:

- a new CI platform;
- a second governance or autonomy engine;
- automatic specialist omission;
- automatic feature adoption;
- automatic merge;
- live model/provider calls;
- release/deployment/policy activation;
- destructive execution;
- branch deletion or cleanup;
- force push/history rewrite.

Those remain existing mechanisms or later separately governed actions.
