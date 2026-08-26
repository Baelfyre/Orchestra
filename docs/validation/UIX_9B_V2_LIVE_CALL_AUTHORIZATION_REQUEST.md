# UIX-9B V2 Live Call Authorization Request

Status: `PENDING_HUMAN_AUTHORIZATION`

This is a request record only. It does not authorize UIX-9C execution.

## Frozen execution identity

```text
CANONICAL_SHA=bf6f14316fa8814eeac91440c4a7d70be0d04b9e
FIXTURE_DIGEST=280f1361eda45c2b632c37dd049ec47dec81ab1e8e9e81c61a7aa0d9fb96b978
TASK_DIGEST=3708f0d7d172a424ed426a6275d5012df6a11b0718ed37cba95ba0724c0c506d
VALIDATOR_DIGEST=285494688ef105c813ef5f449f1e13b75529c8cddbf8a42ea76d283a9d5eecf3
UIX_GUIDANCE_DIGEST=f989ac579875fbcd349f812fa6e241ba5c8505f9f940abcb5e0e30006f1606ab
EVALUATOR_VERSION=uix9b-live-metric-evaluator-v2.0.0
EVALUATOR_DIGEST=d585010eb83ec23b1df2c3512868e9ff5285e7dced1393dcafb0233b835f7ae1
PROVIDER=openai-codex
MODEL=gpt-5.6-luna
MODEL_REVISION=UNRESOLVED_PENDING_LIVE_AUTHORIZATION
CODEX_CLI_VERSION=codex-cli 0.148.0
HOST_OS=Windows-11-10.0.26200-SP0
ARM_COUNT=2
REPETITIONS_PER_ARM=3
EXECUTION_ORDER=A1_B1__B2_A2__A3_B3
```

## Proposed ceilings and accounting

```text
MAX_MODEL_CALLS_PER_RUN=1
MAX_TOTAL_MODEL_CALLS=6
MAX_EXPERIMENTAL_PROVIDER_CALLS=6
MAX_NONEXPERIMENTAL_AVAILABILITY_PROBES=1
MAX_TOTAL_PROVIDER_INTERACTIONS=7
TOKEN_OR_COMPUTE_CEILING=MAX_TOTAL_TOKENS_120000_MAX_PER_RUN_20000
PER_RUN_TIMEOUT_SECONDS=900
TOTAL_CAMPAIGN_TIMEOUT_SECONDS=7200
MAX_RETRIES_FOR_INVALID_INFRASTRUCTURE_RUN=1
MAX_EXTERNAL_REPO_MUTATIONS=0
```

Historical counters are `6` experimental model calls, `6` experimental provider calls, `1` nonexperimental availability probe, `7` total provider interactions, and `0` invalid-infrastructure retries. New-campaign authorization counters are all zero.

## Endpoints and policies

```text
PRIMARY_ENDPOINTS=OBJECTIVE_UI_FIDELITY_METRICS
SECONDARY_ENDPOINTS=IMPLEMENTATION_DIFF_SIZE,NEW_COMPONENT_COUNT,NEW_ARBITRARY_TOKEN_VALUE_COUNT,VALIDATION_REMEDIATION_COUNT,WALL_CLOCK_EXECUTION_TIME,INPUT_TOKENS,OUTPUT_TOKENS,TOTAL_TOKENS
RETRY_POLICY=VALID_UNFAVORABLE_OUTPUT_KEEP_RESULT_NO_RETRY_FOR_OUTCOME;PROVIDER_OUTAGE_CLASSIFY_EXPLICITLY_REPLACEMENT_ONLY_UNDER_FROZEN_OUTAGE_POLICY;HOST_CRASH_CLASSIFY_INVALID_INFRASTRUCTURE_RUN_REPLACEMENT_ALLOWED;RESOURCE_CEILING_EXCEEDED_STOP_RUN_PRESERVE_EVIDENCE_DO_NOT_EXTEND_LIMIT;PROTOCOL_BREACH_FAIL_CLOSED
INVALID_RUN_POLICY=Only HOST_CRASH and a frozen provider outage replacement may replace an invalid infrastructure run; valid unfavorable output is retained.
OUTAGE_POLICY=One nonexperimental availability probe is separately bounded; an experimental provider outage is classified explicitly and replacement requires no valid candidate output and unspent immutable limits.
```

Allowed result classifications are `BENEFIT_ESTABLISHED`, `NO_BENEFIT_ESTABLISHED`, `MIXED_OR_INCONCLUSIVE`, and `PROTOCOL_INVALID`. Benefit requires all frozen multi-metric and hard-guardrail conditions. No-benefit is not a harm claim. Mixed or inconclusive covers conflict or insufficient evidence. Protocol invalid covers any control or evidence-integrity failure.

Evidence is retained under `docs/validation/uix9b-live-evidence-v2/`, with the frozen fixture under `tests/fixtures/ui/uix9-live-project/`. Screenshots are supplemental only. Model self-rating and subjective visual scores are excluded.

## Required stop conditions

Stop on any frozen identity mismatch, hard-guardrail regression, protocol breach, resource ceiling, external mutation attempt, missing or malformed observation, provider/model substitution, or attempt to infer a model behavior claim before all six valid executions.

## Current authority record

```text
LIVE_MODEL_CALLS_AUTHORIZED=false
PROVIDER_CALLS_AUTHORIZED=false
UIX_9C_EXECUTION_AUTHORIZED=false
MAX_NEW_LIVE_CALLS=0
BENEFIT_CLAIM=NONE
HARM_CLAIM=NONE
DIRECTIONAL_MODEL_BEHAVIOR_CLAIM=NONE
```

Human approval would have to explicitly change this request record and independently authorize the next execution phase. This preparation turn does not do so.
