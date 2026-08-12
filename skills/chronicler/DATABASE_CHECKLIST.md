# Database Review Checklist

## Objective and source

- [ ] Database role and review objective are explicit.
- [ ] Authoritative schema, migration, dump, or live metadata is identified.
- [ ] Environment and mutation authority are known.
- [ ] Engine, major version, topology, schema revision, ORM/provider, and migration tool are confirmed.

## Tables and columns

- [ ] Each table has a coherent subject and ownership.
- [ ] Names, types, lengths, nullability, and defaults match domain rules.
- [ ] Sensitive and lifecycle data are identified when relevant.

## Keys and constraints

- [ ] Every entity has an appropriate primary key.
- [ ] Foreign keys match referenced types and confirmed relationships.
- [ ] Unique, check, not-null, and default constraints enforce known rules.
- [ ] Referential actions are explicit and safe.

## Indexes and normalization

- [ ] Indexes map to known queries, joins, ordering, or uniqueness.
- [ ] Redundant and overlapping indexes are identified.
- [ ] Repeating groups, partial dependencies, and transitive dependencies are reviewed.
- [ ] Denormalization has evidence and a consistency plan.
- [ ] Query-plan evidence includes estimates versus actuals, access path, joins, sorts, spills, and representative parameters where available.

## ORM and transaction semantics

- [ ] ORM mapping matches schema types, nullability, keys, cascades, generated values, and concurrency controls.
- [ ] Generated SQL avoids hidden N+1 access, unbounded materialization, accidental client evaluation, and unsafe bulk-write behavior.
- [ ] Isolation requirements name the anomalies to prevent and account for confirmed engine behavior.
- [ ] Lock order, transaction duration, retry ownership, idempotency, timeouts, and deadlock evidence are reviewed.

## Tenant isolation

- [ ] Tenant identity participates in required keys, foreign keys, uniqueness, indexes, and query predicates.
- [ ] Cross-tenant relationships are impossible at the persistence boundary where required.
- [ ] Row-level security, session context, and pooled-connection reset behavior are validated when applicable.

## Reference and seed data

- [ ] Canonical values are unique and stable.
- [ ] Seed scripts are deterministic and repeatable.
- [ ] Duplicate, conflicting, stale, or orphaned values are identified.

## Migrations and auditability

- [ ] Migration order, preconditions, data transformation, and recovery are documented.
- [ ] Destructive operations require approval and backup or rollback planning.
- [ ] Required actor, time, and change-history evidence is retained safely.
- [ ] Compatibility across old and new application versions is explicit for every expand, backfill, validation, switch, and contract step.
- [ ] Backfill batching, checkpointing, throttling, lock/replication limits, observability, and restart behavior are defined.
- [ ] Destructive contract steps remain delayed and separately authorized.

## Reporting and integration

- [ ] Reporting requirements do not silently redefine transactional facts.
- [ ] ORM models, repositories, APIs, and documentation agree with the schema.
- [ ] Transactions and consistency boundaries are documented.

## Security and permissions

- [ ] Credentials are absent from code and output.
- [ ] Roles follow least privilege when permissions are in scope.
- [ ] Sensitive data access, retention, backup, and recovery are documented when required.

## Verification

- [ ] Validation queries are read-only unless mutation is approved.
- [ ] Pre-state and post-state are captured for approved changes.
- [ ] SQL drafts are marked untested until executed safely.
- [ ] Missing evidence and assumptions are explicit.
