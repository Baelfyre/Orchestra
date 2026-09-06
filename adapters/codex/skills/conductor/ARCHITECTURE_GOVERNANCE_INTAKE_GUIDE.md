# Architecture Governance Intake and Route Composition Guide

## Purpose

This guide gives Conductor a deterministic intake vocabulary for changes that
may affect architecture, capacity, tenancy, persistence, product intent,
security, or validation. It is progressive-disclosure knowledge for the
existing `Routing Plan` output. It does not add a new frozen output format or
grant authority to Conductor or to a routed specialist.

The canonical machine record is
the [canonical ArchitectureGovernanceIntake schema](https://github.com/Baelfyre/Orchestra/blob/main/machine/schemas/architecture-governance-intake.v1.schema.json):

```text
ArchitectureGovernanceIntake
owner = conductor
```

The record classifies and sequences work. It does not decide whether a
component, migration, security control, product direction, or validation claim
is correct.

## 1. Intake contract

Every formal intake records these fields using only the canonical values:

| Field | Values | Routing meaning |
| --- | --- | --- |
| `change_materiality` | `TRIVIAL`, `STANDARD`, `ARCHITECTURAL`, `PRODUCTION_CRITICAL` | How much governance and sequencing the change may need |
| `capacity_relevance` | `NONE`, `KNOWN`, `UNKNOWN`, `CHANGED` | Whether workload context affects the present decision |
| `capacity_context_disposition` | `NOT_REQUIRED`, `SUFFICIENT`, `PARTIAL`, `PROMPT_REQUIRED`, `MEASUREMENT_REQUIRED`, `BLOCKING_FOR_CLAIM` | What to do with the available capacity evidence |
| `complexity_delta` | `NONE`, `LOW`, `MATERIAL` | Whether the proposed change may add material architectural complexity |
| `tenancy_impact` | `NONE`, `POSSIBLE`, `CONFIRMED` | Whether tenant or organizational isolation is implicated |
| `persistence_impact` | `NONE`, `DEVELOPMENT_ONLY`, `PRODUCTION_COMPATIBILITY`, `HIGH_RISK` | Whether Chronicler must review persistence consequences |
| `product_decision` | `NONE`, `REQUESTED_SOLUTION`, `STRATEGIC_CHANGE` | Whether product intent must be aligned before technical selection |
| `security_impact` | `NONE`, `POSSIBLE`, `MATERIAL` | Whether Cipher must review technical security or privacy controls |
| `validation_impact` | `NORMAL`, `CONTRACT_DERIVED`, `EMPIRICAL_REQUIRED` | Whether ordinary or evidence-specific validation is needed |

`authority_notice` and `evidence_refs` are optional. When present, they must
retain the evidence and authority boundaries that motivated the classification.

The intake is embedded in the existing Routing Plan:

```markdown
## Architecture Governance Intake

change_materiality: ...
capacity_relevance: ...
capacity_context_disposition: ...
complexity_delta: ...
tenancy_impact: ...
persistence_impact: ...
product_decision: ...
security_impact: ...
validation_impact: ...
evidence_refs: ...
authority_notice: Routing metadata does not create or expand authority.
```

The machine payload remains schema-conformant. A prose route may explain
missing evidence, but it must not add unrecognized machine enum values.

## 2. Classification order

Classify the request in this order, then compose only the route that the
classification requires:

1. Identify whether a Conductor-selected direct single-specialist fast route still suffices.
2. Classify materiality and the actual change, not a keyword in isolation.
3. Separate a business problem or strategic shift from a requested solution.
4. Determine which capacity fact, if any, changes the current decision.
5. Mark complexity only for an actual architectural or operational addition.
6. Identify tenancy, persistence, security, and validation implications.
7. Sequence upstream decisions and evidence before implementation.

Words such as `Redis`, `Kafka`, `Kubernetes`, `microservices`, `tenant`,
`migration`, or `production` are triggers for contextual inspection. They are
not decisions, risk ratings, approval, or implementation instructions.

## 3. Change materiality

### `TRIVIAL`

Use for an isolated typo, label change, local variable rename, or similarly
non-architectural correction. After Conductor selects one direct specialist,
avoid a governance stack, capacity elicitation, or Tuner activation when no
additional trigger exists. The fast route remains Conductor-owned.

### `STANDARD`

Use for an ordinary feature, bounded refactor, development-only persistence
change, or established-pattern implementation. Route the specialist that owns
the actual decision. Add governance only when a material impact is present.

### `ARCHITECTURAL`

Use when the requested change proposes or evaluates a service, cache, queue,
worker, database, replica, multi-region topology, tenant model, or substantial
boundary change. Architecture governance is required, but Clockwork decides
whether the architecture is justified.

### `PRODUCTION_CRITICAL`

Use for live-data migration, production tenant-isolation change, critical
distributed-topology change, or a high-risk schema transition. Compose the
minimum applicable specialist chain and preserve existing human and evidence
gates.

## 4. Adaptive capacity routing

Conductor never runs a universal workload questionnaire. It identifies the
smallest missing value that can change the current decision and sends that
dependency to The Steward. The Steward owns business and workload intent.

| Relevance | Disposition | Conductor behavior |
| --- | --- | --- |
| `NONE` | `NOT_REQUIRED` | Do not ask capacity questions. |
| `KNOWN` | `SUFFICIENT` | Reuse the current authoritative values and their evidence. Do not re-prompt. |
| `UNKNOWN` | `PROMPT_REQUIRED` | Ask The Steward for only the decision-changing value when a stakeholder can provide it. |
| `UNKNOWN` in a prototype or reversible change | `MEASUREMENT_REQUIRED` or `PARTIAL` | Permit the simplest reversible path and identify the measurement needed before scale provisioning. |
| `CHANGED` | `PARTIAL`, `PROMPT_REQUIRED`, or `MEASUREMENT_REQUIRED` | Detect the changed assumption and route the affected decision. Do not perform OR-GOV-6 invalidation. |
| material missing evidence for a quantified claim | `BLOCKING_FOR_CLAIM` | Route to Overseer for empirical evidence. Do not state quantified sufficiency. |

Preserve exact values, ranges, estimates, observations, unknowns, and
`TO_BE_MEASURED` states from `CapacityEnvelope`. Never average a range,
invent traffic, or turn an unknown into a safe number. A partial envelope can
support a reversible decision when the missing values do not affect that
decision.

Example:

```text
"Should we add a queue for burst traffic?"
```

Ask about peak arrival rate, processing duration, and burst shape only if the
queue decision depends on them. Do not ask about tenant count, storage, or
latency unless those facts affect this decision.

For a claim such as `this architecture supports 300 RPS`, missing benchmark or
measurement evidence produces `EMPIRICAL_REQUIRED` and
`BLOCKING_FOR_CLAIM`. The result is `NOT_PROVEN`, not a fabricated pass or
failure.

## 5. Product and strategic intent

Use `product_decision = NONE` when the request is already an aligned technical
task with no unresolved product choice.

Use `REQUESTED_SOLUTION` when a stakeholder names a mechanism such as Redis,
Kafka, or a loop. Route the underlying problem and desired outcome to The
Steward before accepting the mechanism. Preserve:

```text
PROBLEM != REQUESTED_SOLUTION
```

Use `STRATEGIC_CHANGE` for a change such as single-client to SaaS,
single-school to multi-school, or internal tool to public platform. The
Steward aligns the product boundary before Clockwork stabilizes architecture.

Conductor does not accept, reject, or redesign the product decision.

## 6. Complexity and capacity-neutral architecture

Set `complexity_delta = MATERIAL` only when an actual material boundary or
infrastructure addition is proposed. A vague request to scale without a
component proposal does not justify provisioning.

When complexity is implicated, route Clockwork. Clockwork owns
`ArchitectureComplexityDecision`, simpler alternatives, and
`SCALE_READY` versus `SCALE_PROVISIONED`. Conductor preserves the invariant:

```text
FUTURE_SCALABILITY_ALONE_IS_NOT_SUFFICIENT_JUSTIFICATION
```

A capacity-neutral, reversible route may continue while evidence is gathered.
Conductor must not decide that Redis, a queue, a service split, Kubernetes, a
replica, or multi-region deployment is warranted.

## 7. Tenancy and persistence routing

Use `tenancy_impact = NONE` for a confirmed lifetime single-tenant boundary,
`POSSIBLE` for future organizational expansion whose architecture is not yet
mandated, and `CONFIRMED` for an accepted tenant-aware change.

Do not equate a possible future customer with a mandated multi-tenant design.
Route:

```text
possible future expansion, intent unresolved -> the-steward
confirmed tenant persistence change -> clockwork -> chronicler
confirmed tenant isolation with security impact -> clockwork -> chronicler -> cipher
```

Use `persistence_impact = DEVELOPMENT_ONLY` for an explicitly empty local or
test database. Use `PRODUCTION_COMPATIBILITY` for live-version compatibility,
backfills, index operations, or other production persistence transitions. Use
`HIGH_RISK` for destructive, irreversible, live large-table, or unknown
rollback-boundary changes.

If production presence is unknown, do not classify the change as confirmed
development-only and do not emit `production_data = false`. Conductor may
route to Chronicler with:

```text
persistence_impact = PRODUCTION_COMPATIBILITY
PRODUCTION_PRESENCE_UNRESOLVED
CHRONICLER_PRECONTRACT_SCHEMA_GAP_APPLIES
```

This is a routing classification, not proof that production data exists. The
OR-GOV-4 `MigrationRiskContract` v1 schema gap remains unchanged. OR-GOV-5
does not amend that schema or invent a tri-state value inside its boolean
field.

## 8. Security and validation routing

Use `security_impact = NONE` when no security or privacy-control boundary is
implicated. Use `POSSIBLE` for a concern that needs scoped review and
`MATERIAL` for tenant isolation, authorization, sensitive-field movement,
secrets, payments, privacy-sensitive flows, or destructive user actions.
Cipher decides security policy and technical controls. Conductor only routes.

Use `validation_impact = NORMAL` for ordinary checks,
`CONTRACT_DERIVED` when existing upstream contracts create validation
obligations, and `EMPIRICAL_REQUIRED` for performance, capacity, or other
claims that require observation. Overseer owns evidence and readiness
conclusions. Conductor must not turn a missing benchmark into `PASS`.

## 9. Minimum route composition

The route is a conditional composition, not a universal pipeline:

| Decision dependency | Minimum sequence |
| --- | --- |
| Product or strategic intent unresolved | `the-steward` -> `clockwork` when architecture is actually needed |
| Capacity must be supplied by a stakeholder | `the-steward` -> `clockwork` when architecture follows |
| Capacity must be measured | `the-steward` -> `overseer` -> `clockwork` when architecture follows |
| Architecture boundary changes | `clockwork` -> `ponytail` after the boundary is ready |
| Persistence semantics change | `chronicler` -> `ponytail` after persistence guidance is accepted |
| Security requirements affect implementation | `cipher` -> `ponytail` |
| Validation evidence is required before a claim | `overseer` before any readiness or sufficiency claim |

Add a specialist only when its owned decision or evidence is implicated. A
simple UI copy change may use a Conductor-selected direct Cloak or
implementation route. A development-only nullable column may use a
Conductor-selected Chronicler route without a production compatibility stack.
A live tenant migration may route Chronicler and Cipher, with Clockwork only
when an architectural boundary is also changing.

Use The Tuner only through the existing Conductor coordination boundary when
multiple specialist contracts need coordination. OR-GOV-5 does not implement
semantic dependency invalidation, propagation, or minimal re-entry; those are
OR-GOV-6 concerns.

Use Arbiter only through its existing continuity and transition contract.
Conductor consumes supported dispositions but does not invent them or replace
Arbiter freshness decisions.

## 10. Dagger and implementation boundaries

Requests for destructive or resilience simulation remain with Dagger only
when the explicit authorization and guardrail are present. Without them,
classify the route as blocked and keep Dagger unpromoted. OR-GOV-5 never
expands Dagger authority.

Conductor may route to Ponytail only after the required upstream decisions and
contracts are ready. Ponytail implements bounded changes. Conductor does not
execute migrations, production SQL, destructive actions, deployment, release,
policy activation, or provider operations.

## 11. Authority notice and evidence

Every formal intake carries the following notice or an equivalent statement:

```text
Classification does not grant implementation authority.
Classification does not authorize deployment, destructive action, release,
policy activation, production mutation, or installed-integration refresh.
```

Evidence references identify why a classification was made. They do not
become authority merely by appearing in a route. Contradictory, stale, or
missing evidence pauses the applicable workflow and returns the question to
the owning specialist or governance authority.

## 12. Compact examples

| Request | Key intake result | Minimum route |
| --- | --- | --- |
| `Build it so it can scale.` | Architectural context, capacity `UNKNOWN`, no component assumed | Steward for the missing decision-changing context; Clockwork only if architecture is proposed |
| `Add Redis because we might need it later.` | `REQUESTED_SOLUTION`, complexity `MATERIAL`, capacity `UNKNOWN` | `the-steward` -> `clockwork` |
| `20 tenants now; 200 in 12 months; 300 messages per tenant per day.` | Capacity `KNOWN`, disposition `SUFFICIENT` | Reuse evidence; do not re-prompt |
| `Add tenant_id to several million live rows while writes continue.` | `PRODUCTION_CRITICAL`, tenancy `CONFIRMED`, persistence `HIGH_RISK` | Chronicler and Cipher; add Clockwork only for an architecture boundary |
| `Add an optional nullable column to an empty local database.` | `STANDARD`, persistence `DEVELOPMENT_ONLY` | Chronicler only as needed |
| `This architecture supports 300 RPS.` without a benchmark | validation `EMPIRICAL_REQUIRED`, disposition `BLOCKING_FOR_CLAIM` | Overseer for evidence |
| `We need a schema change but do not know whether production data exists.` | production presence unresolved; never `production_data = false` | Chronicler with the pre-contract schema-gap notice |

The smallest correct route wins. A green route, schema-valid payload, or
successful validation run remains evidence, not authority.
