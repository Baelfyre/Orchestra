# Codex C2 Portability R1 Live-Execution Authorization

## Status

`PREPARED_NOT_AUTHORIZED`

This document is a review candidate only. It does not authorize a Codex/model call.

Preparation was explicitly approved with:

> Approved, prepare C2R1 live-execution authorization

That approval authorizes preparation only. It does not authorize commit, publication, canonicalization, activation, slot 1, or slots 2-30.

## Canonical authority

### Orchestra

- main: `e92bb1ec76c17c7bd7b0d9e1b60c374c4d49e48d`
- tree: `a74fba1084768e52181720997556d029eecc9999`
- parent: `d001cec0719a73d5e104e0a7c6d5ede7bb1ad351`
- GitHub signature: `VERIFIED / VALID`
- source PR `#472`: closed / unmerged directly
- signed materialization PR `#473`: merged
- canonical PR `#474`: merged
- signed materialized head: `bc668f4ed6558d6bf5e9e072345194a554eeed05`
- source/materialized/canonical tree equivalence: `EXACT`

Final signed-head validation:

- Governance Check `32555991518` â€” PASS
- validate `32555991517` â€” PASS
- Required Analysis Compatibility `32555991526` â€” PASS
- Cross-platform Validation `32555991524` â€” PASS
- cosmic-ray-confidence `32555991529` â€” PASS

### Padayon

- main: `64b34a6e6af4249bad4e87f8204426d7295def6f`
- tree: `7d3e6e6a9d3a4034537a84879e7397fa740893c1`
- parent: `4062e9147eb576ad08e077aae4d826b0c034ef99`
- canonical PR `#156`
- GitHub signature: `VERIFIED / VALID`

Any canonical SHA/tree drift before slot 1 invalidates the activation basis.

## Exact slot 1

- execution order: `1`
- request ID: `91acbb576029939d6acf5d3e`
- task: `b3-cal-padayon-r5-capability-manifest`
- repetition: `1`
- communication mode: `DEFAULT`
- portable R1 prompt SHA-256: `6ff223d1a9be6dead014f09d29b53e0fdde8962e882510c1da9763b46369a35f`

Slot 1 is one-attempt-only. Automatic retry remains OFF.

## Host binding

- CLI: `0.148.0`
- provider: `openai-codex`
- model: `gpt-5.6-sol`
- reasoning: `medium`
- counter: `codex-cli-0.148.0:jsonl-usage:gpt-5.6-sol:medium`
- binding: `NODE_EXACT_NPM_ENTRYPOINT`
- Node SHA-256: `e921fe5307e29bf6fd00000dd594356affd3a7b044e52720c7f10decbdc305b9`
- codex.js SHA-256: `134063e133f0b4244fa3b251acf973d4fe4b4aeeacbdc135211bf480f59f1477`
- package.json SHA-256: `071f84ec4e6ff199b3dce2c2560a77c2248443b0d8b17e64f6e3f08427d32fc2`

## Resource freeze

- per-call ceiling: `45,000`
- cumulative accepted ceiling: `1,200,000`
- automatic retry: `OFF`
- current accepted C2R1 runs: `0`
- current live C2 calls: `0`

## Activation boundary

This record cannot activate itself.

Before slot 1:
1. review this exact candidate;
2. separately authorize its commit;
3. publish, validate, and canonicalize it;
4. run a fresh zero-live-call preflight;
5. reverify Orchestra/Padayon canonical identities and host hashes;
6. obtain a new explicit human authorization activating slot 1 only.

Slots 2-30 remain unauthorized.

## Preserved non-authority

C1 mutation, C3, A5 execution promotion, A6, B4, release, deployment, and policy activation remain unauthorized.

## Next gate

`HUMAN_REVIEW_PREPARED_RECORD_THEN_SEPARATE_COMMIT_AUTHORIZATION`
