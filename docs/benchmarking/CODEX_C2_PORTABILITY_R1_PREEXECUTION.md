# Codex C2 Portability R1 Pre-Execution Reconciliation

## Status

`PORTABILITY_R1_RECONCILED_PREEXECUTION_LIVE_EXECUTION_LOCKED`

C2 has performed **zero live model calls**.

The original external C2 execution package could not be recovered on the current host. Git-object recovery preserved the historical machine freeze, but no executable launcher or exact prompt package survived. Deterministic reconstruction reproduced **0 of 5** original frozen prompt digests, so the reconstructed prompts are not represented as the original byte identity.

C2 portability R1 is therefore a transparent **pre-execution amendment**, not a result rewrite and not an execution of a different task set.

## Preserved experimental design

The following frozen variables remain unchanged:

- program: `orchestra.shared-comparative-benchmark.v1`
- experiment: `b3-codex-machine-json-prompt-extension-v1`
- benchmark subject: `d95f677dbf23ab79c4698c26645ea30cea9b3019`
- benchmark subject tree: `ceab55bd512ea6fde4e8e76877cbb7006d18500e`
- executable adapter: `0af078f6ad34d5cf406823bbd0e8258496923b60`
- adapter tree: `90255564c13fcbb132a7e4cf8b98eb106d039e39`
- task-set digest: `fd5109b2ec94709883bd75a9b7c6c89b6cd4f9bcc9840554bbd7cbb277a931a8`
- validator: `EXACT_JSON_CONFORMANCE_V1`
- Codex CLI: `0.148.0`
- model: `gpt-5.6-sol`
- reasoning: `medium`
- counter: `codex-cli-0.148.0:jsonl-usage:gpt-5.6-sol:medium`
- five tasks, three communication arms, two repetitions
- exact C1 execution-slot assignment
- no new arm randomization
- per-call ceiling: `45,000` total tokens
- cumulative accepted ceiling: `1,200,000` total tokens
- automatic retry: OFF
- stop on invalid run, identity drift, tool event, or token-ceiling breach

## Original C2 package

The original external artifact identities remain historical provenance only:

- logical freeze envelope: `0285f97f0f509ddd41bebfe7254aec82d9292f6ae0097cf05776923c8f5bcc7b`
- launcher: `b20010df254a329696441565c2827df5d4c880b198f192da3d2c51662573c142`
- execution bundle: `d2d4fcbc67cea1b8f7b898105e39cf0cc6cd47823dfd104d6b6162eba66a874d`

They are no longer current live-execution authority because the original external package is unavailable and its prompt bytes were not recovered.

## Portability R1 prompt identities

The original prompt identity was not recovered:

```text
ORIGINAL_PROMPT_DIGEST_MATCH_COUNT=0
ORIGINAL_PROMPT_IDENTITY_RECOVERED_EXACTLY=false
```

Portable R1 task-prompt digests:

- `b3-cal-padayon-r5-capability-manifest`: `6ff223d1a9be6dead014f09d29b53e0fdde8962e882510c1da9763b46369a35f`
- `b3-cal-padayon-o1-o2-compatibility`: `8773c63736c9147a5a2b094ee0147fbaf8e2df18e5e59feea86ab08257b66f2c`
- `b3-cal-padayon-o3-o4-freshness`: `99d7105bf9cc5a75585fe459d576dc95c608aaa3728c64a56c94789767ddfa6e`
- `b3-cal-padayon-assurance-drift`: `4ba0fd7a26c9fdf82bc23e8ccc1a662fd595e5aca78135a1f631ebd88d5fae4e`
- `b3-cal-padayon-o5-o6-routing`: `8bbe7165b43f8276bfb6e1f09c460d2ca6ab9c25b6eb9bd39368bf5e23bd2d52`

The representation still uses `orchestra.prompt-representation.machine-json.v1` and canonical serialization `sort_keys=true,separators=(comma,colon),ensure_ascii=true`. The C1 natural-language prompt is not embedded.

## Portability R1 artifact identities

- prompt set: `9cb5e34fc4a66911ca702acd52eee12187946a471c81fbba471412c79b805165`
- execution plan: `e780e8c7c4793cd2eff465e0629cb0887c31faad14265232d6524e55560a94f2`
- portability revision: `d8a30e401c71d3625a51b7d265548dff2f31866195d50065b3fcfa2d7ae21b11`
- hash manifest: `dee5a1281c55d32918987279ec32e2d1e6ca34f2f9e2d2733ea7948473091283`
- validated launcher: `014f38025e3b8491b7cf84e46cb19b1ca8484f0ea3a57abfbb65be6ca1c567d3`
- launcher preflight: `c04cf9610605acb1836c9806bfef60c45786c150769805c88bffd0effedb82f6`

Launcher preflight status:

```text
PASS_ZERO_LIVE_CALLS
REQUEST_COUNT=30
LIVE_MODEL_CALLS=0
AUTH_SERVER_VALIDATED=false
LIVE_EXECUTION_AUTHORIZED=false
```

## Windows executable-binding finding

PowerShell's bare `codex` resolved to the npm-installed `0.148.0` shim, but Python `subprocess(..., shell=False)` resolved bare `codex` to the desktop `0.149.0` executable.

Portability R1 therefore binds the canonical executor to the exact npm CLI through the exact Node + `codex.js` entrypoint:

- `node.exe` SHA-256: `e921fe5307e29bf6fd00000dd594356affd3a7b044e52720c7f10decbdc305b9`
- `codex.js` SHA-256: `134063e133f0b4244fa3b251acf973d4fe4b4aeeacbdc135211bf480f59f1477`
- Codex `package.json` SHA-256: `071f84ec4e6ff199b3dce2c2560a77c2248443b0d8b17e64f6e3f08427d32fc2`

This is a host-portability binding only. It does not change the frozen provider, model, reasoning effort, counter identity, benchmark task semantics, communication treatments, or resource boundary.

## Authority boundary

This reconciliation **does not authorize a live C2R1 call**.

A separate explicit local live-authorization record must bind the exact reconciled repository state and the validated portability artifacts before slot 1 can run.

Still unauthorized:

- C1 mutation
- C3 execution
- A5 execution promotion
- A6
- B4
- release/publication
- deployment
- policy activation

Machine-readable authority: `machine/benchmarking/codex-c2-portability-r1-preexecution.v1.json`.
