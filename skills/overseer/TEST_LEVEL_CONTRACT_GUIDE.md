# Test Level and Contract Guide

Choose test level from the observable failure boundary, not from a fixed pyramid quota.

| Level | Best evidence | Does not establish |
| --- | --- | --- |
| Unit | Branches, invariants, errors, and state transitions within one owned component | Serialization, real dependency, deployment, or user-flow behavior |
| Integration | Database, queue, filesystem, network adapter, framework, or service collaboration | Full supported environment or stakeholder acceptance |
| Contract | Versioned request/response/event/schema compatibility between provider and consumer | Provider availability, assembled workflow, or business acceptance |
| System/E2E | Minimal critical journey across deployed boundaries | Exhaustive edge behavior, visual quality, or root cause |
| Acceptance | Observable stakeholder criteria under the intended authority and context | Technical completeness beyond the accepted criteria |

## Contract Evidence

Record provider and consumer revisions, protocol/schema revision, compatibility direction, generated artifacts, test data, negative cases, and publication/deployment assumptions. A consumer-driven contract verifies declared interactions; it does not prove undeclared consumers or production deployment behavior.

Check additive/removal semantics, optional versus required fields, enum expansion, unknown-field behavior, defaulting, ordering, precision, time zones, error envelopes, idempotency, authentication context, and event replay where relevant. Route API architecture to Clockwork, security requirements to Cipher, and persistence semantics to Chronicler.

## Double and Fixture Boundaries

- Use a fake for deterministic domain behavior, a stub for controlled answers, and a mock only when the interaction itself is the contract.
- Do not replace the boundary whose real behavior creates the risk.
- Verify test doubles against the real adapter or contract to prevent drift.
- Avoid E2E duplication when a lower-level test observes the same risk more deterministically.

Ponytail implements test code. Overseer defines the evidence boundary and pass/fail criteria.
