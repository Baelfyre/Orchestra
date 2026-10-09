# Adaptive Behavioral Pattern Learning A3

## Status

A0, A1, A2, and the pre-A3 precedence/materialization hardening are canonical on `main`.

Current canonical pre-A3 baseline:

- commit: `8402a5acbafe923c73904dcdb90f7faca90ced9c`;
- tree: `1d56e1623f3662c59817146092c4135e37dd50ed`.

This document defines **A3.0 contract freeze only**. It introduces machine-readable record contracts for future A3 shadow learning, but it does not activate signal extraction, candidate generation, shadow comparison, promotion, routing, specialist selection, strategy selection, model/worker selection, provider integration, training, or recursive/test-time compute.

## Purpose

A3 is intended to identify repeated user preferences and workflow tendencies while preserving Orchestra's deterministic authority envelope.

The core rule is:

```text
SHADOW_LEARNING_MAY_OBSERVE_AND_COMPARE
SHADOW_LEARNING_MUST_NOT_CONTROL_EXECUTION
```

A3 may eventually produce evidence-backed candidate patterns. During shadow mode, those candidates are evaluated beside the deterministic path rather than being inserted into it.

## Separation from A1 and A2

A1 remains the canonical local adaptive-memory evidence/profile substrate. A2 remains the opt-in read-only specialist context consumer.

A3 shadow state is intentionally separate:

```text
A1 validated observations / governed evidence
  -> future A3 signal extractor
  -> A3 shadow signal log
  -> future candidate learner
  -> A3 shadow candidate state
  -> future shadow comparator
  -> A3 shadow comparison log

existing deterministic Orchestra path
  -> actual execution choice
  -> governed execution
  -> outcome evidence

A3 shadow state
  -/-> A1 materialized profile
  -/-> A2 specialist context
  -/-> routing
  -/-> execution authority
```

A3.0 defines no bridge that appends inferred candidates into the A1 observation log. It also defines no path for A2 to consume A3 shadow state.

This separation prevents an experimental learner from becoming advisory or execution-effective merely because it can generate a plausible candidate.

## Machine-local persistence

A3 shadow records inherit the A1 machine-local persistence boundary.

Default adaptive root:

`~/.orchestra/adaptive`

Optional environment override:

`ORCHESTRA_ADAPTIVE_HOME`

A3 shadow-relative root:

`shadow/a3`

Intended record forms:

- signals: append-only JSONL;
- candidate state: derived or versioned local JSON;
- comparisons: append-only JSONL.

Normal shadow learning must not create repository diffs.

SQLite remains deferred until scale, query complexity, or concurrency evidence justifies it. TOON remains derived and non-authoritative if introduced later.

## Shadow signal contract

The canonical A3.0 signal schema is:

`machine/schemas/adaptive-shadow-signal.schema.json`

Allowed signal families are bounded to:

- user selection;
- user rejection;
- user correction;
- specialist strategy accepted/rejected when an actual strategy-decision artifact exists;
- validation outcome;
- remediation requirement;
- iteration outcome;
- governed terminal disposition;
- trustworthy measured latency;
- trustworthy measured cost.

### Evidence boundary

Raw conversation text is not authoritative A3 learning evidence.

A signal must reference a validated source with a stable reference and digest. Permitted source families include A1 validated observations, governed retrospectives, explicit strategy-decision evidence, validation evidence, remediation evidence, and trustworthy measured telemetry.

A generic successful phase or task does **not** prove that a particular specialist strategy succeeded. Strategy signals require a strategy-decision artifact identifying the strategy that was actually chosen.

Likewise, latency and cost are usable only when they were actually measured by a trustworthy source. Missing values remain missing. A3 must not estimate them and label the estimates as observations.

## Shadow candidate contract

The canonical A3.0 candidate schema is:

`machine/schemas/adaptive-shadow-candidate.schema.json`

Candidate types are limited to:

1. user preference tendency;
2. workflow tendency;
3. specialist strategy tendency.

Every candidate remains `shadow_only=true` and `promotion_state=NOT_PROMOTED`.

The schema deliberately does not contain a `CONFIRMED` candidate status. Allowed states are:

- `CANDIDATE`;
- `BLOCKED_BY_EXPLICIT_PREFERENCE`;
- `REJECTED`;
- `DEPRECATED`.

A future candidate learner must require at least **two distinct supporting signals**. Duplicate evidence cannot satisfy the distinct-support requirement.

A single task-specific choice may remain evidence, but it cannot become a durable shadow candidate by itself.

## Confidence semantics

A3 confidence is evidence metadata, not authority.

```text
0.0 <= confidence <= 1.0
confidence != permission
confidence != promotion
confidence != execution authority
```

A3.0 defines no universal confidence threshold and no threshold-triggered promotion.

Future A3 implementation may define a deterministic evidence-accumulation method under a separately reviewed learner rule, but crossing a numerical value must never by itself confirm a pattern or activate it.

## Explicit preference dominance

The canonical precedence established by A1/A2 and strengthened by the pre-A3 hardening remains unchanged:

```text
Governance / hard authority
  > explicit current instruction
  > explicit scoped preference
  > confirmed learned pattern
  > inferred candidate
  > deterministic default
```

A3 adds another safety rule:

> A shadow candidate conflicting with an applicable explicit preference must be marked blocked, not substituted for the explicit preference.

If the explicit preference is later removed, the blocked candidate does not silently reactivate. New post-removal evidence is required to form a new candidate.

## Scope isolation

A3 retains the A1 scopes:

1. `global_user`;
2. `project`;
3. `specialist`;
4. `task_session`.

User identity is always exact. Project, specialist, and task/session constraints are exact when present.

Cross-user, cross-project, cross-specialist, and cross-task leakage fails closed.

## Non-learnable subjects

A3 may not create signals or candidates that attempt to learn or relax:

- authority;
- capability;
- required specialist ownership;
- governance;
- human approval gates;
- security prohibitions;
- mandatory validation;
- evidence integrity;
- audit requirements;
- fail-closed behavior;
- exact-head rules;
- release or merge gates;
- privacy restrictions;
- provider restrictions;
- resource ceilings.

Historical acceptance never creates permission.

## Shadow comparison contract

The canonical A3.0 comparison schema is:

`machine/schemas/adaptive-shadow-comparison.schema.json`

A future comparator records:

- the candidate identity and digest;
- the shadow recommendation;
- the actual deterministic choice;
- the deterministic choice evidence reference;
- match, mismatch, blocked, or non-comparable disposition;
- optional post-execution governed outcome evidence.

The required invariant is encoded directly in the schema:

```text
execution_controlled_by = DETERMINISTIC_ORCHESTRA
shadow_influenced_execution = false
```

Comparisons are evaluation evidence. They do not grant promotion authority.

## Promotion boundary

A3.0 implements no promotion bridge.

It therefore does not:

- append a shadow candidate into the A1 inferred observation lifecycle;
- create a confirmed learned pattern;
- materialize an A3 candidate into the A1 profile;
- expose A3 candidates through A2 context;
- change routing, strategy, worker, or model selection;
- rewrite an active policy after a successful task.

Promotion criteria remain later A3 exit work. Any actual promotion mechanism requires separate authorization and a separate governed transition.

## Required implementation sequence after A3.0

A3.0 freezes contracts only. Later work should remain decomposed:

### A3.1 Signal extraction

Read only governed evidence and explicit user feedback/corrections. Produce validated A3 shadow signals. Do not produce active preferences.

### A3.2 Candidate learner

Aggregate distinct validated signals into scoped shadow candidates. Do not write A1 profile state or A2 context.

### A3.3 Shadow comparator

Compare the candidate's would-have-recommended value against the actual deterministic choice without affecting execution.

### A3.4 Adversarial and correction validation

Prove at minimum:

- one-off choices do not become durable candidates;
- duplicated evidence does not inflate support;
- conflicting evidence remains reviewable;
- scope leakage fails closed;
- explicit preference dominance holds;
- explicit correction blocks conflicting candidates;
- stale or invalid evidence fails closed;
- strategy success is not inferred from generic phase success;
- unmeasured latency/cost is not invented;
- shadow recommendations do not change execution;
- A1 materialized profiles and A2 context remain untouched;
- authority, capability, governance, and mandatory gates remain unchanged.

### A3 exit

A3 exit may define promotion criteria based on validated shadow evidence, but actual promotion remains a separately authorized transition.

## A4+ boundary

A3.0 does not authorize:

- execution-effective specialist strategy ranking;
- model or worker selection;
- adaptive route ranking;
- Tuner topology learning;
- adaptive context routing;
- offline active-policy promotion;
- provider integration or training;
- recursive/test-time compute.

Those remain A4 through A8 work under issue #340.

## Machine contract

The phase contract is:

`machine/adaptive/a3-shadow-learning-contract.v1.json`

It is the machine-readable statement of this A3.0 boundary. Git identity and protected validation determine whether a candidate revision is canonical; this document does not grant its own promotion authority.
