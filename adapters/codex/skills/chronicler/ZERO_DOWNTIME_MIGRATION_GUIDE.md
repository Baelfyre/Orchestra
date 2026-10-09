# Zero-Downtime Migration Guide

"Zero downtime" is a target that requires observed compatibility and availability evidence. It is not guaranteed by an ORM generator, an `ONLINE` option, or an additive-looking statement.

## Expand-Migrate-Contract

1. **Expand:** add backward-compatible structures. Avoid new required columns without a safe default/backfill plan.
2. **Deploy compatible writers:** write the new representation while preserving old readers. Prefer one authoritative write with a deliberate compatibility mechanism over unconstrained application dual writes.
3. **Backfill:** process stable-key batches with checkpoints, bounded transactions, throttling, restart safety, and replica/lock telemetry.
4. **Validate:** compare counts, nulls, duplicates, checksums or business invariants, and application readback. Record lag and error budgets.
5. **Switch reads:** move consumers gradually while old and new representations remain compatible.
6. **Contract:** remove old columns, constraints, triggers, or compatibility code only after all readers/writers have moved, rollback no longer depends on them, and destructive authority is separately granted.

## Operation Review

For each DDL or data step, confirm engine/version behavior for metadata locks, table rewrite, index build, transaction-log/WAL growth, replication lag, disk headroom, cancellation, and recovery. Online DDL can still block briefly or fall back to a heavier algorithm.

Backfill evidence must include:

- stable batch key and ordering;
- checkpoint and idempotent restart rule;
- batch size and pause/throttle controls;
- rows attempted, changed, skipped, and failed;
- lock waits, latency, replica lag, log growth, and remaining work;
- invariant queries that return rows only on mismatch.

## Rollback Boundaries

Additive expansion is usually reversible by application rollback while compatibility remains. Once old data or structures are removed, rollback may require restore or forward repair. Mark that point explicitly and do not cross it automatically.

Migration files and example SQL remain `PLANNED_UNEXECUTED` until an exact environment, backup/recovery position, command, operator, window, stop conditions, and mutation authority are recorded. Never infer production authority from a validated plan.
