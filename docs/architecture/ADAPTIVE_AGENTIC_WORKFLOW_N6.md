# Adaptive Agentic Workflow N6 - Advanced Adaptation Admission

Status: IMPLEMENTATION CANDIDATE - CURRENT DISPOSITION NO PROMOTION

Canonical prerequisites:

- Orchestra N5 merge: `0b5582e7175cb1ca432b371aad21634f35fa34aa`
- N5 qualified source head: `d3541396f919b6f628768f4eed79924a32610538`
- Padayon N6 authority merge: `61769d2cc67a769967b324afd058be718c7d0f75`
- Controlled AWF routing corpus after N5: 68 scenarios

## Purpose

N6 asks whether advanced adaptation should move beyond deterministic AWF execution.

It evaluates three candidate promotions:

1. A5 execution-effective topology selection;
2. learned routing recommendations;
3. OEE concurrency widening.

N6 is an admission gate, not an execution bridge.

```text
EVIDENCE ADMISSION != EXECUTION PROMOTION
PROMOTION CANDIDATE != PROMOTION EFFECTIVE
```

Even if a future evidence package makes a candidate eligible, N6 only returns a promotion candidate requiring a separate governed transition.

## Current evidence

### A5 topology ranking

The canonical A5 shadow ranker is valid and non-authorizing. The later B2.5 confirmatory experiment produced:

- 40 accepted runs;
- 120 model calls in the replacement confirmatory session;
- complete recomputable context-transfer evidence;
- no quality, safety, governance, or repository mutation failure;
- 14 of 20 directional wins against a preregistered minimum of 15;
- two-sided exact sign-test `p = 0.11531829833984375`, above `0.05`;
- median paired relative context reduction of about 25.53%;
- a passing quality guardrail;
- failed combined preregistered benefit criteria.

The canonical conclusion remains:

```text
CONFIRMATORY_BENEFIT_NOT_ESTABLISHED
A5_EXECUTION_EFFECTIVE_PROMOTION = NOT_AUTHORIZED_AND_NOT_PERFORMED
```

N6 must not reinterpret a descriptive effect size or a shadow top-1 result as promotion authority.

### Learned routing

A3 remains shadow-only. Its candidates are not exact TaskProfile/topology-bound predictive-performance evidence and its promotion bridge remains absent.

Therefore:

```text
LEARNED_ROUTING_RECOMMENDATIONS =
BLOCKED_NO_EXACT_PREDICTIVE_BENEFIT_EVIDENCE
```

### OEE concurrency

The canonical execution budget remains:

```text
max_parallel_specialists = 1
```

No confirmatory evidence establishes benefit from widening the permitted parallel specialist ceiling, and no separate OEE policy authorization exists.

Therefore:

```text
OEE_CONCURRENCY_WIDENING =
BLOCKED_NO_PARALLEL_BENEFIT_OR_POLICY_AUTHORIZATION
```

## Machine admission surface

N6 adds:

- `machine/schemas/advanced-adaptation-admission.v1.schema.json`
- `machine/adaptive/advanced-adaptation-admission.v1.json`
- `orchestra_runtime/domain/adaptive/advanced_adaptation.py`
- `tests/runtime/test_advanced_adaptation_admission.py`

The static machine admission record is recomputed from canonical evidence during tests. A mismatch fails validation.

## Current disposition

```text
AWF-N6 =
COMPLETE_NO_PROMOTION_EVIDENCE_INSUFFICIENT

A5 execution-effective selection =
BLOCKED

Learned routing control =
BLOCKED

OEE concurrency widening =
BLOCKED

Deterministic AWF =
REMAINS ACTIVE

max_parallel_specialists =
1
```

This is a valid negative promotion decision, not a failed implementation.

## Future evidence-positive behavior

Tests also exercise a hypothetical future A5 package in which all required benefit evidence passes.

The expected result is intentionally:

```text
PROMOTION_CANDIDATE_REQUIRES_SEPARATE_GOVERNED_TRANSITION
promotion_effective = false
runtime_executor_attachment = false
conductor_dispatch_mutation = false
```

Thus the admission evaluator cannot self-promote even under favorable evidence.

## Prohibited by N6

N6 does not:

- attach A5 ranking to Conductor dispatch;
- attach learned recommendations to execution;
- change specialist ownership or authority;
- widen OEE concurrency;
- create a new parallel execution mechanism;
- rerun prior experiments merely to seek a favorable result;
- release or deploy;
- activate policy;
- resume UIEF.

Any future promotion requires new qualifying evidence and a separately governed transition.
