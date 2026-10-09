# Database Standards

Apply these standards to confirmed requirements and database evidence, not hypothetical scale.

## Engine and Mapping Identity

- Record the database product, major version, deployment topology, schema revision, migration tool, and ORM/provider version before engine-specific conclusions.
- Compare ORM mappings and generated SQL with the canonical schema, including names, types, nullability, defaults, keys, cascades, concurrency tokens, and value generation.
- Treat ORM auto-generation and schema synchronization as environment-sensitive behavior, not a substitute for reviewed migrations.

## Tables and Columns

- Give each table one coherent subject and stable ownership.
- Use consistent, descriptive names and data types that preserve the domain.
- Define nullability from business rules, not convenience.
- Avoid duplicated facts unless denormalization is justified and maintained.

## Primary Keys

- Give every entity a stable, unique, non-null identifier.
- Choose natural, composite, or surrogate keys from identity and lifecycle requirements.
- Do not expose mutable business data as a key without justification.

## Foreign Keys

- Enforce confirmed relationships with compatible types.
- Define update and delete behavior explicitly.
- Index foreign keys when workload or engine behavior justifies it.

## Constraints and Defaults

- Use unique constraints for candidate keys and duplicate-prevention rules.
- Use check constraints for stable domain rules supported by the engine.
- Use not-null constraints for required facts.
- Use defaults only when the default is valid for every omitted value.

## Indexes

- Tie indexes to known joins, filters, ordering, uniqueness, or measured bottlenecks.
- Review selectivity, column order, covering needs, write cost, and overlap.
- Avoid speculative or duplicate indexes.
- Use actual or safely captured query plans to distinguish scans, seeks, join choices, row-estimate errors, spills, and sort or lookup cost before changing an index.

## Transactions and Concurrency

- Choose isolation from required anomaly prevention and confirmed engine semantics, not from a portable label alone.
- Keep transactions bounded and define retry ownership, idempotency, lock order, timeout handling, and post-failure readback where contention is possible.
- Diagnose deadlocks from wait and victim evidence. Do not mask deterministic lock-order defects with unbounded retries.

## Tenant Isolation

- Carry tenant identity through keys, unique constraints, foreign keys, indexes, and every tenant-scoped query when the data model is shared.
- Validate database-enforced row policies against connection and pooling behavior when row-level security is used.
- Route tenant authorization policy to Cipher while Chronicler owns persistence enforcement mechanics.

## Normalization

- Remove repeating groups and verify atomic values for the intended domain.
- Check partial dependencies for composite keys and transitive dependencies among non-key facts.
- Denormalize only with measured or required read behavior plus a consistency plan.

## Reference Tables and Seed Data

- Give canonical values stable identifiers and documented meanings.
- Enforce uniqueness and active or retired lifecycle rules where required.
- Keep seed scripts deterministic, repeatable, and free of conflicting duplicates.

## Audit Tables

- Record actor, action, time, affected identity, and before or after values only when required.
- Protect audit records from ordinary update paths.
- Document retention, privacy, and access rules.

## Migration Files

- Make order, prerequisites, data transformation, rollback or recovery, and deployment impact explicit.
- Separate destructive steps and require approval.
- Test migrations against representative data and verify constraints afterward.
- Prefer expand, migrate, validate, contract sequencing when old and new application versions overlap.
- Bound backfills by stable keys, make checkpoints resumable, measure lock and replication impact, and delay incompatible cleanup until all readers and writers have moved.

## Data Dictionaries and Documentation

- Document table purpose, ownership, keys, columns, constraints, relationships, lifecycle, and sensitive data classification.
- Match documentation to the authoritative revision.
- Mark inferred or proposed fields clearly.

## Database Testing

- Test valid writes, invalid writes, uniqueness, referential actions, nullability, defaults, migrations, rollback or recovery, and representative queries.
- Capture environment and pre-state before mutation.
- Use non-production data unless explicit production authority exists.
