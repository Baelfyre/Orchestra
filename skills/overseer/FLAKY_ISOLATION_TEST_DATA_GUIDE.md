# Flaky Test, Isolation, and Test Data Guide

A test is flaky when the same identified revision, relevant environment, and intended inputs can produce inconsistent outcomes. First classify whether the instability belongs to the product, test, environment, data, or observability.

## Diagnosis Packet

Capture first failing attempt, all reruns, failure signature, revision, worker/shard, OS/runtime, seed, locale/time zone, ordering, timing, resource pressure, external dependency state, and retained evidence. Preserve the initial failure when a retry passes.

Use deterministic coordination and state polling instead of timing-only sleeps. Check leaked processes, ports, queues, database rows, files, caches, global variables, clock assumptions, random seeds, and parallel identifier collisions.

## Quarantine Contract

Quarantine requires owner, linked defect, exact scope, reason, visible non-passing status, expiry/review date, and restoration criteria. It must not satisfy a required gate or silently reduce the asserted support matrix.

## Isolation Controls

- inject or control clocks and randomness;
- allocate unique worker-scoped resources;
- reset state through owned APIs or disposable environments;
- avoid order dependence and shared mutable fixtures;
- make cleanup idempotent and report cleanup failure separately;
- record external-service simulation limits.

## Test Data Lifecycle

Define provenance, schema/version, factory or fixture revision, relationship rules, uniqueness, setup, reset, retention, redaction, and disposal. Prefer synthetic/minimized data. If production-derived data is explicitly authorized, minimize fields, de-identify with verified re-identification risk controls, restrict access, and record expiry.

Do not fabricate factual user feedback or public records. Cipher owns privacy/security policy, Chronicler owns persistence integrity, Ponytail implements factories/fixtures, and Overseer defines evidence requirements.
