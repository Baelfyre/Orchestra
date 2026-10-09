# Model Traceability and Invalidation Guide

Use this guide to evaluate whether a diagram remains a faithful projection of current source facts.

## Model Ledger

Record diagram type, model revision, source revision, source facts used, owning specialist for each fact, notation/parser version, generated artifact identity, validation result, and last verified time. A visually plausible diagram is not evidence that its relationships are current.

## Contradiction and Unknowns

Do not choose between conflicting source facts. Mark the affected nodes or edges `CONTRADICTED` and route the conflict through Conductor to the owning specialists. Represent missing facts as `UNKNOWN` or omit them with an explicit limitation; never invent a connector to complete the picture.

## Invalidation

Invalidate dependent diagram evidence when an entity, boundary, actor, flow, cardinality, state transition, security zone, deployment fact, or source revision changes. Cosmetic layout-only changes do not invalidate semantic evidence if the model graph is unchanged.

Return `DIAGRAM_CURRENT`, `DIAGRAM_STALE`, `SOURCE_CONTRADICTION`, or `SOURCE_FACTS_INCOMPLETE`. Weaver corrects notation and projection only after owners resolve domain facts.

## Validation

Check parser/render success, source-to-element coverage, labels and legends, edge direction, cardinality, alternative/error flows, and accessibility of the rendered result. Record skipped tooling and unsupported notation. Diagram validation is not architecture, database, security, or transition approval.
