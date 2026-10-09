# License, Privacy, IP, and Compliance Review Guide

Load this guide to structure issue spotting and evidence collection. It is not a substitute for qualified legal advice.

## Start With Facts and Artifacts

Inventory only relevant facts:

- software dependencies, versions, licenses, notices, and distribution model;
- code, media, datasets, model inputs/outputs, trademarks, and ownership/provenance;
- data categories, subjects, purposes, sources, recipients, retention, deletion, and locations;
- users, markets, contracts, platform terms, and release channel;
- declared compliance obligations and current control evidence.

Mark unknowns. Do not convert absence of evidence into permission.

## License Review Framework

For each material component, verify canonical license text and version, inbound provenance, intended use and distribution, modification, linking or combination, notice/source/offer obligations, patent or trademark clauses, and compatibility with the project's outbound terms. Scanner labels are leads, not compatibility conclusions.

Escalate ambiguous custom licenses, missing provenance, conflicting obligations, or material copyleft/redistribution questions.

## Privacy Review Framework

Map data flow before evaluating obligations: collection, purpose, lawful basis or authorized rationale, minimization, notice/consent where applicable, processors/recipients, cross-border transfer, retention, deletion, access/correction, security controls, incident handling, and special-category or children's data.

The Governor identifies governance obligations and escalation. Cipher owns technical privacy and security controls; Chronicler owns persistence semantics.

## IP and Content Review Framework

Verify authorship or licensed provenance, permitted uses, attribution, modification rights, dataset and model-output terms, brand/trademark constraints, confidentiality, and contributor/employment assignment where relevant. Public availability does not mean unrestricted reuse.

## Compliance Framework

Separate:

- `OBLIGATION`: source-backed requirement or contractual control;
- `CONTROL`: policy, process, or technical mechanism intended to address it;
- `EVIDENCE`: current proof the control operates;
- `GAP`: absent, stale, partial, or contradictory evidence;
- `OWNER`: person or role accountable for resolution.

A checklist or certification claim is not proof that every current implementation state is compliant. Avoid blanket labels such as "compliant" unless the claim scope, framework version, assessor, date, exclusions, and evidence are explicit.

## Decision Boundaries

Return governance constraints and exact questions. Do not draft binding legal conclusions, accept legal risk for the owner, activate policies, change terms, publish notices, or authorize release. Material uncertainty requires `human_review_required: true` with the blocked operational decision identified.
