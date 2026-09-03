# Migration Risk Contract Guide

## Purpose

Use this guide when a migration request needs an explicit, evidence-bound
`MigrationRiskContract`. It formalizes the existing migration, locking,
compatibility, backfill, dialect, and zero-downtime guidance. It does not
create a second migration framework and it never grants authority to execute a
migration.

Primary invariant:

```text
MIGRATION SAFETY MUST BE EVIDENCE-BOUND
```

Unknown production facts stay unknown. They are not replaced with a convenient
number, a safe-looking Boolean, or an assumed engine behavior.

## Contract and schema boundary

The contract is `MigrationRiskContract` with schema
`orchestra.migration-risk-contract.v1`, defined by
`machine/schemas/migration-risk-contract.v1.schema.json`. Emit it as a
structured section inside the existing **Caveman** or **Normalization Output**;
do not add a third frontmatter output format.

The v1 schema requires `production_data` to be a Boolean. Therefore:

- confirmed production data is `true`;
- confirmed non-production or development-only data is `false`;
- unknown production presence cannot be emitted as a valid v1 contract;
- never encode unknown production presence as `false`;
- return the pre-contract disposition
  `MIGRATION_RISK_SCHEMA_GAP: UNKNOWN_PRODUCTION_STATE_NOT_REPRESENTABLE`,
  request the missing evidence, and do not produce a production-safety claim.

`affected_records`, `read_traffic`, and `write_traffic` may use the schema's
string form such as `UNKNOWN` or `TO_BE_MEASURED`. That flexibility does not
repair the separate Boolean production-presence gap. A future schema amendment
or v2 contract is a separate governed change and is not silently introduced by
this guide.

## Evidence gate and field discipline

Before dialect-specific reasoning, identify the following from evidence:

| Field | Required reasoning |
| --- | --- |
| `database_engine` | Exact engine family, or an explicit unknown marker |
| `database_version` | Major version at minimum when behavior depends on it |
| `schema_revision` | Current and target schema or migration revision |
| `migration_tool` | Tool and version when generated behavior matters |
| `production_data` | Confirmed `true` or `false`; unknown is a schema-gap disposition |
| `affected_records` | Observed count, bounded evidence, `UNKNOWN`, or `TO_BE_MEASURED` |
| `read_traffic` / `write_traffic` | Observed traffic or an explicit unknown state |
| `evidence_refs` | Sources supporting material facts and measurements |

If the engine or version is missing, generic planning may continue, but exact
locking, online-DDL, concurrent-index, rewrite, transaction, or constraint
claims are blocked as `ENGINE_SPECIFIC_CLAIM_BLOCKED`. Do not turn an engine
name without a version into a universal guarantee.

## Proportionality

Classify the data context before selecting a pattern.

### DEVELOPMENT_ONLY

An empty local or disposable development database with confirmed
`production_data: false` may use `DIRECT`, LOW risk, no production backfill,
and no production compatibility window. Retain ordinary repository validation,
but do not add live-traffic ceremony that the evidence does not require.

### Production compatibility

Confirmed live data, active readers or writers, material record counts,
tenant-sensitive records, or an application rollout with old and new versions
coexisting require production reasoning. Compatibility, locking, backfill,
rollback, observability, and human-gate decisions must be evidence-bound.

Unknown scope is not a development-only classification. Keep unknown fields
unknown and request only the missing production fact needed for the decision.

## Migration pattern selection

Use only the canonical patterns:

`DIRECT`, `EXPAND_CONTRACT`, `BATCHED_BACKFILL`, `DUAL_READ_WRITE`,
`ONLINE_DDL`, `ENGINE_SPECIFIC`, and `OTHER`.

- `DIRECT` is appropriate only when the confirmed data, compatibility, lock,
  and recovery evidence makes a single bounded change safe.
- `EXPAND_CONTRACT` is appropriate when old and new application versions need a
  compatibility window: expand permissively, transition, backfill, validate,
  switch, then contract only after old dependencies are gone.
- `BATCHED_BACKFILL` is appropriate for material data transformation. Define a
  stable key, checkpoint, bounded transaction, retry/idempotency rule,
  throttle, and stop condition. Never invent a batch size.
- `DUAL_READ_WRITE` is reserved for migrations that genuinely require
  overlapping representations. Record consistency, ordering, idempotency,
  source-of-truth transition, failure, and rollback implications first.
- `ONLINE_DDL` is allowed only when the confirmed engine/version and operation
  support it. Online does not mean zero lock, zero latency impact, or zero
  risk.
- `ENGINE_SPECIFIC` or `OTHER` is used when a safe operation cannot be stated
  portably. The exact engine evidence remains required.

Do not produce a one-step destructive enforcement for a live table merely
because the final schema looks simple. A nullable or otherwise permissive
expansion, measured backfill, validation, and later enforcement may be safer.

## Operations that require explicit analysis

### Locking and traffic

Describe the affected object, lock class or equivalent behavior, acquisition
window, expected duration only when measured, wait/cancellation behavior, and
live read/write implications. If traffic or lock duration is unknown, keep it
unknown and identify the measurement needed. Do not claim that a migration is
non-blocking from an option name alone.

### Index operations

Consider table size, build duration, lock behavior, temporary storage,
read/write impact, query-plan transition, cancellation, and rollback. A
concurrent or online form is an engine/version-specific claim, not a portable
instruction.

### Constraint changes

For `NOT NULL`, `UNIQUE`, foreign-key, or check constraints, determine whether
existing records satisfy the invariant. A safer sequence may be permissive
structure, data correction, validation, and enforcement. State the evidence
and engine limitation instead of assuming the constraint is already true.

### Destructive or irreversible changes

For a drop, narrowing, destructive rewrite, or irreversible transformation,
record data loss, downstream readers, backup/recovery evidence, compatibility,
and the human gate. Chronicler plans the persistence risk; it does not execute destructive SQL and does not activate Dagger.

## Rollback, recovery, and completion

Every material migration identifies a `rollback_boundary`, for example before
backfill, after backfill but before contract, or after compatibility removal.
Rollback is not always reverse SQL. After old data or structures are removed,
restore or forward repair may be the only recovery path.

`failure_recovery` must address the applicable failure point:

- DDL failure or cancellation;
- a failed or partial backfill;
- deployment failure while versions coexist;
- new readers unable to consume migrated state;
- divergent writes or inconsistent validation rows.

Do not invent a production runbook. Keep recovery bounded to confirmed engine,
tool, schema, application, and operational evidence.

`observability` names only applicable signals such as attempted/changed/
skipped/failed rows, remaining work, retries, lock waits, latency, replication
lag, log growth, read discrepancies, or constraint status. `completion_criteria`
must prove the accepted requirement: for example zero backfill backlog,
successful invariant queries, validated constraints, no old readers, or an
accepted error threshold. A migration command returning exit code 0 does not prove data completion when rows remain.

Risk is one of `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`, or `UNKNOWN`. It depends on
the evidence combination of data, volume, live traffic, locks,
compatibility, downtime, data loss, rollback, engine behavior, and
observability. Do not use universal row-count thresholds.

`human_gate_required` is proportionate. It is normally required for material
live-data mutation, destructive or irreversible work, high lock/downtime
exposure, critical or unknown rollback, or a material security/compliance
consequence. A confirmed trivial development-only change is not automatically a human blocker.

## Ownership and handoffs

- The Steward owns product and workload assumptions, including upstream
  `CapacityEnvelope` values. Chronicler consumes them without rewriting them.
- Clockwork owns architecture topology when migration safety depends on a
  service, deployment, or persistence-boundary change.
- Cipher reviews tenant isolation, sensitive-field movement, encryption,
  privacy controls, and authorization consequences.
- Overseer owns QA strategy, release validation, and readiness conclusions;
  Chronicler supplies migration-specific validation queries and evidence needs.
- Ponytail implements an accepted bounded migration plan. Chronicler hands off
  the plan and does not run migration CLIs, backfills, DDL, or production SQL.
- Conductor sequences the handoffs. This guide does not grant authority. No contract, route, or successful test grants execution, release, deployment, policy, or destructive authority.

## Contract section

Use this section in an existing Chronicler output. Values must be confirmed,
explicitly unknown, or marked `TO_BE_MEASURED` as permitted by the schema.

```text
CONTRACT: MigrationRiskContract
SCHEMA: orchestra.migration-risk-contract.v1
OWNER: chronicler
REVISION: [non-empty revision]
DATABASE_ENGINE: [confirmed engine or UNKNOWN]
DATABASE_VERSION: [confirmed version or UNKNOWN]
SCHEMA_REVISION: [current/target revision]
MIGRATION_TOOL: [confirmed tool or UNKNOWN]
PRODUCTION_DATA: [true | false; unknown uses the schema-gap disposition]
AFFECTED_RECORDS: [observed value | UNKNOWN | TO_BE_MEASURED]
READ_TRAFFIC: [observed value | UNKNOWN | TO_BE_MEASURED]
WRITE_TRAFFIC: [observed value | UNKNOWN | TO_BE_MEASURED]
LOCKING_IMPLICATIONS: [evidence-bound description]
COMPATIBILITY_REQUIRED: [true | false]
BACKFILL_REQUIRED: [true | false]
INDEX_OPERATION: [applicable operation or none]
MIGRATION_PATTERN: [canonical enum]
DEPLOYMENT_SEQUENCE: [ordered conceptual steps]
ROLLBACK_BOUNDARY: [explicit boundary]
FAILURE_RECOVERY: [bounded recovery guidance]
OBSERVABILITY: [applicable signals]
COMPLETION_CRITERIA: [proof conditions]
RISK: [LOW | MEDIUM | HIGH | CRITICAL | UNKNOWN]
HUMAN_GATE_REQUIRED: [true | false]
EVIDENCE_REFS: [supporting references]
```

The result is a planning and handoff contract. It is not a migration execution
receipt and it must not claim release readiness.
