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

## Specialist boundaries

- Dagger is selected only from AQ2 risk or invariant triggers. Harmless
  copy-only work is not a Dagger trigger, and AQ3 never authorizes Dagger
  execution.
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
