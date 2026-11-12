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

Escalate ambiguous custom licenses, conflicting obligations, and material copyleft or redistribution questions. Escalate missing or materially incomplete provenance when it leaves ownership, permission, or attribution unresolved, or when an applicable legal, contractual, license, or mandatory governance requirement requires that evidence. After proportionate review of available authorship and provenance, applicable terms, permitted use, and any identified similarity, inability to reconstruct every intermediate AI-generation step alone is not a material provenance gap if no concrete conflict or material uncertainty remains and no applicable mandatory gate remains open. This classification does not clear or displace any separate human-review trigger, including the public-release compliance trigger.

## Privacy Review Framework

Map data flow before evaluating obligations: collection, purpose, lawful basis or authorized rationale, minimization, notice/consent where applicable, processors/recipients, cross-border transfer, retention, deletion, access/correction, security controls, incident handling, and special-category or children's data.

The Governor identifies governance obligations and escalation. Cipher owns technical privacy and security controls; Chronicler owns persistence semantics.

## IP and Content Review Framework

Verify authorship or licensed provenance, permitted uses, attribution, modification rights, dataset and model-output terms, brand/trademark constraints, confidentiality, and contributor/employment assignment where relevant. Public availability does not mean unrestricted reuse.

## AI-output and Blocking Rights/IP Findings

Either unsupported, unparticularized AI-output similarity concerns or inability to reconstruct every intermediate AI-generation step alone may be recorded as a scoped `RISKS` warning only after proportionate review, when no concrete conflict or material uncertainty remains, every applicable gate independently passes, and no separate `human_review_required` flag is pending. For a transition-ready Governor review, use scoped `APPROVED` with the existing `RISKS` warning only when those conditions hold. Do not use top-level `ADVISORY_ONLY` for this warning; Covenant maps it to `WAIT_FOR_EVIDENCE`.

A blocking rights/IP finding must record:

- affected asset and version, or explicitly `UNKNOWN`;
- proposed action;
- applicable control or gate;
- specific evidence or identified evidence gap;
- material risk;
- minimum resolution.

Unknown material rights, an open applicable gate, unresolved material facts, or unknown required evidence remain blocking under the existing `BLOCKED` or `REVISION_REQUIRED` criteria and must not be downgraded to `ADVISORY_ONLY` or a `RISKS`-only warning.

A `RISKS` warning is not rights clearance and never satisfies, waives, downgrades, removes, clears, or displaces any gate or separate flag. It does not clear or displace any separate human-review trigger, including the existing public-release trigger. Publication remains gated until every required review and approval is complete. Actual or material conflicts, applicable mandatory clearances, current `human_review_required: true` flags, protected merge/publication approvals, and Steward/Arbiter authority remain unchanged. Prior decisions remain bound to their evidence and policy; only a fresh Governor decision may supersede them.

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
