# Unified Testing Mechanism — Independent Read-Only Efficacy Audit

**Date:** 2026-08-30  
**Audit mode:** READ_ONLY  
**Frozen candidate:** `d5d1c9af408cc229838b68da2bb21ad1d19e76ee`  
**Audit disposition:** PASS_WITH_RECORDED_LIMITATIONS  
**Remediation performed during audit:** none

## Audit scope

This pass independently reviews:

- the frozen canonical UTM contract;
- its Feature Decision Record and falsification criterion;
- the controlled efficacy study design;
- the baseline proxy boundary;
- the 15-case corpus;
- the deterministic result;
- authority separation;
- duplication/complexity risk;
- whether the evidence supports the recommended promotion disposition.

The audit is read-only. It does not modify the frozen candidate, alter metrics after seeing results, remove negative cases, or grant promotion/merge/release authority.

## Findings

### 1. The study tests the incremental capability UTM actually adds — PASS

UTM does not claim to replace domain validators. The baseline proxy therefore retains item-level evidence checks while excluding the common T0-T9 applicability/aggregation rules introduced by UTM. This makes the comparison targeted rather than duplicating specialist correctness tests.

### 2. Ground truth is explicit and preserved — PASS

Each case declares whether readiness evidence should be complete before evaluation. Four clean controls and eleven unsafe/incomplete cases are retained. No case is excluded because of its outcome.

### 3. UTM produces measurable incremental detection value — PASS

The frozen result shows:

- decision accuracy: 53.33% baseline proxy -> 100% UTM;
- unsafe-case detection: 36.36% -> 100%;
- structural-integrity detection: 28.57% -> 100%;
- missing-required-evidence detection: 0% -> 100%;
- clean-case false positives: 0% for both arms.

The 46.67 percentage-point decision-accuracy gain exceeds the preregistered 20-point minimum.

### 4. Authority boundaries remain intact — PASS

The evaluator checks valid UTM verdicts for false authority flags. Invalid packets are treated as fail-closed not-ready outcomes and do not synthesize authority. The efficacy result itself is explicitly advisory.

### 5. The design does not create a second QA engine — PASS

The evaluator calls the canonical UTM aggregator and uses synthetic evidence packets. It does not reimplement Cipher, Cloak, Dagger, Overseer, CodeQL, runtime tests, cross-platform validation, or merge readiness.

### 6. Complexity is real but bounded — PASS WITH LIMITATION

The experimental candidate added a moderate permanent contract surface. The measured benefit is large in the bounded calibration and there are no new runtime dependencies or default integration. However maintenance burden remains non-zero.

This supports optional adoption more strongly than mandatory/default adoption.

## Limitations

1. **Baseline proxy limitation.** `DISTRIBUTED_EVIDENCE_PROXY_V1` is a controlled proxy for the documented aggregation gap, not a reconstruction of every historical human review.
2. **Fixture coupling.** The corpus uses canonical UTM stage vocabulary and deliberately targets its declared fail-closed rules. This is appropriate for contract calibration but weaker than a longitudinal field study.
3. **Operator-effort evidence is absent.** Human coordination time was not measured.
4. **Live token/cost/latency evidence is absent.** Zero live model/provider calls were made.
5. **Cross-host evidence is not applicable.** UTM evaluation is deterministic and host-independent in this campaign; no host-execution claim is made.
6. **Default adoption is therefore not supported.** The current evidence supports keeping the capability opt-in/reversible.

These limitations do not invalidate the core completeness/detection result, but they constrain the promotion recommendation.

## Audit conclusion

```text
CONTROLLED_EVALUATION = PASS
INDEPENDENT_READ_ONLY_AUDIT = PASS
CORE_INCREMENTAL_VALUE = ESTABLISHED_FOR_BOUNDED_CALIBRATION
DEFAULT_USE_EFFICIENCY = NOT_ESTABLISHED
LIVE_HOST_COST_BENEFIT = NOT_ESTABLISHED
RECOMMENDED_PROMOTION = ADOPT_OPTIONAL
```

`ADOPT_OPTIONAL` preserves the demonstrated coordination benefit while retaining reversibility and avoiding a claim that UTM should become mandatory or default.

```text
AUDIT_PASS != MERGE_AUTHORITY
AUDIT_PASS != RELEASE_AUTHORITY
AUDIT_PASS != POLICY_AUTHORITY
```
