# UIX-9C V2 Windows UTF-8 Recovery

Status: `RECOVERY_PREPARED_WAITING_REVISED_HUMAN_LIVE_CEILING`

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

## Host remediation

The frozen V2 runner remains unchanged. Windows execution is routed through:

```text
python internal/uix9c_windows_utf8_launcher.py execute --execution-mode live --live-call-gate
```

The launcher re-executes the frozen runner using:

```text
python -X utf8
```

This changes only Python host text decoding. It does not change:

- provider or model identity;
- reasoning effort;
- task, fixture, validator, evaluator, or guidance digests;
- treatment/control prompts;
- execution order;
- result logic;
- external mutation boundary.

## Restart discipline

The invalid A1 attempt is preserved separately before a new clean evidence campaign begins. The restarted campaign still requires exactly six valid observations in the frozen order:

```text
A1,B1,B2,A2,A3,B3
```

The failed infrastructure interaction is never replaced by a seventh valid observation.

## Revised ceiling requiring explicit human authorization

Because one experimental provider/model interaction was consumed without yielding a valid observation, completing six valid observations requires an overall ceiling of seven experimental interactions for this scientific effort:

```text
PRIOR_INVALID_INFRASTRUCTURE_INTERACTIONS=1
FRESH_CAMPAIGN_MAX_NEW_MODEL_CALLS=6
FRESH_CAMPAIGN_MAX_NEW_PROVIDER_CALLS=6
MAX_VALID_OBSERVATIONS=6
OVERALL_EXPERIMENTAL_INTERACTION_CEILING=7
MAX_INVALID_INFRASTRUCTURE_REPLACEMENTS=1
```

The fresh campaign remains capped at six new calls. The seventh total interaction exists only because the preserved failed infrastructure attempt already consumed one interaction.

This ceiling expansion is not inferred from Full Autonomous mode. Live restart remains blocked until explicit human scientific authorization is recorded.

## Protected boundaries

```text
RECOVERY_PREPARATION != LIVE_CALL_AUTHORITY
INVALID_INFRASTRUCTURE != SCIENTIFIC_RESULT
SEVEN_TOTAL_INTERACTIONS != SEVEN_VALID_OBSERVATIONS
VALIDATION_PASS != LIVE_CALL_AUTHORITY
```
