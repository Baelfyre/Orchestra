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
