# Domain Narrative Modeling Guide

## Purpose

Use this guide when Scribe must capture or reconstruct a problem domain in documentation before, during, or after implementation.

Scribe owns the **documented domain narrative**: context, vocabulary, stakeholders, business rules, processes, states, assumptions, constraints, and candidate concepts. Scribe does **not** decide software architecture, DDD aggregates, persistence models, database schemas, UML correctness, or implementation structure.

## Core Rule

A domain narrative is evidence-backed documentation, not automatic software design.

Use this progression when it fits the task:

```text
Context
  -> Problem / Opportunity
  -> Stakeholders and Actors
  -> Vocabulary
  -> Rules and Processes
  -> Candidate Concepts
  -> Relationships / Events / States
  -> Constraints and Boundaries
  -> Requirement Links
  -> Specialist Validation
```

Do not force every project through every step.

## Evidence Labels

Classify important statements so readers can distinguish fact from interpretation:

- `OBSERVED`: directly supported by repository, runtime, dataset, document, interview record, or other reviewed evidence.
- `PROVIDED`: explicitly supplied by an authorized stakeholder or governing project source.
- `CANDIDATE`: a useful concept inferred from domain language but not yet technically validated.
- `UNRESOLVED`: available evidence is insufficient or contradictory.

Never silently promote a `CANDIDATE` or `UNRESOLVED` concept into a verified entity, component, table, aggregate, or requirement.

## Domain Narrative Elements

Capture only what is relevant:

### Context and Scope

- real-world environment;
- problem or opportunity;
- affected stakeholders;
- in-scope and out-of-scope concerns;
- external systems or organizations;
- operational, institutional, legal, time, cost, or technology constraints.

### Vocabulary and Ambiguity

Maintain a domain glossary for terms whose meaning matters. Record:

- preferred term;
- definition supported by project evidence;
- aliases or conflicting usage;
- source or evidence reference;
- unresolved ambiguity.

### Actors and Responsibilities

Document actors and responsibilities without converting them automatically into software roles or authorization policy. Security-sensitive roles and permissions require Cipher validation.

### Rules, Processes, Events, and States

Record:

- business rules;
- normal process flow;
- exceptions;
- observable domain events;
- lifecycle states and allowed transitions where evidence supports them;
- assumptions that still require validation.

### Candidate Concept Discovery

Scribe may use nouns, repeated phrases, user language, business records, and workflow steps to discover candidate concepts.

**Noun extraction is a discovery heuristic only.** A noun is not automatically a class, entity, aggregate, table, service, or component.

For each candidate concept, record where useful:

| Field | Meaning |
|---|---|
| Candidate | Domain term or concept |
| Evidence | Where it was observed or provided |
| Possible classification | Actor, entity-like concept, value-like concept, attribute, event, rule, process, context, other |
| Relationships | Other domain concepts it interacts with |
| Open questions | What is not yet known |
| Technical validation owner | Clockwork, Chronicler, Weaver, Cipher, Cloak, or another specialist |

## Problem-to-Objective Mapping

Use a simple mapping when project intent needs structure:

| Problem / Need | Impact | Objective | Candidate Capability | Evidence / Source | Status |
|---|---|---|---|---|---|

Do not treat a candidate capability as implemented until repository evidence supports that state.

## Domain-to-Requirement Handoff

A documented domain concept can inform requirements, but requirements should remain independently identifiable and testable where applicable.

Trace in both directions when evidence exists:

```text
Domain Need -> Objective -> Requirement -> Design / Model -> Implementation -> Validation
Validation -> Implementation -> Requirement -> Objective -> Domain Need
```

Use `NOT_APPLICABLE` where a link legitimately does not exist. Do not fabricate links for completeness.

## Specialist Boundaries

Route technical decisions as follows:

- Clockwork: architecture, service/module boundaries, architectural constraints and decisions.
- Chronicler: persistence semantics, schemas, entities as stored data, normalization, migrations.
- Weaver: formal UML, ERD, system diagrams, model consistency.
- Cipher: security roles, authorization, privacy/security controls.
- Cloak: UX/UI interaction and visible interface behavior.
- Overseer: verification strategy, validation evidence, QA conclusions.
- Ponytail or the appropriate implementation specialist: source-code changes.

Scribe records verified specialist outputs and keeps them traceable to the domain narrative.

## Reference Foundation

This guide is original Orchestra guidance informed by public descriptions of established standards and primary sources. It does not reproduce proprietary standard text.

- ISO/IEC/IEEE 42010 distinguishes an architecture from the architecture description that expresses it. This supports the boundary that Clockwork defines architectural truth while Scribe documents it.
- OMG UML is the formal reference family for UML terminology and modeling concepts. Scribe does not replace Weaver's formal-model ownership.
- Project-specific institutional or domain rules remain authoritative over generic guidance.
