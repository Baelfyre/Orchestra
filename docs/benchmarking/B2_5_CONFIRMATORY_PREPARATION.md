# B2.5 Confirmatory Measurement Preparation

## Frozen boundary

B2.5 is a held-out confirmatory measurement package. It does not establish a benefit claim, provide A5 promotion evidence, or attach any production runtime capability.

The package is frozen against canonical `main` commit `68be3fff54f44dff30e3eaa198c126f3c7dc7188` and tree `c312db258b62da2484c335d25f292596d3d06d8a`. The selected task set is new synthetic work: exactly one task for each B0 stratum, in the frozen order recorded by `machine/benchmarking/b2-5-held-out-task-set.v1.json`. B2 calibration tasks and B2.4 pilot tasks are excluded, and no prior outcome or benefit result participates in selection.

The ten tasks are:

1. `b2-confirm-single-domain-state-transition`
2. `b2-confirm-multi-domain-order-entitlement`
3. `b2-confirm-architecture-plugin-boundary`
4. `b2-confirm-debugging-event-duplication`
5. `b2-confirm-security-capability-scope`
6. `b2-confirm-validation-partial-write`
7. `b2-confirm-doc-implementation-contract`
8. `b2-confirm-dependency-version-skew`
9. `b2-confirm-parallel-artifact-join`
10. `b2-confirm-high-coordination-contract-rollout`

Each task is topology-sensitive, self-contained, synthetic, and validated by `EXACT_JSON_CONFORMANCE_V1`. The required specialist set is Clockwork and Overseer, communication mode is `DEFAULT`, network and repository mutation are prohibited, and every response must carry `authority_expansion=false`.

## Exact plan and resources

The executable manifest and deterministic plan freeze two repetitions per task across both sequential topology arms: `Clockwork -> Overseer` and `Overseer -> Clockwork`. The seeded paired-block scheduler produces 40 slots, one attempt per slot, with three Codex calls per slot and a maximum of 120 underlying model calls.

The resource boundary is 75,000 tokens per run, 3,000,000 accepted tokens cumulatively, a 600-second call timeout, no automatic retry, and stop-on-first-invalid or validator failure. Specialist advisory retention is capped at 16,384 UTF-8 bytes; overflow invalidates the run without truncation.

Machine records:

- `machine/benchmarking/b2-5-held-out-task-set.v1.json`
- `machine/benchmarking/b2-5-confirmatory-preregistration.v1.json`
- `machine/benchmarking/b2-5-confirmatory-manifest.v1.json`
- `machine/benchmarking/b2-5-confirmatory-plan.v1.json`
- `machine/benchmarking/b2-5-confirmatory-freeze.v1.json`

## Preflight and driver

`scripts/b2_5_confirmatory_preflight.py` validates the frozen task, manifest, plan, topology envelope, executable hashes, host binding, workspace boundary, and resource identities. Static validation performs zero model calls. Exact-host validation may invoke only the pinned Codex `--version` command and reports `codex_exec_invoked=false` and `live_model_calls=0`.

`scripts/b2_5_confirmatory_driver.py` requires an exact live authorization bound to the freeze, task-set, manifest, plan, and preparation Git identities. It uses the corrected executor flags `--codex-command-prefix-json` and `--workspace-dir`, preserves the complete B2.3.1 evidence contract and session artifacts, and stops before the next slot after any invalid run, validator failure, identity drift, repository mutation, evidence mismatch, counter-provenance failure, or resource overflow. The driver is not run during preparation.

## Authority state

The preparation freeze records `live_execution_authorized=false`, `benefit_claim_allowed=false`, and `a5_promotion_evidence_allowed=false`. B2.5 live execution is a separately gated action after exact-head validation, signed materialization, canonicalization, and independent canonical verification. A5 effective promotion, production attachment, B4, release, deployment, policy activation, integration refresh, destructive cleanup, force push, and history rewrite remain unauthorized.

## Next gate

Complete exact-head validation and signed canonicalization of this preparation package. Only then may the separately authorized B2.5 execution session be created and run once against the frozen 40-slot plan.
