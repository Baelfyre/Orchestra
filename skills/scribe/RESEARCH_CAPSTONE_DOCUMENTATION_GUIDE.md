# Research and Capstone Documentation Guide

## Purpose

Use this guide when Scribe must document a research-backed software project, capstone, thesis-like system study, prototype evaluation, or implementation-led research record.

This guide is intentionally institution-neutral. The user's institution, course, adviser, panel, ethics office, research office, rubric, required template, and submission rules remain authoritative when supplied.

Do not force a Chapter 1-5 structure when the governing template differs.

## Core principle

Research documentation and system development may proceed in more than one valid order. Scribe must represent the actual evidence trail instead of rewriting the project into an idealized sequence.

Supported patterns include:

### Plan first

`Problem -> Research -> Requirements -> Design -> Build -> Test -> Results`

### Prototype first

`Idea -> Prototype -> Observe -> Formalize Problem -> Evaluation -> Refine -> Evidence -> Research Documentation`

### Existing system

`Existing App -> Audit -> Reconstruct Requirements / Domain -> Determine Evaluatable Claims -> Evaluation -> Documentation`

### Continuous

`Requirement Change -> Implementation Change -> Test Change -> Evidence Change -> Documentation Change`

## Adaptable research concepts

Use only the concepts required by the governing project or research design:

- research or project problem;
- research questions;
- general and specific objectives;
- scope, delimitations, and limitations;
- stakeholders, users, participants, or data subjects;
- related literature;
- related systems;
- conceptual, domain, or system framework;
- requirements;
- methodology;
- system design;
- implementation record;
- evaluation method;
- evaluation criteria;
- data and evidence;
- results;
- discussion;
- conclusions;
- recommendations;
- future work;
- appendices and project artifacts;
- citation and source provenance.

Scribe may reorganize these concepts to match the required institutional structure without changing their factual meaning.

## Evidence separation

Keep these evidence classes separate:

- **Research-source evidence**: literature, official standards, regulations, prior studies, related systems, datasets, and externally published material.
- **Project evidence**: requirements, source files, configuration, commits, schemas, tests, screenshots, runtime records, benchmark outputs, surveys, interview records, and approved project decisions.
- **Specialist evidence**: architecture from Clockwork, data semantics from Chronicler, security/privacy controls from Cipher, formal diagrams from Weaver, UI facts from Cloak, validation evidence from Overseer, and governance decisions from the applicable governance authority.
- **Interpretation**: analysis or discussion derived from evidence. It must not be mislabeled as raw evidence.

AI-generated prose is not evidence by itself.

## Claim discipline

Research conclusions must come from evidence.

A pre-existing system may inform research questions and evaluation design, but Scribe must never reverse-engineer a convenient conclusion from an already-built feature.

Do not silently convert:

- a feature description into proof of effectiveness;
- implementation completion into research validation;
- user feedback into a statistically generalizable conclusion;
- a benchmark into human usability evidence;
- a related study into proof that the current implementation works;
- a planned evaluation into completed results.

Unsupported or incompletely supported statements must be marked `MISSING_EVIDENCE`, `PENDING_VALIDATION`, `INFERRED`, or the project's equivalent.

## Literature and related-work handling

For each external source, preserve at minimum when available:

- stable title and author/organization identity;
- publication venue or issuing body;
- publication/revision date;
- stable URL, DOI, repository identifier, or equivalent locator;
- what claim or design question the source informs;
- whether the material was used as a reference, dataset, implementation source, standard, or comparison point;
- license/reuse status when source text, data, code, figures, templates, or other protected material may be incorporated.

Citation does not automatically authorize copying. Public availability does not automatically authorize reuse. Route legal, licensing, privacy-obligation, or IP interpretation to **The Governor** through **Conductor**.

When consulting standards or formal methodologies, summarize concepts in original Orchestra wording. Do not reproduce substantial copyrighted standards text or institutional templates.

Useful reference families may include software/system requirements, documentation lifecycle, architecture-description, UML/modeling, systems-engineering, academic reporting, and reproducibility guidance, but the exact source must be verified before making source-specific claims.

## Capstone evidence map

A useful evidence map can link:

| Research/System Item | Status | Evidence | Owner/Source | Claim Allowed? | Limitation |
| --- | --- | --- | --- | --- | --- |
| Problem | | | | | |
| Objective | | | | | |
| Requirement | | | | | |
| Implementation | | | | | |
| Evaluation | | | | | |
| Result | | | | | |
| Documented claim | | | | | |

Delete irrelevant rows rather than filling them with generic text.

## System-to-research reconstruction

When documenting an existing system:

1. inventory current implementation and available evidence;
2. distinguish current behavior from historical intent;
3. reconstruct candidate problem/objective/requirement relationships only where supported;
4. identify which claims are actually evaluatable;
5. design or document evaluation only under the proper validation/research authority;
6. preserve negative, null, failed, skipped, and unresolved outcomes;
7. write conclusions only after evidence exists.

## Quality checks

Before finalizing a research/capstone document:

- required institutional structure is satisfied or explicitly unresolved;
- research questions and objectives are not invented from implementation alone;
- system claims trace to project evidence;
- external-source claims trace to source evidence;
- source reuse/copyright constraints are visible where relevant;
- methods are separated from results;
- results are separated from interpretation;
- limitations and missing evidence are explicit;
- failed or null findings remain visible;
- recommendations do not masquerade as completed implementation.
