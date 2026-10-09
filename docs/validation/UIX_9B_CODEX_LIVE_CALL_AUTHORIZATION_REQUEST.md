# UIX-9B Codex Live-Call Authorization Request

Request state: `UIX_9B_HOST_REMEDIATION_COMPLETE_WAITING_UIX_9C_AUTHORIZATION`

This is a preparation and authorization request record, not execution
authorization. The prior `gpt-5.3-codex` freeze is preserved as historical
`UNVERIFIED_CLIENT_FAILURE` evidence. Before any experimental result existed,
the model was re-frozen by explicit human selection to `gpt-5.6-luna` with
`xhigh` reasoning. Host validation accepted that configuration and one isolated
non-experimental availability probe returned the exact expected response. No
live UIX experimental task call, model substitution, or UIX-9C execution
occurred.

```text
CANONICAL_SHA=bf6f14316fa8814eeac91440c4a7d70be0d04b9e
FIXTURE_DIGEST=280f1361eda45c2b632c37dd049ec47dec81ab1e8e9e81c61a7aa0d9fb96b978
TASK_DIGEST=3708f0d7d172a424ed426a6275d5012df6a11b0718ed37cba95ba0724c0c506d
VALIDATOR_DIGEST=285494688ef105c813ef5f449f1e13b75529c8cddbf8a42ea76d283a9d5eecf3
UIX_GUIDANCE_DIGEST=f989ac579875fbcd349f812fa6e241ba5c8505f9f940abcb5e0e30006f1606ab
PROVIDER=openai-codex
MODEL=gpt-5.6-luna
MODEL_AVAILABILITY=AVAILABLE
MODEL_SUBSTITUTION_PERFORMED=false
MODEL_REVISION=NOT_EXPOSED_BY_PROVIDER
REASONING_EFFORT=xhigh
CODEX_CLI_VERSION=codex-cli 0.148.0
HOST_OS=Windows-11-10.0.26200-SP0
ARM_COUNT=2
REPETITIONS_PER_ARM=3
EXECUTION_ORDER=A1_B1__B2_A2__A3_B3
EXPERIMENTAL_SESSIONS_PER_RUN=1
MAX_VALID_EXPERIMENTAL_SESSIONS=6
MAX_MODEL_CALLS_PER_RUN=1
MAX_TOTAL_MODEL_CALLS=6
MAX_PROVIDER_CALLS=6
TOKEN_CEILING_MODE=OBSERVATIONAL_RESOURCE_CEILING
TOTAL_CAMPAIGN_TIMEOUT_SECONDS=7200
INTERNAL_MODEL_CALL_COUNT_CAPABILITY=UNAVAILABLE
INTERNAL_PROVIDER_CALL_COUNT_CAPABILITY=UNAVAILABLE
PER_RUN_TIMEOUT_SECONDS=900
MAX_RETRIES_FOR_INVALID_INFRASTRUCTURE_RUN=1
MAX_EXTERNAL_REPO_MUTATIONS=0
MAX_INPUT_TOKENS_PER_RUN=50000
MAX_OUTPUT_TOKENS_PER_RUN=12000
MAX_TOTAL_TOKENS=372000
PYTEST_PLUGIN_AUTOLOAD_POLICY=PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
PROBE_PROMPT_IDENTITY=Return exactly: UIX9_MODEL_AVAILABILITY_PROBE_OK
PREVIOUS_FROZEN_MODEL=gpt-5.3-codex
PREVIOUS_MODEL_STATUS=UNVERIFIED_CLIENT_FAILURE
ACTIVE_FROZEN_MODEL=gpt-5.6-luna
MODEL_REFREEZE_REASON=HUMAN_SELECTED_PRE_EXPERIMENT_MODEL
EXPERIMENTAL_RESULTS_EXISTED_AT_REFREEZE=false
HOST_REMEDIATION_STATUS=PASS
PRECAMPAIGN_PROVIDER_PROBES_EXECUTED=2
PRECAMPAIGN_PROVIDER_CALLS_EXECUTED=1
PRECAMPAIGN_MODEL_CALLS_EXECUTED=1
PROBE_STATUS=PASS
PROVIDER_RESPONSE_SUCCESS=true
PROVIDER_FAILURE_CLASSIFICATION=NONE
EXPERIMENTAL_CONTEXT_EXPOSED_TO_PROBE=false
UIX_GUIDANCE_EXPOSED_TO_PROBE=false
UIX_FIXTURE_EXPOSED_TO_PROBE=false
LIVE_EXPERIMENTAL_RUNS_EXECUTED=0
LIVE_UIX9_TASK_CALLS_EXECUTED=0
PROVIDER_CALLS_EXECUTED=0
REPOSITORY_MUTATIONS=0
FROZEN_DIGESTS_UNCHANGED=true
PROBE_EVIDENCE_PATH=docs/validation/UIX_9B_HOST_REMEDIATION_2026-08-26.md
PREVIOUS_PROBE_EVIDENCE_PATH=docs/validation/UIX_9B_MODEL_AVAILABILITY_PROBE_2026-08-26.md
```

The active model and reasoning configuration is frozen as
`MODEL=gpt-5.6-luna` and `REASONING_EFFORT=xhigh`. The host accepted the
configuration, and the single remediation probe returned exactly
`UIX9_MODEL_AVAILABILITY_PROBE_OK`. The previous failed probe remains preserved
at `UIX_9B_MODEL_AVAILABILITY_PROBE_2026-08-26.md`; it was not retried and its
model was not substituted during that historical record.

## Frozen policy

```text
VALID_UNFAVORABLE_OUTPUT=KEEP_RESULT_NO_RETRY_FOR_OUTCOME
PROVIDER_OUTAGE=CLASSIFY_EXPLICITLY_REPLACEMENT_ONLY_UNDER_FROZEN_OUTAGE_POLICY
HOST_CRASH=CLASSIFY_INVALID_INFRASTRUCTURE_RUN_REPLACEMENT_ALLOWED
RESOURCE_CEILING_EXCEEDED=STOP_RUN_PRESERVE_EVIDENCE_DO_NOT_EXTEND_LIMIT
PROTOCOL_BREACH=FAIL_CLOSED_APPLY_FROZEN_INVALIDATION_POLICY
```

Primary endpoint:

```text
OBJECTIVE_UI_FIDELITY_METRICS
```

Secondary endpoints:

```text
IMPLEMENTATION_DIFF_SIZE
NEW_COMPONENT_COUNT
NEW_ARBITRARY_TOKEN_VALUE_COUNT
VALIDATION_REMEDIATION_COUNT
WALL_CLOCK_EXECUTION_TIME
INPUT_TOKENS
OUTPUT_TOKENS
TOTAL_TOKENS
```

Allowed result classifications are `BENEFIT_ESTABLISHED`,
`NO_BENEFIT_ESTABLISHED`, `MIXED_OR_INCONCLUSIVE`, and `PROTOCOL_INVALID`.
Benefit requires all preregistered hard-guardrail, acceptance, paired-repetition,
multi-metric, and validity conditions. No single metric decides the result.

## External mutation boundary

No mutation is permitted to external repositories, Orderly, Padayon, Registry,
production infrastructure or services, installed integrations, release tags,
GitHub Releases, canonical `main`, deployments, secrets, or customer data.

Evidence retention paths are:

```text
docs/validation/UIX_9B_CODEX_LIVE_CALL_AUTHORIZATION_REQUEST.md
docs/validation/uix9b-live-evidence/
tests/fixtures/ui/uix9-live-project/
```

Stop if a hard guardrail regresses, fixture or validator nondeterminism appears,
the protocol is breached, a ceiling is exceeded, an unauthorized mutation is
observed, an endpoint changes, or provider/model identity remains unresolved at
the authorization gate.

```text
LIVE_MODEL_CALLS_AUTHORIZED=false
PROVIDER_CALLS_AUTHORIZED=false
UIX_9C_EXECUTION_AUTHORIZED=false
```

The exact machine-readable record is
`machine/ui/uix9-live-call-authorization-request.v1.json`.

```text
UIX_9B_HOST_REMEDIATION_COMPLETE_WAITING_UIX_9C_AUTHORIZATION
LIVE_MODEL_CALLS_AUTHORIZED=false
PROVIDER_CALLS_AUTHORIZED=false
UIX_9C_EXECUTION_AUTHORIZED=false
NEXT_REQUIRED_GATE=HUMAN_UIX_9C_LIVE_CALL_AUTHORIZATION
```
