# UIX-9C V2 authorization record reconciliation

Status: `DOCUMENTATION_RECONCILIATION_ONLY`. This addendum does not grant, revoke, extend, or activate model/provider-call authority.

Review date: 2026-11-14 (Asia/Manila)
Source checkpoint: Kaos PR #1008 `b39fa1f4d1e275ad5e18506a363a045f48ab2d0d` against main `67439db443a12bf61f44b351435b0c105780d3bd`.

## Recorded sequence

1. `docs/project/UIX_9B_LIVE_PROOF_EXECUTION_PROTOCOL_V2.md` records the frozen experiment at its preparation stage, when the authority flags were `false` and the approved live-call envelope had not yet been recorded.
2. The repository subsequently recorded a separate scoped approval on 2026-08-27. Relevant commits include `2e5d554` (V2 envelope) and `fc4466b` (human approval record).
3. `docs/validation/UIX_9B_V2_LIVE_CALL_AUTHORIZATION_REQUEST.md` and `machine/ui/uix9b-live-call-authorization-request.v2.json` now record `authorization_status=APPROVED`, the three live-call authorization flags as `true`, and `current_request_max_new_live_calls=6`. This is a historical record of campaign-scoped approval, not general authority for all UIX9 activity.
4. The UIX9 V1 request and V2 re-preparation validation contain earlier false-authorization records for different preparation stages and are not silently rewritten here.

## Current interpretation and execution boundary

The frozen preparation protocol's statement that authority was `false` describes the earlier preparation stage. It must not be used to contradict the later, separately recorded V2 authorization. Conversely, the later approval must not be treated as authorizing unrelated sessions, releases, merges, experiments, or modified provider/model identities.

The approved experimental identity specifies provider `openai-codex`, model `gpt-5.6-luna`, and historical CLI identity `codex-cli 0.148.0`. At this reconciliation checkpoint, the installed Codex CLI reported `0.163.0`. No current host or model compatibility is certified by this addendum. The approved campaign is still subject to frozen identities, resource ceilings, and the runner's separate `--execution-mode live --live-call-gate` switches. A mismatched provider or model must not be substituted.

The current PR #1008 assurance work has **no authorization to perform live UIX9 calls**. Its code/CI verification and PRAI reviews are separate from experimental execution. No live UIX9 model or provider calls were made during this documentation reconciliation.

## Scope and release controls

- This is an explanation of existing records, not an amendment to `machine/ui/uix9b-live-call-authorization-request.v2.json`.
- Frozen scientific parameters, V1/V2 treatment identities, original protocol text, and historical evidence remain unchanged.
- PR #1008 remains subject to independent PRAI and Arbiter decisions before protected integration.
- PR #1005 rebrand integration and v1.12.0 release qualification retain their separate governance gates.
- This addendum does not authorize policy activation, protected merge, deployment, publication, production access, or external repository mutation.
