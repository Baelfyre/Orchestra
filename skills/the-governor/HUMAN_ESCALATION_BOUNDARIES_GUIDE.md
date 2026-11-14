<!-- @codebase_provenance_JEO -->
# Human Escalation Boundaries Guide

Load this guide when legal, regulatory, privacy, licensing, IP, contractual, or policy uncertainty may affect a governed transition.

## Escalate a Decision, Not a Topic

An escalation packet should state:

- the exact operational decision that cannot safely proceed;
- the unresolved interpretation or risk-acceptance question;
- affected jurisdiction, agreement, policy, license, or rights holder;
- current authoritative sources and their version/effective dates;
- verified project facts, assumptions, and missing facts;
- plausible options and technical/business consequences without recommending legal advice;
- deadline or transition date when real;
- human role needed, such as maintainer, privacy lead, licensing counsel, or qualified local counsel;
- safe interim state and actions that remain permitted.

Avoid "legal review needed" without a decision question.

## Required Human Boundaries

Set `human_review_required: true` when material uncertainty remains about applicability, interpretation, license compatibility, ownership, contractual permission, privacy obligation, required notice/terms, public claim, or risk acceptance. Also escalate when authoritative sources conflict or cannot be obtained.

Do not escalate solely because a project mentions legal, health, finance, employment, education, AI, or personal data. First identify the concrete fact and unresolved decision.

## Safe Interim Dispositions

- `REVISION_REQUIRED`: evidence or project facts can be completed without legal interpretation.
- `BLOCKED`: a prohibited or clearly incompatible condition prevents the transition.
- `APPROVED` with constraints: current scoped posture is acceptable and no material uncertainty remains.
- `human_review_required: true`: human authority or qualified interpretation is necessary before the named decision.

Governor approval is not release, publication, policy activation, deployment, or risk-acceptance authority.

## Re-entry and Expiry

Bind the disposition to the reviewed facts, source versions, effective dates, scope, and release state. Re-enter when any of these change or when the review expiry/checkpoint is reached. A prior legal or compliance review must not be treated as timeless approval.

Record the human decision, decision maker, date, constraints, and source packet. Do not rewrite the earlier escalation; link a superseding record.

## Proportional finding identity and evidence reuse

For each material finding, record: the requirement/control; stable identity derived from requirement/control + subject + action/distribution scope + evidence scope; exact operational decision and lifecycle stage; candidate/tree and source/asset/evidence identity; intended channel/distribution; risk/materiality/uncertainty and known/missing facts; authoritative evidence references with source version/effective date; source-backed closure evidence or corrective action; named human decision owner; and invalidation triggers, expiry, and any required periodic source re-check. If legal interpretation or risk acceptance is needed, record the question for the human owner; the Governor does not provide binding legal conclusions or accept owner risk. Classify applicability across ideation/read-only inspection, isolated implementation/testing, local commit/draft review, branch push, protected merge, public installation/distribution, and release. This is an applicability map only and grants no authorization. This guide's [Release-scoped rights applicability section](#release-scoped-rights-applicability) defines the release-only rights scope; the current-unit true-flag rule remains governed by the shared Governance Decision Protocol (docs/governance/GOVERNANCE_DECISION_PROTOCOL.md#shared-gate-contract). Reuse evidence only when it is verified, unchanged, current, and still applicable; record any required periodic external-source re-check. Re-enter on changes to candidate/tree, source, asset, evidence scope, use/distribution/channel, jurisdiction, governing source/version/effective date, material facts, or expiry. Repeated unchanged findings remain open and gated; consolidate the exact unanswered questions, source-backed closure evidence/corrective action, and owner in one list. No retry/loop-suppression count approves, dismisses, or waives a finding. Human owner approval remains required for policy activation and release; Governor cannot approve its own exception; Steward and Arbiter retain independent decisions. Owner-attested AI generation, candidate hash, or visual approval does not establish third-party rights, license, or trademark clearance; missing sources are NOT_FOUND and unknown facts remain UNKNOWN. An owner-supplied photo hash proves file identity only; it does not establish that the photo was the exact AI input or prove the final-work lineage, and a visible HONOR X9b watermark is a provenance question, not presumed third-party infringement. Public release requires the `IP/copyright cleared` release gate to pass, any required human review to be complete, and all required publication approvals to be recorded. Unsupported, unparticularized AI-output similarity concerns or inability to reconstruct every intermediate AI-generation step alone may remain a scoped `RISKS` warning only after proportionate review, when no concrete conflict or material uncertainty remains, every applicable gate independently passes, and no separate `human_review_required` flag is pending. Unknown required evidence, unresolved material facts, or concrete rights conflicts remain blocking; this does not claim or grant rights clearance, and deferring or restricting use does not itself establish clearance.

## Release-scoped rights applicability

A rights finding scoped to public distribution/release blocks that release decision and actions dependent on its clearance. It does not automatically block a separate non-protected read-only or isolated implementation/testing unit when that unit has separate current authorization and its operating mode, envelope/phase, allowed paths, baseline, applicable requirements, and security/policy gates permit the work, and it does not exercise the blocked publication/release path. Keep the finding open; local work is not rights clearance or permission to commit, push, merge, release, or publish. Lifecycle contexts in the Governor applicability record classify scope only and grant no execution authority; existing mode, authorization, protected-path, security, and Arbiter gates remain. A human_review_required: true in the current unit's active governance evidence still pauses that unit under the shared protocol. This section does not filter, downgrade, or clear a true flag. Ideation, Prototype, Implementation, Audit, and Release mode requirements continue.
