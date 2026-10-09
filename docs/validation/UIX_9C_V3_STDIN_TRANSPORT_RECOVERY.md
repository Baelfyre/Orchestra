# UIX-9C V3 Stdin Transport Recovery

Status: `IMPLEMENTED_PENDING_ZERO_CALL_VALIDATION_AND_HUMAN_LIVE_AUTHORIZATION`

Recorded: 2026-08-27

## Purpose

Recover the controlled UIX-9C proof campaign from two Windows host-transport failures without changing the frozen scientific task, fixture, A/B treatment, evaluator, validator, model, reasoning effort, execution order, or result logic.

## Preserved prior invalid studies

### Initial V2 attempt

The first authorized A1 interaction consumed one model/provider interaction but produced no scientific observation because Python on Windows decoded Codex UTF-8 JSONL using the local `cp1252` codec. The evidence is preserved and classified as invalid infrastructure.

### UTF-8 recovery study

The first UTF-8 recovery study consumed three new interactions:

- A1: candidate observation and metric were persisted pending Pair 1 adjudication;
- B1 attempt 1: `HOST_CRASH` with `[WinError 206] The filename or extension is too long`;
- B1 attempt 2: the same `HOST_CRASH` after the single bounded invalid-run retry.

The study is terminally `PROTOCOL_INVALID_INCOMPLETE`. Its A1 observation is not salvaged into a new comparison because Pair 1 never completed and selective reuse after a transport failure would weaken the preregistered execution protocol.

Across both invalid studies, four experimental interactions were consumed. They remain historical invalid-infrastructure evidence and are not scientific evidence for benefit, no benefit, or harm.

## Root cause

The frozen V2 runner places the entire prompt in the Windows process argument vector. The baseline A prompt is small enough to launch. The governed B prompt appends the full canonical UIX-1 through UIX-8 treatment and exceeded the Windows process command-line boundary, producing WinError 206 before Codex could execute the task.

This is a host transport defect, not model behavior.

## V3 transport correction

V3 keeps the frozen prompt bytes and prompt digest but changes only their transport:

```text
V2: codex exec ... <FULL_PROMPT_IN_ARGV>
V3: codex exec ... -
    stdin = exact UTF-8 prompt bytes
```

The explicit `-` sentinel forces Codex exec to read the prompt from stdin. The harness uses explicit UTF-8 encoding for stdin, stdout, and stderr.

V3 must prove before live authorization that:

1. the positional prompt is absent from argv;
2. the final Codex positional prompt sentinel is `-`;
3. the exact V2 prompt string is sent as stdin;
4. V2 prompt digests remain unchanged;
5. both baseline and governed arms use the same transport;
6. the V2 evaluator, validator, fixture, guidance, model, reasoning effort, and execution order remain unchanged;
7. tests and transport verification use zero model/provider calls;
8. all prior invalid evidence is preserved and not reused as a valid observation.

## Proposed fresh campaign ceiling

The V3 proposal is a new study, not an extension of the invalid seven-interaction study:

```text
MAX_NEW_MODEL_CALLS=7
MAX_NEW_PROVIDER_CALLS=7
MAX_NEW_PROVIDER_INTERACTIONS=7
MAX_VALID_OBSERVATIONS=6
MAX_INVALID_INFRASTRUCTURE_REPLACEMENTS=1
SEVENTH_VALID_OBSERVATION_AUTHORIZED=false
```

The seventh interaction, if separately authorized, is only a replacement for one objectively classified invalid-infrastructure/provider-outage attempt. It can never create a seventh valid observation and cannot be used for outcome-based retry.

This resource ceiling is only a proposal until explicit human scientific authorization is recorded in `v3-stdin-transport-authorization.v1.json`.

## Authority boundary

```text
TRANSPORT_FIX != LIVE_CALL_AUTHORITY
ZERO_CALL_VALIDATION != LIVE_CALL_AUTHORITY
PRIOR_A1_OBSERVATION != VALID_PAIR_EVIDENCE
PROTOCOL_INVALID != NO_BENEFIT
PROTOCOL_INVALID != HARM
```

No merge, release, deployment, policy activation, external repository mutation, destructive cleanup, branch deletion, force push, or history rewrite is authorized by this recovery record.
