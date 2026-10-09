# SQL Review Guide

Review SQL against the target engine, schema revision, transaction behavior, and approved environment.

## CREATE TABLE

- Verify purpose, key, types, nullability, defaults, unique rules, checks, foreign keys, and engine behavior.
- Identify missing integrity rules without inventing requirements.

## ALTER TABLE

- Identify lock, rewrite, compatibility, and deployment impact.
- Separate additive, data-transforming, and destructive steps.
- Require recovery guidance and approval for destructive changes.

## INSERT Seed Scripts

- Check explicit columns, canonical identifiers, uniqueness, order, and repeatability.
- Detect duplicate or conflicting values and exclude credentials or personal data.

## SELECT Validation Queries

- Keep validation read-only and narrowly scoped.
- Check nulls, duplicates, orphans, cardinality, totals, and reference values.

## JOIN Correctness

- Confirm keys, type compatibility, cardinality, and inner or outer semantics.
- Check row multiplication, outer-join filters, and missing tenant or status predicates.

## Transaction Safety

- Group dependent writes under the correct atomic boundary.
- Define failure, retry, isolation, and idempotency behavior when relevant.

## Migration Safety

- State preconditions, recovery, data transformation, verification, and deployment order.
- Test on representative data before production.

## Safe Update Behavior

- Preview affected rows with a matching `SELECT` and selective predicate.
- Capture affected count and post-state.
- Use a transaction when safe rollback is supported.

## Destructive SQL Warnings

Treat `DROP`, `TRUNCATE`, unscoped `DELETE` or `UPDATE`, destructive column changes, and irreversible transformations as approval-required. Do not run them automatically. Provide impact, backup, recovery, and verification guidance first.
