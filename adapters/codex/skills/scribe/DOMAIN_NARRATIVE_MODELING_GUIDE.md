# Domain Narrative Modeling Guide

## Purpose

Use this guide when Scribe must turn verified project evidence, a problem statement, stakeholder input, or an existing system into a maintainable domain narrative without taking over architecture, persistence, UML, security, QA, UI, governance, or implementation ownership.

Domain narrative is a documentation artifact. It explains the language, actors, processes, rules, states, constraints, and boundaries of the problem space. It may identify candidate concepts for later specialist modeling, but it is not itself a formal architecture, class model, database schema, or UML model.

## Evidence-first rule

Every asserted domain fact must be classified as one of:

- `OBSERVED`: directly visible in source, configuration, runtime evidence, approved records, or supplied artifacts.
- `APPROVED`: explicitly accepted requirement, policy, objective, or business rule.
- `INFERRED`: a plausible interpretation supported by evidence but not independently confirmed.
- `HISTORICAL`: evidence of prior intent or behavior that may not describe current implementation.
- `UNRESOLVED`: conflicting or insufficient evidence.
- `NOT_APPLICABLE`: intentionally outside the project or artifact scope.

Never present `INFERRED`, `HISTORICAL`, or `UNRESOLVED` content as current verified truth.

## Recommended domain narrative

Include only relevant sections:

1. **Context**: problem environment, system boundary, and why the domain matters.
2. **Vocabulary and glossary**: preferred terms, synonyms, ambiguous terms, and terms to avoid.
3. **Stakeholders and actors**: who participates, who is affected, and documented responsibilities.
4. **Processes and workflows**: current or intended business/process flow described in prose.
5. **Business rules**: constraints or policies supported by approved evidence.
6. **Events and state changes**: notable occurrences and lifecycle transitions when evidence exists.
7. **Candidate concepts**: nouns or concepts that may need formal modeling later.
8. **Relationships**: evidence-backed relationships between candidate concepts.
9. **Assumptions and constraints**: explicit limits, unresolved assumptions, external dependencies, and jurisdictional or institutional constraints.
10. **External systems**: verified integrations or external actors without inventing interface semantics.
11. **Scope boundaries**: in-scope, out-of-scope, deferred, and not-applicable areas.
12. **Traceability**: links from domain statements to objectives, requirements, source artifacts, specialist outputs, or evidence.

## Candidate-concept rule

Noun extraction is discovery only. Do not automatically convert nouns into:

- classes;
- entities;
- aggregates;
- tables;
- services;
- modules;
- components.

When formal technical modeling is required:

- route architecture and bounded-context decisions to **Clockwork**;
- route persistence/entity/schema decisions to **Chronicler**;
- route formal UML/ERD notation to **Weaver**;
- route implementation to **Ponytail** or the routed implementation specialist.

Scribe may document the resulting verified model after those owners define it.

## Existing-system reconstruction

For `SYSTEM_TO_DOCS`, reconstruct the domain from evidence in this order where available:

1. public behavior and user-visible workflows;
2. tests and acceptance evidence;
3. source/configuration contracts;
4. persistence/data semantics verified by Chronicler when needed;
5. architecture boundaries verified by Clockwork when needed;
6. current documentation and historical records;
7. commit or release history when intent cannot be established from current source.

If current implementation and historical intent disagree, document both and mark the relationship explicitly. Do not rewrite history to make it appear consistent.

## Domain narrative quality checks

Before finalizing:

- terminology is internally consistent;
- every strong claim has evidence or an explicit status label;
- current behavior is separated from desired behavior;
- candidate concepts are not silently promoted into technical models;
- specialist-owned facts remain attributed to the owning specialist or source;
- unresolved contradictions remain visible;
- scope boundaries are explicit;
- the narrative can be traced back to the problem/objective or forward to requirements where those artifacts exist.
