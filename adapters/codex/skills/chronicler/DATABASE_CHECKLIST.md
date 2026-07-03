# Database Review Checklist

## Objective and source

- [ ] Database role and review objective are explicit.
- [ ] Authoritative schema, migration, dump, or live metadata is identified.
- [ ] Environment and mutation authority are known.

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

## Reference and seed data

- [ ] Canonical values are unique and stable.
- [ ] Seed scripts are deterministic and repeatable.
- [ ] Duplicate, conflicting, stale, or orphaned values are identified.

## Migrations and auditability

- [ ] Migration order, preconditions, data transformation, and recovery are documented.
- [ ] Destructive operations require approval and backup or rollback planning.
- [ ] Required actor, time, and change-history evidence is retained safely.

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
