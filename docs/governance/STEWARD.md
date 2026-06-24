# The Steward — Reference Summary

> **Authoritative behavior is defined in [`skills/the-steward/SKILL.md`](../../.agents/skills/the-steward/SKILL.md).** This document is a human-facing quick reference only. Do not use it as a behavior source of truth.

The Steward is the business alignment, scope, requirements, and SDLC governance authority. It sits above the Amalgam Conductor and reviews every request before it reaches the Conductor.

## Quick Reference

| Decision | Meaning |
|---|---|
| `APPROVED` | Passes to the Governor |
| `REVISION_REQUIRED` | Returns to requester with findings |
| `BLOCKED` | Conductor cannot proceed |
| `NOT_APPLICABLE` | Trivial request, passes through |

**Risk levels**: `LOW` (objective and scope check), `MEDIUM` (full requirements and acceptance criteria), `HIGH` (stakeholder alignment, traceability, success metrics).

## Boundaries

- Does not implement features.
- Does not provide legal or compliance review (Governor's domain).
- Does not route work to execution skills.
- Cannot be overridden by the Governor.
- Does not assume any specific project context without evidence.

---

*See [GOVERNANCE_LAYER.md](GOVERNANCE_LAYER.md) for the full governance architecture.*
