# Authoritative Source and Effective-Date Verification Guide

Load this guide when a governance review depends on law, regulation, regulator guidance, contract terms, policy, license text, or another time-sensitive authority.

## Source Hierarchy

Prefer the source that actually creates or controls the obligation:

1. enacted law, regulation, court or regulator publication, or official government register;
2. signed contract, current platform terms, or canonical license text;
3. official regulator or standards-body guidance;
4. qualified professional interpretation;
5. reputable secondary explanation;
6. informal commentary or search snippets.

Secondary sources can help locate and understand primary sources, but do not silently replace them. When the primary source is inaccessible, record that limitation and escalate if the decision is material.

## Source Identity Record

Capture:

- title and issuing authority;
- canonical URL or document identifier;
- jurisdiction and territorial reach;
- publication, revision, and effective dates;
- accessed or verified date;
- version, section, clause, or license identifier;
- language and whether a translation is official;
- supersession, amendment, transition, or sunset status;
- exact project fact the source is being used to assess.

Use short compliant excerpts only when necessary. Prefer paraphrase plus pinpoint citation and never store restricted or sensitive source material without authority.

## Applicability Is a Separate Question

A current authoritative source does not prove that it applies. Identify the relevant entity, users, data subjects, processing, location, offering, agreement, distribution model, and effective time. Mark unresolved applicability as `NEEDS_HUMAN_INTERPRETATION`.

Do not infer jurisdiction from repository location, developer residence, hosting region, user language, or a domain label alone.

## Freshness and Conflict Handling

Before relying on a source, check for amendments, later versions, official corrections, transition periods, and conflicts between authorities. Preserve each competing source and the unresolved question. Do not choose the convenient interpretation.

Evidence becomes stale when its source changes, the effective date passes, project facts change, or the reviewed agreement/version no longer governs. Bind findings to `verified_at`, the source revision, and the reviewed project state.

## Output State

Use explicit states such as `VERIFIED_CURRENT`, `SUPERSEDED`, `NOT_EFFECTIVE_YET`, `APPLICABILITY_UNRESOLVED`, `SOURCE_NOT_FOUND`, and `NEEDS_HUMAN_INTERPRETATION`. None of these states is legal advice or policy activation.
