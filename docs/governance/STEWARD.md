# The Steward - Reference Summary

> **Authoritative behavior is defined in [`skills/the-steward/SKILL.md`](../../skills/the-steward/SKILL.md).** This document is a human-facing quick reference only. Do not use it as a behavior source of truth.

The Steward is the business alignment, scope, requirements, and SDLC governance authority. It sits above the Conductor and reviews every request before it reaches the Conductor.

## Quick Reference

| Decision | Meaning |
|---|---|
| `APPROVED` | Passes to the Governor |
| `REVISION_REQUIRED` | Returns to requester with findings |
| `BLOCKED` | Conductor cannot proceed |
| `NOT_APPLICABLE` | Trivial request, passes through |

**Risk levels**: `LOW` (objective and scope check), `MEDIUM` (full requirements and acceptance criteria), `HIGH` (stakeholder alignment, traceability, success metrics).

## Governance Strictness Levels

The Steward participates according to the derived `GSL` level:
- `GSL-0`: context hygiene only.
- `GSL-1`: light objective, scope, and continuity-hygiene check.
- `GSL-2`: required context, scope, requirements, and SDLC-alignment check.
- `GSL-3`: required full requirements, scope, and documentation alignment review.
- `GSL-4`: required and blocking review for release, business readiness, or other high-impact governed work.
- `GSL-5`: maximum strictness for complete objective, scope, traceability, and documentation readiness before governance-heavy work proceeds.

The Steward owns objectives, scope, requirements, SDLC alignment, and continuity hygiene for sufficient context and documentation to continue safely. Arbiter still owns continuation verdicts, source-of-truth disputes, branch safety, and handoff readiness. The Steward does not own legal/compliance/IP review, implementation, validation execution, or routing.

## Boundaries

- Does not implement features.
- Does not provide legal or compliance review (Governor's domain).
- Does not route work to execution skills.
- Cannot be overridden by the Governor.
- Does not assume any specific project context without evidence.

---

*See [GOVERNANCE_LAYER.md](GOVERNANCE_LAYER.md) for the full governance architecture.*
