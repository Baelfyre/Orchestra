# UIX-9B V2 Live Controlled-Proof Execution Protocol

Status: prepared, frozen, and waiting for a separate human UIX-9C authorization. This document does not authorize model calls, provider calls, or experimental execution.

## Scientific question

Does adding canonical Orchestra UIX-1 through UIX-8 guidance materially improve objective UI implementation fidelity when provider, model, task, starting project, permitted dependencies, resource ceiling, validator, acceptance requirements, and retry policy remain the same?

The protocol excludes model self-rating and primary subjective visual scores. No metric, threshold, repetition count, retry policy, or endpoint may change after the first live result.

## Historical boundary

UIX-9A remains the deterministic zero-call proof layer. The six historical UIX-9C observations remain immutable `PROTOCOL_BREACH` records with `MISSING_FROZEN_LIVE_METRIC_EVALUATOR` and scientific weight zero. They are not calibration fixtures and do not contribute results.

V2 adds separate artifacts. It does not rewrite V1 schemas, fixtures, runner, or historical evidence.

## Frozen identities

The frozen identity record is `machine/ui/uix9b-live-proof-v2-identity.json`.

| Identity | Value |
| --- | --- |
| Canonical SHA | `bf6f14316fa8814eeac91440c4a7d70be0d04b9e` |
| Fixture digest | `280f1361eda45c2b632c37dd049ec47dec81ab1e8e9e81c61a7aa0d9fb96b978` |
| Task digest | `3708f0d7d172a424ed426a6275d5012df6a11b0718ed37cba95ba0724c0c506d` |
| Validator digest | `285494688ef105c813ef5f449f1e13b75529c8cddbf8a42ea76d283a9d5eecf3` |
| UIX-1 through UIX-8 guidance digest | `f989ac579875fbcd349f812fa6e241ba5c8505f9f940abcb5e0e30006f1606ab` |
| Evaluator version | `uix9b-live-metric-evaluator-v2.0.0` |
| Evaluator digest | `d585010eb83ec23b1df2c3512868e9ff5285e7dced1393dcafb0233b835f7ae1` |

The evaluator also revalidates the canonical UIX guidance manifest and every listed material digest. A mismatch fails closed.

## Frozen task and arms

Both arms receive the same frozen fixture, task, component inventory, reference material, assets, permitted dependencies, validator, acceptance requirements, resource ceiling, provider/model, and retry policy.

Arm A is `BASELINE_NO_ORCHESTRA_UIX_GUIDANCE` with `guidance_digest_or_NONE=NONE`.

Arm B is `GOVERNED_CANONICAL_UIX_1_8_GUIDANCE` with the frozen UIX-1 through UIX-8 manifest and digest. UIX-9 result logic, historical observations, calibration outputs, and adjudication results are excluded from treatment.

The only intended treatment difference is the presence of canonical UIX-1 through UIX-8 guidance. The frozen task is `tests/fixtures/ui/uix9-live-project/task.md`.

## Deterministic evaluator

`scripts/uix9_live_metric_evaluator_v2.py` accepts a completed fixture bundle and an independent validator result. It performs zero model calls, zero provider calls, zero network access, zero subprocess calls, and zero external repository mutation. Its scoring function receives no arm, order, repetition, session, guidance treatment, or campaign outcome input.

The exact input, computation, datatype/range, missing-input behavior, invalid-input behavior, and aggregation rule for each metric are frozen in `machine/ui/uix9b-live-metric-evaluator.v2.json`.

The result is machine-readable and validated by `machine/schemas/uix9b-live-metric-result.v2.schema.json`. An observation must additionally validate against `machine/schemas/uix9b-live-proof-observation.v2.schema.json`. Pair and campaign adjudication are deterministic and closed by `scripts/uix9b_live_proof_adjudicator_v2.py` and `machine/schemas/uix9b-live-pair-adjudication.v2.schema.json` / `machine/schemas/uix9b-live-proof-result.v2.schema.json`.

## Primary metric directions

`COMPONENT_REUSE`, `ASSET_PROVENANCE`, `RESPONSIVE_CONTAINMENT`, `ACCESSIBILITY_INVARIANTS`, and `DETERMINISTIC_ACCEPTANCE` are true-is-better. `STATE_COVERAGE` is higher-is-better. `DUPLICATE_COMPONENT_COUNT`, `TOKEN_VIOLATIONS`, `ARBITRARY_STYLE_DRIFT`, and `UNRESOLVED_MAPPINGS` are lower-is-better. `ASSET_SUBSTITUTION`, `REVISION_MISMATCH`, and `VISUAL_BASELINE_REPLACEMENT` are false-is-better.

No single metric decides the result. Hard-guardrail regressions prevent a governed improvement classification.

## Calibration

The frozen calibration manifest is `machine/ui/uix9b-live-calibration-manifest.v2.json`. It contains synthetic known-answer positive, negative, boundary, malformed, and missing-artifact cases. Expected thirteen-metric outputs are frozen before any future live authorization. No historical UIX-9C output was used.

## Repetition and isolation

The planned order is `A1_THEN_B1`, `B2_THEN_A2`, `A3_THEN_B3`. Every execution starts from a fresh exact copy of the frozen fixture. No implementation output, generated file, source modification, conversational output, or arm-specific cache may cross a run boundary.

## Provider accounting and proposed ceilings

Historical counters are retained separately: six experimental model calls, six experimental provider calls, one nonexperimental availability probe, seven total provider interactions, and zero invalid-infrastructure retries.

The fresh authorization proposal uses separate immutable limits:

- six experimental model calls, one per planned valid execution;
- six experimental provider calls;
- at most one nonexperimental availability probe;
- seven total provider interactions across the campaign, including that probe;
- one replacement retry for an invalid infrastructure run;
- zero retries for a valid unfavorable output;
- 20,000 total tokens per run and 120,000 total campaign tokens, if trustworthy host counters are available;
- 900 seconds per run and 7,200 seconds for the campaign;
- zero external repository mutations.

These are proposed ceilings only. They are not active authority in this preparation state.

## Retry and invalid-run policy

Valid unfavorable output is retained and never rerun for outcome. Provider outage is classified explicitly and can only be replaced under the frozen outage policy and unspent limits. Host crash is an invalid infrastructure run and may be replaced once. Resource ceiling exhaustion stops the run and preserves evidence. Protocol breach fails closed under the frozen invalidation policy.

## Result classifications

The only result classifications are `BENEFIT_ESTABLISHED`, `NO_BENEFIT_ESTABLISHED`, `MIXED_OR_INCONCLUSIVE`, and `PROTOCOL_INVALID`. Benefit requires no governed hard-guardrail regression, governed deterministic acceptance equal to or better than baseline, multiple structural improvements across a majority of pairs, no single-metric dependency, and all counted runs valid. No-benefit does not imply harm. Conflicting or insufficient evidence is mixed or inconclusive. Unpreservable controls or evidence integrity are protocol invalid.

## Authority and boundary

The V2 runner is `scripts/uix9b_live_proof_runner_v2.py`. It verifies every frozen identity and refuses the execution command in preparation mode. The machine authorization request is `machine/ui/uix9b-live-call-authorization-request.v2.json`; the human-readable request is `docs/validation/UIX_9B_V2_LIVE_CALL_AUTHORIZATION_REQUEST.md`.

Current authority is explicitly false:

```text
LIVE_MODEL_CALLS_AUTHORIZED=false
PROVIDER_CALLS_AUTHORIZED=false
UIX_9C_EXECUTION_AUTHORIZED=false
MAX_NEW_LIVE_CALLS=0
```

No external repository or protected-system mutation is permitted. No production credentials or customer data are permitted. No deployment or policy activation is permitted.
