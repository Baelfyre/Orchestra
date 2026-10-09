# Requirements Traceability Guide

## Purpose

Use this guide when Scribe must maintain an evidence-backed connection between why a system exists, what it is expected to do, what was implemented, how it was evaluated, and what documentation may truthfully claim.

Traceability is documentation evidence. It does not grant implementation, governance, architecture, QA, release, or approval authority.

## Generic traceability chain

Use only the nodes relevant to the project:

`Problem -> Objective -> Research Question / Business Goal -> Requirement -> Domain Concept / Use Case -> Design Decision -> Architecture / Model -> Implementation -> Test / Evaluation -> Evidence -> Documented Claim`

Reverse tracing must also be possible when the corresponding nodes exist:

`Documented Claim -> Evidence -> Test / Evaluation -> Implementation -> Requirement -> Objective -> Problem`

A missing node must be recorded as `NOT_APPLICABLE`, `MISSING_EVIDENCE`, or `UNRESOLVED` rather than fabricated.

## Recommended identifiers

Use stable local identifiers when the project does not already provide them:

- `PRB-###` problem or problem statement;
- `OBJ-###` objective;
- `RQ-###` research question;
- `REQ-###` requirement;
- `UC-###` use case or scenario;
- `DEC-###` design decision;
- `IMP-###` implementation evidence item;
- `TST-###` test or evaluation item;
- `EVD-###` evidence item;
- `CLM-###` documented claim.

Do not replace existing repository, institution, issue, ticket, or requirement identifiers merely to match this pattern.

## Traceability record

A useful record contains:

| Field | Meaning |
| --- | --- |
| `id` | Stable local or project-native identifier |
| `type` | Problem, objective, requirement, implementation, evidence, claim, or other supported node |
| `status` | Current lifecycle/evidence status |
| `statement` | Concise human-readable meaning |
| `source` | File, record, specialist output, issue, commit, test, or supplied artifact |
| `links_to` | Forward relationships |
| `derived_from` | Reverse/provenance relationships |
| `owner` | Specialist or project authority that owns the underlying fact |
| `last_verified` | Date or revision when the relationship can drift |
| `notes` | Limitations, conflict, or not-applicable reason |

## State and evidence discipline

Never silently convert:

- `PROPOSED` to `APPROVED`;
- `PLANNED` to `IMPLEMENTED`;
- `IMPLEMENTED` to `VALIDATED`;
- `FAILED` to `PASSED`;
- `SKIPPED` to `PASSED`;
- `NOT_RUN` to `PASSED`;
- `ASSUMED` to `VERIFIED`.

When project lifecycle vocabulary differs, preserve the project-native state and map it explicitly rather than creating a competing state machine.

Useful documentation-facing statuses include:

- `PROPOSED`;
- `APPROVED`;
- `PLANNED`;
- `IMPLEMENTED`;
- `VALIDATED`;
- `DEPRECATED`;
- `SUPERSEDED`;
- `DOC_DRIFT`;
- `IMPLEMENTATION_DRIFT`;
- `MISSING_EVIDENCE`;
- `UNRESOLVED`;
- `NOT_APPLICABLE`.

## Forward trace procedure

For `SPEC_TO_SYSTEM`:

1. establish the problem/objective source;
2. record approved requirements without expanding them;
3. link requirements to domain/use-case narrative;
4. attach specialist-owned design and architecture decisions when produced;
5. link implemented artifacts after implementation evidence exists;
6. link tests/evaluations supplied or verified by Overseer or the owning validation surface;
7. permit a documented claim only when its evidence chain supports it.

## Reverse trace procedure

For `SYSTEM_TO_DOCS`:

1. identify the candidate documented claim;
2. locate current implementation or runtime evidence;
3. locate tests/evaluations that establish validated behavior, if any;
4. reconstruct the requirement only when supported by approved records or clearly label it as inferred;
5. connect the evidence to objectives/problem statements when those are available;
6. leave unresolved intent visible rather than inventing historical requirements.

## Conflict handling

When two nodes conflict:

- do not pick a winner based solely on recency;
- identify the authority and evidence class of each source;
- route unresolved technical truth to the owning specialist;
- route governance/approval conflicts through Conductor to the appropriate authority;
- mark `DOC_DRIFT` when documentation contradicts current verified implementation/evidence;
- mark `IMPLEMENTATION_DRIFT` when verified implementation departs from an approved specification without a documented supersession or accepted change;
- mark `UNRESOLVED` when the direction of correction is not yet authorized.

## Minimum quality checks

A traceability artifact passes Scribe review when:

- no strong claim has an invented link;
- reverse navigation is possible for validated claims;
- not-applicable nodes are explicit;
- drift is visible rather than silently repaired;
- specialist-owned technical facts retain attribution;
- current state and historical intent are not conflated;
- evidence locations are precise enough to re-check later.
