# Unified Testing Mechanism — Controlled Efficacy Calibration

**Date:** 2026-08-30
**Frozen UTM candidate:** `d5d1c9af408cc229838b68da2bb21ad1d19e76ee`
**Tree:** `36d7376a1ab087f0a7814141667b48c934179645`
**Status:** CONTROLLED_EVALUATION_PASS / PROMOTION_RECOMMENDATION_ONLY
**Live model/provider calls:** 0

## Question

Does Orchestra's experimental Unified Testing Mechanism (UTM) improve revision-bound readiness evidence completeness and fail-closed risk detection over a distributed-evidence aggregation baseline, without creating false-positive blocking or protected-action authority?

The study is intentionally scoped to the capability UTM adds: a common T0-T9 applicability/evidence contract and deterministic aggregate verdict. It does not re-test whether Overseer, Cipher, Cloak, Dagger, CodeQL, runtime tests, or cross-platform CI perform their own domain work correctly.

## Frozen comparison

The calibration compares two deterministic evaluators over the same 15 cases.

### Baseline — `DISTRIBUTED_EVIDENCE_PROXY_V1`

The baseline proxy inspects independent evidence-item signals that can exist without UTM:

- exact subject SHA syntax;
- evidence revision equality;
- terminal evidence references;
- explicit `FAIL`;
- explicit `PENDING`.

It deliberately does **not** add the cross-stage rules under evaluation:

- required-stage completeness;
- mandatory T0/T9 applicability;
- duplicate stage-evidence rejection;
- evidence-for-`NOT_APPLICABLE` rejection;
- canonical specialist ownership mapping;
- complete T0-T9 declaration.

This proxy is a controlled representation of the documented pre-UTM aggregation gap. It is not a claim that every historical/manual Orchestra review behaved exactly this way.

### UTM — `CANONICAL_UTM_AGGREGATOR_V1`

The UTM arm uses the frozen canonical `orchestra_runtime/unified_testing.py` contract. Valid packets are evaluated through `aggregate_packet()`. Malformed or contradictory packets fail closed as not-ready evidence.

## Corpus

The study contains:

- 4 clean controls;
- 2 missing-required-evidence cases;
- 2 explicit risk-signal cases;
- 7 structural-integrity cases.

Injected conditions cover:

- missing T7 security evidence;
- missing T8 regression evidence;
- explicit functional failure;
- pending security evidence;
- stale revision evidence;
- duplicate stage evidence;
- evidence for a stage declared `NOT_APPLICABLE`;
- T0 incorrectly declared `NOT_APPLICABLE`;
- missing T-stage declaration;
- canonical specialist-owner drift;
- terminal PASS evidence without an evidence reference.

All cases are retained. No outcome-based retry, selective exclusion, or post-start metric change is permitted.

## Preregistered thresholds

The study requires all of the following:

- UTM decision accuracy >= 95%;
- UTM accuracy improvement over baseline >= 20 percentage points;
- UTM unsafe-case detection >= 95%;
- UTM false-positive rate <= 5%;
- UTM false-negative rate <= 5%;
- UTM structural-integrity detection >= 95%;
- UTM missing-evidence detection >= 95%;
- all UTM authority flags remain false;
- zero model/provider calls;
- zero new runtime dependencies;
- no second QA/test engine;
- runtime integration remains disabled.

## Results

| Metric | Distributed proxy | UTM |
| --- | ---: | ---: |
| Decision accuracy | 8/15 — 53.33% | 15/15 — 100% |
| Unsafe-case detection | 4/11 — 36.36% | 11/11 — 100% |
| False positives on clean controls | 0/4 — 0% | 0/4 — 0% |
| False negatives on unsafe cases | 7/11 — 63.64% | 0/11 — 0% |
| Structural-integrity detection | 2/7 — 28.57% | 7/7 — 100% |
| Missing-evidence detection | 0/2 — 0% | 2/2 — 100% |

UTM improved decision accuracy by **46.67 percentage points** in this controlled calibration. All preregistered thresholds passed.

## Complexity and operating boundary

The canonical experimental UTM candidate changed seven files and added 815 lines relative to its frozen parent. It introduced:

- no new runtime dependency;
- no new CI platform;
- no second test engine;
- no default runtime integration.

The feature remains a thin evidence/applicability layer over existing specialist and CI mechanisms.

The following were **not measured** and no benefit claim is made for them:

```text
HUMAN_OPERATOR_TIME = UNMEASURED
LIVE_HOST_TOKEN_COST = UNMEASURED
LIVE_HOST_LATENCY = UNMEASURED
CROSS_HOST_CONSISTENCY = NOT_APPLICABLE_NO_HOST_EXECUTION
```

These omissions matter for the promotion disposition. The calibration establishes core coordination value, but not enough evidence to justify making UTM mandatory/default.

## Authority result

Every valid UTM verdict retained:

```text
release_authorized = false
merge_authorized = false
deployment_authorized = false
policy_activation_authorized = false
```

Malformed packets failed closed before producing readiness-complete evidence.

```text
READINESS_EVIDENCE_COMPLETE != RELEASE_AUTHORITY
QUALIFIED != MERGE_AUTHORITY
EFFICACY_PASS != PROMOTION_AUTHORITY
```

## Evidence recommendation

The deterministic evaluator returns:

```text
EVIDENCE_RECOMMENDATION = ADOPT_OPTIONAL
ALL_PREREGISTERED_THRESHOLDS_PASSED = true
```

`ADOPT_OPTIONAL` is the conservative evidence-backed recommendation because the calibration establishes measurable completeness/risk-detection value while operator-time and live-host cost remain unmeasured.

This document does not itself change the Feature Decision Record or authorize merge, release, deployment, policy activation, destructive operations, or default runtime integration.
