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

For release gating, The Governor decides whether security, privacy, and compliance governance is sufficiently addressed to proceed. `Cipher` owns the technical defensive security review, security-control findings, and related remediation boundaries that may feed that release decision.

## Bounded trademark exception evidence (protected amendment proposal)

A single-use, exact-candidate protected governance decision may record an **exception-qualified evidence disposition**, distinct from trademark/IP clearance. The sole initially eligible case is the [Issue #1003 PointCross ORCHESTRA escalation](https://github.com/Baelfyre/Orchestra/issues/1003), applied to the unchanged v1.12.0 candidate head `665ec5536641683eab4c2739fb20b60835a7beed`, tree `e165cbc7687cdf3c115b4077d949030f0914843f`, for public GitHub/IDE plugin source distribution only.

A valid, **separately human-approved** `APPROVE_BOUNDED_EXCEPTION` may be represented as `EXCEPTION_QUALIFIED`, **not `PASS` or `NOT_APPLICABLE`**, for only the named PointCross trademark-review component of `IP/copyright cleared` and `Human legal review completed (if flagged)`. Other intellectual-property clearance and legal compliance requirements remain unchanged. The record must bind the specific control, source, case, owner decision, independent specialist review, subsequent Governor reconsideration, channel, single-use and consumption limits, and expiration; it must explicitly state that trademark clearance has **not** been established.

A `BLOCKED` Governor finding **does not disappear** when an exception is proposed or approved. Governor must separately reconsider and explicitly supersede that finding in a fresh context. Steward and Arbiter must then record their own required decisions; final publication still needs explicit human authority. Unrelated mandatory gates remain enforced; missing owner approval, stale source, other actual IP gaps, or absent review evidence remain blocking. An automated release evidence validator cannot authenticate external decision signatories and must never authorize publication.

This subsection and its related schema/validator only become governing after separately authorized review, standard PR checks, merge and independent readback. They do **not** retroactively exempt issue #991 or approve the owner exception.

## Evidence-First Release Review

The issue [#993](https://github.com/Baelfyre/Orchestra/issues/993) amendment was separately authorized for development on 2026-11-07. This procedure applies only after separately reviewed and authorized integration into the governing branch. It never applies retroactively to release issue #991 or clears existing blockers without fresh release-specific evidence and governing decisions. This is a proportional *review procedure*, not a waiver of any required gate.

For each current Pre-Release Checklist gate, evaluate three independently traceable questions:

1. **Relevance:** Is the obligation `REQUIRED`, or genuinely `NOT_APPLICABLE` under the verified release channel, affected feature, data/processor, and jurisdiction? The record must cite the applicable policy and supporting evidence. Unknown applicability is not N/A, and an unconditional "Yes" gate may not be exempted.
2. **Validation:** Do reproducible technical checks, independent domain findings, and documentation match the exact reviewed candidate, governing policy revision, and required frameworks? Use existing CI evidence once per exact revision, rather than repeating unchanged tests for each specialist. CI does not authenticate human attestations, factual legal claims, actual provider behavior, or rights ownership.
3. **Compliance:** Does that evidence demonstrate the required rule was met? Show the rights, privacy, security, and distribution obligations actually triggered by this release. Do not call an upstream license declaration complete redistribution clearance or a documentation template a completed data inventory.

The read-only evidence projection is `scripts/validate_release_evidence_review.py --record <review.json>`, with schema `machine/schemas/release-evidence-review.v1.schema.json`. It derives the complete gate inventory from the Pre-Release Checklist, rejects missing/duplicate gates, binds evidence to candidate head and current governing policy bytes, and classifies outcomes. Its recorded CI states are assertions requiring an independent GitHub/current-source read before consequential use. A successful command does **not** approve a release.

Within an already valid delegated envelope, use existing `AUTO_CONTINUE` when in-scope technical prerequisites pass, `AUTO_REMEDIATE_AND_REVALIDATE` for deterministic authorized corrections within the existing three-attempt / zero-scope-growth limit, and `WAIT_FOR_EVIDENCE` for missing or stale inputs. After each fix, rebuild exact-head evidence; never recycle earlier CI conclusions. Do not open repetitive human-review loops for a deterministic error that can be safely fixed and retested within granted scope.

Escalate unresolved contradictions, unverifiable owner/host/jurisdiction facts, legal or IP judgments, material risk acceptance, required authority decisions, and failures of the permitted remediation budget. Any policy, validator, or gate change needed to make the *originating blocked candidate* pass follows [Protected Governance Escalation](PROTECTED_GOVERNANCE_ESCALATION_PROTOCOL.md), with an independent decision and fresh execution context. This procedure cannot change the same gates that evaluate it without that protection.

When all applicable evidence is reconciled, produce one concise `EVIDENCE_READY_FOR_FINAL_REVIEW` packet for the designated human release authority. This is readiness for decision, **not** `APPROVED`, merge authority, publication authorization, or a substitute for the Governor/Steward/Arbiter decisions required by the active policy. For v1.12.0, retain all existing blockers until updated attributable review decisions are recorded.

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

