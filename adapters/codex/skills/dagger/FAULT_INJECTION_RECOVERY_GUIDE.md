# Fault Injection and Recovery Measurement Guide

Use this guide for bounded dependency and infrastructure-failure simulations in explicitly authorized non-production environments. Start with a stub or protocol-level simulation; increase realism only when lower-risk evidence is insufficient.

## Fault taxonomy

- latency and deadline overrun;
- timeout, reset, refusal, or unreachable dependency;
- bounded error responses or rejection;
- malformed, stale, partial, or out-of-order response fixture;
- intermittent failure with a deterministic schedule;
- service restart or process termination in a disposable stack;
- resource quota, pool, or queue saturation;
- clock skew or expiry-boundary simulation through an injectable clock;
- storage read/write rejection through a mock or disposable volume.

Do not inject faults into production, public networks, shared infrastructure, real user data, or third-party systems. Do not use credential bypass, exploit chains, or unbounded packet/traffic disruption.

## Fault envelope

Define target component, injection point, failure type, start condition, duration or count, probability or deterministic schedule, affected identities, blast radius, ceiling, stop conditions, removal method, and recovery window. Change one fault dimension at a time unless interaction is the hypothesis.

## Retry and degradation checks

Verify per-attempt timeout, overall deadline, maximum attempts, backoff, jitter, retryable classifications, idempotency, concurrency limit, retry budget, circuit state, fallback freshness, and user-visible status. Watch for retry amplification, synchronized retries, queue growth, stale fallback, duplicate work, and recovery that depends on manual hidden state.

Safe degradation preserves critical invariants, exposes reduced capability honestly, avoids sensitive leakage, and does not silently accept work that cannot complete.

## Recovery objectives

- RTO: target time to restore an accepted service level after the fault ends.
- RPO: maximum acceptable loss or reprocessing window for durable state.
- Detection time: fault start to observable detection.
- Mitigation time: detection to safe degradation or containment.
- Recovery time: fault removal to accepted service level.
- Reconciliation time: accepted service to queues, replicas, caches, and durable state being consistent.

These objectives come from product/architecture/governance owners; Dagger measures scenarios against supplied objectives and does not invent business tolerance.

## Recovery verification

After removing the fault, confirm health probes, traffic acceptance, queue drain, pool recovery, circuit closure, retry cessation, cache/replica freshness, idempotent replay, absence of duplicate or orphan state, audit/telemetry continuity, and removal of every injection rule. Continue observation long enough to detect delayed work.

## Evidence timeline

Record synchronized timestamps for baseline, fault start, detection, mitigation, stop condition, fault removal, service recovery, reconciliation, and cleanup completion. Retain revision, environment identity, injector/tool version, configuration hash, telemetry sources, known clock error, before/after state, and missing evidence.

## Fail closed

If the injection cannot be independently stopped, target identity is uncertain, telemetry is missing, rollback is unproven, a shared dependency may be affected, or production connectivity is possible, keep the scenario planning-only.
