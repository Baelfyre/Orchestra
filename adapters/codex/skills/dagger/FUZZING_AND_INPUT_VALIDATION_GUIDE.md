# Fuzzing and Input Validation Guide

Use fuzzing defensively to discover validation and parsing failures in an authorized, isolated target. Prefer bounded, reproducible input sets over uncontrolled traffic.

## Validation layers

- UI: immediate guidance and safe rendering, never the only enforcement layer.
- API: schema, type, size, format, authorization, and rate enforcement.
- Backend: business invariants, state transitions, normalization, and safe errors.
- Database: types, lengths, nullability, keys, checks, uniqueness, and transactions.

## Input classes

Test empty, null, missing, malformed, unexpected-type, boundary, oversized, Unicode, special-character, duplicate, out-of-order, and randomized inputs. Seed randomized runs and retain the minimal reproducing input.

## Safe protocol

1. Confirm authorization, isolation, target endpoints, traffic ceiling, duration, and stop conditions.
2. Begin with deterministic malformed and boundary cases.
3. Add seeded random variation only where it adds coverage.
4. Limit request rate, payload size, concurrency, and generated cases.
5. Stop on instability, cross-tenant effects, sensitive output, or resource exhaustion.
6. Redact secrets and personal data from corpora, logs, and reports.

Do not fuzz production, public third-party targets, authentication bypass paths, or unbounded resource-consumption surfaces. Report only defensive findings and remediation.
