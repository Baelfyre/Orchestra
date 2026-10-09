# Database Dialect and ORM Guide

Use this guide only after repository evidence identifies the database engine, major version, schema revision, ORM/provider, and migration tool. A product name without a version is insufficient for syntax or operational claims.

## Dialect Evidence

| Surface | PostgreSQL | MySQL | SQL Server | SQLite |
| --- | --- | --- | --- | --- |
| Generated identity | Identity or sequence behavior is version and mapping dependent | `AUTO_INCREMENT` behavior depends on engine and mode | `IDENTITY` or sequence mapping affects insert behavior | `INTEGER PRIMARY KEY` has rowid-specific semantics |
| Upsert | `ON CONFLICT` needs an exact conflict target | `ON DUPLICATE KEY UPDATE` may react to any matching unique key | `MERGE` has product-specific concurrency cautions; prefer evidence-backed alternatives | `ON CONFLICT` support depends on bundled version |
| Boolean and time | Native boolean and time-zone-aware types exist | Boolean aliases, modes, and timestamp conversion require verification | `bit`, datetime families, and session settings differ | Dynamic typing and adapter conversion require explicit checks |
| DDL behavior | Lock level and rewrite behavior vary by operation and version | Online/in-place labels do not guarantee no blocking | Online options depend on edition, operation, and version | Many alterations rebuild a table through tool-managed steps |

This table is a review cue, not executable syntax. Confirm behavior in the vendor documentation for the exact version and validate on representative non-production data.

## ORM Mapping Review

Trace both directions:

```text
domain field -> ORM metadata -> generated SQL -> database column/constraint
database default/generated value -> returned row -> ORM state -> domain field
```

Check:

- type width, precision, collation, time zone, enum conversion, and nullability;
- primary, alternate, and composite keys plus foreign-key column order;
- cascade, orphan removal, eager/lazy loading, and ownership of relationship changes;
- optimistic concurrency tokens and the affected-row behavior for stale writes;
- server-generated identifiers/defaults and whether the ORM refreshes them;
- query filters, soft-delete rules, and tenant predicates on every access path;
- migrations generated from the same model/provider version that production will use.

## Generated SQL Failure Modes

- N+1 reads hidden by navigation access;
- Cartesian multiplication from multiple collection joins;
- client-side filtering after broad materialization;
- per-row writes where a bounded set operation is intended;
- missing concurrency predicate on update or delete;
- schema-qualified or case-sensitive identifiers that differ by environment;
- migration-history drift where the database, migration ledger, and ORM model disagree.

Never resolve migration-history drift by deleting ledger rows or marking a migration applied without proving exact schema equivalence and obtaining mutation authority. Ponytail implements an accepted mapping change. Overseer owns executable validation. Cipher owns authorization and sensitive-data policy.
