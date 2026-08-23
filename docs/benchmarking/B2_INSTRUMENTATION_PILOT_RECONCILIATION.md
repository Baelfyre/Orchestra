# B2.4 Instrumentation Pilot Evidence Reconciliation

## Status

```text
State: B2_4_COMPLETE_VALID_REPLACEMENT_RECONCILIATION
Prior stopped attempt: 1 invalid slot, 0 model calls
Replacement session: 8 accepted runs / 8 planned
Replacement model calls: 24 / 24
Automatic retry inside replacement: OFF
Benefit claim: NOT ALLOWED
A5 promotion: NOT AUTHORIZED
B2.5 next gate: HELD-OUT TASK-SET FREEZE AND ZERO-CALL PREFLIGHT
```

The separately authorized replacement session executed the complete frozen B2.4 plan after the executor command-contract defect was corrected. The prior stopped attempt remains retained as invalid evidence and is not pooled as an accepted run.

## Frozen identity

The replacement session was bound to canonical preparation SHA `5acfdeebd2871cdad8183342520bff64d77b33fa`, tree `6ed83b48ac76f600057738c50b7f8c1b5f8f2d62`, freeze digest `398560ce170191743360438dd5100578ea1e1a0c421b549663d826e3d7c4fa4c`, manifest digest `d7ca2eed1a087c5509ed529b151e5f06342cdc5ad796282419e87392aba3b04a`, and plan digest `716d6f4a5c8c21647dbb8725307741e2e8bb1069a3d4891fff38672c572297d9`.

Host binding remained `openai-codex`, Codex CLI `0.148.0`, `gpt-5.6-sol`, medium reasoning, DEFAULT communication, and the isolated read-only Git workspace.

## Execution and integrity

```text
planned runs:                 8
accepted runs:                8
invalid runs:                 0
failed runs:                  0
Codex model calls:            24 / 24
accepted cumulative tokens:  251,862 / 1,200,000
automatic retry:              OFF
stop reason:                  none
```

Independent reconciliation passed:

- 8/8 request, executor-result, and run-record bijections;
- 8/8 run-index digest recomputations and experiment-order matches;
- 8/8 exact JSON validator passes;
- 8/8 evidence recomputations, including UTF-8 advisory bytes and context-transfer ledgers;
- 8/8 topology stage orders matching the frozen arm;
- all safety and authority-expansion flags false;
- exactly three retained calls per run: two specialists and one fixed finalizer;
- cached-input counters greater than input counters rejected by the evidence contract;
- bounded 16,384-byte advisory retention ceiling enforced.

The raw evidence archive is retained outside the repository:

```text
ORCHESTRA_B2_4_REPLACEMENT_PILOT_20260823T224707Z.zip
SHA-256: 99ef150786874f513579ebdf9af6a937c59ef5839e910bc4c8f04e49b83bc65d
files: 29
uncompressed bytes: 193,101
```

## Descriptive pilot results

| Arm | Runs | Exact passes | Observed tokens | Context-transfer bytes |
|---|---:|---:|---:|---:|
| Clockwork -> Overseer | 4 | 4/4 | 123,524 | 4,800 |
| Overseer -> Clockwork | 4 | 4/4 | 128,338 | 6,324 |

These are instrumentation-pilot observations only. They do not establish topology benefit, token efficiency, A5 promotion, production attachment, or parallel capability.

## Counter stability

The pilot exercised and retained all canonical classifications: `STABLE_EXACT`, `CACHE_STATE_VARIANT`, `INPUT_COUNTER_VARIANT`, and `UNSTABLE_ATTRIBUTION`. The observed counter instability remains descriptive. No token-efficiency benefit claim is permitted without the later attribution gate.

## Prior stopped attempt

The first session stopped before model invocation because the driver used obsolete executor flags. Its raw archive remains anchored by SHA-256 `f03db6a617ff469fc1ef5f549800e386fc4deed308c2a00e7f3c0c7f2d009aa2`. It produced zero accepted runs and zero actual model calls. The corrected driver uses `--codex-command-prefix-json` and `--workspace-dir`, with regression coverage bound to that parser contract.

## Next gate and authority boundary

B2.4 evidence is now valid for instrumentation and B2.5 design entry. The next authorized unit is the held-out B2.5 task-set freeze and zero-call preflight. B2.5 execution must remain bound to its own frozen task set, plan, host identity, and resource ceiling.

This reconciliation grants no A5 execution-effective promotion, production runtime attachment, A6-A8 authority, B4 authority, release publication, deployment, policy activation, installed-integration refresh, destructive cleanup, branch deletion, force push, or history rewrite.
