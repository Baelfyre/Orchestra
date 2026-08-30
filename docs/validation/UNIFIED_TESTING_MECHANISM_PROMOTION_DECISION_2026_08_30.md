# Unified Testing Mechanism Promotion Decision

Date: 2026-08-30

Decision owner: Baelfyre maintainer

Disposition: `ADOPT_OPTIONAL`

## Decision

The Unified Testing Mechanism T0-T9 is adopted as a supported optional evidence and applicability layer.

The decision is deliberately not `ADOPT` as mandatory or default behavior. The controlled efficacy campaign established bounded coordination value, but it did not measure human operator time, live-host token cost, live-host latency, or cross-host generalization. The distributed-evidence baseline is also a controlled proxy rather than an exact reconstruction of every historical Orchestra workflow.

## Machine-readable status

```text
promotion.status = DECIDED
promotion.disposition = ADOPT_OPTIONAL
UNIFIED_TESTING_MECHANISM = SUPPORTED_OPTIONAL
UTM_DEFAULT = NON_MANDATORY
UTM_READINESS = EVIDENCE_ONLY
RUNTIME_INTEGRATION = false
HUMAN_OPERATOR_TIME = UNMEASURED
LIVE_HOST_TOKEN_COST = UNMEASURED
LIVE_HOST_LATENCY = UNMEASURED
```

## Evidence basis

The canonical efficacy evidence is bound to:

- canonical commit `c5601f68ba3c84272c17a16bd94e0ddeb67f83b2`
- canonical tree `51845f70b3952f3017ba89f1f8e2ff9386cbcf7b`
- canonical efficacy PR `#648`
- `docs/validation/UNIFIED_TESTING_MECHANISM_EFFICACY_2026_08_30.md`
- `docs/validation/UNIFIED_TESTING_MECHANISM_EFFICACY_INDEPENDENT_AUDIT_2026_08_30.md`
- `machine/benchmarking/utm-efficacy-study.v1.json`
- `machine/benchmarking/utm-efficacy-result.v1.json`
- `machine/benchmarking/utm-efficacy-qualification-plan.v1.json`

The frozen 15-case controlled study reported:

- distributed-evidence proxy readiness-decision accuracy: 8/15, 53.33%
- UTM readiness-decision accuracy: 15/15, 100%
- distributed-evidence proxy unsafe-case detection: 4/11, 36.36%
- UTM unsafe-case detection: 11/11, 100%
- UTM false positives: 0/4
- UTM false negatives: 0/11
- distributed-evidence proxy structural-integrity detection: 2/7
- UTM structural-integrity detection: 7/7
- distributed-evidence proxy missing-required-evidence detection: 0/2
- UTM missing-required-evidence detection: 2/2
- readiness-decision accuracy gain: +46.67 percentage points
- preregistered efficacy thresholds: all passed
- model/provider calls: 0

The independent read-only audit concluded `PASS_WITH_RECORDED_LIMITATIONS` and supported optional rather than mandatory/default adoption.

## Why `ADOPT_OPTIONAL`

The study establishes useful bounded value for revision-bound applicability, omitted-stage reasoning, heterogeneous evidence aggregation, and fail-closed readiness interpretation. UTM also reuses existing specialist and CI validation surfaces rather than introducing a second QA engine.

Optional adoption preserves the demonstrated coordination capability while avoiding claims that the evidence does not support. It also preserves reversibility and prevents an experimental evidence layer from becoming mandatory governance complexity without measured operational-cost evidence.

## Claims intentionally not made

This decision does not claim:

- measured human operator-time savings
- measured live-host token savings or cost reduction
- measured live-host latency improvement
- cross-provider or cross-host efficacy generalization
- exact equivalence between the controlled distributed-evidence proxy and every historical Orchestra testing workflow
- release readiness, deployment readiness, policy approval, or protected-action authority from UTM readiness evidence

## Authority boundary

`ADOPT_OPTIONAL` is a feature disposition, not execution authority.

UTM evidence, `READINESS_EVIDENCE_COMPLETE`, `QUALIFIED`, efficacy success, or this promotion record cannot independently grant implementation, merge, release, deployment, policy activation, installed-integration refresh, destructive cleanup, branch deletion, force push, history rewrite, or any other protected-action authority.

Runtime integration remains disabled by this decision. UTM remains a thin applicability and evidence-aggregation layer over existing QA and CI mechanisms.

## Priority 1 closeout

This decision closes the governed Priority 1 Unified Testing Mechanism lifecycle once this decision record itself is canonically qualified and merged. It does not start, authorize, or imply implementation of Priority 2 multi-model provider work or Priority 3 self-learning work.
