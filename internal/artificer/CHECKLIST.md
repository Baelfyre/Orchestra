# Artificer Evaluation Checklist

Use this checklist during every repository audit to evaluate design patterns for potential Orchestra integration.

## Phase 0: Intake and Pre-Verification
- [ ] Confirm target repository matches authorized scope.
- [ ] Verify repository metadata (owner, URL, branch, commit SHA).
- [ ] Inspect license file and record license type.
- [ ] Check if the license is compatible with Orchestra's license (MIT).
- [ ] Confirm no dynamic scripts or packages are downloaded/installed from the target.

## Phase 1: Security Scan
- [ ] Inspect target code for embedded instructions, comments, or README prompts targeting agents.
- [ ] Scan for secret keys, tokens, or endpoints.
- [ ] Verify that files are read statically and never evaluated (`eval()`, `exec()`, or sub-process execution).

## Phase 2: Pattern Analysis
- [ ] Identify candidate design patterns (separating layout, business logic, persistence, and state).
- [ ] Map each candidate pattern to a specific Orchestra specialist domain.
- [ ] Classify extraction type (e.g., `REFERENCE_ONLY`, `ADAPTED_PATTERN`, `CODE_REUSE_REVIEW_REQUIRED`) according to Phase 4 `PATTERN_SCHEMA.json`. (Governance outcomes like `REJECTED` are handled separately).
- [ ] Document specific files, line ranges, and behavioral context for each pattern.

## Phase 3: Governance Mapping
- [ ] Verify that no copied code is added without explicit Governor approval.
- [ ] Ensure attribution blocks are generated if the pattern relies on adapted code.
- [ ] Check if the proposed change requires changes to the Orchestra public manifest (`plugin.json`) — if yes, verify why and flag for review.

## Phase 4: Amalgamation and Proposal (Phase 4 Contracts)
- [ ] Generate the Individual Source Audit JSON record (`AUDIT_REPORT_SCHEMA.json`).
- [ ] Draft the Orchestra-native Evolution Proposal JSON record (`EVOLUTION_PROPOSAL_SCHEMA.json`).
- [ ] Draft independent Governance Decisions (`GOVERNANCE_DECISION_SCHEMA.json`) for items that are blocked, rejected, deferred, or duplicate.
- [ ] Route the proposal to Arbiter for validation check.
- [ ] Route the proposal to Governor and Steward for business and legal clearance.
