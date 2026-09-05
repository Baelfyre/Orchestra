# Orchestra Execution Efficiency V1

Status: OEE-0 guardrail contract

## Invariant

```text
MINIMIZE_EXECUTION_COST_WITHOUT_MINIMIZING_REQUIRED_EVIDENCE_OR_IMPLEMENTATION_QUALITY
```

Execution efficiency is a constraint on redundant work, not permission to skip required evidence, implementation quality, security, governance, validation, or human gates.

## OEE-0 boundary

OEE-0 installs the machine contract and validation primitives only. It does not rewrite Conductor dispatch, resume UIEF, or authorize later OEE phases.

The canonical machine record is:

`machine/governance/execution-budget.v1.json`

Schema:

`machine/schemas/execution-budget.v1.schema.json`

Runtime domain primitives:

`orchestra_runtime/domain/orchestration/execution_efficiency.py`

## Evidence budget

Work progresses through E0-E5:

1. E0 ORIENTATION
2. E1 INPUT_INTEGRITY
3. E2 TARGETED_ANALYSIS
4. E3 IMPLEMENTATION
5. E4 QUALIFICATION
6. E5 PROMOTION

A higher tier may not begin until all required prior tiers are complete.

## Default execution budget

- maximum parallel specialists: 1
- specialist retry limit after the initial attempt: 1
- owner-first routing required
- broad search requires exhaustion of narrower search levels
- reusable evidence must remain bound to exact source identity
- full validation requires a stable candidate
- passive CI waiting must not consume active model reasoning
- autonomous campaigns load one phase at a time
- optional review cannot become blocking without explicit authority

## Search escalation

```text
EXACT_PATH
-> EXACT_SYMBOL
-> BOUNDED_DIRECTORY
-> REPOSITORY_WIDE
-> EXTERNAL
```

Escalation may advance by one level only after the narrower level is insufficient.

## Validation escalation

```text
SYNTAX_SCHEMA
-> DIRECT_TESTS
-> SUBSYSTEM
-> REPOSITORY_QUALIFICATION
-> PROTECTED_GATES
```

Expensive validation is deferred until the candidate is stable.

## Earliest decisive evidence

A decisive stop signal records:

- owner
- evidence_sufficient
- stop_required
- downstream_execution_allowed
- reason
- evidence_refs

When evidence is sufficient and stop is required, downstream execution must be false.

## Existing authority is preserved

Conductor owns routing and sequencing. Arbiter retains transition/stop authority. Overseer retains validation evidence authority. The Tuner retains evidence freshness/invalidation coordination. Scribe records durable measurements. The Governor remains legal/compliance governance and is not converted into an execution owner.

OEE does not create a new specialist or expand existing authority.
