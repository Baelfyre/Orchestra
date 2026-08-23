# B2.4 Instrumentation Pilot Evidence Reconciliation

## Status

```text
State: B2_4_STOPPED_INVALID_DRIVER_COMMAND_CONTRACT
Attempted slots: 1 / 8
Accepted runs: 0 / 8
Actual live model calls: 0 / 24
Automatic retry: OFF
Benefit claim: NOT ALLOWED
B2.5 eligibility: BLOCKED
```

The authorized B2.4 driver stopped before slot 2. No retry or replacement run was attempted.

## Frozen identity

The attempt was bound to canonical preparation SHA `30772ff6aa581dfa43337ed029d233e5a43aa64c`, tree `f1ff75ceeed63053bb91f31b7c9aa8d0281a9615`, freeze digest `70df095f14428a8ac3a4fc0117e96d727690f4c76e80d9c7efdc8791f9a912d9`, manifest digest `d7ca2eed1a087c5509ed529b151e5f06342cdc5ad796282419e87392aba3b04a`, and plan digest `716d6f4a5c8c21647dbb8725307741e2e8bb1069a3d4891fff38672c572297d9`.

## Failure and call reconciliation

The first executor launch used obsolete argument names:

```text
observed: --codex-prefix-json, --workspace
required: --codex-command-prefix-json, --workspace-dir
```

The executor's argument parser exited with status 2 before reading the request or reaching `run_codex_call`. The session summary conservatively booked three calls for the attempted slot, but the retained subprocess evidence and executable control flow independently establish that `codex exec` was not invoked. Reconciled actual live model calls are therefore `0`.

The later generic result validator reported the secondary message `A5 experiment requires a5_shadow_observation`. That message is retained verbatim but is not the root failure.

## Evidence archive

The eight-file raw session is retained outside the repository:

```text
ORCHESTRA_B2_4_INSTRUMENTATION_PILOT_20260823T193531Z.zip
SHA-256: f03db6a617ff469fc1ef5f549800e386fc4deed308c2a00e7f3c0c7f2d009aa2
```

It contains the authorization, frozen plan, first request, raw executor result, partial stderr, empty run index, experiment record, and terminal session summary. No accepted run record exists.

## Forward remediation

The driver now uses the executor's exact parser flags, and a zero-live-call regression test binds those names. The corrected driver SHA-256 is `0c08ed5920687e3d32aa7c614e521887ac305ab348b09a6538b3ff4dfb196424`; the corrected, non-authorizing freeze digest is `398560ce170191743360438dd5100578ea1e1a0c421b549663d826e3d7c4fa4c`.

This correction does not validate the pilot and does not authorize a retry. B2.5 cannot begin because B2.4 instrumentation evidence is incomplete.

## Next gate

A separate later human authorization must explicitly authorize a B2.4 retry and bind the corrected freeze digest. Until then:

```text
B2.4 = STOPPED_REPREPARED_NOT_AUTHORIZED
B2.5 = NOT ELIGIBLE
A5 execution promotion = NOT AUTHORIZED
B4 = BLOCKED
```
