# Padayon Post-Restructure Repository Realignment Notice

## Purpose

This repository-local notice mirrors the post-restructure Padayon reconciliation requirements so they remain searchable from the Orchestra repository itself.

It is a continuity and source-reality reconciliation guide. It is not an implementation-authority grant, release authorization, deployment authorization, provider-routing authorization, policy activation, or destructive-operation authorization.

## Padayon restructuring state

Padayon completed its governed M0-M6 knowledge-architecture restructuring before this notice was added to Orchestra.

The restructuring established project-centric durable human-knowledge namespaces while preserving the existing distinction between source repositories, operational trackers, derived projections, machine/runtime state, and historical evidence.

The governing precedence remains:

```text
LIVE_SOURCE_REPOSITORY > PADAYON_CONTINUITY_MIRROR
STALE_PADAYON_TRACKER != CURRENT_SOURCE_STATE
NO_FRESH_CANONICAL_READ = NO_PHASE_INFERENCE
APPROVED_DIRECTION != IMPLEMENTATION_AUTHORITY
DERIVED_PROJECTION != AUTHORITATIVE_TRACKER
```

## Required repository realignment procedure

Before continuing a new Orchestra implementation phase after Padayon restructuring:

1. Re-read live `Baelfyre/Orchestra` `main` and the relevant current pull-request/check state.
2. Re-read live `Baelfyre/Padayon` `main` and the current Orchestra continuity surfaces.
3. Compare Padayon's recorded Orchestra state with current canonical Orchestra source reality.
4. Treat live Orchestra source, canonical merge state, exact-head validation evidence, and current governance contracts as authoritative for implementation state.
5. Classify any drift explicitly rather than silently rewriting history.
6. Reconcile Padayon only from evidence-backed source reality.
7. Preserve historical records as history when they are superseded or stale.
8. Refresh derived Padayon projections only through the repository-native compiler/validation tooling.
9. Validate the Padayon reconciliation before treating it as current continuity state.
10. Resume Orchestra only from the actual current canonical boundary. Do not infer the next phase from an older handoff, stale tracker, or historical PR.

Useful drift classifications include:

```text
PADAYON_TRACKER_STALE
MISSING_FROM_PADAYON
PLAN_EVOLVED
IMPLEMENTED_EVOLVED
HISTORICAL_PRECURSOR
SUPERSEDED
DEFERRED
REQUIRES_FRESH_AUTHORIZATION
```

## Post-restructure Padayon routing relevant to Orchestra

The current separation of concerns is:

- `Baelfyre/Orchestra` remains authoritative for Orchestra source-code reality, implementation state, repository governance, validation evidence, and release state.
- `implementation-phase-prompts/orchestra/current-tracker.json` remains Padayon's detailed authoritative Orchestra operational continuity tracker.
- `projects/orchestra/` contains lifecycle-oriented durable human knowledge such as approved direction and delivery/source-reality records.
- `padayon/projects/orchestra/projection.json` remains derived/read-only and must not be treated as the authoritative human project-knowledge source.
- historical or compatibility records may remain in older paths, but stale location or age does not create current authority.

## Current Orchestra reconciliation checkpoint

At the time this notice was added, live Orchestra source reality had already advanced beyond the older CUIR-1 handoff.

```text
ORCHESTRA_CANONICAL_HEAD = c2fc34943c528e05123ae57d34a490a33152a936
ORCHESTRA_CANONICAL_TREE = 48e45f760224cee381fa78da950425ab9161aa1f
AR_2_SHARED_CANONICALIZATION = COMPLETE_CANONICAL_VERIFIED
AR_2_DOMAIN_EXTRACTION = CURRENT
AR_2_DOMAIN_CONTEXT_EXTRACTION = READY_NOT_STARTED
AR_3_STARTED = false
PUBLIC_RELEASE = v1.7.0
V1_8_PUBLICATION = HELD_FOR_EXPLICIT_FINAL_REVIEW
```

These identifiers are evidence checkpoints, not permanent anchors. Every future mutation must begin with a fresh live read.

## Search and discovery keywords

This document intentionally includes the following repository-search terms:

```text
Padayon post-restructure
Padayon M0-M6
knowledge architecture restructuring
repository realignment
source reality reconciliation
source-reality reconciliation
stale Padayon tracker
current-tracker.json
projects/orchestra
Padayon projection
approved direction
implementation authority
canonical source read
fresh canonical read
AR-2 Domain Extraction
AR-2 domain context extraction
Orchestra Padayon reconciliation
continuity mirror
```

## Non-authority boundary

This notice does not itself authorize:

- AR-2 source mutation beyond a separately authorized bounded unit;
- AR-3 start;
- release or tag publication;
- deployment or production mutation;
- provider routing or fallback;
- credentials or installed-integration refresh;
- policy or ruleset activation/bypass;
- destructive cleanup;
- branch deletion;
- force push or history rewrite.

The safe rule is:

```text
SEARCHABLE_CONTINUITY_RECORD != EXECUTION_AUTHORITY
LIVE_CANONICAL_STATE OVERRIDES STALE HANDOFF INFORMATION
```
