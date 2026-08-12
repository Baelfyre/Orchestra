# Concurrency and Resource Pressure Guide

Use this guide to design deterministic, bounded scenarios for competing operations and finite resources. It does not authorize changing host limits or exhausting resources.

## Concurrency hypotheses

Test one invariant at a time:

- no lost update when two actors modify the same version;
- no duplicate effect after repeated, retried, or concurrent submission;
- required ordering is preserved or violations are rejected;
- cancellation releases locks, leases, reservations, and permits;
- deadlock and lock-wait behavior is bounded and observable;
- stale reads do not authorize invalid state transitions;
- queue consumers preserve ownership, acknowledgement, and redelivery rules;
- idempotency keys have correct identity, scope, lifetime, and result replay.

Prefer deterministic coordination through barriers, latches, controlled clocks, dependency stubs, fixed seeds, or recorded schedules. Repeated random concurrency without a reproducible schedule is discovery evidence, not a stable regression.

## Resource model

For each finite resource, identify demand, capacity, saturation signal, safe rejection/degradation behavior, recovery signal, and cleanup:

| Resource | Demand signal | Saturation signal | Expected safe behavior |
|---|---|---|---|
| CPU | runnable work, utilization | run queue, throttling, tail latency | bound work, shed or degrade |
| Memory | allocation and working set | reclaim, paging, OOM proximity | bound queues/caches, reject early |
| Disk | bytes, IOPS, temporary growth | latency, queue, free-space floor | quota, cleanup, safe read-only mode |
| Connections | active/idle/waiters | pool wait and timeout | bound concurrency and wait |
| File handles/sockets | open descriptors | limit proximity, accept failures | close reliably, reject safely |
| Queue | arrival and service rate | depth and oldest-item age | backpressure, shedding, bounded drain |
| Threads/tasks | active and queued work | executor queue, starvation | admission control, cancellation |
| External quota | calls or bytes | 429/quota rejection | pace, cache, defer, stop retrying |

## Safe scenario shape

1. Confirm isolated target and synthetic data.
2. Capture baseline state and resource ceilings.
3. Coordinate the smallest competing operation or resource step.
4. Verify both response and durable final state.
5. Observe queue, locks, pools, retries, resource usage, and generator health.
6. Stop at the first approved threshold.
7. Remove pressure and verify resource normalization and residual state.

Do not lower operating-system limits, fill disks, exhaust pools, or create sustained contention outside a separately approved disposable environment. Use stubs, small configured pools, quotas, or local container limits only when those exact changes are authorized and recoverable.

## Evidence

Record revision, environment, schedule/barrier, actor identities, initial versions, operation IDs, idempotency keys, final state, ordering, lock/queue/pool telemetry, errors, stop reason, cleanup, and reproduction count. Mark a race suspected until the failing schedule and state evidence are retained.

## Ownership

Dagger owns the pressure scenario. Chronicler interprets transaction/locking semantics. Clockwork interprets concurrency and queue ownership. Cipher interprets access or isolation impact. Overseer owns formal acceptance and readiness. Ponytail owns fixes and test code.
