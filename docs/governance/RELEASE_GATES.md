# Release Gates

Release gates enforce governance compliance before any release. **Release Mode** is the strictest governance path in the ecosystem. Formal, comprehensive governance review is mandatory before any release, client delivery, open-source distribution, production deployment, or external publication.

For app, marketplace, and other public software releases, The Governor must also verify the [App Release Compliance Gate](APP_RELEASE_COMPLIANCE_GATE.md).

## Governance Strictness Note

Release Mode usually maps to `GSL-4` or `GSL-5`, depending on public exposure, data sensitivity, compliance sensitivity, and human-review triggers.

`Release Mode` and `production` are related but not synonymous:
- `Release Mode` is the active task intent for release, distribution, deployment, or delivery work.
- `production` is a release-stage lifecycle state in the project context.
- A production issue may still be handled outside Release Mode until a release or distribution step begins, while staging or external-delivery work may still enter Release Mode before production.

## Pre-Release Checklist

| Gate | Authority | Must Pass |
|---|---|---|
| Business alignment verified | The Steward | Yes |
| Scope confirmed | The Steward | Yes |
| Requirements traceable | The Steward | Yes |
| Acceptance criteria met | The Steward | Yes |
| SDLC documentation complete | The Steward | Yes |
| Legal compliance confirmed | The Governor | Yes |
| App Release Compliance Gate reviewed | The Governor | Yes, when applicable |
| Privacy review completed | The Governor | Yes |
| IP/copyright cleared | The Governor | Yes |
| License compatibility confirmed | The Governor | Yes |
| ToS/Privacy Policy updated (if needed) | The Governor | Yes |
| Human legal review completed (if flagged) | The Governor | Yes |
| Security governance satisfied | The Governor | Yes |
| Audit documentation sufficient | The Governor | Yes |
| Access / Visibility Authorization Parity | Arbiter and Overseer | Yes (for release mode & access/visibility tasks) |
| Continuation state verified | Arbiter | Yes |
| Source of truth confirmed | Arbiter | Yes |
| Branch and merge readiness reviewed | Arbiter | Yes |
| QA validation passed | Overseer | Yes |
| No unresolved `BLOCKED` decisions | Governance authorities | Yes |
| No unresolved Arbiter `HOLD` verdicts | Arbiter | Yes |
| No pending `human_review_required` flags | The Governor | Yes |

## Gate Enforcement

- **Release Mode Enforcement**: The Conductor and Governance authorities (The Steward, The Governor, and Arbiter) enforce complete Basis of Review and continuation-state checks for all release activities. Bypassing compliance, scope, validation, or continuity checks is prohibited.
- The Conductor must check for unresolved governance findings before routing release work.
- The Conductor must call Arbiter before merge, pull request, release handoff, or continuation after uncertain state.
- Release-related requests (publish, deploy, tag, distribute, client delivery, or public distribution) require explicit governance clearance.
- For app release workflows, missing privacy, data inventory, retention, deletion, or IP clearance artifacts must result in `BLOCKED`.
- For app release workflows, privacy, terms, data inventory, retention, deletion, account deletion documentation when accounts exist, platform disclosures, third-party processor disclosures, and IP clearance are not optional when applicable.
- High-impact releases require both Steward and Governor `APPROVED` decisions.
- Transition-sensitive releases require Arbiter `READY` or `READY_WITH_MINOR_FIXES`.

## Evidence

Each gate pass should reference the governance review output that cleared it:

```
GATE: license_compatibility
STATUS: PASSED
EVIDENCE: Governor review [timestamp], decision: APPROVED
```

### Access / Visibility Authorization Parity Evidence
Must include:
- named persona proof
- source-of-truth authority source
- UI navigation result
- direct route or screen result
- backend/service authorization result
- known unsupported cases

## Enforcement Limitation

Current enforcement is instruction-level governance. The Conductor must follow the governance gate before planning or routing work, but no runtime blocker exists yet. Runtime enforcement may be added later if CI checks, schema validation, or automated release gates become necessary.

