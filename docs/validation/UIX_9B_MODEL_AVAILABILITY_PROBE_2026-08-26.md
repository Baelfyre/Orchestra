# UIX-9B Model Availability Probe Evidence

Terminal: `UIX_9B_MODEL_AVAILABILITY_PROBE_COMPLETE`

This record captures the one authorized non-experimental probe attempt. It did
not expose the UIX task, fixture, UIX-1 through UIX-8 guidance, prior results,
or repository context to the probe.

```text
PROVIDER=openai-codex
MODEL=gpt-5.3-codex
MODEL_REVISION=NOT_EXPOSED_BY_PROVIDER
REASONING_EFFORT=high
PROBE_PROMPT_IDENTITY=Return exactly: UIX9_MODEL_AVAILABILITY_PROBE_OK
PRECAMPAIGN_PROVIDER_PROBES_EXECUTED=1
```

## Result

The Codex session API rejected the requested model and reasoning combination
during local host validation before creating a session or contacting the
provider. The rejection was not an explicit provider response stating that the
model is unavailable.

```text
PROBE_STATUS=INVALID_INFRASTRUCTURE_PROBE
MODEL_AVAILABILITY=UNVERIFIED
PROVIDER_RESPONSE_SUCCESS=false
PROVIDER_FAILURE_CLASSIFICATION=CLIENT_FAILURE
```

The direct CLI help probe and the failed session-API validation do not establish
provider availability. No retry is permitted under the frozen probe policy.

## Isolation and side effects

```text
EXPERIMENTAL_CONTEXT_EXPOSED_TO_PROBE=false
UIX_GUIDANCE_EXPOSED_TO_PROBE=false
UIX_FIXTURE_EXPOSED_TO_PROBE=false
LIVE_EXPERIMENTAL_RUNS_EXECUTED=0
LIVE_UIX9_TASK_CALLS_EXECUTED=0
PROVIDER_CALLS_EXECUTED=0
REPOSITORY_MUTATIONS=0
EXTERNAL_REPO_MUTATIONS=0
FROZEN_DIGESTS_UNCHANGED=true
UIX_9C_EXECUTION_AUTHORIZED=false
NEXT_REQUIRED_GATE=UIX_9B_HOST_REMEDIATION
```

The frozen fixture, task, validator, and UIX guidance digests remain unchanged.
No model substitution, authentication change, software installation, CLI
upgrade, repository mutation, or external mutation was performed.
