# Adaptive assurance AQ-3: specialist assurance contracts

AQ-3 binds a qualified AQ-2 normalized risk profile to a deterministic,
structured Conductor routing receipt. The receipt is an evidence contract, not
an execution or transition command.

## Contract surface

The declarative contract is
`machine/adaptive/aq3-specialist-assurance-contract.v1.json`, validated by
`machine/schemas/specialist-assurance-contract.v1.schema.json`. The pure
domain implementation is
`orchestra_runtime/domain/adaptive/specialist_assurance.py`.

Every receipt requires explicit non-empty source identities and records:

- AQ1 development mode and protected gates;
- AQ2 changed domains, quality dimensions, risk characteristics, invariants,
  and normalized risk fingerprint;
- selected canonical specialist slugs;
- the required assurance set;
- the AQ2-derived Dagger decision;
- the authority boundary; and
- the next transition target as a descriptive handoff only.

The receipt preserves the AQ2 risk fingerprint and may only add explicitly
declared, registry-bound coordination or assurance entries. It cannot remove
an AQ2 requirement. Selection does not grant dispatch, implementation,
validation, transition, provider, or production authority.

AQ3 evaluates only a qualified `AdaptiveRiskProfile` and revalidates the
receipt against that exact profile before any assurance decision. A receipt
with a valid-looking fingerprint is insufficient. AQ2 specialist, assurance,
Dagger, protected-gate, and authority-boundary requirements remain
monotonic.

## Assurance decisions

Overseer independently evaluates both
`IMPLEMENTATION_CONTRACT_SATISFIED` and
`INVARIANT_PRESERVATION_SUFFICIENT`. Evidence authored and validated only by
Ponytail is not independent. Evidence must be source-bound, fresh,
authoritative, attributable, and logically unique.

Arbiter compares three explicit sets:

1. `REQUIRED_ASSURANCE_SET` from the receipt;
2. `ACTUAL_EVIDENCE_SET` from usable evidence and an independent Overseer
   review; and
3. `CLAIMED_COMPLETION_STATE` constrained by AQ1.

Missing, stale, weaker, duplicate, wrong-source, or non-authoritative
evidence blocks progression. Green CI does not substitute for security,
concurrency, or adversarial evidence. A protected gate remains blocking until
its separately attributable evidence is present.

Overseer reviews are bound to the receipt fingerprint, AQ2 profile fingerprint,
exact evidence IDs, and explicit candidate, work-item, freshness, and version
context. Arbiter independently recomputes the review for the current evidence
set and rejects forged, stale, or differently bound review objects.

For claimed completion states, Arbiter delegates qualification to the AQ1
`validate_completion_escalation` contract with explicit AQ1
`AssuranceEvidence` and the complete verifier context. Missing verifier-owned
authority, required evidence metadata or layers, claim scope, or source and
revision bindings fails closed. AQ3 does not create canonical or product
completion authority.

## Specialist boundaries

- Dagger preserves every AQ2 risk or invariant trigger and adds the AQ3
  triggers `AUTHORIZATION`, `MULTI_TENANT`, `PRIVILEGE_MUTATION`,
  `CONCURRENCY`, `MULTI_ACTOR`, `AGGREGATE_INVARIANT`, `STATE_MACHINE`,
  `RETRY_IDEMPOTENCY`, `RECOVERY_ROLLBACK`, `EXTERNAL_INPUT`, `PROVENANCE`,
  `RESOURCE_PRESSURE`, the `DESTRUCTIVE_LIFECYCLE` quality dimension, and the
  normalized `PARTIAL_FAILURE` material-behavior marker. Harmless copy-only
  work is not a Dagger trigger, path names alone never trigger Dagger, and AQ3
  never authorizes Dagger execution.
- Scribe cannot infer historical intent. Historical claims retain AQ1 source
  truth and authority requirements.
- Cipher cannot let a tenant administrator mutate global authority.
- Chronicler cannot treat row-level or row-version evidence as proof of a
  tenant-wide aggregate invariant. Aggregate concurrency analysis is required.

## Explicit limits

AQ-3 contains no provider or production side effects, specialist dispatch,
test execution, AQ4 manifest or receipt persistence, signed materialization,
Padayon reconciliation, merge, release, or publication authority. AQ2 source
and test paths remain read-only for this phase.
