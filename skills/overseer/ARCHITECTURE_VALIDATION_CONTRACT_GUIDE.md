# Architecture Validation Contract Guide

Use this guide when an accepted governance or cross-specialist contract creates
a validation obligation. It is a progressive-disclosure companion to the
existing QA review and evidence formats, not a second test framework.

## Contract identity

The `ArchitectureValidationContract` is owned by Overseer and uses the
canonical repository schema at
machine/schemas/architecture-validation-contract.v1.schema.json.
Keep these fields exact and non-empty:

- `contract_refs`: every accepted upstream contract that the validation basis
  consumes;
- `exact_revision`: the exact revision of the accepted subject and validation
  basis under review;
- `environment_identity`: the actual environment used for observed evidence.

At planning time, when no execution environment exists, use an explicit
truthful planning descriptor such as `PLANNING_NO_EXECUTION_ENVIRONMENT`. This
is a provenance disposition, not an environment claim, and it cannot produce
`PROVEN` evidence by itself.

## Applicability and proof

State applicability for every validation dimension before evaluating evidence.
Use `REQUIRED` with one or more accepted criteria, or `NOT_REQUIRED` when the
upstream contracts establish that the dimension does not apply. Missing
applicability is incomplete input, not implicit `NOT_REQUIRED`.

The seven dimensions are:

```text
functional_validation
capacity_validation
performance_validation
tenant_isolation_validation
migration_validation
failure_behavior_validation
compatibility_validation
```

The evaluator accepts observed evidence only. A current evidence record must
match the complete `contract_refs` set, `exact_revision`, and
`environment_identity`, and must identify the criteria it observed.

```text
all required criteria currently proven -> PROVEN
any matching criterion failure        -> FAILED
required evidence absent/incomplete   -> NOT_PROVEN
accepted dimension not applicable     -> NOT_REQUIRED
```

`NOT_PROVEN` means that the accepted claim is not established by current
evidence. It is not a product failure. `FAILED` requires an executed
observation that contradicts an accepted criterion. A skipped check, crashed
runner, stale or mismatched report, flaky result that cannot establish the
criterion, or missing metric remains `NOT_PROVEN` and must be listed as a
limitation.

## Contract-derived obligations

Derive criteria from accepted inputs, not from a universal checklist:

- Product intent acceptance criteria produce functional obligations.
- Capacity values preserve their source semantics: exact, range, observed,
  estimated, unknown, or to-be-measured. Do not average ranges or invent
  targets.
- `SCALE_READY` alone does not require an arbitrary load test. A
  `SCALE_PROVISIONED` decision requires outcome evidence only when a quantified
  capacity or performance target justified the provisioning.
- Migration risk produces only the applicable schema, backfill, compatibility,
  constraint, completion, rollback, and recovery checks. Chronicler still owns
  migration semantics and does not execute them here.
- Tenant isolation uses accepted Cipher and persistence requirements; Overseer
  defines evidence and Ponytail implements safe tests.
- Failure behavior and compatibility checks exist only when accepted
  requirements declare them.

Do not convert an accepted request into a requirement when Steward accepted a
different problem or solution. Do not manufacture a benchmark, environment,
tenant policy, migration result, or release conclusion.

## Evidence scope and freshness

Evidence proves only the criterion, revision, environment, workload, and
duration it actually observed. A 50-user result does not prove 500 users. A
unit test does not prove database safety, browser behavior, load capacity, or
tenant isolation.

When The Tuner marks evidence stale, preserve the historical reference but
remove it from current proof. The current dimension becomes `NOT_PROVEN` until
replacement exact-bound evidence exists. Stale evidence is not rewritten as
`FAILED`.

Partial criteria do not average to a pass. Two proven criteria and one missing
criterion produce `NOT_PROVEN`; one failed criterion produces `FAILED`.

## Authority boundaries

Overseer derives validation obligations, evaluates supplied evidence, and
reports limitations. Overseer does not:

- implement test code or run a general test runner;
- alter ProductIntentContract, CapacityEnvelope, ArchitectureComplexityDecision,
  MigrationRiskContract, or Cipher requirements;
- decide architecture, persistence, security policy, or migration semantics;
- route specialists or issue Arbiter transition dispositions;
- activate Dagger, execute destructive or resilience tests, execute migrations,
  authorize deployment, or authorize release.

Architecture validation is evidence. It does not grant merge, continuation,
deployment, release, or policy authority.

The OR-GOV-4 `MigrationRiskContract` unknown-production schema gap remains
unchanged. Unknown production presence is never represented as
`production_data=false` by this contract.
