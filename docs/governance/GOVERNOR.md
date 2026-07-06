# The Governor — Reference Summary

> **Authoritative behavior is defined in [`skills/the-governor/SKILL.md`](../../.agents/skills/the-governor/SKILL.md).** This document is a human-facing quick reference only. Do not use it as a behavior source of truth.

The Governor is the legal, compliance, privacy, IP, copyright, and licensing governance authority. It sits above the Conductor and reviews every request after the Steward approves it.

## Quick Reference

| Decision | Meaning |
|---|---|
| `APPROVED` | Passes to the Conductor |
| `REVISION_REQUIRED` | Returns with remediation steps |
| `BLOCKED` | Conductor cannot proceed |
| `NOT_APPLICABLE` | No compliance concerns identified |

**Risk levels**: `LOW` (lightweight), `MEDIUM` (standard), `HIGH` (expanded with human review).

Sets `human_review_required: true` when legal interpretation is uncertain, regulatory applicability is unclear, license compatibility cannot be confirmed, or public release has compliance implications.

## Release Mode App Compliance

For Release Mode app workflows, The Governor should review the [App Release Compliance Gate](APP_RELEASE_COMPLIANCE_GATE.md).

Missing required privacy, data inventory, retention, deletion, account deletion documentation when accounts exist, platform disclosures, or IP clearance artifacts should return `REVISION_REQUIRED` or `BLOCKED`, depending on release context and severity.

## Boundaries

- Does not provide legal advice.
- Does not implement features.
- Does not review business alignment (Steward's domain).
- Does not route work to execution skills.
- Cannot be overridden by the Conductor.

---

*See [GOVERNANCE_LAYER.md](GOVERNANCE_LAYER.md) for the full governance architecture.*
