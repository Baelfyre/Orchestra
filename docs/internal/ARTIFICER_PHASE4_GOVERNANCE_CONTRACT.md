# Artificer Phase 4 Governance Contract

## 1. Purpose and Phase 4 Boundaries
This document defines the strict governance contract for Artificer Phase 4. It establishes the separation between raw source evidence and governed decision-making. Phase 4 introduces structured, machine-readable schemas for audit reports, governance decisions, evolution proposals, and promotion records. Artificer remains a non-approving, non-executing orchestrator.

## 2. Separation of Immutable Source Evidence and Governed Review Records
Phase 3 introduced immutable source-intake and pattern records stored within `internal/artificer/records/`. These source bundles represent raw, objective evidence and must not be modified by the governance process.
Governed review records (audit reports, decisions, proposals, and promotions) are managed entirely separately from the immutable source bundles, residing in their own dedicated registries.

## 3. Registry Layouts
The governance registries are strictly isolated:
*   `internal/artificer/reviews/`: Stores `audit-report.json` files organized by bundle ID.
*   `internal/artificer/decisions/`: Stores pattern-specific decision files (`<pattern-slug>.json`) organized by bundle ID.
*   `internal/artificer/proposals/`: Stores `EVOLUTION_PROPOSAL_SCHEMA.json` instances by proposal ID.
*   `internal/artificer/promotions/`: Stores `PROMOTION_RECORD_SCHEMA.json` instances by catalog pattern ID.

## 4. Pattern Classification vs. Governance Decision vs. Promotion Lifecycle
This separation is enforced by the schemas, not merely recommended:
*   **Pattern Classification**: A descriptive property (e.g., `ADAPTED_PATTERN`) belonging to the pattern record itself.
*   **Governance Decision**: The outcome of the review (e.g., `APPROVED`, `REVISION_REQUIRED`) belonging to the decision record.
*   **Promotion Lifecycle**: The status within the Pattern Catalog (e.g., `IMPLEMENTING`, `IMPLEMENTED`) belonging to the promotion record.
`REJECTED`, `DEFERRED`, and `DUPLICATE` are governance concepts and are not valid `PATTERN_SCHEMA.json` classifications.

## 4A. Source-Intake Contract
`default_branch` is required in every source-intake record. `runtime_behavior_tested: true` means only that separately authorized isolated external validation occurred; it never means Artificer executed external code in the Orchestra workspace.

## 5. Finding/Recommendation Separation
Audit reports strictly separate objective findings from remediation recommendations in discrete `finding` and `recommendation` fields.

## 6. Evidence-Bucket Model
Each finding in an audit report requires traceable evidence mapped to specific buckets:
*   `SOURCE_CONFIRMED`
*   `DOCUMENTATION_CLAIM`
*   `STATIC_ANALYSIS`
*   `EXISTING_TEST_EVIDENCE`
*   `RUNTIME_CONFIRMED_BY_AUTHORIZED_EXTERNAL_VALIDATION`
*   `INFERENCE`
*   `UNVERIFIED`

## 7. Specialist Routing
Assigned specialists own the implementation and specific review components (e.g., security, docs). Artificer routes to these specialists but does not bypass them.

## 8. Governance Authority
*   **Arbiter** reviews evidence and duplicate concerns.
*   **Governor** handles licensing and IP clearance.
*   **Steward** handles scope and business alignment.
*   **Maintainer** gives the final decision.
*   **Artificer never approves its findings.**

## 9. Manual Pattern Catalog Promotion
Promotion into the Pattern Catalog is entirely manual. Only governance-approved patterns may be manually promoted. Artificer will not automatically update the Catalog.

## 10. Specialist-Owned Implementation
Implementation status belongs to the designated implementation specialist and must never be controlled by Artificer.

## 11. No Clone, No Install, No Execution, No Automatic Cherry-Pick
Inspect the external repository through an approved read-only source connector at a pinned commit SHA.
Do not clone, fetch, install, compile, or execute the external repository inside the Orchestra workspace.
There is no automatic cherry-picking of source code.

## 12. Phase 4B Validator Responsibilities
Phase 4B provides deterministic validation for governance records and cross-record relationships, including reviews, decisions, proposals, and promotions. It validates only committed contracts and never rewrites source bundles, executes external code, or grants Artificer approval authority. Empty governance registries remain valid.

## 13. Phase 4C Renderer and Catalog-Gate Responsibilities
Phase 4C-A renders a validated `audit-report.json` record as deterministic
Markdown. Rendering is read-only, writes only to standard output, and never
updates governance JSON, source evidence, or `PATTERN_CATALOG.md`. Rendered
Markdown is not governance authority; validated JSON records remain canonical.

Phase 4C-B separately owns Pattern Catalog synchronization and its governance
gate. Promotion remains manual. Promotion JSON remains canonical. The Catalog
is only a deterministic human-readable projection and the validator never edits
the Catalog. Every validated promotion requires exactly one Catalog index row
and exactly one Catalog entry. No ungoverned Catalog row or entry is allowed.
Catalog lifecycle status mirrors the promotion record exactly. `--print-expected`
is preview-only and writes only to standard output. Artificer receives no
approval, implementation, or Catalog authority.

## 14. Phase 4.5 Pilot Sources
The canonical Phase 4.5 pilot repositories are strictly defined as:
*   `CristianOlivera1/openhero` (https://github.com/CristianOlivera1/openhero)
*   `usestrix/strix` (https://github.com/usestrix/strix)

**Explicit constraints on pilot sources:**
*   Phase 4C-B is complete through PR #166.
*   OpenHero Phase 4.5-A is completed through PR #167 and remains frozen for this audit.
*   Strix is the active Phase 4.5-B pilot and is pinned to commit `09872744f5a9d3ffad750478f823e656ac1a7c88`.
*   The Strix pilot has a heightened no-execution boundary for offensive-security source inspection.
*   Offensive skills, payloads, exploit directories, and proof-of-concept content are excluded from inspection.
*   No files are copied.
*   No external code is executed.
*   The audit implies no governance outcome, approval, proposal, promotion, or Pattern Catalog action.
*   Both pilot audits remain independently reviewable.

## Phase 5 Governance Decision Records
Phase 5 records governance outcomes separately from immutable source evidence. Phase 5A provides independent read-only reviewer recommendations; Phase 5B records Maintainer-adopted governance decisions.
*   Phase 5B-A covers only OpenHero decisions.
*   Phase 5B-B covers only Strix decisions and requires Governor review for every record.
*   Decision records are created only in `internal/artificer/decisions/` and reference immutable pattern records and audit reports.
*   Approved `REFERENCE_ONLY` patterns must use `implementation_restriction: CONCEPT_ONLY`.
*   Approved Strix `REFERENCE_ONLY` decisions use `implementation_restriction: CONCEPT_ONLY`.
*   The Strix `OUT_OF_SCOPE` fail-open prompt-rendering anti-pattern is rejected with `implementation_restriction: IMPLEMENTATION_BLOCKED`.
*   `OUT_OF_SCOPE` patterns cannot receive `APPROVED` status; they must be deferred, rejected, or blocked.
*   Governor status `NOT_REQUIRED` is invalid for Strix records.
*   Apache-2.0 compatibility does not automatically authorize source reuse.
*   Governor approval accepts the governance disposition and restriction only; it does not approve source, prompt, payload, exploit, media, documentation expression, or implementation reuse.
*   Direct source adaptation requires separate notice, attribution, patent, distribution, dependency, and reuse review.
*   Decision creation does not create a proposal, promotion, Pattern Catalog entry, or implementation authority.
*   Phase 5 records do not modify immutable source-intake, pattern, or audit records.
*   Phase 5 decision record creation is local and governed; it does not imply external source execution or code reuse authorization.
