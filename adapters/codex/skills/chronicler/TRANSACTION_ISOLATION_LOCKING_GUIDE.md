# Transaction Isolation and Locking Guide

Isolation names are not portable behavioral guarantees. Start with the invariant and anomaly, then confirm the target engine's MVCC, snapshot, and locking behavior for its exact version and configuration.

## Anomaly-to-Evidence Map

| Risk | Evidence to reproduce or exclude | Persistence response to evaluate |
| --- | --- | --- |
| Dirty read | Reader observes a value later rolled back | Minimum isolation and engine configuration |
| Non-repeatable read | Same row changes inside one logical transaction | Row/version protection or stronger snapshot boundary |
| Phantom or write skew | A predicate changes or two writers preserve local checks but violate a global invariant | Predicate protection, constraint redesign, serialization, or explicit locking |
| Lost update | Two writers read one version and one update silently replaces the other | Atomic update, version predicate, lock, or conflict result |
| Duplicate effect | Retry commits the same logical action more than once | Idempotency key and uniqueness at the persistence boundary |

Do not choose `READ COMMITTED`, `REPEATABLE READ`, `SERIALIZABLE`, or snapshot isolation from the label alone. Record the invariant, concurrent schedule, observed result, engine/version, and retry behavior.

## Locking Review

- Identify the locked object or key range, acquisition order, duration, wait timeout, and escalation behavior.
- Keep external calls and user think-time outside transactions.
- Use `NOWAIT` or `SKIP LOCKED` only when the product semantics explicitly allow fail-fast or work-skipping behavior.
- Verify queue consumers cannot starve old rows or process one logical item twice.
- Treat long-running readers, idle transactions, DDL, and maintenance jobs as possible blockers.

## Deadlock Diagnosis

1. Capture the deadlock graph or equivalent victim/wait evidence.
2. Map each statement to its transaction boundary and lock acquisition order.
3. Reproduce with deterministic coordination, not timing-only sleeps.
4. Prefer a consistent lock order or smaller atomic boundary.
5. Add bounded retry only for engine-classified transient victims and only when the operation is idempotent.
6. Verify rollback removed partial state and the retry produced one logical effect.

Unbounded retries can amplify contention. A timeout without wait evidence does not prove a deadlock. Chronicler defines persistence semantics, Clockwork owns broader concurrency boundaries, Ponytail implements, and Overseer defines the concurrency validation gate.
