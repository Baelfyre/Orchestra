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
Phase 4B will introduce deterministic validation for governance records and cross-record relationships, including reviews, decisions, proposals, and promotions. Phase 4A focuses exclusively on the source-intake and pattern contracts and schemas; it does not validate those governance records, decisions, reviews, proposals, or promotions.

## 13. Phase 4C Renderer and Catalog-Gate Responsibilities
Phase 4C will introduce markdown rendering for these records and implement the catalog-gate to prevent unapproved implementations.

## 14. Phase 4.5 Pilot Sources
The canonical Phase 4.5 pilot repositories are strictly defined as:
*   `CristianOlivera1/openhero` (https://github.com/CristianOlivera1/openhero)
*   `usestrix/strix` (https://github.com/usestrix/strix)

**Explicit constraints on pilot sources:**
*   Neither repository is being audited in Phase 4A.
*   No commit SHA is pinned yet.
*   No files are copied.
*   No external code is executed.
*   The repositories will be audited independently after Phase 4 is complete.
