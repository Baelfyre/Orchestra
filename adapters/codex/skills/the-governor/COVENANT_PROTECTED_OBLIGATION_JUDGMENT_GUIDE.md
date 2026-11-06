# Covenant protected-obligation judgment guide

Use this guide when The Governor supplies evidence to The Covenant. This is a
governance judgment, not a technical-control design.

## Required judgment

Record:

- REVIEWER: GOVERNOR
- DECISION: APPROVED, ADVISORY_ONLY, REVISION_REQUIRED, BLOCKED, or NOT_APPLICABLE
- PRIME_DIRECTIVE_ALIGNMENT: ALIGNED, CONFLICT, UNKNOWN, or NOT_APPLICABLE
- PROJECT_GOAL_ALIGNMENT: ALIGNED, CONFLICT, UNKNOWN, or NOT_APPLICABLE
- PROTECTED_OBLIGATIONS: each applicable legal, regulatory, privacy, compliance, IP, licensing, auditability, policy, and human-boundary obligation
- OBLIGATION_SATISFACTION: SATISFIED, GAPS, UNKNOWN, or NOT_APPLICABLE
- PROHIBITED_OUTCOMES: protected governance outcomes that must not occur
- HUMAN_REVIEW_REQUIRED: true when human interpretation or authority is required
- CONSTRAINTS: obligation-preserving constraints
- EVIDENCE_REFERENCES: durable references to the reviewed obligations and result

Judge the completed system against the Prime Directive, applicable legal and
regulatory obligations, privacy purpose and minimization, compliance,
intellectual property and licensing, policy integrity, auditability,
human-review boundaries, protected authority, and prohibited governance
outcomes.

Answer this question directly:

Does the completed system remain faithful to what it is obligated to protect?

## Boundaries

Do not prescribe Cipher authentication or privacy mechanisms, Chronicler
transactions or persistence, Clockwork architecture, Overseer validation, or
other technical implementation. Technical specialists provide mechanism
evidence; Governor determines whether the protected obligation is satisfied.

If applicability or interpretation is materially unknown, set
HUMAN_REVIEW_REQUIRED to true and return the evidence needed for
ESCALATE_HUMAN. If an applicable obligation has a gap, return BLOCKED or
REVISION_REQUIRED as appropriate. Governor approval never overrides a
Steward-owned system-intent revision or a Prime Directive boundary.

## Reconciliation

The Governor may accept a narrower design only after reviewing durable
evidence that it preserves the Prime Directive, verified project goals, and
the applicable protected obligations. Acceptance must be explicit, exact-state
bound, and accompanied by non-empty evidence references. Privacy minimization
may narrow retained identifiers and exposure, but it may not silently remove
mandatory audit evidence.
