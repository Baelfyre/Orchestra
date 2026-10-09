# UIX-9C V2 Windows UTF-8 Recovery

Status: `RECOVERY_AUTHORIZED_WAITING_FRESH_LOCAL_EXECUTION`

## Observed invalid infrastructure attempt

The first live UIX-9C A1 attempt on 2026-08-27 reached the authenticated Codex subprocess but failed in the Windows host output-capture layer before a valid scientific observation could be produced.

Observed accounting from the preserved local campaign state:

```text
RUN=A1
ATTEMPTS=1
VALID_SESSION=false
STATUS=PROTOCOL_BREACH
MODEL_CALLS=1
PROVIDER_CALLS=1
PROVIDER_INTERACTIONS=1
INVALID_RETRIES=0
FINAL_OBSERVATIONS=0
FINAL_METRIC_RESULTS=0
```

The terminal traceback showed Python 3.12 decoding the Codex JSONL pipe using Windows `cp1252` and raising `UnicodeDecodeError` on byte `0x9d`. The stored runner failure (`Codex JSONL is missing thread.started`) is a downstream symptom of that failed host-side decode, not a model-quality result.

This attempt is classified for recovery purposes as:

```text
INVALID_INFRASTRUCTURE=WINDOWS_HOST_OUTPUT_DECODING_FAILURE
SCIENTIFIC_OBSERVATION=false
CALIBRATION_INPUT=false
BENEFIT_CLAIM=NONE
HARM_CLAIM=NONE
DIRECTIONAL_MODEL_BEHAVIOR_CLAIM=NONE
```

The failed attempt must remain preserved and auditable. It must not be deleted, rewritten into a valid observation, or counted as an A-arm result.

## Human scientific authorization

On 2026-08-27, the maintainer explicitly approved:

> 7 total experimental interactions, consisting of the 1 already-preserved invalid-infrastructure attempt plus at most 6 fresh calls producing at most 6 valid observations.

The machine-readable authorization is frozen at:

```text
docs/validation/uix9b-live-evidence-v2/recovery-authorization.v1.json
```

This approval authorizes only the bounded restart described below. It does not grant merge, release, deployment, policy activation, external repository mutation, branch deletion, destructive cleanup, force push, or history rewrite authority.

## Host remediation

The frozen V2 scientific runner remains unchanged. Windows execution is routed through:

```text
python internal/uix9c_windows_utf8_launcher.py execute --execution-mode live --live-call-gate
```

The launcher re-executes the frozen runner using:

```text
python -X utf8
```

This changes only Python host text decoding and recovery gating. It does not change:

- provider or model identity;
- reasoning effort;
- task, fixture, validator, evaluator, or guidance digests;
- treatment/control prompts;
- execution order;
- result logic;
- external mutation boundary.

## Restart discipline

The invalid A1 attempt remains in the parent evidence surface. A new clean campaign must write only to:

```text
docs/validation/uix9b-live-evidence-v2/restart-20260827
```

The launcher owns this evidence-root selection for live recovery execution and rejects a caller-supplied override.

The restarted campaign retains the frozen order:

```text
A1,B1,B2,A2,A3,B3
```

The failed infrastructure interaction is never rewritten into an A-arm observation and never replaced by a seventh valid observation.

## Approved revised ceiling

The approved scientific-effort accounting is:

```text
PRIOR_INVALID_INFRASTRUCTURE_INTERACTIONS=1
FRESH_CAMPAIGN_MAX_NEW_MODEL_CALLS=6
FRESH_CAMPAIGN_MAX_NEW_PROVIDER_CALLS=6
FRESH_CAMPAIGN_MAX_NEW_PROVIDER_INTERACTIONS=6
MAX_VALID_OBSERVATIONS=6
OVERALL_EXPERIMENTAL_INTERACTION_CEILING=7
SEVENTH_VALID_OBSERVATION_AUTHORIZED=false
ADDITIONAL_CEILING_EXPANSION_AUTHORIZED=false
```

The fresh campaign remains capped at six new calls. The seventh total interaction exists only because the preserved failed infrastructure attempt already consumed one interaction.

If another infrastructure failure occurs, any frozen runner retry may consume part of the remaining six-call fresh budget, but it may not extend the overall ceiling above seven. If six valid observations can no longer be completed within the approved ceiling, the campaign must stop or remain invalid rather than infer additional authority.

## Protected boundaries

```text
RECOVERY_AUTHORIZATION = LIVE_RESTART_AUTHORITY_ONLY
INVALID_INFRASTRUCTURE != SCIENTIFIC_RESULT
SEVEN_TOTAL_INTERACTIONS != SEVEN_VALID_OBSERVATIONS
VALIDATION_PASS != MERGE_AUTHORITY
VALIDATION_PASS != RELEASE_AUTHORITY
```
