# Planning-Only Expand-Contract Example

## Status

`PLANNED_UNEXECUTED`. No schema or data mutation occurred.

## Confirmed Inputs

- Target: PostgreSQL 16 non-production clone, exact schema revision recorded in the execution packet.
- Existing readers require `customer.display_name`.
- Target model separates `given_name` and `family_name` while preserving the old field during compatibility.
- Production execution, destructive cleanup, and live-data access are not authorized by this example.

## Phase Plan

1. Expand with nullable target columns after confirming the exact lock behavior for the reviewed DDL.
2. Deploy a compatible writer that maintains the old representation and derives the new fields under one accepted transaction contract.
3. Backfill by stable `customer_id` ranges using resumable checkpoints and bounded transactions.
4. Validate mismatches, null coverage, duplicate effects, application readback, lock waits, WAL growth, and replica lag.
5. Switch reads behind a reversible application control while monitoring both representations.
6. Treat removal of `display_name` and compatibility code as a later destructive contract step requiring separate authority.

## Stop Conditions

- lock wait or request latency exceeds the approved bound;
- replica lag, WAL growth, error rate, or disk headroom crosses its recorded threshold;
- a validation query returns a mismatch;
- checkpoint progress cannot resume idempotently;
- an old reader or writer remains active before contract.

## Evidence Packet

Record engine/version, schema and application revisions, reviewed migration hash, batch configuration, pre-state, per-batch counts, telemetry timeline, invariant results, post-state, rollback boundary, and operator disposition.

This example is guidance only. Ponytail may implement an accepted migration artifact, Overseer defines execution evidence, Clockwork owns application compatibility boundaries, Cipher reviews sensitive-data and tenant-policy concerns, and Conductor controls sequencing. No executable production command is provided.
