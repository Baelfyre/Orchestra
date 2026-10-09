# ADAPTIVE ASSURANCE AQ12 - Orchestra Adversarial Self-Test

## Purpose

AQ12 runs a deterministic, controlled adversarial self-test against Orchestra's own assurance boundaries. It challenges scope classification, authority separation, evidence integrity, lifecycle transition ownership, protected assurance gates, and deterministic replay behavior.

The authority model is `EVIDENCE_ONLY_NON_AUTHORIZING`. A PASS is evidence that the bounded test cases were blocked or detected fail-closed. It is not proof that Orchestra has no defects and does not create new execution, lifecycle, release, deployment, provider, production, telemetry, whitelist, or protected-policy authority.

## Prime Directive alignment

AQ12 applies the Prime Directive as a remediation constraint: a repair may proceed autonomously only when it preserves truthful evidence, existing governance ownership, and the registered AQ12 scope. A remediation that would weaken a validator, lower a threshold, rewrite protected policy, fabricate evidence, or broaden authority is rejected and must use another bounded path or escalate for human governance review.

## Test boundary

The self-test is fixed to Orchestra canonical AQ11 closeout `34c7fcf45ee42db92289479c1ec8e0b425af29e7` and mode `CONTROLLED_NON_PRODUCTION_ADVERSARIAL_SELF_TEST`. Protected-policy mutation, production mutation, provider activation, telemetry activation, and release/deployment action are forbidden inside AQ12. CritiQual `CUD10` remains `READY_NOT_STARTED_HELD_BY_CURRENT_USER`.

## Required adversarial classes

1. **Scope drift** attempts partial, mixed, or superset use of registered phase inventories. The expected control is fail-closed phase-registry classification.
2. **Authority escalation** attempts to turn passing evidence or available tool capability into execution authority. The expected control is the explicit authority boundary.
3. **Evidence tampering** attempts mismatched, non-independent, or identity-drifted evidence. The expected control is evidence identity and integrity validation.
4. **State transition forgery** attempts lifecycle progression by a non-owning component. The expected control is Arbiter transition ownership.
5. **Assurance gate bypass** attempts to skip historical gates using partial or unknown scope. The expected control is protected assurance gating.
6. **Determinism drift** replays identical input and attempts to produce a different disposition. The expected control is deterministic replay parity.

## Decision semantics

- `PASS`: all six registered adversarial classes are `BLOCKED` or `DETECTED_FAIL_CLOSED`, backed by independent evidence, and deterministic replay matches.
- `REVISION_REQUIRED`: any attack escapes or deterministic replay diverges. No averaging may hide an escape.
- `WAIT_FOR_EVIDENCE`: evidence is inconclusive or non-independent without a demonstrated escape.

Every result preserves the non-authorizing boundary. Deterministic replay is mandatory because inconsistent dispositions are themselves an assurance defect.

## Fail-closed rules

Unknown attack classes, missing or duplicate classes, duplicate case identities, expected-control drift, malformed evidence, unsafe context flags, or container/type mismatches are rejected. AQ12 never mutates the human-policy phase registry and cannot reinterpret its inventory.

## Continuity

AQ12 may produce evidence for the already-authorized sequential AQ9-AQ14 campaign. It does not authorize AQ13 by itself; canonical source qualification, signed materialization where applicable, canonical promotion, post-merge verification, and Padayon reconciliation remain required before the next phase starts.
