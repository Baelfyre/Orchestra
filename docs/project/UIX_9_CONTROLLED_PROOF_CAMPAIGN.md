# UIX-9 Controlled Proof Campaign

Status: `UIX_9_PROOF_PREPARED_WAITING_LIVE_CALL_AUTHORIZATION`

Recorded: 2026-08-24

Entry baseline: `093babeea188c502cded8756f97648291bc0fea0`

## Scope

UIX-9A prepares a bounded, repository-only proof protocol for the question: does the same frozen UI task and project requirement set produce different objective design-fidelity evidence when canonical UIX-1 through UIX-8 guidance is present versus absent?

The baseline arm is `BASELINE_NO_ORCHESTRA_UIX_GUIDANCE`. The governed arm is `GOVERNED_CANONICAL_UIX_1_8_GUIDANCE`. The only intended treatment difference is UIX guidance presence or absence. Task requirements, project fixture, endpoint identity, validators, resource ceilings, and authority boundaries remain fixed.

## Objective measurements

The protocol records component reuse, duplicate component count, token violations, arbitrary-style drift, state coverage, asset provenance, asset substitution, responsive containment, accessibility invariants, unresolved mappings, revision mismatch, visual-baseline replacement, and deterministic acceptance.

These are objective fixture and validator fields. They are not a model self-rating and do not use a primary subjective visual score.

Secondary fields are implementation diff size, new component count, new arbitrary token/value count, validation remediation count, and time or token usage only when trustworthy comparable counters are available.

Controlled variables are task semantics, starting project state, permitted dependencies, provider/model if later authorized, resource ceiling, validator, acceptance requirements, and retry policy. Measurement direction is frozen before live execution; unavailable metrics remain unavailable, invalid observations are not silently excluded, provider outages are explicitly classified, valid unfavorable results are not retried, and no single metric grants promotion.

## Repository-only dry run

The machine plan is `machine/ui/uix9-proof-plan.v1.json`. The closed schemas are:

- `machine/schemas/uix-proof-plan.schema.json`
- `machine/schemas/uix-proof-observation.schema.json`
- `machine/schemas/uix-proof-result.schema.json`

The dedicated project requirements are frozen at `tests/fixtures/ui/uix9-proof-project/requirements.json`. Positive and negative validator bundles are `tests/fixtures/ui/uix9-proof-positive.json` and `tests/fixtures/ui/uix9-proof-negative.json`.

`scripts/uix9_proof_harness.py` validates the plan and both bundles locally. It makes zero model calls, zero provider calls, zero external repository mutations, zero model self-ratings, zero subjective visual scores, and zero endpoint changes. `tests/runtime/test_uix9_proof_protocol.py` exercises the positive case, negative case, and fail-closed authority and call-count mutations.

The dry run proves protocol determinism and validator behavior only. It does not observe model behavior, establish benefit, compare live baseline and governed outcomes, or authorize live calls.

Evidence is write-isolated under the UIX-9 fixture scope and does not touch canonical benchmark evidence. The prepared authorization request records provider, model, host/CLI version, task and arm counts, repetitions, maximum calls, resource ceiling, timeout, retry policy, invalid-run policy, endpoints, stop conditions, and exact frozen task/validator identities as not authorized or not yet assigned.

## Terminal boundary

The valid current terminal is `UIX_9_PROOF_PREPARED_WAITING_LIVE_CALL_AUTHORIZATION`. A live proof request would require separate authorization with the exact provider and model revision, frozen task and project identities, arm treatment, repetition plan, call and resource ceilings, endpoint identity, evidence retention, and external-mutation boundary specified before any outcome is observed.

No runtime authority, dependency, adapter, external call, model self-rating, subjective visual score, endpoint change, release, deployment, policy activation, or destructive action is introduced.

Current-state README editorial realignment remains queued for the final campaign reconciliation stage.
